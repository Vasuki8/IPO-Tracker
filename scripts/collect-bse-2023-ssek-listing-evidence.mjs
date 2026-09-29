import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {auditNextBatch,TARGETS} from './audit-bse-2023-ssek-identities.mjs';

export const ROOT=fileURLToPath(new URL('../',import.meta.url));
export const PLAN='data/discovery/bse-2023-ssek-listing-source-plan-2026-09-29.json';
export const FIELD_REVIEW='data/discovery/bse-2023-ssek-field-review-2026-09-29.json';
const MAX_SOURCE_BYTES=70*1024*1024,MAX_TOTAL_BYTES=240*1024*1024;
const CODES=TARGETS.map(t=>t.code);
const APPROVED_URLS=new Map([
 ['544059','https://www.bseindia.com/xml-data/corpfiling/AttachHis/7ef41283-ff90-4b34-ab83-815414cc3de9.pdf'],
 ['543970','https://www.bseindia.com/xml-data/corpfiling/AttachHis/5785622d-c982-49ae-88ac-86ef96b89feb.pdf'],
 ['543895','https://exhiconevents.in/wp-content/uploads/2025/06/Annual-Report-FY-2023-24.pdf'],
 ['543953','https://www.khazanchi.co.in/files/Khazanchi%20Jewellers%20AR24.pdf']
]);
const sha256=b=>createHash('sha256').update(b).digest('hex');
const gitBlobSha=b=>{const bytes=Buffer.from(b);return createHash('sha1').update(Buffer.from('blob '+bytes.length+'\0')).update(bytes).digest('hex');};
const req=(ok,message)=>{if(!ok)throw new Error(message);};
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const stamp=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(s)&&Number.isFinite(Date.parse(s));
function approvedSource(code,value){
 req(APPROVED_URLS.get(code)===value,'unapproved_listing_source');
 const u=new URL(value);req(u.protocol==='https:'&&!u.username&&!u.password&&!u.search&&!u.hash&&u.href===value,'unsafe_listing_source_url');
 return value;
}
export function validatePlan(planBytes,{fieldReviewBytes}={}){
 const p=JSON.parse(Buffer.from(planBytes).toString('utf8'));
 req(p?.schema_version==='1.0.0'&&p.status==='listing_source_collection_only'&&p.batch_id==='bse-2023-ssek-listing','invalid_listing_source_plan');
 req(p.publication_import_allowed===false&&p.semantic_review_complete===false&&p.complete_indian_ipo_universe===false,'unsafe_listing_source_scope');
 req(p.field_review?.path===FIELD_REVIEW&&/^[a-f0-9]{40}$/.test(p.field_review.git_blob_sha),'invalid_field_review_binding');
 req(Array.isArray(p.issuers)&&same(p.issuers.map(i=>i?.discovery_bse_scrip_code),CODES),'unexpected_listing_batch_identity');
 const rows=new Set();
 for(const i of p.issuers){
  req(Number.isSafeInteger(i.source_row_index)&&i.source_row_index>=0&&!rows.has(i.source_row_index),'invalid_source_row');rows.add(i.source_row_index);
  req(typeof i.candidate_id==='string'&&i.candidate_id.length>5&&typeof i.issuer_name==='string'&&i.issuer_name.length>5,'invalid_issuer_identity');
  approvedSource(i.discovery_bse_scrip_code,i.source_url);
  req(i.document_type==='annual_report'&&i.reporting_period==='FY2023-24'&&typeof i.document_identity==='string'&&i.document_identity.includes('Annual Report'),'invalid_document_identity');
  req(i.listing_date===null&&i.verified_bse_scrip_code===null&&i.board===null,'semantic_value_laundered_into_collection_plan');
 }
 if(fieldReviewBytes){
  req(gitBlobSha(fieldReviewBytes)===p.field_review.git_blob_sha,'field_review_blob_mismatch');
  const r=JSON.parse(Buffer.from(fieldReviewBytes).toString('utf8'));
  req(r.status==='reviewed_prospectus_terms_listing_evidence_pending'&&r.prospectus_terms_reviewed===true&&r.ipo_release_review_complete===false&&r.publication_import_allowed===false,'field_review_not_at_listing_boundary');
  req(same(r.actions.map(a=>a.discovery_bse_scrip_code),CODES)&&r.actions.every(a=>a.terms?.listing_date?.value===null&&a.terms?.listing_date?.status==='missing'),'field_review_listing_state_changed');
 }
 return p;
}
async function limitedBody(response,max){
 if(!response.body){const b=Buffer.from(await response.arrayBuffer());req(b.length<=max,'source_size_limit');return b;}
 const chunks=[];let length=0;
 for await(const chunk of response.body){length+=chunk.length;req(length<=max,'source_size_limit');chunks.push(Buffer.from(chunk));}
 return Buffer.concat(chunks);
}
export async function collectListingEvidence({planBytes,fieldReviewBytes,evidenceDir,fetchImpl=fetch,clock=()=>new Date().toISOString()}){
 const p=validatePlan(planBytes,{fieldReviewBytes});
 fs.mkdirSync(evidenceDir);
 fs.writeFileSync(path.join(evidenceDir,'source-plan.json'),planBytes,{flag:'wx'});
 fs.writeFileSync(path.join(evidenceDir,'field-review-snapshot.json'),fieldReviewBytes,{flag:'wx'});
 const started=clock(),documents=[];let total=0;
 for(const i of p.issuers){
  const url=approvedSource(i.discovery_bse_scrip_code,i.source_url);
  const d={code:i.discovery_bse_scrip_code,candidate_id:i.candidate_id,issuer_name:i.issuer_name,url,document_identity:i.document_identity,document_type:i.document_type,reporting_period:i.reporting_period,requested_at:clock(),collected_at:null,http_status:null,content_type:null,accepted:false,error:null,evidence_file:null,response_sha256:null,response_bytes:0};
  let body=null;
  try{
   const remaining=MAX_TOTAL_BYTES-total;req(remaining>0,'total_size_limit');
   const headers={'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36','accept':'application/pdf','cache-control':'no-cache'};
   if(new URL(url).hostname==='www.bseindia.com')headers.referer='https://www.bseindia.com/';
   const response=await fetchImpl(url,{redirect:'error',signal:AbortSignal.timeout(90000),headers});
   d.http_status=response.status;d.content_type=response.headers?.get?.('content-type')??null;
   req(!response.url||response.url===url,'unexpected_final_url');
   body=await limitedBody(response,Math.min(MAX_SOURCE_BYTES,remaining));
   req(response.status===200,'http_status');
   req(body.length>5&&body.subarray(0,5).toString('ascii')==='%PDF-','unexpected_body_type');
   d.accepted=true;
  }catch(e){d.error=['source_size_limit','total_size_limit','unexpected_final_url','http_status','unexpected_body_type'].includes(e.message)?e.message:'network_error';}
  if(body?.length){
   d.evidence_file=i.discovery_bse_scrip_code+'-annual-2023-24.'+(d.accepted?'pdf':'response');
   fs.writeFileSync(path.join(evidenceDir,d.evidence_file),body,{flag:'wx'});
   d.response_sha256=sha256(body);d.response_bytes=body.length;total+=body.length;
  }
  d.collected_at=clock();documents.push(d);
 }
 const accepted=documents.filter(d=>d.accepted).length;
 const receipt={schema_version:'1.0.0',collector_version:'1.0.0',batch_id:p.batch_id,status:accepted===CODES.length?'complete':'partial',plan_path:PLAN,plan_sha256:sha256(planBytes),field_review_path:FIELD_REVIEW,field_review_git_blob_sha:p.field_review.git_blob_sha,collection_started_at:started,collection_completed_at:clock(),source_documents_expected:CODES.length,source_documents_accepted:accepted,total_response_bytes:total,publication_import_allowed:false,semantic_review_complete:false,complete_indian_ipo_universe:false,documents};
 fs.writeFileSync(path.join(evidenceDir,'source-receipt.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
 return receipt;
}
async function main(){
 const args=process.argv.slice(2);req(args.length===1&&args[0].startsWith('--out='),'use --out=ABSOLUTE_NEW_DIRECTORY');
 const dir=args[0].slice(6);req(path.isAbsolute(dir),'absolute_evidence_directory_required');
 const planBytes=fs.readFileSync(path.join(ROOT,PLAN)),fieldReviewBytes=fs.readFileSync(path.join(ROOT,FIELD_REVIEW));
 validatePlan(planBytes,{fieldReviewBytes});
 const identity=auditNextBatch(ROOT);req(same(identity.next_bounded_review_codes,CODES),'listing_batch_no_longer_next');
 fs.mkdirSync(path.dirname(dir),{recursive:true});
 const receipt=await collectListingEvidence({planBytes,fieldReviewBytes,evidenceDir:dir});
 const preflight={...identity,checked_at:new Date().toISOString(),repository_ref:process.env.GITHUB_SHA??null,publication_import_allowed:false};
 fs.writeFileSync(path.join(dir,'identity-preflight.json'),JSON.stringify(preflight,null,2)+'\n',{flag:'wx'});
 console.log(JSON.stringify({status:receipt.status,accepted:receipt.source_documents_accepted,expected:CODES.length,bytes:receipt.total_response_bytes,identity_holds:identity.identity_holds,publication_import_allowed:false},null,2));
 if(receipt.status!=='complete')process.exitCode=1;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href)main().catch(e=>{console.error(e.message);process.exitCode=1;});
