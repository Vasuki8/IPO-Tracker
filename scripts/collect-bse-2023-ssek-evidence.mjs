import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {auditNextBatch,TARGETS} from './audit-bse-2023-ssek-identities.mjs';

const ROOT=fileURLToPath(new URL('../',import.meta.url));
export const PLAN='data/discovery/bse-2023-ssek-source-plan-2026-09-29.json';
const QUEUE='data/discovery/bse-2023-review-queue-2026-09-28.json';
const MAX_SOURCE_BYTES=70*1024*1024,MAX_TOTAL_BYTES=260*1024*1024;
const CODES=TARGETS.map(t=>t.code);
const sha=b=>createHash('sha256').update(b).digest('hex');
const req=(ok,message)=>{if(!ok)throw new Error(message);};
const stamp=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(s)&&Number.isFinite(Date.parse(s));
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function sourceUrl(value,kind){
  req(typeof value==='string'&&!/[?#@%\\]/.test(value)&&!value.includes('..'),'unsafe_source_url');
  const u=new URL(value);req(u.origin==='https://www.sebi.gov.in'&&u.href===value,'untrusted_source_url');
  req((kind==='landing'?/^\/filings\/public-issues\/[a-z]{3}-\d{4}\/[a-z0-9-]+_\d+\.html$/:/^\/sebi_data\/attachdocs\/[a-z]{3}-\d{4}\/[^/]+\.pdf$/i).test(u.pathname),'unexpected_source_path');
  return value;
}
export function validatePlan(planBytes,{queueBytes}={}){
  const p=JSON.parse(Buffer.from(planBytes).toString('utf8'));
  req(p?.schema_version==='1.0.0'&&p.status==='source_collection_only'&&p.batch_id==='bse-2023-ssek','invalid_plan');
  req(p.publication_import_allowed===false&&p.semantic_review_complete===false&&p.complete_indian_ipo_universe===false,'unsafe_plan_scope');
  req(p.source_queue===QUEUE&&/^[a-f0-9]{64}$/.test(p.source_queue_sha256)&&stamp(p.discovery_source_collected_at),'invalid_queue_reference');
  req(Array.isArray(p.issuers)&&same(p.issuers.map(i=>i?.discovery_bse_scrip_code),CODES),'unexpected_batch_identity');
  const urls=new Set(),indices=new Set();
  for(const i of p.issuers){
    req(Number.isSafeInteger(i.source_row_index)&&i.source_row_index>=0&&!indices.has(i.source_row_index),'invalid_source_row');indices.add(i.source_row_index);
    req(typeof i.issuer_name==='string'&&i.issuer_name.trim().length>5,'invalid_issuer_name');
    req(/^20(?:23|24)-\d{2}-\d{2}$/.test(i.landing_displayed_date)&&Number.isFinite(Date.parse(i.landing_displayed_date))&&i.document_date===null,'unreviewed_document_date');
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
const sources=p=>p.issuers.flatMap(i=>['landing','prospectus'].map(kind=>({code:i.discovery_bse_scrip_code,kind,url:i[kind+'_url']})));
const bodyType=(bytes,kind)=>kind==='prospectus'?bytes.subarray(0,5).toString('ascii')==='%PDF-':/^\s*(?:\uFEFF)?\s*<(?:!doctype\s+html|html)(?:\s|>)/i.test(bytes.subarray(0,1024).toString('utf8'));
function hasPdfLink(html,pdf){for(const match of html.matchAll(/(?:href|src)\s*=\s*["']([^"']+)["']/gi)){try{const u=new URL(match[1].replace(/&amp;/g,'&'),'https://www.sebi.gov.in');if(u.href===pdf||(u.origin==='https://www.sebi.gov.in'&&/^\/web\/?$/.test(u.pathname)&&u.searchParams.get('file')===pdf))return true;}catch{}}return false;}
async function limitedBody(response,max){if(!response.body){const b=Buffer.from(await response.arrayBuffer());req(b.length<=max,'source_size_limit');return b;}const chunks=[];let length=0;for await(const chunk of response.body){length+=chunk.length;req(length<=max,'source_size_limit');chunks.push(Buffer.from(chunk));}return Buffer.concat(chunks);}
export async function collectEvidence({planBytes,evidenceDir,fetchImpl=fetch,clock=()=>new Date().toISOString()}){
  const p=validatePlan(planBytes);fs.mkdirSync(evidenceDir);fs.writeFileSync(path.join(evidenceDir,'source-plan.json'),planBytes,{flag:'wx'});
  const started=clock(),documents=[];let total=0;
  for(const s of sources(p)){
    const d={...s,requested_at:clock(),collected_at:null,http_status:null,content_type:null,accepted:false,error:null,evidence_file:null,response_sha256:null,response_bytes:0};
    let body=null;
    try{
      const remaining=MAX_TOTAL_BYTES-total;req(remaining>0,'total_size_limit');
      const response=await fetchImpl(s.url,{redirect:'error',signal:AbortSignal.timeout(90000),headers:{'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36','accept':s.kind==='prospectus'?'application/pdf':'text/html','cache-control':'no-cache'}});
      d.http_status=response.status;d.content_type=response.headers?.get?.('content-type')??null;req(!response.url||response.url===s.url,'unexpected_final_url');
      body=await limitedBody(response,Math.min(MAX_SOURCE_BYTES,remaining));req(response.status===200,'http_status');req(body.length>0&&bodyType(body,s.kind),'unexpected_body_type');d.accepted=true;
    }catch(e){d.error=['source_size_limit','total_size_limit','unexpected_final_url','http_status','unexpected_body_type'].includes(e.message)?e.message:'network_error';}
    if(body?.length){const ext=d.accepted?(s.kind==='prospectus'?'pdf':'html'):'response';d.evidence_file=`${s.code}-${s.kind}.${ext}`;fs.writeFileSync(path.join(evidenceDir,d.evidence_file),body,{flag:'wx'});d.response_sha256=sha(body);d.response_bytes=body.length;total+=body.length;}
    d.collected_at=clock();documents.push(d);
  }
  const bindings=p.issuers.map(i=>{const d=documents.find(x=>x.code===i.discovery_bse_scrip_code&&x.kind==='landing');return{code:i.discovery_bse_scrip_code,link_found:d.accepted&&hasPdfLink(fs.readFileSync(path.join(evidenceDir,d.evidence_file),'utf8'),i.prospectus_url)};});
  const accepted=documents.filter(d=>d.accepted).length;
  const receipt={schema_version:'1.0.0',collector_version:'1.0.0',batch_id:p.batch_id,status:accepted===8&&bindings.every(b=>b.link_found)?'complete':'partial',plan_path:PLAN,plan_sha256:sha(planBytes),source_queue:p.source_queue,source_queue_sha256:p.source_queue_sha256,discovery_source_collected_at:p.discovery_source_collected_at,discovery_source_refetched:false,collection_started_at:started,collection_completed_at:clock(),source_documents_expected:8,source_documents_accepted:accepted,total_response_bytes:total,publication_import_allowed:false,semantic_review_complete:false,complete_indian_ipo_universe:false,documents,landing_pdf_bindings:bindings};
  fs.writeFileSync(path.join(evidenceDir,'source-receipt.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
  return receipt;
}
async function main(){
  const args=process.argv.slice(2);req(args.length===1&&args[0].startsWith('--out='),'use --out=ABSOLUTE_NEW_DIRECTORY');const dir=args[0].slice(6);req(path.isAbsolute(dir),'absolute_evidence_directory_required');
  const planBytes=fs.readFileSync(path.join(ROOT,PLAN)),queueBytes=fs.readFileSync(path.join(ROOT,QUEUE));validatePlan(planBytes,{queueBytes});
  const identity=auditNextBatch(ROOT);req(same(identity.next_bounded_review_codes,CODES),'source_batch_no_longer_next');
  fs.mkdirSync(path.dirname(dir),{recursive:true});
  const receipt=await collectEvidence({planBytes,evidenceDir:dir});
  fs.writeFileSync(path.join(dir,'identity-preflight.json'),JSON.stringify({...identity,checked_at:new Date().toISOString(),repository_ref:process.env.GITHUB_SHA??null},null,2)+'\n',{flag:'wx'});
  fs.writeFileSync(path.join(dir,'queue-snapshot.json'),queueBytes,{flag:'wx'});
  console.log(JSON.stringify({status:receipt.status,accepted:receipt.source_documents_accepted,expected:8,bytes:receipt.total_response_bytes,identity_holds:identity.identity_holds,publication_import_allowed:false},null,2));
  if(receipt.status!=='complete')process.exitCode=1;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href)main().catch(e=>{console.error(e.message);process.exitCode=1;});
