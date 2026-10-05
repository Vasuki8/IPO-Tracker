import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';

const ROOT=fileURLToPath(new URL('../',import.meta.url));
export const PLAN='data/discovery/bse-2023-mish-source-plan-2026-10-05.json';
const QUEUE='data/discovery/bse-2023-review-queue-2026-09-28.json';
const PROGRESS='data/discovery/bse-2023-review-progress-2026-09-28.json';
const CODE='544015';
const MAX_SOURCE_BYTES=80*1024*1024;
const MAX_TOTAL_BYTES=140*1024*1024;
const sha=b=>createHash('sha256').update(b).digest('hex');
const req=(ok,message)=>{if(!ok)throw new Error(message);};
const stamp=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(s)&&Number.isFinite(Date.parse(s));
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const EXPECTED_URLS=new Map([
 ['issuer_investor_relations','https://mishindia.com/investor-relations/'],
 ['final_prospectus','https://mishindia.com/Investor_Assets/Initial%20Public%20Offer/Prospectus_of_Mish_Designs_Limited.pdf'],
 ['bse_annual_report_2023_24','https://www.bseindia.com/xml-data/corpfiling/AttachHis/3d4860b3-2d30-4edc-8430-f6181ad45bfd.pdf'],
]);
const EXPECTED_ROLES={
 issuer_investor_relations:['Mish Designs Limited','official_issuer_investor_relations','html'],
 final_prospectus:['Mish Designs Limited','final_prospectus','pdf'],
 bse_annual_report_2023_24:['BSE Limited','actual_listing_and_identity','pdf'],
};

function exactKeys(value,expected,label){
 req(value&&typeof value==='object'&&!Array.isArray(value),label+'_object');
 req(same(Object.keys(value).sort(),[...expected].sort()),label+'_fields');
}
function exactSource(source){
 exactKeys(source,['key','authority','role','kind','url'],'source');
 const expected=EXPECTED_ROLES[source.key];req(expected,'unknown_source_key');
 req(source.authority===expected[0]&&source.role===expected[1]&&source.kind===expected[2],'source_role_mismatch:'+source.key);
 req(source.url===EXPECTED_URLS.get(source.key),'source_url_mismatch:'+source.key);
 const u=new URL(source.url);req(u.protocol==='https:'&&!u.username&&!u.password&&!u.search&&!u.hash,'unsafe_source_url');
 if(source.key==='issuer_investor_relations')req(u.hostname==='mishindia.com'&&u.pathname==='/investor-relations/','issuer_landing_path');
 if(source.key==='final_prospectus')req(u.hostname==='mishindia.com'&&decodeURIComponent(u.pathname)==='/Investor_Assets/Initial Public Offer/Prospectus_of_Mish_Designs_Limited.pdf','prospectus_path');
 if(source.key==='bse_annual_report_2023_24')req(u.hostname==='www.bseindia.com'&&/^\/xml-data\/corpfiling\/AttachHis\/[a-f0-9-]+\.pdf$/.test(u.pathname),'bse_report_path');
 return source;
}
export function validatePlan(planBytes,{queueBytes}={}){
 const p=JSON.parse(Buffer.from(planBytes).toString('utf8'));
 exactKeys(p,['schema_version','status','batch_id','source_queue','source_queue_sha256','discovery_source_collected_at','publication_import_allowed','semantic_review_complete','complete_indian_ipo_universe','issuer','notes'],'plan');
 req(p.schema_version==='1.0.0'&&p.status==='source_collection_only'&&p.batch_id==='bse-2023-mish','invalid_plan');
 req(p.source_queue===QUEUE&&/^[a-f0-9]{64}$/.test(p.source_queue_sha256)&&stamp(p.discovery_source_collected_at),'invalid_queue_reference');
 req(p.publication_import_allowed===false&&p.semantic_review_complete===false&&p.complete_indian_ipo_universe===false,'unsafe_plan_scope');
 exactKeys(p.issuer,['discovery_bse_scrip_code','source_row_index','issuer_name','sources'],'issuer');
 req(p.issuer.discovery_bse_scrip_code===CODE&&p.issuer.source_row_index===27&&p.issuer.issuer_name==='Mish Designs Limited','unexpected_issuer_identity');
 req(Array.isArray(p.issuer.sources)&&p.issuer.sources.length===3,'invalid_sources');
 req(same(p.issuer.sources.map(s=>s.key),[...EXPECTED_URLS.keys()]),'source_order_or_identity');
 p.issuer.sources.forEach(exactSource);
 req(Array.isArray(p.notes)&&p.notes.length>=4&&p.notes.every(n=>typeof n==='string'&&n.length>20),'invalid_plan_notes');
 if(queueBytes){
  req(sha(queueBytes)===p.source_queue_sha256,'source_queue_hash_mismatch');
  const q=JSON.parse(Buffer.from(queueBytes).toString('utf8'));
  req(q.source_year===2023&&q.source_collected_at===p.discovery_source_collected_at&&q.auto_import_allowed===false&&Array.isArray(q.rows),'invalid_source_queue');
  const hits=q.rows.filter(r=>r.bse_scrip_code===CODE);
  req(hits.length===1&&hits[0].source_row_index===27&&hits[0].issuer_name==='Mish Designs Limited'&&hits[0].disposition==='awaiting_review','source_queue_identity_mismatch');
 }
 return p;
}
function bodyType(bytes,kind){
 if(kind==='pdf')return bytes.subarray(0,5).toString('ascii')==='%PDF-';
 return /^\s*(?:\uFEFF)?\s*<(?:!doctype\s+html|html)(?:\s|>)/i.test(bytes.subarray(0,2048).toString('utf8'));
}
function landingLinksProspectus(html,prospectusUrl){
 for(const match of html.matchAll(/href\s*=\s*["']([^"']+)["']/gi)){
  try{
   const url=new URL(match[1].replace(/&amp;/g,'&'),'https://mishindia.com/investor-relations/');
   if(url.href===prospectusUrl)return true;
  }catch{}
 }
 return false;
}
async function limitedBody(response,max){
 if(!response.body){const b=Buffer.from(await response.arrayBuffer());req(b.length<=max,'source_size_limit');return b;}
 const chunks=[];let length=0;
 for await(const chunk of response.body){length+=chunk.length;req(length<=max,'source_size_limit');chunks.push(Buffer.from(chunk));}
 return Buffer.concat(chunks);
}
function expectedSources(p){return p.issuer.sources.map(s=>({...s}));}

export async function collectEvidence({planBytes,evidenceDir,fetchImpl=fetch,clock=()=>new Date().toISOString(),maxSourceBytes=MAX_SOURCE_BYTES,maxTotalBytes=MAX_TOTAL_BYTES}){
 const p=validatePlan(planBytes);
 req(Number.isSafeInteger(maxSourceBytes)&&maxSourceBytes>0&&maxSourceBytes<=MAX_SOURCE_BYTES,'invalid_source_size_limit');
 req(Number.isSafeInteger(maxTotalBytes)&&maxTotalBytes>0&&maxTotalBytes<=MAX_TOTAL_BYTES,'invalid_total_size_limit');
 fs.mkdirSync(evidenceDir);
 fs.writeFileSync(path.join(evidenceDir,'source-plan.json'),planBytes,{flag:'wx'});
 const started=clock(),documents=[];let total=0;
 for(const source of expectedSources(p)){
  const d={key:source.key,authority:source.authority,role:source.role,kind:source.kind,url:source.url,requested_at:clock(),collected_at:null,http_status:null,content_type:null,accepted:false,error:null,evidence_file:null,response_sha256:null,response_bytes:0};
  let body=null;
  try{
   const remaining=maxTotalBytes-total;req(remaining>0,'total_size_limit');
   const response=await fetchImpl(source.url,{redirect:'error',signal:AbortSignal.timeout(60000),headers:{
    'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
    'accept':source.kind==='pdf'?'application/pdf,application/octet-stream;q=0.9,*/*;q=0.1':'text/html,application/xhtml+xml;q=0.9,*/*;q=0.1',
    'cache-control':'no-cache',
    'referer':source.key==='bse_annual_report_2023_24'?'https://www.bseindia.com/':'https://mishindia.com/'
   }});
   d.http_status=response.status;d.content_type=response.headers?.get?.('content-type')??null;
   req(!response.url||response.url===source.url,'unexpected_final_url');
   body=await limitedBody(response,Math.min(maxSourceBytes,remaining));
   req(response.status===200,'http_status');req(body.length>0&&bodyType(body,source.kind),'unexpected_body_type');
   d.accepted=true;
  }catch(e){
   d.error=['source_size_limit','total_size_limit','unexpected_final_url','http_status','unexpected_body_type'].includes(e.message)?e.message:'network_error';
  }
  if(body?.length){
   const extension=d.accepted?source.kind:'response';
   d.evidence_file=source.key+'.'+extension;
   fs.writeFileSync(path.join(evidenceDir,d.evidence_file),body,{flag:'wx'});
   d.response_sha256=sha(body);d.response_bytes=body.length;total+=body.length;
  }
  d.collected_at=clock();documents.push(d);
 }
 const landing=documents.find(d=>d.key==='issuer_investor_relations');
 const prospectus=p.issuer.sources.find(s=>s.key==='final_prospectus').url;
 const landingBinding=Boolean(landing?.accepted&&landingLinksProspectus(fs.readFileSync(path.join(evidenceDir,landing.evidence_file),'utf8'),prospectus));
 const accepted=documents.filter(d=>d.accepted).length;
 const receipt={schema_version:'1.0.0',collector_version:'1.0.0',batch_id:p.batch_id,status:accepted===3&&landingBinding?'complete':'partial',plan_path:PLAN,plan_sha256:sha(planBytes),source_queue:p.source_queue,source_queue_sha256:p.source_queue_sha256,discovery_source_collected_at:p.discovery_source_collected_at,discovery_source_refetched:false,collection_started_at:started,collection_completed_at:clock(),source_documents_expected:3,source_documents_accepted:accepted,total_response_bytes:total,publication_import_allowed:false,semantic_review_complete:false,complete_indian_ipo_universe:false,issuer_landing_links_prospectus:landingBinding,documents,workflow_artifact:null};
 validateReceipt(receipt,planBytes,evidenceDir);
 fs.writeFileSync(path.join(evidenceDir,'source-receipt.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
 return receipt;
}
export function validateReceipt(r,planBytes,evidenceDir){
 const p=validatePlan(planBytes),expected=expectedSources(p);
 req(r?.schema_version==='1.0.0'&&r.collector_version==='1.0.0'&&r.batch_id===p.batch_id&&r.plan_path===PLAN&&r.plan_sha256===sha(planBytes),'receipt_plan_mismatch');
 req(r.publication_import_allowed===false&&r.semantic_review_complete===false&&r.complete_indian_ipo_universe===false&&r.discovery_source_refetched===false,'unsafe_receipt_scope');
 req(r.source_queue===p.source_queue&&r.source_queue_sha256===p.source_queue_sha256&&r.discovery_source_collected_at===p.discovery_source_collected_at,'receipt_queue_mismatch');
 req(stamp(r.collection_started_at)&&stamp(r.collection_completed_at)&&r.collection_started_at<=r.collection_completed_at,'invalid_collection_clock');
 req(Array.isArray(r.documents)&&r.documents.length===3&&r.source_documents_expected===3,'invalid_receipt_documents');
 req(sha(fs.readFileSync(path.join(evidenceDir,'source-plan.json')))===r.plan_sha256,'retained_plan_mismatch');
 let total=0,accepted=0,last=r.collection_started_at;
 for(let i=0;i<expected.length;i++){
  const s=expected[i],d=r.documents[i];req(d.key===s.key&&d.authority===s.authority&&d.role===s.role&&d.kind===s.kind&&d.url===s.url,'receipt_source_mismatch');
  req(stamp(d.requested_at)&&stamp(d.collected_at)&&last<=d.requested_at&&d.requested_at<=d.collected_at&&d.collected_at<=r.collection_completed_at,'invalid_document_clock');last=d.collected_at;
  req(typeof d.accepted==='boolean'&&Number.isSafeInteger(d.response_bytes)&&d.response_bytes>=0&&d.response_bytes<=MAX_SOURCE_BYTES,'invalid_document_metadata');
  req(d.accepted?(d.http_status===200&&d.error===null):['network_error','source_size_limit','total_size_limit','unexpected_final_url','http_status','unexpected_body_type'].includes(d.error),'invalid_document_result');
  if(d.response_bytes){
   const extension=d.accepted?s.kind:'response';req(d.evidence_file===s.key+'.'+extension,'unsafe_evidence_file');
   const b=fs.readFileSync(path.join(evidenceDir,d.evidence_file));req(b.length===d.response_bytes&&sha(b)===d.response_sha256,'response_bytes_mismatch');if(d.accepted)req(bodyType(b,s.kind),'accepted_body_type_mismatch');
  }else req(!d.accepted&&d.evidence_file===null&&d.response_sha256===null,'missing_response_bytes');
  total+=d.response_bytes;if(d.accepted)accepted++;
 }
 req(total===r.total_response_bytes&&total<=MAX_TOTAL_BYTES&&accepted===r.source_documents_accepted,'receipt_totals_mismatch');
 const landing=r.documents.find(d=>d.key==='issuer_investor_relations');
 const prospectus=p.issuer.sources.find(s=>s.key==='final_prospectus').url;
 const binding=Boolean(landing?.accepted&&landingLinksProspectus(fs.readFileSync(path.join(evidenceDir,landing.evidence_file),'utf8'),prospectus));
 req(binding===r.issuer_landing_links_prospectus,'landing_binding_mismatch');
 req(r.status===(accepted===3&&binding?'complete':'partial'),'receipt_status_mismatch');
 return {accepted,expected:3,bytes:total,status:r.status,publication_import_allowed:false};
}

async function main(){
 const args=process.argv.slice(2);req(args.length===1&&/^--(?:out|validate-dir)=/.test(args[0]),'use --out=ABSOLUTE_NEW_DIRECTORY or --validate-dir=ABSOLUTE_DIRECTORY');
 const [flag,...rest]=args[0].split('='),dir=rest.join('=');req(path.isAbsolute(dir),'absolute_evidence_directory_required');
 const relative=path.relative(ROOT,path.resolve(dir));req(relative.startsWith('..'+path.sep)||path.isAbsolute(relative),'evidence_must_be_outside_repository');
 const planBytes=fs.readFileSync(path.join(ROOT,PLAN));
 if(flag==='--validate-dir'){console.log(JSON.stringify(validateReceipt(JSON.parse(fs.readFileSync(path.join(dir,'source-receipt.json'))),planBytes,dir),null,2));return;}
 const queueBytes=fs.readFileSync(path.join(ROOT,QUEUE)),progressBytes=fs.readFileSync(path.join(ROOT,PROGRESS));
 validatePlan(planBytes,{queueBytes});
 const {checkProgress}=await import('./check-bse-2023-progress.mjs');
 const preflight=checkProgress(ROOT);
 req(Array.isArray(preflight.next)&&preflight.next[0]===CODE,'mish_no_longer_first_next_candidate');
 const r=await collectEvidence({planBytes,evidenceDir:dir});
 fs.writeFileSync(path.join(dir,'identity-preflight.json'),JSON.stringify({checked_at:new Date().toISOString(),repository_ref:process.env.GITHUB_SHA??null,progress_sha256:sha(progressBytes),candidate_code:CODE,candidate_first_in_next_batch:true,progress:preflight,publication_import_allowed:false},null,2)+'\n',{flag:'wx'});
 fs.writeFileSync(path.join(dir,'queue-snapshot.json'),queueBytes,{flag:'wx'});
 fs.writeFileSync(path.join(dir,'progress-observed.json'),progressBytes,{flag:'wx'});
 console.log(JSON.stringify({status:r.status,accepted:r.source_documents_accepted,expected:3,bytes:r.total_response_bytes,issuer_landing_links_prospectus:r.issuer_landing_links_prospectus,publication_import_allowed:false},null,2));
 if(r.status!=='complete')process.exitCode=1;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href)main().catch(e=>{console.error(e.message);process.exitCode=1;});
