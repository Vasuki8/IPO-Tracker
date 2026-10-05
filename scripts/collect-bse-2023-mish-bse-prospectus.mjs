import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';

const ROOT=fileURLToPath(new URL('../',import.meta.url));
export const PLAN='data/discovery/bse-2023-mish-bse-prospectus-plan-2026-10-05.json';
const PRIOR='data/evidence/bse-2023-mish-source-receipt-2026-10-05.json';
const BSE_URL='https://www.bseindia.com/corporates/download/394119/SME_IPO%20Open/Prospectus_Final_20231109201146.pdf';
const MAX_BYTES=80*1024*1024;
const sha=b=>createHash('sha256').update(b).digest('hex');
const req=(ok,message)=>{if(!ok)throw new Error(message);};
const stamp=v=>typeof v==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(v)&&Number.isFinite(Date.parse(v));

export function validatePlan(planBytes,{priorReceiptBytes}={}){
 const p=JSON.parse(Buffer.from(planBytes).toString('utf8'));
 req(p?.schema_version==='1.0.0'&&p.status==='supplemental_source_collection_only'&&p.batch_id==='bse-2023-mish-bse-prospectus','invalid_plan');
 req(p.issuer_name==='Mish Designs Limited'&&p.discovery_bse_scrip_code==='544015','unexpected_identity');
 req(p.prior_source_receipt===PRIOR,'prior_receipt_mismatch');
 req(p.publication_import_allowed===false&&p.semantic_review_complete===false,'unsafe_plan_scope');
 req(p.source?.key==='bse_final_prospectus'&&p.source.authority==='BSE Limited'&&p.source.role==='final_prospectus_publication_candidate'&&p.source.kind==='pdf'&&p.source.url===BSE_URL,'source_mismatch');
 const u=new globalThis.URL(p.source.url);req(u.protocol==='https:'&&u.hostname==='www.bseindia.com'&&!u.username&&!u.password&&!u.hash,'unsafe_source_url');
 req(/^\/corporates\/download\/394119\/SME_IPO%20Open\/Prospectus_Final_20231109201146\.pdf$/.test(u.pathname),'unexpected_source_path');
 req(Array.isArray(p.notes)&&p.notes.length>=3,'missing_notes');
 if(priorReceiptBytes){
   const prior=JSON.parse(Buffer.from(priorReceiptBytes).toString('utf8'));
   req(prior.batch_id==='bse-2023-mish'&&prior.candidate?.issuer_name==='Mish Designs Limited'&&prior.candidate?.discovery_bse_scrip_code==='544015','invalid_prior_receipt');
   req(prior.publication_import_allowed===false&&prior.semantic_review_complete===false,'unsafe_prior_receipt');
   const issuer=prior.documents?.find(d=>d.key==='final_prospectus');
   req(issuer?.authority==='Mish Designs Limited'&&issuer.role==='final_prospectus'&&/^[a-f0-9]{64}$/.test(issuer.response_sha256)&&Number.isSafeInteger(issuer.response_bytes)&&issuer.response_bytes>0,'missing_prior_prospectus');
 }
 return p;
}
async function limitedBody(response,max){
 if(!response.body){const b=Buffer.from(await response.arrayBuffer());req(b.length<=max,'source_size_limit');return b;}
 const chunks=[];let length=0;
 for await(const chunk of response.body){length+=chunk.length;req(length<=max,'source_size_limit');chunks.push(Buffer.from(chunk));}
 return Buffer.concat(chunks);
}
export async function collectEvidence({planBytes,priorReceiptBytes,evidenceDir,fetchImpl=fetch,clock=()=>new Date().toISOString()}){
 const p=validatePlan(planBytes,{priorReceiptBytes});fs.mkdirSync(evidenceDir);
 fs.writeFileSync(path.join(evidenceDir,'source-plan.json'),planBytes,{flag:'wx'});
 fs.writeFileSync(path.join(evidenceDir,'prior-source-receipt.json'),priorReceiptBytes,{flag:'wx'});
 const requested_at=clock();
 const d={key:p.source.key,authority:p.source.authority,role:p.source.role,url:p.source.url,requested_at,collected_at:null,http_status:null,content_type:null,accepted:false,error:null,evidence_file:null,response_sha256:null,response_bytes:0};
 let body=null;
 try{
   const response=await fetchImpl(BSE_URL,{redirect:'error',signal:AbortSignal.timeout(60000),headers:{
     'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
     'accept':'application/pdf,application/octet-stream;q=0.9,*/*;q=0.1',
     'referer':'https://www.bseindia.com/',
     'cache-control':'no-cache'
   }});
   d.http_status=response.status;d.content_type=response.headers?.get?.('content-type')??null;
   req(!response.url||response.url===BSE_URL,'unexpected_final_url');
   body=await limitedBody(response,MAX_BYTES);
   req(response.status===200,'http_status');
   req(body.length>0&&body.subarray(0,5).toString('ascii')==='%PDF-','unexpected_body_type');
   d.accepted=true;
 }catch(e){d.error=['source_size_limit','unexpected_final_url','http_status','unexpected_body_type'].includes(e.message)?e.message:'network_error';}
 if(body?.length){
   d.evidence_file=d.accepted?'bse_final_prospectus.pdf':'bse_final_prospectus.response';
   fs.writeFileSync(path.join(evidenceDir,d.evidence_file),body,{flag:'wx'});
   d.response_sha256=sha(body);d.response_bytes=body.length;
 }
 d.collected_at=clock();
 const prior=JSON.parse(Buffer.from(priorReceiptBytes).toString('utf8'));
 const issuer=prior.documents.find(x=>x.key==='final_prospectus');
 const r={schema_version:'1.0.0',collector_version:'1.0.0',batch_id:p.batch_id,status:d.accepted?'complete':'partial',plan_path:PLAN,plan_sha256:sha(planBytes),prior_source_receipt:PRIOR,prior_source_receipt_sha256:sha(priorReceiptBytes),issuer_prospectus_reference:{response_sha256:issuer.response_sha256,response_bytes:issuer.response_bytes,pdf_pages:issuer.pdf_pages},collection_started_at:requested_at,collection_completed_at:d.collected_at,publication_import_allowed:false,semantic_review_complete:false,document:d,workflow_artifact:null};
 validateReceipt(r,planBytes,priorReceiptBytes,evidenceDir);
 fs.writeFileSync(path.join(evidenceDir,'source-receipt.json'),JSON.stringify(r,null,2)+'\n',{flag:'wx'});
 return r;
}
export function validateReceipt(r,planBytes,priorReceiptBytes,evidenceDir){
 validatePlan(planBytes,{priorReceiptBytes});
 req(r?.schema_version==='1.0.0'&&r.collector_version==='1.0.0'&&r.batch_id==='bse-2023-mish-bse-prospectus','invalid_receipt');
 req(r.plan_path===PLAN&&r.plan_sha256===sha(planBytes)&&r.prior_source_receipt===PRIOR&&r.prior_source_receipt_sha256===sha(priorReceiptBytes),'receipt_binding');
 req(r.publication_import_allowed===false&&r.semantic_review_complete===false,'unsafe_receipt_scope');
 req(stamp(r.collection_started_at)&&stamp(r.collection_completed_at)&&r.collection_started_at<=r.collection_completed_at,'invalid_clock');
 const prior=JSON.parse(Buffer.from(priorReceiptBytes).toString('utf8')).documents.find(x=>x.key==='final_prospectus');
 req(r.issuer_prospectus_reference.response_sha256===prior.response_sha256&&r.issuer_prospectus_reference.response_bytes===prior.response_bytes&&r.issuer_prospectus_reference.pdf_pages===prior.pdf_pages,'issuer_reference_mismatch');
 const d=r.document;req(d.key==='bse_final_prospectus'&&d.authority==='BSE Limited'&&d.role==='final_prospectus_publication_candidate'&&d.url===BSE_URL,'document_identity');
 req(stamp(d.requested_at)&&stamp(d.collected_at)&&r.collection_started_at===d.requested_at&&d.collected_at===r.collection_completed_at,'document_clock');
 req(typeof d.accepted==='boolean'&&Number.isSafeInteger(d.response_bytes)&&d.response_bytes>=0&&d.response_bytes<=MAX_BYTES,'document_metadata');
 req(d.accepted?(d.http_status===200&&d.error===null):['network_error','source_size_limit','unexpected_final_url','http_status','unexpected_body_type'].includes(d.error),'document_result');
 if(d.response_bytes){
   req(d.evidence_file===(d.accepted?'bse_final_prospectus.pdf':'bse_final_prospectus.response'),'evidence_file');
   const b=fs.readFileSync(path.join(evidenceDir,d.evidence_file));
   req(b.length===d.response_bytes&&sha(b)===d.response_sha256,'retained_bytes_mismatch');
   if(d.accepted)req(b.subarray(0,5).toString('ascii')==='%PDF-','retained_pdf_invalid');
 }else req(!d.accepted&&d.evidence_file===null&&d.response_sha256===null,'missing_response_bytes');
 req(r.status===(d.accepted?'complete':'partial'),'status_mismatch');
 return {status:r.status,accepted:d.accepted,bytes:d.response_bytes,publication_import_allowed:false};
}
async function main(){
 const arg=process.argv[2];req(process.argv.length===3&&/^--(?:out|validate-dir)=/.test(arg),'use --out=ABSOLUTE_NEW_DIRECTORY or --validate-dir=ABSOLUTE_DIRECTORY');
 const [flag,...rest]=arg.split('='),dir=rest.join('=');req(path.isAbsolute(dir),'absolute_directory_required');
 const rel=path.relative(ROOT,path.resolve(dir));req(rel.startsWith('..'+path.sep)||path.isAbsolute(rel),'evidence_must_be_outside_repository');
 const planBytes=fs.readFileSync(path.join(ROOT,PLAN)),priorReceiptBytes=fs.readFileSync(path.join(ROOT,PRIOR));
 if(flag==='--validate-dir'){console.log(JSON.stringify(validateReceipt(JSON.parse(fs.readFileSync(path.join(dir,'source-receipt.json'))),planBytes,priorReceiptBytes,dir),null,2));return;}
 const r=await collectEvidence({planBytes,priorReceiptBytes,evidenceDir:dir});
 console.log(JSON.stringify({status:r.status,accepted:r.document.accepted,bytes:r.document.response_bytes,publication_import_allowed:false},null,2));
 if(r.status!=='complete')process.exitCode=1;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href)main().catch(e=>{console.error(e.message);process.exitCode=1;});
