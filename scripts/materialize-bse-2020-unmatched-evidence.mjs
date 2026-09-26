import fs from "node:fs";
import path from "node:path";
import {createHash} from "node:crypto";
import {fileURLToPath,pathToFileURL} from "node:url";

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
export const REVIEW_PATH="data/discovery/bse-2020-unmatched-review-2026-09-26.json";
export const RECEIPT_PATH="data/evidence/bse-2020-unmatched-source-receipt-2026-09-26.json";
const MAX_FILE=90*1024*1024,MAX_TOTAL=400*1024*1024;
const UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";
export const sha256=v=>createHash("sha256").update(v).digest("hex");
const canonical=v=>JSON.stringify(v);
const hash=v=>typeof v==="string"&&/^[a-f0-9]{64}$/.test(v);
const stamp=v=>typeof v==="string"&&Number.isFinite(Date.parse(v));

export function trustedSourceUrl(value){
  try{
    const u=new URL(String(value));
    const hosts=new Set(["www.sebi.gov.in","sebi.gov.in","www.bseindia.com","bseindia.com","www.likhitha.co.in","likhitha.co.in","nsearchives.nseindia.com"]);
    return u.protocol==="https:"&&!u.username&&!u.password&&hosts.has(u.hostname.toLowerCase())?u.href:null;
  }catch{return null;}
}
function detectedType(bytes,contentType,url){
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
  if(review?.schema_version!=="1.0.0"||review?.status!=="reviewed_bse_2020_unmatched_issuer_batch"||
     review?.source_year!==2020||review?.import_allowed!==false||review?.publication_change!==false||
     !Array.isArray(review.actions)||review.actions.length!==4||!Array.isArray(review.sources)||review.sources.length!==11)
    throw new Error("invalid_bse_2020_unmatched_review");
  const expected=new Map([["Likhitha Infrastructure Limited","543240"],["SecMark Consultancy Limited","543234"],["SM Auto Stamping Limited","543065"],["Shine Fashions (India) Limited","543244"]]);
  const actionKeys=new Set();
  for(const action of review.actions){
    if(actionKeys.has(action.key)||expected.get(action.issuer_name)!==action.bse_scrip_code||
       action.bse_audit_match!=="unmatched"||action.decision!=="confirmed_missing_historical_ipo_candidate")
      throw new Error("invalid_bse_2020_unmatched_action:"+action?.key);
    actionKeys.add(action.key);
  }
  if(actionKeys.size!==4)throw new Error("invalid_bse_2020_unmatched_action_count");
  const keys=new Set(),urls=new Set();
  for(const source of review.sources){
    if(!source.key||keys.has(source.key)||!trustedSourceUrl(source.url)||urls.has(source.url)||!source.projection||!hash(source.projection_sha256)||
       sha256(Buffer.from(canonical(source.projection)))!==source.projection_sha256)
      throw new Error("invalid_bse_2020_unmatched_source:"+source?.key);
    keys.add(source.key);urls.add(source.url);
  }
  for(const action of review.actions){
    for(const key of [...(action.identity_sources||[]),...Object.values(action.field_sources||{})])
      if(!keys.has(key))throw new Error("missing_bse_2020_unmatched_source:"+action.key+":"+key);
  }
  return{actions:actionKeys.size,sources:keys.size};
}
export async function collect({review,reviewBytes,outDir,fetchImpl=fetch,clock=()=>new Date().toISOString()}){
  validateReview(review);if(!Buffer.isBuffer(reviewBytes))reviewBytes=Buffer.from(reviewBytes);
  fs.mkdirSync(outDir,{recursive:true});let total=0;const documents=[];
  for(const source of review.sources){
    const requested_at=clock(),url=trustedSourceUrl(source.url);
    const response=await fetchImpl(url,{redirect:"follow",signal:AbortSignal.timeout(45000),headers:{"user-agent":UA,accept:"application/pdf,text/html,*/*","cache-control":"no-cache"}});
    const final_url=trustedSourceUrl(response.url||url);
    if(!response.ok||!final_url)throw new Error("source_fetch_failed:"+source.key+":"+response.status);
    const bytes=await body(response,MAX_FILE);total+=bytes.length;if(total>MAX_TOTAL)throw new Error("total_size_limit");
    const type=detectedType(bytes,response.headers.get("content-type"),final_url);
    if(!type)throw new Error("unrecognized_source_type:"+source.key);
    const file=source.key+type.ext;fs.writeFileSync(path.join(outDir,file),bytes);
    documents.push({key:source.key,authority:source.authority,document_type:source.document_type,source_url:url,final_url,
      http_status:response.status,content_type:response.headers.get("content-type"),detected_type:type.kind,response_bytes:bytes.length,
      response_sha256:sha256(bytes),requested_at,collected_at:clock(),evidence_file:file,projection_sha256:source.projection_sha256});
  }
  const receipt={schema_version:"1.0.0",collector_version:"1.0.0",status:"complete",review_path:REVIEW_PATH,review_sha256:sha256(reviewBytes),
    collection_started_at:documents[0].requested_at,collection_completed_at:documents.at(-1).collected_at,
    source_documents_expected:review.sources.length,source_documents_collected:documents.length,total_response_bytes:total,
    documents,workflow_run_id:null,workflow_artifact:null,import_allowed:false};
  validateReceipt(receipt,review,reviewBytes);return receipt;
}
export function validateReceipt(receipt,review,reviewBytes){
  const expected=validateReview(review);if(!Buffer.isBuffer(reviewBytes))reviewBytes=Buffer.from(reviewBytes);
  if(receipt?.schema_version!=="1.0.0"||receipt?.collector_version!=="1.0.0"||receipt?.status!=="complete"||
    receipt.review_path!==REVIEW_PATH||receipt.review_sha256!==sha256(reviewBytes)||receipt.source_documents_expected!==expected.sources||
    receipt.source_documents_collected!==expected.sources||!Array.isArray(receipt.documents)||receipt.documents.length!==expected.sources||
    !stamp(receipt.collection_started_at)||!stamp(receipt.collection_completed_at)||receipt.import_allowed!==false)
    throw new Error("invalid_bse_2020_unmatched_receipt");
  let total=0;const keys=new Set();
  const sourceMap=new Map(review.sources.map(s=>[s.key,s]));
  for(const d of receipt.documents){
    const source=sourceMap.get(d.key);
    if(!source||keys.has(d.key)||d.source_url!==source.url||d.projection_sha256!==source.projection_sha256||
      !hash(d.response_sha256)||!Number.isSafeInteger(d.response_bytes)||d.response_bytes<=0||!stamp(d.requested_at)||!stamp(d.collected_at)||
      !trustedSourceUrl(d.final_url))throw new Error("invalid_bse_2020_unmatched_receipt_document:"+d?.key);
    keys.add(d.key);total+=d.response_bytes;
  }
  if(total!==receipt.total_response_bytes)throw new Error("bse_2020_unmatched_receipt_byte_mismatch");
  return{documents:keys.size,bytes:total};
}
if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url){
  const args=Object.fromEntries(process.argv.slice(2).map(arg=>{const i=arg.indexOf("=");if(i<1)throw new Error("arguments_must_use_equals");return[arg.slice(2,i),arg.slice(i+1)];}));
  try{
    const reviewFile=args.review||REVIEW_PATH,reviewBytes=fs.readFileSync(path.resolve(ROOT,reviewFile)),review=JSON.parse(reviewBytes);
    if(args["evidence-dir"]&&args.receipt){
      const receipt=await collect({review,reviewBytes,outDir:args["evidence-dir"]});
      fs.writeFileSync(args.receipt,JSON.stringify(receipt,null,2)+"\n");
      console.log(JSON.stringify({bse_2020_unmatched_evidence:{documents:receipt.source_documents_collected,bytes:receipt.total_response_bytes}}));
    }else if(args["validate-receipt"]){
      const receipt=JSON.parse(fs.readFileSync(path.resolve(ROOT,args["validate-receipt"]),"utf8"));
      console.log(JSON.stringify({bse_2020_unmatched_receipt:validateReceipt(receipt,review,reviewBytes)}));
    }else throw new Error("--evidence-dir/--receipt or --validate-receipt required");
  }catch(error){console.error(error);process.exitCode=1;}
}
