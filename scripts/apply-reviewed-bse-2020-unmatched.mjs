import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {validateReview,validateReceipt} from "./materialize-bse-2020-unmatched-evidence.mjs";
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const REVIEW="data/discovery/bse-2020-unmatched-review-2026-09-26.json";
const RECEIPT="data/evidence/bse-2020-unmatched-source-receipt-2026-09-26.json";
const MANIFEST="data/verified-bse-listings/2026-09-26-bse-2020-unmatched-four.json";
const TARGET="data/recovery/2020/nse-issue-information.json";
const CHECK=process.argv.includes("--check");
const read=p=>JSON.parse(fs.readFileSync(path.join(ROOT,p),"utf8"));
const reviewBytes=fs.readFileSync(path.join(ROOT,REVIEW)),review=JSON.parse(reviewBytes),receipt=read(RECEIPT),manifest=read(MANIFEST);
validateReview(review);validateReceipt(receipt,review,reviewBytes);
if(manifest?.status!=="approved_bse_2020_unmatched_import"||manifest.target_year!==2020||manifest.actions?.length!==4)throw new Error("invalid_manifest");
const sources=new Map(review.sources.map(s=>[s.key,s])),docs=new Map(receipt.documents.map(d=>[d.key,d]));
const actions=new Map(review.actions.map(a=>[a.key,a]));
const descriptor=key=>{const s=sources.get(key),d=docs.get(key);if(!s||!d||s.url!==d.source_url||s.projection_sha256!==d.projection_sha256)throw new Error("source_receipt_mismatch:"+key);return{url:s.url,document_type:s.document_type,document_identity:s.document_type+" ["+key+"]",publication_date:s.publication_date??null,page:s.page??null,collected_at:d.collected_at,document_sha256:d.response_sha256};};
const field=(value,key)=>{if(value==null)return{value:null,status:"missing",source:null,corrections:[]};const source=descriptor(key);return{value,source_value:value,status:"verified",page:source.page,source,corrections:[]};};
const document=key=>{const s=descriptor(key);return{type:s.document_type,identity:s.document_identity,url:s.url,publication_date:s.publication_date,collected_at:s.collected_at,document_sha256:s.document_sha256};};
function record(entry){
 const a=actions.get(entry.key); if(!a||a.stable_id!==entry.stable_id)throw new Error("manifest_review_mismatch:"+entry.key);
 const t=a.target, keys=[...(a.identity_sources||[]),...Object.values(a.field_sources||{})], unique=[...new Set(keys)].filter(key=>key!=="likhitha_issuer_investors");
 const get=n=>a.field_sources?.[n];
 return {id:a.stable_id,issuer_name:a.issuer_name,board:t.board,sector:null,status:"listed",
  nse_symbol:t.nse_symbol??null,nse_series:t.nse_symbol?"EQ":null,nse_source:t.nse_symbol?descriptor(get("nse_symbol")):null,
  bse_symbol:t.bse_symbol??null,bse_scrip_code:a.bse_scrip_code,isin:t.isin??null,bse_source:descriptor(get("bse_scrip_code")),
  terms:{price_band:null,market_lot:null,minimum_bid_quantity:null,open_date:null,close_date:null},
  documents:unique.map(document),first_observed_at:receipt.collection_completed_at,last_collected_at:receipt.collection_completed_at,
  board_evidence:[descriptor(get("board"))],status_evidence:[descriptor(get("listing_date"))],
  price_band:{value:null,status:"missing",source:null,corrections:[]},issue_price:field(t.issue_price,get("issue_price")),
  issue_size_inr:{value:null,status:"missing",source:null,corrections:[]},
  market_lot:field(t.market_lot??null,get("market_lot")),minimum_bid_quantity:{value:null,status:"missing",source:null,corrections:[]},
  open_date:field(t.open_date??null,get("open_date")),close_date:field(t.close_date??null,get("close_date")),
  listing_date:field(t.listing_date,get("listing_date")),
  bse_2020_unmatched_import:{manifest:MANIFEST,review:REVIEW,receipt:RECEIPT,action_key:a.key,artifact_id:receipt.workflow_artifact?.artifact_id??null,artifact_digest:receipt.workflow_artifact?.artifact_digest??null}
 };
}
const target=read(TARGET), existing=new Map((target.records||[]).map(r=>[r.id,r]));
for(const m of manifest.actions){const next=record(m),old=existing.get(next.id);if(old&&JSON.stringify(old)!==JSON.stringify(next))throw new Error("collision:"+next.id);existing.set(next.id,next);}
target.records=[...existing.values()];
const out=JSON.stringify(target,null,2)+"\n",current=fs.readFileSync(path.join(ROOT,TARGET),"utf8");
if(CHECK){const parsed=JSON.parse(out);for(const m of manifest.actions){const r=parsed.records.find(x=>x.id===m.stable_id);if(!r)throw new Error("missing:"+m.stable_id);}console.log(JSON.stringify({bse_2020_unmatched_import:{records:4,changed:out!==current}}));}
else if(out!==current)fs.writeFileSync(path.join(ROOT,TARGET),out);
