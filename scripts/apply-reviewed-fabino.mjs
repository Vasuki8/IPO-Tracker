import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { validateFabinoReceipt } from "./materialize-fabino-listing-evidence.mjs";

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
export const REVIEW_PATH="data/discovery/bse-fabino-listing-year-review-2026-09-26.json";
export const RECEIPT_PATH="data/evidence/fabino-listing-year-source-receipt-2026-09-26.json";
export const MANIFEST_PATH="data/verified-bse-listings/2026-09-26-fabino-correction.json";
const RECOVERY_ROOT=path.join(ROOT,"data","recovery");
const slug=value=>String(value??"").toLowerCase().replace(/&/g," and ").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");
const issuerKey=value=>String(value??"").toLowerCase().replace(/&/g," and ").replace(/\bltd\.?\b/g," limited ").replace(/[^a-z0-9]+/g," ").replace(/\blimited\s*$/g,"").replace(/\s+/g," ").trim();
const validDate=value=>typeof value==="string"&&/^\d{4}-\d\d-\d\d$/.test(value)&&new Date(value).toISOString().slice(0,10)===value;
const validIsin=value=>typeof value==="string"&&/^IN[A-Z0-9]{10}$/.test(value);
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const requireThat=(ok,msg)=>{if(!ok)throw new Error(msg);};

function sourceMaps(review,receipt){
  return{
    review:new Map(review.sources.map(source=>[source.key,source])),
    receipt:new Map(receipt.documents.map(doc=>[doc.key,doc]))
  };
}
function checkedSource(key,maps){
  const source=maps.review.get(key),doc=maps.receipt.get(key);
  requireThat(source&&doc,"missing_fabino_source:"+key);
  requireThat(source.url===doc.source_url&&source.projection_sha256===doc.projection_sha256,"fabino_source_receipt_mismatch:"+key);
  return{source,doc};
}
function evidence(key,maps){
  const {source,doc}=checkedSource(key,maps);
  return{
    url:source.url,
    document_type:source.document_type,
    document_identity:source.document_identity,
    publication_date:source.publication_date??null,
    page:source.page??null,
    collected_at:doc.collected_at,
    document_sha256:doc.response_sha256,
    evidence_locator:source.evidence_locator??null
  };
}
function verifiedField(value,sourceValue,key,maps,corrections=[]){
  const src=evidence(key,maps);
  return{value,source_value:sourceValue??value,status:"verified",page:src.page??null,source:src,corrections};
}

export function validateFabinoImportManifest(manifest,review,receipt,reviewBytes){
  validateFabinoReceipt(receipt,review,reviewBytes);
  requireThat(manifest?.schema_version==="1.0.0"&&manifest.importer_version==="1.0.0"&&
    manifest.status==="approved_fabino_listing_year_correction_and_historical_ipo_import"&&
    manifest.review_path===REVIEW_PATH&&manifest.receipt_path===RECEIPT_PATH&&
    manifest.issuer_name==="Fabino Life Sciences Limited"&&manifest.bse_scrip_code==="543444"&&
    manifest.bse_symbol==="FABINO"&&manifest.isin==="INE0DRT01018"&&manifest.board==="SME"&&
    manifest.target_year===2022&&manifest.listing_date==="2022-01-13","invalid_fabino_import_manifest");
  requireThat(receipt.workflow_artifact?.artifact_id&&/^sha256:[a-f0-9]{64}$/.test(receipt.workflow_artifact?.artifact_digest||""),"fabino_artifact_identity_missing");
  requireThat(review.decision.correct_listing_date===manifest.listing_date&&review.decision.correct_listing_year===2022,"fabino_review_manifest_date_mismatch");
  requireThat(review.issuer.bse_scrip_code===manifest.bse_scrip_code&&review.issuer.isin===manifest.isin&&review.issuer.board===manifest.board,"fabino_review_manifest_identity_mismatch");
  requireThat(validDate(manifest.listing_date)&&validIsin(manifest.isin),"invalid_fabino_identity");

  const maps=sourceMaps(review,receipt);
  const notice=checkedSource("bse_listing_notice",maps).source.projection;
  const index=checkedSource("bse_sme_index_press_release",maps).source.projection;
  const prospectus=checkedSource("bse_prospectus",maps).source.projection;
  const sebi=checkedSource("sebi_final_offer_page",maps).source.projection;

  requireThat(notice.bse_scrip_code===manifest.bse_scrip_code&&notice.symbol===manifest.bse_symbol&&notice.isin===manifest.isin&&
    notice.issue_price_inr===manifest.fields.issue_price.value&&notice.market_lot===manifest.fields.market_lot.value&&
    notice.conflicting_listing_statement===manifest.listing_date_correction.conflicting_source_value&&notice.corroborating_spos_date===manifest.listing_date,
    "fabino_listing_notice_projection_mismatch");
  requireThat(index.bse_scrip_code===manifest.bse_scrip_code&&index.listing_date===manifest.listing_date,"fabino_index_projection_mismatch");
  requireThat(prospectus.isin===manifest.isin&&prospectus.offer_open===manifest.fields.open_date.value&&
    prospectus.offer_close===manifest.fields.close_date.value&&prospectus.issue_price_inr===manifest.fields.issue_price.value&&
    prospectus.listing_venue==="BSE SME","fabino_prospectus_projection_mismatch");
  requireThat(sebi.label==="Fabino Life Sciences Limited-SME IPO","fabino_sebi_projection_mismatch");
  requireThat(manifest.fields.listing_date.source==="bse_sme_index_press_release"&&
    manifest.listing_date_correction.conflicting_source==="bse_listing_notice"&&
    manifest.listing_date_correction.resolved_source==="bse_sme_index_press_release"&&
    manifest.listing_date_correction.resolved_value===manifest.listing_date,"fabino_correction_policy_mismatch");
  return{maps,notice,index,prospectus,sebi};
}

export function fabinoRecoveryRecord(manifest,review,receipt,reviewBytes){
  const checked=validateFabinoImportManifest(manifest,review,receipt,reviewBytes),maps=checked.maps;
  const noticeEvidence=evidence("bse_listing_notice",maps);
  const indexEvidence=evidence("bse_sme_index_press_release",maps);
  const prospectusEvidence=evidence("bse_prospectus",maps);
  const correction={
    corrected_at:receipt.collection_completed_at,
    previous_value:"2021-01-13",
    previous_source_value:manifest.listing_date_correction.conflicting_source_value,
    replacement_value:manifest.listing_date,
    reason:manifest.listing_date_correction.reason,
    evidence:[{
      url:noticeEvidence.url,
      document_type:noticeEvidence.document_type,
      document_identity:noticeEvidence.document_identity,
      publication_date:noticeEvidence.publication_date,
      page:noticeEvidence.page,
      collected_at:noticeEvidence.collected_at
    },{
      url:indexEvidence.url,
      document_type:indexEvidence.document_type,
      document_identity:indexEvidence.document_identity,
      publication_date:indexEvidence.publication_date,
      page:indexEvidence.page,
      collected_at:indexEvidence.collected_at
    }]
  };
  return{
    id:slug(manifest.issuer_name),
    issuer_name:manifest.issuer_name,
    board:"SME",sector:null,status:"listed",
    nse_symbol:null,nse_series:null,nse_source:null,
    bse_symbol:manifest.bse_symbol,bse_scrip_code:manifest.bse_scrip_code,isin:manifest.isin,
    bse_source:{...indexEvidence},
    terms:{price_band:null,market_lot:null,minimum_bid_quantity:null,open_date:null,close_date:null},
    documents:manifest.documents.map(key=>{
      const src=evidence(key,maps);
      return{type:src.document_type,identity:src.document_identity,url:src.url,publication_date:src.publication_date,collected_at:src.collected_at,document_sha256:src.document_sha256};
    }),
    first_observed_at:receipt.collection_completed_at,
    last_collected_at:receipt.collection_completed_at,
    board_evidence:[{...noticeEvidence,page:null}],
    status_evidence:[{...indexEvidence,page:indexEvidence.page??null}],
    open_date:verifiedField(manifest.fields.open_date.value,manifest.fields.open_date.value,"bse_prospectus",maps),
    close_date:verifiedField(manifest.fields.close_date.value,manifest.fields.close_date.value,"bse_prospectus",maps),
    issue_price:verifiedField(manifest.fields.issue_price.value,"Issue Price for the current Public issue Rs. 36/- per share","bse_listing_notice",maps),
    market_lot:verifiedField(manifest.fields.market_lot.value,"Market Lot 3000","bse_listing_notice",maps),
    listing_date:verifiedField(manifest.listing_date,manifest.listing_date,"bse_sme_index_press_release",maps,[correction]),
    fabino_listing_year_correction:{
      manifest:MANIFEST_PATH,review:REVIEW_PATH,receipt:RECEIPT_PATH,importer_version:manifest.importer_version,
      workflow_run_id:receipt.workflow_run_id,artifact_id:receipt.workflow_artifact.artifact_id,
      artifact_digest:receipt.workflow_artifact.artifact_digest,
      conflict_preserved:true,
      notice_document_sha256:noticeEvidence.document_sha256,
      resolved_listing_document_sha256:indexEvidence.document_sha256
    }
  };
}

function matchRecord(record,candidate){
  return record?.id===candidate.id||
    issuerKey(record?.issuer_name)===issuerKey(candidate.issuer_name)||
    String(record?.bse_scrip_code||"")===candidate.bse_scrip_code||
    String(record?.isin||"").toUpperCase()===candidate.isin;
}
export function applyReviewedFabino(recoveryByYear,published,manifest,review,receipt,reviewBytes){
  const candidate=fabinoRecoveryRecord(manifest,review,receipt,reviewBytes);
  const recovery=structuredClone(recoveryByYear);
  const matches=Object.entries(recovery).flatMap(([year,data])=>(data.records||[]).filter(r=>matchRecord(r,candidate)).map(record=>({year,record})));
  const publicHits=(published.records||[]).filter(r=>r.id===candidate.id||issuerKey(r.issuer_name)===issuerKey(candidate.issuer_name));
  if(matches.length){
    requireThat(matches.length===1&&matches[0].year==="2022","fabino_cross_year_or_identity_collision");
    const existing=matches[0].record;
    requireThat(existing.id===candidate.id&&issuerKey(existing.issuer_name)===issuerKey(candidate.issuer_name)&&
      String(existing.bse_scrip_code||"")===candidate.bse_scrip_code&&String(existing.isin||"")===candidate.isin&&
      existing.listing_date?.value===candidate.listing_date.value&&existing.fabino_listing_year_correction?.manifest===MANIFEST_PATH,
      "fabino_existing_record_conflict");
    requireThat(publicHits.length<=1&&publicHits.every(r=>r.id===candidate.id),"fabino_public_identity_conflict");
    return{recovery,stats:{added:0,already_present:1},changed_years:[]};
  }
  requireThat(publicHits.length===0,"fabino_public_without_recovery");
  requireThat(recovery["2022"]?.records&&Array.isArray(recovery["2022"].records),"missing_2022_recovery");
  recovery["2022"].records.push(candidate);
  recovery["2022"].records.sort((a,b)=>a.issuer_name.localeCompare(b.issuer_name));
  recovery["2022"].generated_at=[recovery["2022"].generated_at,receipt.collection_completed_at].filter(Boolean).sort().at(-1);
  return{recovery,stats:{added:1,already_present:0},changed_years:["2022"]};
}
export function loadRecovery(root=ROOT){
  const result={};
  for(const year of fs.readdirSync(path.join(root,"data","recovery")).filter(x=>/^20\d{2}$/.test(x))){
    const file=path.join(root,"data","recovery",year,"nse-issue-information.json");
    if(fs.existsSync(file))result[year]=JSON.parse(fs.readFileSync(file,"utf8"));
  }
  return result;
}
function loadInputs(){
  const reviewBytes=fs.readFileSync(path.join(ROOT,REVIEW_PATH));
  return{
    reviewBytes,review:JSON.parse(reviewBytes),
    receipt:JSON.parse(fs.readFileSync(path.join(ROOT,RECEIPT_PATH),"utf8")),
    manifest:JSON.parse(fs.readFileSync(path.join(ROOT,MANIFEST_PATH),"utf8")),
    recovery:loadRecovery(ROOT),
    published:JSON.parse(fs.readFileSync(path.join(ROOT,"data","ipos.json"),"utf8"))
  };
}
function run(){
  requireThat(process.argv.slice(2).every(arg=>arg==="--check"),"only_--check_supported");
  const input=loadInputs(),plan=applyReviewedFabino(input.recovery,input.published,input.manifest,input.review,input.receipt,input.reviewBytes);
  if(process.argv.includes("--check")){
    console.log(JSON.stringify({reviewed_fabino_import:plan.stats,changed_years:plan.changed_years}));
    return;
  }
  for(const year of plan.changed_years)fs.writeFileSync(path.join(RECOVERY_ROOT,year,"nse-issue-information.json"),JSON.stringify(plan.recovery[year],null,2)+"\n");
  console.log(JSON.stringify({reviewed_fabino_import:plan.stats,changed_years:plan.changed_years}));
}
const isMain=process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url;
if(isMain){try{run();}catch(error){console.error(error);process.exit(1);}}
