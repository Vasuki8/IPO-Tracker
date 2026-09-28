import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';

const ROOT=fileURLToPath(new URL('../',import.meta.url));
export const PLAN='data/discovery/bse-2023-irms-source-plan-2026-09-28.json';
const QUEUE='data/discovery/bse-2023-review-queue-2026-09-28.json';
const PROGRESS='data/discovery/bse-2023-review-progress-2026-09-28.json';
const CODES=['544026','544053','544060','543963'];
const MAX_SOURCE_BYTES=60*1024*1024,MAX_TOTAL_BYTES=250*1024*1024;
const sha=b=>createHash('sha256').update(b).digest('hex');
const req=(ok,message)=>{if(!ok)throw new Error(message);};
const stamp=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(s)&&Number.isFinite(Date.parse(s));
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function keys(value,expected){req(value&&typeof value==='object'&&!Array.isArray(value)&&same(Object.keys(value).sort(),[...expected].sort()),'unexpected_plan_fields');}
function sourceUrl(value,kind){
 req(typeof value==='string'&&!/[?#@%\\]/.test(value)&&!value.includes('..'),'unsafe_source_url');
 const u=new URL(value);
 req(u.origin==='https://www.sebi.gov.in'&&u.href===value,'untrusted_source_url');
 req((kind==='landing'?/^\/filings\/public-issues\/[a-z]{3}-\d{4}\/[a-z0-9-]+_\d+\.html$/:/^\/sebi_data\/attachdocs\/[a-z]{3}-\d{4}\/\d+\.pdf$/).test(u.pathname),'unexpected_source_path');
 return value;
}
export function validatePlan(planBytes,{queueBytes}={}){
 const p=JSON.parse(Buffer.from(planBytes).toString('utf8'));
 keys(p,['schema_version','status','batch_id','source_queue','source_queue_sha256','discovery_source_collected_at','publication_import_allowed','semantic_review_complete','complete_indian_ipo_universe','issuers','notes']);
 req(p.schema_version==='1.0.0'&&p.status==='source_collection_only'&&p.batch_id==='bse-2023-irms','invalid_plan');
 req(p.publication_import_allowed===false&&p.semantic_review_complete===false&&p.complete_indian_ipo_universe===false,'unsafe_plan_scope');
 req(p.source_queue===QUEUE&&/^[a-f0-9]{64}$/.test(p.source_queue_sha256)&&stamp(p.discovery_source_collected_at),'invalid_queue_reference');
 req(Array.isArray(p.issuers)&&same(p.issuers.map(i=>i?.discovery_bse_scrip_code),CODES),'unexpected_batch_identity');
 req(Array.isArray(p.notes)&&p.notes.every(n=>typeof n==='string'),'invalid_plan_notes');
 const urls=new Set(),indices=new Set();
 for(const i of p.issuers){
  keys(i,['discovery_bse_scrip_code','source_row_index','issuer_name','landing_url','landing_displayed_date','prospectus_url','document_date']);
  req(Number.isSafeInteger(i.source_row_index)&&i.source_row_index>=0&&!indices.has(i.source_row_index),'invalid_source_row');indices.add(i.source_row_index);
  req(typeof i.issuer_name==='string'&&i.issuer_name.trim().length>5,'invalid_issuer_name');
  req(/^2023-\d{2}-\d{2}$/.test(i.landing_displayed_date)&&Number.isFinite(Date.parse(i.landing_displayed_date))&&i.document_date===null,'unreviewed_document_date');
  for(const kind of ['landing','prospectus']){const u=sourceUrl(i[kind+'_url'],kind);req(!urls.has(u),'duplicate_source_url');urls.add(u);}
 }
 if(queueBytes){
  req(sha(queueBytes)===p.source_queue_sha256,'source_queue_hash_mismatch');
  const q=JSON.parse(Buffer.from(queueBytes).toString('utf8'));
  req(q.source_year===2023&&q.source_collected_at===p.discovery_source_collected_at&&q.auto_import_allowed===false&&Array.isArray(q.rows),'invalid_source_queue');
  for(const i of p.issuers){const hits=q.rows.filter(r=>r.bse_scrip_code===i.discovery_bse_scrip_code);req(hits.length===1&&hits[0].source_row_index===i.source_row_index&&hits[0].issuer_name.trim().toLowerCase()===i.issuer_name.trim().toLowerCase(),'source_queue_identity_mismatch');}
 }
 return p;
}
function sources(p){return p.issuers.flatMap(i=>['landing','prospectus'].map(kind=>({code:i.discovery_bse_scrip_code,kind,url:i[kind+'_url']})));}
function bodyType(bytes,kind){return kind==='prospectus'?bytes.subarray(0,5).toString('ascii')==='%PDF-':/^\s*(?:\uFEFF)?\s*<(?:!doctype\s+html|html)(?:\s|>)/i.test(bytes.subarray(0,1024).toString('utf8'));}
function hasPdfLink(html,pdf){
 for(const match of html.matchAll(/(?:href|src)\s*=\s*["']([^"']+)["']/gi)){
  try{const u=new URL(match[1].replace(/&amp;/g,'&'),'https://www.sebi.gov.in');if(u.href===pdf||(u.origin==='https://www.sebi.gov.in'&&/^\/web\/?$/.test(u.pathname)&&u.searchParams.get('file')===pdf))return true;}catch{}
 }
 return false;
}
function bindings(p,documents,evidenceDir){return p.issuers.map(i=>{
 const d=documents.find(x=>x.code===i.discovery_bse_scrip_code&&x.kind==='landing');
 return {code:i.discovery_bse_scrip_code,link_found:d.accepted&&hasPdfLink(fs.readFileSync(path.join(evidenceDir,d.evidence_file),'utf8'),i.prospectus_url)};
});}
async function limitedBody(response,max){
 if(!response.body){const b=Buffer.from(await response.arrayBuffer());req(b.length<=max,'source_size_limit');return b;}
 const chunks=[];let length=0;
 for await(const chunk of response.body){length+=chunk.length;req(length<=max,'source_size_limit');chunks.push(Buffer.from(chunk));}
 return Buffer.concat(chunks);
}
// A successful collection is not a semantic review and never authorizes import.
// All failures are retained in a partial receipt, not converted into empty values.
export async function collectEvidence({planBytes,evidenceDir,fetchImpl=fetch,clock=()=>new Date().toISOString(),maxSourceBytes=MAX_SOURCE_BYTES,maxTotalBytes=MAX_TOTAL_BYTES}){
 const p=validatePlan(planBytes);
 req(Number.isSafeInteger(maxSourceBytes)&&maxSourceBytes>0&&maxSourceBytes<=MAX_SOURCE_BYTES&&Number.isSafeInteger(maxTotalBytes)&&maxTotalBytes>0&&maxTotalBytes<=MAX_TOTAL_BYTES,'invalid_size_limit');
 fs.mkdirSync(evidenceDir); // Deliberately refuses reuse of an existing collection.
 fs.writeFileSync(path.join(evidenceDir,'source-plan.json'),planBytes,{flag:'wx'});
 const started=clock(),documents=[];let total=0;
 for(const s of sources(p)){
  const d={...s,requested_at:clock(),collected_at:null,http_status:null,content_type:null,accepted:false,error:null,evidence_file:null,response_sha256:null,response_bytes:0};
  let body=null;
  try{
   const remaining=maxTotalBytes-total;req(remaining>0,'total_size_limit');
   const response=await fetchImpl(s.url,{redirect:'error',signal:AbortSignal.timeout(45000),headers:{'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36','accept':s.kind==='prospectus'?'application/pdf':'text/html','cache-control':'no-cache'}});
   d.http_status=response.status;d.content_type=response.headers?.get?.('content-type')??null;
   req(!response.url||response.url===s.url,'unexpected_final_url');
   body=await limitedBody(response,Math.min(maxSourceBytes,remaining));
   req(d.http_status===200,'http_status');req(body.length>0&&bodyType(body,s.kind),'unexpected_body_type');d.accepted=true;
  }catch(e){d.error=['source_size_limit','total_size_limit','unexpected_final_url','http_status','unexpected_body_type'].includes(e.message)?e.message:'network_error';}
  if(body?.length){
   const extension=d.accepted?(s.kind==='prospectus'?'pdf':'html'):'response';d.evidence_file=`${s.code}-${s.kind}.${extension}`;
   fs.writeFileSync(path.join(evidenceDir,d.evidence_file),body,{flag:'wx'});d.response_sha256=sha(body);d.response_bytes=body.length;total+=body.length;
  }
  d.collected_at=clock();documents.push(d);
 }
 const links=bindings(p,documents,evidenceDir),accepted=documents.filter(d=>d.accepted).length;
 const r={schema_version:'1.0.0',collector_version:'1.0.0',batch_id:p.batch_id,status:accepted===8&&links.every(b=>b.link_found)?'complete':'partial',plan_path:PLAN,plan_sha256:sha(planBytes),source_queue:p.source_queue,source_queue_sha256:p.source_queue_sha256,discovery_source_collected_at:p.discovery_source_collected_at,discovery_source_refetched:false,collection_started_at:started,collection_completed_at:clock(),source_documents_expected:8,source_documents_accepted:accepted,total_response_bytes:total,publication_import_allowed:false,semantic_review_complete:false,complete_indian_ipo_universe:false,documents,landing_pdf_bindings:links,workflow_artifact:null};
 validateReceipt(r,planBytes,evidenceDir);
 fs.writeFileSync(path.join(evidenceDir,'source-receipt.json'),JSON.stringify(r,null,2)+'\n',{flag:'wx'});
 return r;
}
export function validateReceipt(r,planBytes,evidenceDir){
 const p=validatePlan(planBytes),expected=sources(p);
 req(r?.schema_version==='1.0.0'&&r.collector_version==='1.0.0'&&r.batch_id===p.batch_id&&r.plan_path===PLAN&&r.plan_sha256===sha(planBytes),'receipt_plan_mismatch');
 req(r.publication_import_allowed===false&&r.semantic_review_complete===false&&r.complete_indian_ipo_universe===false&&r.discovery_source_refetched===false,'unsafe_receipt_scope');
 req(r.source_queue===p.source_queue&&r.source_queue_sha256===p.source_queue_sha256&&r.discovery_source_collected_at===p.discovery_source_collected_at,'receipt_queue_mismatch');
 req(stamp(r.collection_started_at)&&stamp(r.collection_completed_at)&&r.collection_started_at<=r.collection_completed_at,'invalid_collection_clock');
 req(Array.isArray(r.documents)&&r.documents.length===8&&r.source_documents_expected===8,'invalid_receipt_documents');
 req(sha(fs.readFileSync(path.join(evidenceDir,'source-plan.json')))===r.plan_sha256,'retained_plan_mismatch');
 let total=0,accepted=0,last=r.collection_started_at;
 for(let n=0;n<expected.length;n++){
  const d=r.documents[n],s=expected[n];req(d.code===s.code&&d.kind===s.kind&&d.url===s.url,'receipt_source_mismatch');
  req(stamp(d.requested_at)&&stamp(d.collected_at)&&last<=d.requested_at&&d.requested_at<=d.collected_at&&d.collected_at<=r.collection_completed_at,'invalid_document_clock');last=d.collected_at;
  req(typeof d.accepted==='boolean'&&Number.isSafeInteger(d.response_bytes)&&d.response_bytes>=0&&d.response_bytes<=MAX_SOURCE_BYTES,'invalid_document_metadata');
  req(d.http_status===null||(Number.isInteger(d.http_status)&&d.http_status>=100&&d.http_status<=599),'invalid_http_status');
  req(d.accepted?(d.http_status===200&&d.error===null):['network_error','source_size_limit','total_size_limit','unexpected_final_url','http_status','unexpected_body_type'].includes(d.error),'invalid_document_result');
  if(d.response_bytes){
   const extension=d.accepted?(s.kind==='prospectus'?'pdf':'html'):'response';req(d.evidence_file===`${s.code}-${s.kind}.${extension}`,'unsafe_evidence_file');
   const b=fs.readFileSync(path.join(evidenceDir,d.evidence_file));req(b.length===d.response_bytes&&sha(b)===d.response_sha256,'response_bytes_mismatch');
   if(d.accepted)req(bodyType(b,s.kind),'accepted_body_type_mismatch');
  }else req(!d.accepted&&d.evidence_file===null&&d.response_sha256===null,'missing_response_bytes');
  total+=d.response_bytes;if(d.accepted)accepted++;
 }
 req(total===r.total_response_bytes&&total<=MAX_TOTAL_BYTES&&accepted===r.source_documents_accepted,'receipt_totals_mismatch');
 const links=bindings(p,r.documents,evidenceDir);req(same(links,r.landing_pdf_bindings),'landing_binding_mismatch');
 req(r.status===(accepted===8&&links.every(b=>b.link_found)?'complete':'partial'),'receipt_status_mismatch');
 return {accepted,expected:8,bytes:total,status:r.status,publication_import_allowed:false};
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
 const preflight=checkProgress(ROOT);req(same(preflight.next,CODES),'source_batch_no_longer_next');
 const checkedAt=new Date().toISOString();
 const r=await collectEvidence({planBytes,evidenceDir:dir});
 fs.writeFileSync(path.join(dir,'identity-preflight.json'),JSON.stringify({checked_at:checkedAt,repository_ref:process.env.GITHUB_SHA??null,progress_sha256:sha(progressBytes),...preflight,publication_import_allowed:false},null,2)+'\n',{flag:'wx'});
 fs.writeFileSync(path.join(dir,'queue-snapshot.json'),queueBytes,{flag:'wx'});
 fs.writeFileSync(path.join(dir,'progress-observed.json'),progressBytes,{flag:'wx'});
 console.log(JSON.stringify({status:r.status,accepted:r.source_documents_accepted,expected:8,bytes:r.total_response_bytes,publication_import_allowed:false,identity_warnings:preflight.warnings},null,2));
 if(r.status!=='complete')process.exitCode=1;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href)main().catch(e=>{console.error(e.message);process.exitCode=1;});
