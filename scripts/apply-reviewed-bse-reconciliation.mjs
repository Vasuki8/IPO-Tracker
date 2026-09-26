import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { validateReceipt } from "./materialize-bse-audit-conflict-evidence.mjs";

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
export const REVIEW_PATH="data/discovery/bse-issue-summary-high-priority-reconciliation-2026-09-26.json";
export const RECEIPT_PATH="data/evidence/bse-high-priority-reconciliation-source-receipt-2026-09-26.json";
export const AUDIT_PATH="data/discovery/bse-issue-summary-coverage-audit-2026-09-26.json";
export const MANIFEST_PATH="data/verified-bse-listings/2026-09-26-bse-reconciliation-five.json";
const RECOVERY_ROOT=path.join(ROOT,"data","recovery");

const requireThat=(ok,msg)=>{if(!ok)throw new Error(msg);};
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const issuerKey=value=>String(value??"").toLowerCase().replace(/&/g," and ").replace(/\bltd\.?\b/g," limited ")
  .replace(/[^a-z0-9]+/g," ").replace(/\blimited\s*$/g,"").replace(/\s+/g," ").trim();
const validDate=value=>typeof value==="string"&&/^\d{4}-\d\d-\d\d$/.test(value)&&new Date(value).toISOString().slice(0,10)===value;
const validIsin=value=>typeof value==="string"&&/^IN[A-Z0-9]{10}$/.test(value);

function sourceMaps(review,receipt){
  return{review:new Map(review.sources.map(s=>[s.key,s])),receipt:new Map(receipt.documents.map(d=>[d.key,d]))};
}
function checkedSource(key,maps,issuer=null){
  const source=maps.review.get(key),doc=maps.receipt.get(key);
  requireThat(source&&doc,"missing_reconciliation_source:"+key);
  requireThat(source.url===doc.source_url&&source.projection_sha256===doc.projection_sha256,"reconciliation_source_receipt_mismatch:"+key);
  if(issuer)requireThat(issuerKey(source.projection?.issuer)===issuerKey(issuer),"reconciliation_source_issuer_mismatch:"+key);
  return{source,doc};
}
function descriptor(key,maps,issuer=null){
  const {source,doc}=checkedSource(key,maps,issuer);
  return{
    url:source.url,document_type:source.document_type,
    document_identity:(issuer||source.projection?.issuer||"Official issuer")+" — "+source.document_type+" ["+key+"]",
    publication_date:source.publication_date??null,page:source.page??null,collected_at:doc.collected_at,
    document_sha256:doc.response_sha256,evidence_locator:source.evidence_locator??null
  };
}
function publicEvidence(src){
  return{url:src.url,document_type:src.document_type,document_identity:src.document_identity,
    publication_date:src.publication_date??null,page:src.page??null,collected_at:src.collected_at};
}
function correction(previousValue,replacementValue,reason,oldField,newSource,collectedAt){
  const evidence=[];
  if(oldField?.source)evidence.push(publicEvidence({...oldField.source,collected_at:oldField.source.collected_at??collectedAt}));
  if(newSource)evidence.push(publicEvidence(newSource));
  return{corrected_at:collectedAt,previous_value:previousValue,previous_source_value:oldField?.source_value??previousValue,
    replacement_value:replacementValue,reason,evidence};
}
function verifiedField(value,sourceValue,key,maps,issuer,corrections=[]){
  const src=descriptor(key,maps,issuer);
  return{value,source_value:sourceValue??value,status:"verified",page:src.page??null,source:src,corrections};
}
function documentFrom(key,maps,issuer){
  const s=descriptor(key,maps,issuer);
  return{type:s.document_type,identity:s.document_identity,url:s.url,publication_date:s.publication_date,collected_at:s.collected_at,document_sha256:s.document_sha256};
}
function appendDocuments(existing,extra){
  const map=new Map((existing||[]).map(d=>[(d.url||"")+"|"+(d.identity||""),d]));
  for(const d of extra)map.set((d.url||"")+"|"+(d.identity||""),d);
  return[...map.values()];
}
function auditFact(audit,issuer){
  const hit=(audit.high_priority_reconciliation||[]).find(x=>issuerKey(x.issuer_name)===issuerKey(issuer));
  requireThat(hit,"missing_bse_audit_fact:"+issuer);
  return hit;
}
function allMatches(recovery,id){
  return Object.entries(recovery).flatMap(([year,data])=>(data.records||[]).filter(r=>r.id===id).map(record=>({year,record})));
}
function fieldValue(record,name){return record?.[name]?.value??null;}

export function validateManifest(manifest,review,receipt,reviewBytes,audit){
  validateReceipt(receipt,review,reviewBytes);
  requireThat(manifest?.schema_version==="1.0.0"&&manifest.importer_version==="1.0.0"&&
    manifest.status==="approved_bse_high_priority_reconciliation_import"&&manifest.review_path===REVIEW_PATH&&
    manifest.receipt_path===RECEIPT_PATH&&manifest.audit_path===AUDIT_PATH&&Array.isArray(manifest.actions)&&manifest.actions.length===5,
    "invalid_bse_reconciliation_manifest");
  requireThat(receipt.workflow_artifact?.artifact_id&&/^sha256:[a-f0-9]{64}$/.test(receipt.workflow_artifact?.artifact_digest||""),
    "missing_bse_reconciliation_artifact_identity");
  requireThat(audit?.status==="complete_read_only_bse_issue_summary_coverage_audit"||audit?.status==="complete","invalid_bse_coverage_audit");
  const reviewActions=new Map(review.actions.map(a=>[a.issuer_name,a]));
  const maps=sourceMaps(review,receipt);
  for(const action of manifest.actions){
    const reviewed=reviewActions.get(action.target?.issuer_name||action.expected_current?.issuer_name||action.key);
    requireThat(reviewed&&reviewed.decision===action.decision,"manifest_review_action_mismatch:"+action.key);
    if(action.target?.listing_date)requireThat(validDate(action.target.listing_date),"invalid_target_listing_date:"+action.key);
    if(action.target?.isin)requireThat(validIsin(action.target.isin),"invalid_target_isin:"+action.key);
    for(const key of action.identity_sources||[])checkedSource(key,maps,action.target?.issuer_name||reviewed.issuer_name);
    for(const key of Object.values(action.field_sources||{}))checkedSource(key,maps,action.target?.issuer_name||reviewed.issuer_name);

    const fact=auditFact(audit,reviewed.issuer_name);
    requireThat(String(fact.bse_scrip_code||"")===String(action.target?.bse_scrip_code||fact.bse_scrip_code||""),"bse_audit_scrip_mismatch:"+action.key);
    requireThat(fact.bse_listing_date===action.target?.listing_date||fact.recovery?.listing_date===action.target?.listing_date,
      "bse_audit_listing_mismatch:"+action.key);
  }

  const cams=manifest.actions.find(a=>a.key==="cams"),protean=manifest.actions.find(a=>a.key==="protean"),fabtech=manifest.actions.find(a=>a.key==="fabtech");
  const cp=checkedSource("cams_prospectus",maps,cams.target.issuer_name).source.projection;
  const cl=checkedSource("cams_nse_listing",maps,cams.target.issuer_name).source.projection;
  requireThat(cp.offer_open===cams.target.open_date&&cp.offer_close===cams.target.close_date&&cp.issue_price_inr===cams.target.issue_price&&
    cl.listing_date===cams.target.listing_date&&cl.symbol===cams.target.nse_symbol&&cl.isin===cams.target.isin,"cams_projection_mismatch");

  const pp=checkedSource("protean_prospectus",maps,protean.target.issuer_name).source.projection;
  const po=checkedSource("protean_original_bse_listing",maps,protean.target.issuer_name).source.projection;
  const ps=checkedSource("protean_secondary_nse",maps,protean.target.issuer_name).source.projection;
  requireThat(pp.offer_open===protean.target.open_date&&pp.offer_close===protean.target.close_date&&pp.issue_price_inr===protean.target.issue_price&&
    pp.minimum_bid_quantity===protean.target.minimum_bid_quantity&&po.listing_date===protean.target.listing_date&&
    po.bse_scrip_code===protean.target.bse_scrip_code&&ps.nse_listing_date==="2025-02-06"&&ps.isin===protean.target.isin,"protean_projection_mismatch");

  const fp=checkedSource("fabtech_prospectus",maps,fabtech.target.issuer_name).source.projection;
  const fl=checkedSource("fabtech_nse_listing",maps,fabtech.target.issuer_name).source.projection;
  const fc=checkedSource("fabtech_cleanrooms_identity",maps).source.projection;
  requireThat(fp.offer_open===fabtech.target.open_date&&fp.offer_close===fabtech.target.close_date&&fp.issue_price_inr===fabtech.target.issue_price&&
    fp.minimum_bid_quantity===fabtech.target.minimum_bid_quantity&&fl.listing_date===fabtech.target.listing_date&&
    fl.symbol===fabtech.target.nse_symbol&&fl.isin===fabtech.target.isin&&issuerKey(fc.issuer)!==issuerKey(fabtech.target.issuer_name),
    "fabtech_projection_mismatch");

  return{maps};
}

function marker(action,receipt,sourceHashes,previous){
  return{
    manifest:MANIFEST_PATH,review:REVIEW_PATH,receipt:RECEIPT_PATH,audit:AUDIT_PATH,importer_version:"1.0.0",
    action_key:action.key,decision:action.decision,workflow_run_id:receipt.workflow_run_id,
    artifact_id:receipt.workflow_artifact.artifact_id,artifact_digest:receipt.workflow_artifact.artifact_digest,
    applied_at:receipt.collection_completed_at,source_hashes:sourceHashes,previous
  };
}
function hashes(keys,maps){
  return Object.fromEntries([...new Set(keys)].map(key=>[key,checkedSource(key,maps).doc.response_sha256]));
}
function moveCams(existing,action,maps,receipt){
  const t=action.target,issuer=t.issuer_name;
  const prospectus=descriptor("cams_prospectus",maps,issuer),listing=descriptor("cams_nse_listing",maps,issuer);
  const out=structuredClone(existing);
  const previous={year:action.source_year,listing_date:existing.listing_date,issue_price:existing.issue_price,nse_source:existing.nse_source};
  out.issuer_name=issuer;out.board=t.board;out.status="listed";out.nse_symbol=t.nse_symbol;out.nse_series=existing.nse_series||"EQ";
  out.nse_source={...listing};out.bse_scrip_code=t.bse_scrip_code;out.isin=t.isin;
  out.open_date=verifiedField(t.open_date,t.open_date,"cams_prospectus",maps,issuer);
  out.close_date=verifiedField(t.close_date,t.close_date,"cams_prospectus",maps,issuer);
  out.issue_price=verifiedField(t.issue_price,t.issue_price,"cams_prospectus",maps,issuer,[
    correction(fieldValue(existing,"issue_price"),t.issue_price,action.correction_reason,existing.issue_price,prospectus,receipt.collection_completed_at)
  ]);
  out.listing_date=verifiedField(t.listing_date,t.listing_date,"cams_nse_listing",maps,issuer,[
    correction(fieldValue(existing,"listing_date"),t.listing_date,action.correction_reason,existing.listing_date,listing,receipt.collection_completed_at)
  ]);
  out.board_evidence=[...(existing.board_evidence||[]),{...listing}];
  out.status_evidence=[...(existing.status_evidence||[]),{...listing}];
  out.documents=appendDocuments(existing.documents,[documentFrom("cams_prospectus",maps,issuer),documentFrom("cams_nse_listing",maps,issuer)]);
  out.last_collected_at=receipt.collection_completed_at;
  out.bse_issue_summary_reconciliation=marker(action,receipt,hashes(["cams_prospectus","cams_nse_listing"],maps),previous);
  return out;
}
function moveProtean(existing,action,maps,receipt){
  const t=action.target,issuer=t.issuer_name;
  const prospectus=descriptor("protean_prospectus",maps,issuer),original=descriptor("protean_original_bse_listing",maps,issuer),secondary=descriptor("protean_secondary_nse",maps,issuer);
  const out=structuredClone(existing);
  const previous={year:action.source_year,listing_date:existing.listing_date,issue_price:existing.issue_price,nse_source:existing.nse_source};
  out.issuer_name=issuer;out.board=t.board;out.status="listed";out.nse_symbol=t.nse_symbol;out.nse_series=existing.nse_series||"EQ";
  out.nse_source={...secondary};out.bse_source={...original};out.bse_scrip_code=t.bse_scrip_code;out.isin=t.isin;
  out.open_date=verifiedField(t.open_date,t.open_date,"protean_prospectus",maps,issuer);
  out.close_date=verifiedField(t.close_date,t.close_date,"protean_prospectus",maps,issuer);
  out.issue_price=verifiedField(t.issue_price,t.issue_price,"protean_prospectus",maps,issuer,[
    correction(fieldValue(existing,"issue_price"),t.issue_price,action.correction_reason,existing.issue_price,prospectus,receipt.collection_completed_at)
  ]);
  out.minimum_bid_quantity=verifiedField(t.minimum_bid_quantity,t.minimum_bid_quantity+" Equity Shares","protean_prospectus",maps,issuer,
    fieldValue(existing,"minimum_bid_quantity")===t.minimum_bid_quantity?[]:[
      correction(fieldValue(existing,"minimum_bid_quantity"),t.minimum_bid_quantity,action.correction_reason,existing.minimum_bid_quantity,prospectus,receipt.collection_completed_at)
    ]);
  out.listing_date=verifiedField(t.listing_date,t.listing_date,"protean_original_bse_listing",maps,issuer,[
    correction(fieldValue(existing,"listing_date"),t.listing_date,action.correction_reason,existing.listing_date,original,receipt.collection_completed_at)
  ]);
  out.board_evidence=[...(existing.board_evidence||[]),{...original}];out.status_evidence=[...(existing.status_evidence||[]),{...original}];
  out.documents=appendDocuments(existing.documents,[
    documentFrom("protean_prospectus",maps,issuer),documentFrom("protean_original_bse_listing",maps,issuer),documentFrom("protean_secondary_nse",maps,issuer)
  ]);
  out.secondary_listings=[...(existing.secondary_listings||[]),{
    exchange:"NSE",listing_date:"2025-02-06",symbol:"PROTEAN",isin:t.isin,event:"later secondary listing",source:{...secondary}
  }];
  out.last_collected_at=receipt.collection_completed_at;
  out.bse_issue_summary_reconciliation=marker(action,receipt,hashes(["protean_prospectus","protean_original_bse_listing","protean_secondary_nse"],maps),previous);
  return out;
}
function addFabtech(action,maps,receipt){
  const t=action.target,issuer=t.issuer_name,listing=descriptor("fabtech_nse_listing",maps,issuer);
  return{
    id:action.stable_id,issuer_name:issuer,board:t.board,sector:null,status:"listed",
    nse_symbol:t.nse_symbol,nse_series:"EQ",nse_source:{...listing},bse_symbol:null,bse_scrip_code:t.bse_scrip_code,isin:t.isin,bse_source:null,
    terms:{price_band:null,market_lot:null,minimum_bid_quantity:null,open_date:null,close_date:null},
    documents:[documentFrom("fabtech_prospectus",maps,issuer),documentFrom("fabtech_nse_listing",maps,issuer)],
    first_observed_at:receipt.collection_completed_at,last_collected_at:receipt.collection_completed_at,
    board_evidence:[{...listing}],status_evidence:[{...listing}],
    open_date:verifiedField(t.open_date,t.open_date,"fabtech_prospectus",maps,issuer),
    close_date:verifiedField(t.close_date,t.close_date,"fabtech_prospectus",maps,issuer),
    issue_price:verifiedField(t.issue_price,t.issue_price,"fabtech_prospectus",maps,issuer),
    minimum_bid_quantity:verifiedField(t.minimum_bid_quantity,t.minimum_bid_quantity+" Equity Shares","fabtech_prospectus",maps,issuer),
    listing_date:verifiedField(t.listing_date,t.listing_date,"fabtech_nse_listing",maps,issuer),
    bse_issue_summary_reconciliation:marker(action,receipt,hashes(["fabtech_prospectus","fabtech_nse_listing","fabtech_cleanrooms_identity"],maps),null)
  };
}
function renameRecord(existing,action,sourceKey,maps,receipt){
  const out=structuredClone(existing),issuer=action.target.issuer_name,src=descriptor(sourceKey,maps,issuer);
  const previous={issuer_name:existing.issuer_name,bse_scrip_code:existing.bse_scrip_code??null};
  out.issuer_name=issuer;out.bse_scrip_code=action.target.bse_scrip_code;
  if(sourceKey==="happy_identity")out.bse_source={...src};
  out.documents=appendDocuments(existing.documents,[documentFrom(sourceKey,maps,issuer)]);
  out.last_collected_at=receipt.collection_completed_at;
  out.bse_issue_summary_reconciliation=marker(action,receipt,hashes([sourceKey],maps),previous);
  return out;
}
function completedRecord(record,action){
  if(record?.bse_issue_summary_reconciliation?.manifest!==MANIFEST_PATH||record?.bse_issue_summary_reconciliation?.action_key!==action.key)return false;
  const t=action.target;
  return record.id===action.stable_id&&record.issuer_name===t.issuer_name&&
    (t.listing_date==null||fieldValue(record,"listing_date")===t.listing_date)&&
    (t.issue_price==null||fieldValue(record,"issue_price")===t.issue_price)&&
    (t.bse_scrip_code==null||String(record.bse_scrip_code||"")===String(t.bse_scrip_code));
}

export function applyReviewedBseReconciliation(recoveryByYear,published,manifest,review,receipt,reviewBytes,audit){
  const {maps}=validateManifest(manifest,review,receipt,reviewBytes,audit);
  const recovery=structuredClone(recoveryByYear),changed=new Set();
  const stats={moved:0,added:0,renamed:0,already_present:0};
  const cleanroomsBefore=JSON.stringify((recovery["2025"]?.records||[]).find(r=>r.id==="fabtech-technologies-cleanrooms-limited")||null);
  requireThat(cleanroomsBefore!=="null","fabtech_cleanrooms_missing_before_reconciliation");

  for(const action of manifest.actions){
    let matches=allMatches(recovery,action.stable_id);
    if(matches.length===1&&completedRecord(matches[0].record,action)){stats.already_present++;continue;}
    if(action.decision==="add_distinct_historical_ipo"){
      requireThat(matches.length===0,"fabtech_target_already_exists_without_review_marker");
      requireThat(!(recovery["2025"].records||[]).some(r=>String(r.bse_scrip_code||"")===String(action.target.bse_scrip_code)||String(r.isin||"")===String(action.target.isin)),
        "fabtech_identity_collision");
      recovery["2025"].records.push(addFabtech(action,maps,receipt));recovery["2025"].records.sort((a,b)=>a.issuer_name.localeCompare(b.issuer_name));
      changed.add("2025");stats.added++;continue;
    }

    requireThat(matches.length===1,"expected_single_recovery_record:"+action.key);
    const {year,record}=matches[0];
    requireThat(Number(year)===action.source_year,"unexpected_source_year:"+action.key);
    requireThat(record.issuer_name===action.expected_current.issuer_name&&record.nse_symbol===action.expected_current.nse_symbol&&
      fieldValue(record,"listing_date")===action.expected_current.listing_date,"unexpected_current_identity_or_listing:"+action.key);
    if(action.expected_current.issue_price!=null)requireThat(fieldValue(record,"issue_price")===action.expected_current.issue_price,"unexpected_current_price:"+action.key);

    if(action.decision.startsWith("move_and_correct")){
      const replacement=action.key==="cams"?moveCams(record,action,maps,receipt):moveProtean(record,action,maps,receipt);
      requireThat(!allMatches(recovery,action.stable_id).some(x=>x.year===String(action.target_year)&&x.record!==record),"target_year_collision:"+action.key);
      recovery[year].records=recovery[year].records.filter(r=>r.id!==action.stable_id);
      recovery[String(action.target_year)].records.push(replacement);
      recovery[String(action.target_year)].records.sort((a,b)=>a.issuer_name.localeCompare(b.issuer_name));
      changed.add(year);changed.add(String(action.target_year));stats.moved++;continue;
    }
    if(action.decision.startsWith("correct_legal_name")){
      const replacement=renameRecord(record,action,action.key==="happy"?"happy_identity":"kronox_identity",maps,receipt);
      const idx=recovery[year].records.findIndex(r=>r.id===action.stable_id);recovery[year].records[idx]=replacement;
      recovery[year].records.sort((a,b)=>a.issuer_name.localeCompare(b.issuer_name));
      changed.add(year);stats.renamed++;continue;
    }
    throw new Error("unsupported_reconciliation_decision:"+action.decision);
  }

  for(const year of changed){
    recovery[year].generated_at=[recovery[year].generated_at,receipt.collection_completed_at].filter(Boolean).sort().at(-1);
  }
  requireThat(JSON.stringify((recovery["2025"]?.records||[]).find(r=>r.id==="fabtech-technologies-cleanrooms-limited")||null)===cleanroomsBefore,
    "fabtech_cleanrooms_changed");

  const expectedIds=new Set(manifest.actions.map(a=>a.stable_id));
  const publicHits=(published.records||[]).filter(r=>expectedIds.has(r.id));
  requireThat(publicHits.length<=4,"unexpected_public_reconciliation_duplicates");
  return{recovery,stats,changed_years:[...changed].sort()};
}
export function loadRecovery(root=ROOT){
  const out={};
  for(const year of fs.readdirSync(path.join(root,"data","recovery")).filter(x=>/^20\d{2}$/.test(x))){
    const file=path.join(root,"data","recovery",year,"nse-issue-information.json");
    if(fs.existsSync(file))out[year]=JSON.parse(fs.readFileSync(file,"utf8"));
  }
  return out;
}
function loadInputs(){
  const reviewBytes=fs.readFileSync(path.join(ROOT,REVIEW_PATH));
  return{
    reviewBytes,review:JSON.parse(reviewBytes),receipt:JSON.parse(fs.readFileSync(path.join(ROOT,RECEIPT_PATH),"utf8")),
    manifest:JSON.parse(fs.readFileSync(path.join(ROOT,MANIFEST_PATH),"utf8")),audit:JSON.parse(fs.readFileSync(path.join(ROOT,AUDIT_PATH),"utf8")),
    recovery:loadRecovery(ROOT),published:JSON.parse(fs.readFileSync(path.join(ROOT,"data","ipos.json"),"utf8"))
  };
}
function run(){
  requireThat(process.argv.slice(2).every(x=>x==="--check"),"only_--check_supported");
  const i=loadInputs(),plan=applyReviewedBseReconciliation(i.recovery,i.published,i.manifest,i.review,i.receipt,i.reviewBytes,i.audit);
  if(process.argv.includes("--check")){console.log(JSON.stringify({bse_reconciliation_plan:plan.stats,changed_years:plan.changed_years}));return;}
  for(const year of plan.changed_years)fs.writeFileSync(path.join(RECOVERY_ROOT,year,"nse-issue-information.json"),JSON.stringify(plan.recovery[year],null,2)+"\n");
  console.log(JSON.stringify({bse_reconciliation_import:plan.stats,changed_years:plan.changed_years}));
}
const isMain=process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url;
if(isMain){try{run();}catch(e){console.error(e);process.exit(1);}}
