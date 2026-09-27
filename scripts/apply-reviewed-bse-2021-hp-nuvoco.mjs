import fs from "node:fs";
import path from "node:path";
import {isDeepStrictEqual as same} from "node:util";
import {fileURLToPath,pathToFileURL} from "node:url";

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
export const REVIEW="data/discovery/bse-2021-hp-nuvoco-review-2026-09-27.json";
export const RECEIPT="data/evidence/bse-2021-hp-nuvoco-source-receipt-2026-09-27.json";
export const MANIFEST="data/verified-bse-listings/2026-09-27-hp-nuvoco.json";
const TARGET="data/recovery/2021/nse-issue-information.json";
export const FIELDS=["price_band","issue_price","issue_size_inr","market_lot","minimum_bid_quantity","open_date","close_date","listing_date"];
const read=p=>JSON.parse(fs.readFileSync(path.join(ROOT,p),"utf8"));
const req=(ok,m)=>{if(!ok)throw new Error(m)};
export const issuerKey=v=>String(v??"").toLowerCase().replace(/&/g," and ").replace(/\bltd\.?\b/g," limited ").replace(/[^a-z0-9]+/g," ").replace(/\blimited\s*$/g,"").replace(/\s+/g," ").trim();
const missing=()=>({value:null,status:"missing",source:null,corrections:[]});

export function context(){
  const review=read(REVIEW),receipt=read(RECEIPT),manifest=read(MANIFEST);
  req(review?.schema_version==="1.0.0"&&review.actions?.length===2&&review.sources?.length===3,"invalid_review_scope");
  req(receipt?.status==="reviewed_original_sebi_documents"&&receipt.documents?.length===3,"invalid_receipt_scope");
  req(manifest?.status==="approved_bse_2021_hp_nuvoco_import"&&manifest.actions?.length===2&&manifest.target_year===2021,"invalid_manifest_scope");
  req(receipt.artifact_id===manifest.source_artifact_id&&receipt.artifact_sha256===manifest.source_artifact_sha256,"artifact_binding_mismatch");
  req(receipt.documents.reduce((n,d)=>n+d.response_bytes,0)===receipt.total_response_bytes,"receipt_byte_mismatch");
  const docs=new Map(receipt.documents.map(d=>[d.key,d])),sources=new Map(review.sources.map(s=>[s.key,s]));
  for(const [key,s] of sources){
    const d=docs.get(key);
    req(d&&d.source_url===s.url&&d.final_url===s.url&&d.http_status===200&&Number.isSafeInteger(d.response_bytes)&&d.response_bytes>0&&/^[a-f0-9]{64}$/.test(d.response_sha256),"source_receipt_mismatch:"+key);
    req(new URL(s.url).hostname==="www.sebi.gov.in","unsupported_source_host:"+key);
  }
  return{review,receipt,manifest,docs,sources};
}
function descriptor(ctx,key,issuer){
  const s=ctx.sources.get(key),d=ctx.docs.get(key);
  req(s&&d&&issuerKey(s.projection?.issuer)===issuerKey(issuer),"source_issuer_mismatch:"+key);
  return{url:s.url,document_type:s.document_type,document_identity:issuer+" — "+s.document_type+" ["+key+"]",publication_date:s.publication_date??null,page:s.page??null,collected_at:d.collected_at,document_sha256:d.response_sha256,evidence_locator:s.evidence_locator??null};
}
function supported(ctx,a,name,value){
  if(value==null)return null;
  const key=a.field_sources?.[name],s=ctx.sources.get(key);
  req(key&&s&&same(s.projection?.[name],value),"projection_mismatch:"+a.key+":"+name);
  return descriptor(ctx,key,a.issuer_name);
}
const field=(value,source)=>value==null?missing():({value,source_value:value,status:"verified",page:source.page,source,corrections:[]});

export function expected(ctx){
  const actions=new Map(ctx.review.actions.map(a=>[a.key,a]));
  return ctx.manifest.actions.map(m=>{
    const a=actions.get(m.key);
    req(a&&a.stable_id===m.stable_id&&a.decision==="confirmed_missing_historical_ipo_candidate","manifest_review_mismatch:"+m.key);
    req((a.identity_sources||[]).some(k=>ctx.sources.get(k)?.projection?.issue_type==="IPO"),"ipo_identity_not_supported:"+a.key);
    const t=a.target,src={};
    for(const name of ["listing_date","issue_price","issue_size_inr","open_date","close_date","market_lot","minimum_bid_quantity"]) if(t[name]!=null)src[name]=supported(ctx,a,name,t[name]);
    const keys=[...new Set([...(a.identity_sources||[]),...Object.values(a.field_sources||{})])];
    const docs=keys.map(k=>descriptor(ctx,k,a.issuer_name));
    const last=[...docs].map(d=>d.collected_at).sort().at(-1);
    const out={
      id:a.stable_id,issuer_name:a.issuer_name,board:null,sector:null,status:"listed",
      nse_symbol:null,nse_series:null,nse_source:null,bse_symbol:null,bse_scrip_code:null,isin:null,bse_source:null,
      terms:{price_band:null,market_lot:null,minimum_bid_quantity:null,open_date:null,close_date:null},
      documents:docs.map(s=>({type:s.document_type,identity:s.document_identity,url:s.url,publication_date:s.publication_date,collected_at:s.collected_at,document_sha256:s.document_sha256})),
      first_observed_at:last,last_collected_at:last,board_evidence:[],status_evidence:[src.listing_date],
      bse_2021_hp_nuvoco_import:{manifest:MANIFEST,review:REVIEW,receipt:RECEIPT,action_key:a.key,discovery_bse_scrip_code:a.discovery_bse_scrip_code,artifact_id:ctx.receipt.artifact_id,artifact_sha256:ctx.receipt.artifact_sha256}
    };
    for(const name of FIELDS)out[name]=field(t[name]??null,src[name]??null);
    return out;
  });
}
export function loadRecovery(){
  const dir=path.join(ROOT,"data/recovery");
  return Object.fromEntries(fs.readdirSync(dir).filter(y=>/^20\d{2}$/.test(y)&&fs.existsSync(path.join(dir,y,"nse-issue-information.json"))).map(y=>[y,read("data/recovery/"+y+"/nse-issue-information.json")]));
}
function assertExisting(old,next){
  req(old.issuer_name===next.issuer_name&&old.status===next.status,"changed_import_identity:"+next.id);
  for(const name of FIELDS.filter(k=>next[k].value!=null))req(same(old[name],next[name]),"changed_import_fact:"+next.id+":"+name);
  req(old.board===null&&old.bse_scrip_code===null,"changed_import_identity_fields:"+next.id);
  req(same(old.bse_2021_hp_nuvoco_import,next.bse_2021_hp_nuvoco_import),"changed_import_metadata:"+next.id);
}
export function apply(all,ctx,now){
  req(Number.isFinite(Date.parse(now)),"invalid_generation_clock");
  const out=structuredClone(all),rows=expected(ctx);
  req(Array.isArray(out["2021"]?.records),"missing_2021_recovery");
  const existing=Object.entries(out).flatMap(([year,m])=>(m.records||[]).map(record=>({year,record})));
  req(new Set(existing.map(x=>x.record.id)).size===existing.length,"duplicate_existing_id");
  let added=0,skipped=0;
  for(const next of rows){
    const discovery=next.bse_2021_hp_nuvoco_import.discovery_bse_scrip_code;
    const hits=existing.filter(({record:r})=>r.id===next.id||issuerKey(r.issuer_name)===issuerKey(next.issuer_name)||(discovery&&String(r.bse_scrip_code||"")===discovery));
    if(hits.length){
      req(hits.length===1&&hits[0].year==="2021"&&hits[0].record.id===next.id,"identity_collision:"+next.id);
      assertExisting(hits[0].record,next);skipped++;continue;
    }
    out["2021"].records.push(next);existing.push({year:"2021",record:next});added++;
  }
  if(added)out["2021"].generated_at=now;
  return{recovery:out,stats:{records:rows.length,added,skipped,changed:added>0}};
}
if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url){
  try{
    const arg=process.argv[2];req(["--check","--apply"].includes(arg),"use_--check_or_--apply");
    const x=apply(loadRecovery(),context(),new Date().toISOString());
    if(arg==="--apply"&&x.stats.changed)fs.writeFileSync(path.join(ROOT,TARGET),JSON.stringify(x.recovery["2021"],null,2)+"\n");
    console.log(JSON.stringify({bse_2021_hp_nuvoco:x.stats}));
  }catch(e){console.error(e.message);process.exitCode=1;}
}
