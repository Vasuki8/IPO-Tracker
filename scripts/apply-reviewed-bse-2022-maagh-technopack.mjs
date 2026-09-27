import fs from "node:fs";
import path from "node:path";
import {isDeepStrictEqual as same} from "node:util";
import {fileURLToPath,pathToFileURL} from "node:url";
import {sha256,strictDate} from "./verify-bse-listing-candidates.mjs";

export const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
export const REVIEW="data/discovery/bse-2022-maagh-technopack-review-2026-09-27.json";
export const RECEIPT="data/evidence/bse-2022-maagh-technopack-source-receipt-2026-09-27.json";
export const MANIFEST="data/verified-bse-listings/2026-09-27-maagh-technopack.json";
const TARGET="data/recovery/2022/nse-issue-information.json";
export const FIELDS=["price_band","issue_price","issue_size_inr","market_lot","minimum_bid_quantity","open_date","close_date","listing_date"];
const read=p=>JSON.parse(fs.readFileSync(path.join(ROOT,p),"utf8"));
const bytes=p=>fs.readFileSync(path.join(ROOT,p));
const req=(x,m)=>{if(!x)throw Error(m)};
export const issuerKey=v=>String(v??"").toLowerCase().replace(/&/g," and ").replace(/\bltd\.?\b/g," limited ").replace(/[^a-z0-9]+/g," ").replace(/\blimited\s*$/g,"").replace(/\s+/g," ").trim();
const missing=()=>({value:null,status:"missing",source:null,corrections:[]});
const validTarget=(name,v)=>{
  if(v==null)return name==="price_band";
  if(["open_date","close_date","listing_date"].includes(name))return strictDate(v)===v;
  if(["market_lot","minimum_bid_quantity"].includes(name))return Number.isSafeInteger(v)&&v>0;
  return Number.isFinite(v)&&v>0;
};
export function context(){
  const review=read(REVIEW),receipt=read(RECEIPT),manifest=read(MANIFEST);
  req(review?.schema_version==="1.0.0"&&review.status==="reviewed_bse_2022_maagh_technopack"&&review.actions?.length===2&&review.sources?.length===4,"invalid_review_scope");
  req(receipt?.schema_version==="1.0.0"&&receipt.status==="reviewed_original_official_documents"&&receipt.documents?.length===4,"invalid_receipt_scope");
  req(manifest?.schema_version==="1.0.0"&&manifest.status==="approved_bse_2022_maagh_technopack_import"&&manifest.actions?.length===2&&manifest.target_year===2022,"invalid_manifest_scope");
  req(receipt.review_path===REVIEW&&receipt.review_sha256===sha256(bytes(REVIEW)),"review_receipt_binding_mismatch");
  req(manifest.review_path===REVIEW&&manifest.review_sha256===sha256(bytes(REVIEW)),"review_manifest_binding_mismatch");
  req(manifest.receipt_path===RECEIPT&&manifest.receipt_sha256===sha256(bytes(RECEIPT)),"receipt_manifest_binding_mismatch");
  req(receipt.artifact_id===manifest.source_artifact_id&&receipt.artifact_sha256===manifest.source_artifact_sha256,"artifact_binding_mismatch");
  req(receipt.documents.reduce((n,d)=>n+d.response_bytes,0)===receipt.total_response_bytes,"receipt_byte_mismatch");
  const docs=new Map(receipt.documents.map(d=>[d.key,d])),sources=new Map(review.sources.map(s=>[s.key,s]));
  req(docs.size===4&&sources.size===4,"duplicate_source_key");
  for(const[key,s]of sources){
    const d=docs.get(key);req(d&&d.source_url===s.url&&d.final_url===s.url&&d.http_status===200&&Number.isSafeInteger(d.response_bytes)&&d.response_bytes>0&&/^[a-f0-9]{64}$/.test(d.response_sha256),"source_receipt_mismatch:"+key);
    const u=new URL(s.url);req(u.protocol==="https:"&&["www.sebi.gov.in","www.bseindia.com"].includes(u.hostname)&&!u.username&&!u.password,"unsupported_source_host:"+key);
    req(strictDate(s.document_date)===s.document_date,"invalid_document_date:"+key);
    req(s.publication_date==null||strictDate(s.publication_date)===s.publication_date,"invalid_publication_date:"+key);
    req(typeof s.document_identity==="string"&&s.document_identity.length>12,"missing_document_identity:"+key);
  }
  const actions=new Map(review.actions.map(a=>[a.key,a]));req(actions.size===2,"duplicate_action_key");
  for(const a of review.actions){
    req(a.decision==="confirmed_missing_historical_ipo_candidate"&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(a.stable_id),"invalid_action:"+a.key);
    req(/^\d{6}$/.test(a.discovery_bse_scrip_code)&&a.identity_sources?.length>=2,"invalid_identity:"+a.key);
    req(a.identity_sources.some(k=>sources.get(k)?.projection?.issue_type==="IPO"),"ipo_identity_not_supported:"+a.key);
    req(a.target.board==="SME","invalid_board:"+a.key);
    for(const name of FIELDS){req(validTarget(name,a.target[name]),"invalid_field:"+a.key+":"+name);if(a.target[name]!=null){const key=a.field_sources?.[name],s=sources.get(key);req(key&&s&&issuerKey(s.projection?.issuer)===issuerKey(a.issuer_name)&&same(s.projection?.[name],a.target[name]),"projection_mismatch:"+a.key+":"+name)}}
    const bs=sources.get(a.field_sources?.board);req(bs&&bs.projection?.board==="SME","board_projection_mismatch:"+a.key);
  }
  return{review,receipt,manifest,docs,sources,actions};
}
function descriptor(ctx,key,issuer,page=null,locator=null){
  const s=ctx.sources.get(key),d=ctx.docs.get(key);req(s&&d&&issuerKey(s.projection?.issuer)===issuerKey(issuer),"source_issuer_mismatch:"+key);
  return{url:s.url,document_type:s.document_type,document_identity:s.document_identity,publication_date:s.publication_date??null,page,collected_at:d.collected_at,document_sha256:d.response_sha256,evidence_locator:locator};
}
const field=(v,s)=>v==null?missing():({value:v,source_value:v,status:"verified",page:s.page,source:s,corrections:[]});
export function expected(ctx){
  const manifestActions=new Map(ctx.manifest.actions.map(a=>[a.key,a]));
  return ctx.review.actions.map(a=>{
    const m=manifestActions.get(a.key);req(m&&m.stable_id===a.stable_id,"manifest_review_mismatch:"+a.key);
    const src={};
    for(const name of FIELDS){if(a.target[name]!=null){const k=a.field_sources[name];src[name]=descriptor(ctx,k,a.issuer_name,null,ctx.sources.get(k)?.evidence_locator??null)}}
    const boardSource=descriptor(ctx,a.field_sources.board,a.issuer_name,null,ctx.sources.get(a.field_sources.board)?.evidence_locator??null);
    const docs=[...new Set(a.identity_sources)].map(k=>descriptor(ctx,k,a.issuer_name));
    const last=docs.map(d=>d.collected_at).sort().at(-1);
    const out={id:a.stable_id,issuer_name:a.issuer_name,board:a.target.board,sector:null,status:"listed",nse_symbol:null,nse_series:null,nse_source:null,bse_symbol:null,bse_scrip_code:null,isin:null,bse_source:null,terms:{price_band:null,market_lot:null,minimum_bid_quantity:null,open_date:null,close_date:null},documents:docs.map(s=>({type:s.document_type,identity:s.document_identity,url:s.url,publication_date:s.publication_date,collected_at:s.collected_at,document_sha256:s.document_sha256})),first_observed_at:last,last_collected_at:last,board_evidence:[boardSource],status_evidence:[src.listing_date],bse_2022_maagh_technopack_import:{manifest:MANIFEST,review:REVIEW,receipt:RECEIPT,action_key:a.key,discovery_bse_scrip_code:a.discovery_bse_scrip_code,artifact_id:ctx.receipt.artifact_id,artifact_sha256:ctx.receipt.artifact_sha256}};
    for(const name of FIELDS)out[name]=field(a.target[name]??null,src[name]??null);
    return out;
  });
}
export function loadRecovery(){const dir=path.join(ROOT,"data/recovery");return Object.fromEntries(fs.readdirSync(dir).filter(y=>/^20\d{2}$/.test(y)&&fs.existsSync(path.join(dir,y,"nse-issue-information.json"))).map(y=>[y,read("data/recovery/"+y+"/nse-issue-information.json")]))}
function assertExisting(old,next){req(old.issuer_name===next.issuer_name&&old.status===next.status&&old.board===next.board,"changed_import_identity:"+next.id);for(const name of FIELDS)req(same(old[name],next[name]),"changed_import_fact:"+next.id+":"+name);req(old.bse_scrip_code===null,"changed_bse_identity:"+next.id);req(same(old.bse_2022_maagh_technopack_import,next.bse_2022_maagh_technopack_import),"changed_import_metadata:"+next.id)}
export function apply(all,ctx,now){
  req(Number.isFinite(Date.parse(now)),"invalid_generation_clock");const out=structuredClone(all),rows=expected(ctx);req(Array.isArray(out["2022"]?.records),"missing_2022_recovery");
  const existing=Object.entries(out).flatMap(([year,m])=>(m.records||[]).map(record=>({year,record})));req(new Set(existing.map(x=>x.record.id)).size===existing.length,"duplicate_existing_id");let added=0,skipped=0;
  for(const next of rows){const discovery=next.bse_2022_maagh_technopack_import.discovery_bse_scrip_code,hits=existing.filter(({record:r})=>r.id===next.id||issuerKey(r.issuer_name)===issuerKey(next.issuer_name)||(discovery&&String(r.bse_scrip_code||"")===discovery));if(hits.length){req(hits.length===1&&hits[0].year==="2022"&&hits[0].record.id===next.id,"identity_collision:"+next.id);assertExisting(hits[0].record,next);skipped++;continue}out["2022"].records.push(next);existing.push({year:"2022",record:next});added++}
  if(added)out["2022"].generated_at=now;return{recovery:out,stats:{records:rows.length,added,skipped,changed:added>0}};
}
if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url){try{const arg=process.argv[2];req(["--check","--apply"].includes(arg),"use_--check_or_--apply");const x=apply(loadRecovery(),context(),new Date().toISOString());if(arg==="--apply"&&x.stats.changed)fs.writeFileSync(path.join(ROOT,TARGET),JSON.stringify(x.recovery["2022"],null,2)+"\n");console.log(JSON.stringify({bse_2022_maagh_technopack:x.stats}))}catch(e){console.error(e.message);process.exitCode=1}}
