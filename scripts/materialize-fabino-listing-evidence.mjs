import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
export const REVIEW_PATH="data/discovery/bse-fabino-listing-year-review-2026-09-26.json";
export const RECEIPT_PATH="data/evidence/fabino-listing-year-source-receipt-2026-09-26.json";
export const MAX_SOURCE_BYTES=60*1024*1024;
export const MAX_TOTAL_BYTES=160*1024*1024;
const USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";
export const sha256=value=>createHash("sha256").update(value).digest("hex");
const validHash=value=>typeof value==="string"&&/^[a-f0-9]{64}$/.test(value);
const stamp=value=>typeof value==="string"&&Number.isFinite(Date.parse(value));

export function trustedFabinoSourceUrl(value){
  try{
    const url=new URL(String(value));
    if(url.protocol!=="https:"||url.username||url.password)return null;
    const hosts=new Set(["www.bseindia.com","bseindia.com","www.sebi.gov.in","sebi.gov.in"]);
    return hosts.has(url.hostname.toLowerCase())?url.href:null;
  }catch{return null;}
}

function detectedType(bytes,contentType,sourceUrl){
  const ct=String(contentType??"").toLowerCase();
  if(bytes.subarray(0,5).toString("ascii")==="%PDF-")return{kind:"pdf",extension:".pdf"};
  const prefix=bytes.subarray(0,Math.min(bytes.length,512)).toString("utf8").trimStart().toLowerCase();
  if(ct.includes("text/html")||prefix.startsWith("<!doctype html")||prefix.startsWith("<html"))return{kind:"html",extension:".html"};
  try{
    const ext=path.extname(new URL(sourceUrl).pathname).toLowerCase();
    if([".html",".htm"].includes(ext))return{kind:"html",extension:".html"};
  }catch{}
  return null;
}
async function readLimited(response,maxBytes){
  if(!response.body){
    const bytes=Buffer.from(await response.arrayBuffer());
    if(bytes.length>maxBytes)throw new Error("fabino_source_size_limit");
    return bytes;
  }
  const chunks=[];let size=0;
  for await(const chunk of response.body){
    size+=chunk.length;
    if(size>maxBytes)throw new Error("fabino_source_size_limit");
    chunks.push(Buffer.from(chunk));
  }
  return Buffer.concat(chunks);
}

export function validateFabinoReview(review){
  if(review?.schema_version!=="1.0.0"||review?.status!=="resolved_bse_listing_year_conflict_import_pending"||
     review?.issuer?.issuer_name!=="Fabino Life Sciences Limited"||review?.issuer?.bse_scrip_code!=="543444"||
     review?.issuer?.isin!=="INE0DRT01018"||review?.decision?.correct_listing_date!=="2022-01-13"||
     !Array.isArray(review.sources)||review.sources.length!==4){
    throw new Error("invalid_fabino_listing_year_review");
  }
  const keys=new Set(),urls=new Set();
  for(const source of review.sources){
    if(!source?.key||keys.has(source.key)||!trustedFabinoSourceUrl(source.url)||urls.has(source.url)||
       !source.projection||!validHash(source.projection_sha256)||
       sha256(Buffer.from(JSON.stringify(source.projection)))!==source.projection_sha256){
      throw new Error("invalid_fabino_source_review");
    }
    keys.add(source.key);urls.add(source.url);
  }
  return{source_keys:keys,source_urls:urls};
}

export async function collectFabinoEvidence({
  review,reviewBytes,evidenceDir,fetchImpl=fetch,clock=()=>new Date().toISOString(),
  maxSourceBytes=MAX_SOURCE_BYTES,maxTotalBytes=MAX_TOTAL_BYTES
}){
  validateFabinoReview(review);
  if(!Buffer.isBuffer(reviewBytes))reviewBytes=Buffer.from(reviewBytes);
  fs.mkdirSync(evidenceDir,{recursive:true});
  const documents=[];let totalBytes=0;
  for(const source of review.sources){
    const requestedAt=clock();
    const requestedUrl=trustedFabinoSourceUrl(source.url);
    const response=await fetchImpl(requestedUrl,{
      redirect:"follow",
      signal:AbortSignal.timeout(45000),
      headers:{"user-agent":USER_AGENT,accept:"application/pdf,text/html,application/xhtml+xml;q=0.9,*/*;q=0.4","cache-control":"no-cache"}
    });
    const finalUrl=trustedFabinoSourceUrl(response.url||requestedUrl);
    if(!response.ok||!finalUrl)throw new Error("fabino_source_fetch_failed:"+source.key+":"+response.status);
    const bytes=await readLimited(response,maxSourceBytes);
    totalBytes+=bytes.length;
    if(totalBytes>maxTotalBytes)throw new Error("fabino_source_total_size_limit");
    const type=detectedType(bytes,response.headers?.get?.("content-type"),finalUrl);
    if(!type)throw new Error("fabino_source_type_unrecognized:"+source.key);
    const evidenceFile=source.key+type.extension;
    fs.writeFileSync(path.join(evidenceDir,evidenceFile),bytes);
    documents.push({
      key:source.key,authority:source.authority,document_type:source.document_type,
      source_url:requestedUrl,final_url:finalUrl,http_status:response.status,
      content_type:response.headers?.get?.("content-type")??null,detected_type:type.kind,
      response_bytes:bytes.length,response_sha256:sha256(bytes),requested_at:requestedAt,collected_at:clock(),
      evidence_file:evidenceFile,page:source.page??null,evidence_locator:source.evidence_locator??null,
      projection_sha256:source.projection_sha256
    });
  }
  const receipt={
    schema_version:"1.0.0",collector_version:"1.0.0",status:"complete",
    review_path:REVIEW_PATH,review_sha256:sha256(reviewBytes),
    collection_started_at:documents[0]?.requested_at??clock(),
    collection_completed_at:documents.at(-1)?.collected_at??clock(),
    source_documents_expected:review.sources.length,source_documents_collected:documents.length,
    total_response_bytes:totalBytes,documents,workflow_artifact:null,import_allowed:false,
    note:"Original source bytes are retained in the associated GitHub Actions artifact. The repository receipt retains exact official URLs, per-document SHA-256 hashes, byte counts and locators. Import is a separate reviewed step."
  };
  validateFabinoReceipt(receipt,review,reviewBytes);
  return receipt;
}

export function validateFabinoReceipt(receipt,review,reviewBytes){
  const {source_keys}=validateFabinoReview(review);
  if(!Buffer.isBuffer(reviewBytes))reviewBytes=Buffer.from(reviewBytes);
  if(receipt?.schema_version!=="1.0.0"||receipt?.collector_version!=="1.0.0"||receipt?.status!=="complete"||
     receipt.review_path!==REVIEW_PATH||receipt.review_sha256!==sha256(reviewBytes)||
     !stamp(receipt.collection_started_at)||!stamp(receipt.collection_completed_at)||
     !Array.isArray(receipt.documents)||receipt.documents.length!==review.sources.length||
     receipt.source_documents_expected!==review.sources.length||receipt.source_documents_collected!==review.sources.length){
    throw new Error("invalid_fabino_evidence_receipt");
  }
  const keys=new Set(),files=new Set();let bytes=0;
  for(const doc of receipt.documents){
    if(!source_keys.has(doc.key)||keys.has(doc.key)||files.has(doc.evidence_file)||
       !trustedFabinoSourceUrl(doc.source_url)||!trustedFabinoSourceUrl(doc.final_url)||doc.http_status!==200||
       !["pdf","html"].includes(doc.detected_type)||!Number.isInteger(doc.response_bytes)||doc.response_bytes<=0||
       !validHash(doc.response_sha256)||!stamp(doc.requested_at)||!stamp(doc.collected_at)||
       typeof doc.evidence_file!=="string"||!/^[A-Za-z0-9._-]+\.(?:pdf|html)$/.test(doc.evidence_file)){
      throw new Error("invalid_fabino_evidence_document:"+(doc?.key??"unknown"));
    }
    keys.add(doc.key);files.add(doc.evidence_file);bytes+=doc.response_bytes;
  }
  if(bytes!==receipt.total_response_bytes)throw new Error("fabino_evidence_byte_count_mismatch");
  return{documents:receipt.documents.length,bytes};
}

async function run(){
  const args=Object.fromEntries(process.argv.slice(2).map(arg=>{
    const i=arg.indexOf("=");if(i<1)throw new Error("arguments_must_use_equals");return[arg.slice(0,i),arg.slice(i+1)];
  }));
  const reviewPath=args["--review"]||REVIEW_PATH;
  const reviewFile=path.isAbsolute(reviewPath)?reviewPath:path.join(ROOT,reviewPath);
  const reviewBytes=fs.readFileSync(reviewFile),review=JSON.parse(reviewBytes);
  if(args["--validate-receipt"]){
    const file=path.isAbsolute(args["--validate-receipt"])?args["--validate-receipt"]:path.join(ROOT,args["--validate-receipt"]);
    const receipt=JSON.parse(fs.readFileSync(file,"utf8"));
    const result=validateFabinoReceipt(receipt,review,reviewBytes);
    if(!receipt.workflow_artifact?.artifact_id||!/^sha256:[a-f0-9]{64}$/.test(receipt.workflow_artifact?.artifact_digest||"")||
       receipt.workflow_artifact?.retention_days!==14)throw new Error("missing_fabino_artifact_identity");
    console.log(JSON.stringify({fabino_evidence_receipt:result,artifact_id:receipt.workflow_artifact.artifact_id,artifact_digest:receipt.workflow_artifact.artifact_digest}));
    return;
  }
  const evidenceDir=args["--evidence-dir"],receiptPath=args["--receipt"];
  if(!evidenceDir||!receiptPath)throw new Error("--evidence-dir and --receipt are required");
  const receipt=await collectFabinoEvidence({review,reviewBytes,evidenceDir});
  fs.mkdirSync(path.dirname(receiptPath),{recursive:true});
  fs.writeFileSync(receiptPath,JSON.stringify(receipt,null,2)+"\n");
  console.log(JSON.stringify({fabino_evidence:{documents:receipt.source_documents_collected,bytes:receipt.total_response_bytes,review_sha256:receipt.review_sha256}}));
}
const isMain=process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url;
if(isMain)run().catch(error=>{console.error(error);process.exit(1);});
