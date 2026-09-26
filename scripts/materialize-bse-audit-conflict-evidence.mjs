import fs from "node:fs";
import path from "node:path";
import {createHash} from "node:crypto";
import {fileURLToPath,pathToFileURL} from "node:url";

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
export const REVIEW_PATH="data/discovery/bse-issue-summary-high-priority-reconciliation-2026-09-26.json";
export const RECEIPT_PATH="data/evidence/bse-high-priority-reconciliation-source-receipt-2026-09-26.json";
const MAX_FILE=80*1024*1024,MAX_TOTAL=350*1024*1024;
const UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";
export const sha256=v=>createHash("sha256").update(v).digest("hex");
const hash=v=>typeof v==="string"&&/^[a-f0-9]{64}$/.test(v);
const stamp=v=>typeof v==="string"&&Number.isFinite(Date.parse(v));
function canonical(v){return JSON.stringify(v);}
export function trustedSourceUrl(value){
  try{
    const u=new URL(String(value));
    const hosts=new Set(["www.sebi.gov.in","sebi.gov.in","nsearchives.nseindia.com","archives.nseindia.com","www.bseindia.com","bseindia.com"]);
    return u.protocol==="https:"&&!u.username&&!u.password&&hosts.has(u.hostname.toLowerCase())?u.href:null;
  }catch{return null;}
}
function typeOf(bytes,contentType,url){
  if(bytes.subarray(0,5).toString("ascii")==="%PDF-")return{kind:"pdf",ext:".pdf"};
  const prefix=bytes.subarray(0,512).toString("utf8").trimStart().toLowerCase();
  if(String(contentType||"").toLowerCase().includes("text/html")||prefix.startsWith("<!doctype html")||prefix.startsWith("<html"))return{kind:"html",ext:".html"};
  try{if(/\.html?$/i.test(new URL(url).pathname))return{kind:"html",ext:".html"};}catch{}
  return null;
}
async function body(response,max){
  const chunks=[];let total=0;
  for await(const chunk of response.body){total+=chunk.length;if(total>max)throw new Error("source_size_limit");chunks.push(Buffer.from(chunk));}
  return Buffer.concat(chunks);
}
export function validateReview(review){
  if(review?.schema_version!=="1.0.0"||review?.status!=="reviewed_bse_issue_summary_high_priority_reconciliation"||
     !Array.isArray(review.actions)||review.actions.length!==5||!Array.isArray(review.sources)||review.sources.length!==10||
     review.auto_import_allowed!==false)throw new Error("invalid_reconciliation_review");
  const keys=new Set(),urls=new Set();
  for(const s of review.sources){
    if(!s.key||keys.has(s.key)||!trustedSourceUrl(s.url)||urls.has(s.url)||!s.projection||!hash(s.projection_sha256)||
       sha256(Buffer.from(canonical(s.projection)))!==s.projection_sha256)throw new Error("invalid_reconciliation_source:"+s?.key);
    keys.add(s.key);urls.add(s.url);
  }
  return{keys};
}
export async function collect({review,reviewBytes,outDir,fetchImpl=fetch,clock=()=>new Date().toISOString()}){
  validateReview(review);if(!Buffer.isBuffer(reviewBytes))reviewBytes=Buffer.from(reviewBytes);
  fs.mkdirSync(outDir,{recursive:true});let total=0;const docs=[];
  for(const source of review.sources){
    const requested_at=clock(),url=trustedSourceUrl(source.url);
    const response=await fetchImpl(url,{redirect:"follow",signal:AbortSignal.timeout(45000),headers:{"user-agent":UA,accept:"application/pdf,text/html,*/*","cache-control":"no-cache"}});
    const final_url=trustedSourceUrl(response.url||url);
    if(!response.ok||!final_url)throw new Error("source_fetch_failed:"+source.key+":"+response.status);
    const bytes=await body(response,MAX_FILE);total+=bytes.length;if(total>MAX_TOTAL)throw new Error("total_size_limit");
    const detected=typeOf(bytes,response.headers.get("content-type"),final_url);if(!detected)throw new Error("unrecognized_source_type:"+source.key);
    const file=source.key+detected.ext;fs.writeFileSync(path.join(outDir,file),bytes);
    docs.push({key:source.key,authority:source.authority,document_type:source.document_type,source_url:url,final_url,http_status:response.status,
      content_type:response.headers.get("content-type"),detected_type:detected.kind,response_bytes:bytes.length,response_sha256:sha256(bytes),
      requested_at,collected_at:clock(),evidence_file:file,projection_sha256:source.projection_sha256});
  }
  const receipt={schema_version:"1.0.0",collector_version:"1.0.0",status:"complete",review_path:REVIEW_PATH,review_sha256:sha256(reviewBytes),
    collection_started_at:docs[0].requested_at,collection_completed_at:docs.at(-1).collected_at,source_documents_expected:10,source_documents_collected:docs.length,
    total_response_bytes:total,documents:docs,workflow_artifact:null,import_allowed:false};
  validateReceipt(receipt,review,reviewBytes);return receipt;
}
export function validateReceipt(receipt,review,reviewBytes){
  const {keys}=validateReview(review);if(!Buffer.isBuffer(reviewBytes))reviewBytes=Buffer.from(reviewBytes);
  if(receipt?.schema_version!=="1.0.0"||receipt?.collector_version!=="1.0.0"||receipt?.status!=="complete"||
    receipt.review_path!==REVIEW_PATH||receipt.review_sha256!==sha256(reviewBytes)||receipt.source_documents_expected!==10||
    receipt.source_documents_collected!==10||!Array.isArray(receipt.documents)||receipt.documents.length!==10||
    !stamp(receipt.collection_started_at)||!stamp(receipt.collection_completed_at))throw new Error("invalid_reconciliation_receipt");
  let total=0;const seen=new Set();
  for(const d of receipt.documents){
    if(!keys.has(d.key)||seen.has(d.key)||!trustedSourceUrl(d.source_url)||!trustedSourceUrl(d.final_url)||d.http_status!==200||
      !["pdf","html"].includes(d.detected_type)||!Number.isInteger(d.response_bytes)||d.response_bytes<=0||!hash(d.response_sha256)||
      !stamp(d.requested_at)||!stamp(d.collected_at)||!hash(d.projection_sha256))throw new Error("invalid_reconciliation_document:"+d?.key);
    seen.add(d.key);total+=d.response_bytes;
  }
  if(total!==receipt.total_response_bytes)throw new Error("receipt_byte_mismatch");return{documents:10,bytes:total};
}
async function run(){
  const args=Object.fromEntries(process.argv.slice(2).map(x=>{const i=x.indexOf("=");if(i<1)throw new Error("args_use_equals");return[x.slice(0,i),x.slice(i+1)];}));
  const reviewPath=args["--review"]||REVIEW_PATH,reviewFile=path.isAbsolute(reviewPath)?reviewPath:path.join(ROOT,reviewPath);
  const reviewBytes=fs.readFileSync(reviewFile),review=JSON.parse(reviewBytes);
  if(args["--validate-receipt"]){
    const p=path.isAbsolute(args["--validate-receipt"])?args["--validate-receipt"]:path.join(ROOT,args["--validate-receipt"]);
    const receipt=JSON.parse(fs.readFileSync(p,"utf8")),result=validateReceipt(receipt,review,reviewBytes);
    if(!receipt.workflow_artifact?.artifact_id||!/^sha256:[a-f0-9]{64}$/.test(receipt.workflow_artifact?.artifact_digest||""))throw new Error("missing_artifact_identity");
    console.log(JSON.stringify({reconciliation_evidence_receipt:result,artifact_id:receipt.workflow_artifact.artifact_id}));return;
  }
  if(!args["--evidence-dir"]||!args["--receipt"])throw new Error("evidence_dir_and_receipt_required");
  const receipt=await collect({review,reviewBytes,outDir:args["--evidence-dir"]});
  fs.writeFileSync(args["--receipt"],JSON.stringify(receipt,null,2)+"\n");
  console.log(JSON.stringify({reconciliation_evidence:{documents:receipt.source_documents_collected,bytes:receipt.total_response_bytes}}));
}
if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url)run().catch(e=>{console.error(e);process.exit(1);});
