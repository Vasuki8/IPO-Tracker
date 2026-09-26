import fs from "node:fs";
import path from "node:path";
import {fileURLToPath,pathToFileURL} from "node:url";
import {validateReceipt} from "./materialize-bse-audit-conflict-evidence.mjs";

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
export const REVIEW_PATH="data/discovery/bse-issue-summary-high-priority-reconciliation-2026-09-26.json";
export const RECEIPT_PATH="data/evidence/bse-high-priority-reconciliation-source-receipt-2026-09-26.json";
export const AUDIT_PATH="data/discovery/bse-issue-summary-coverage-audit-2026-09-26.json";
export const MANIFEST_PATH="data/verified-bse-reconciliations/2026-09-26-high-priority.json";
const RECOVERY_ROOT=path.join(ROOT,"data","recovery");
const requireThat=(ok,msg)=>{if(!ok)throw new Error(msg);};
const issuerKey=v=>String(v??"").toLowerCase().replace(/&/g," and ").replace(/\bltd\.?\b/g," limited ").replace(/[^a-z0-9]+/g," ").replace(/\blimited\s*$/g,"").replace(/\s+/g," ").trim();
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const validDate=v=>typeof v==="string"&&/^\d{4}-\d\d-\d\d$/.test(v)&&new Date(v).toISOString().slice(0,10)===v;

function maps(review,receipt){return{review:new Map(review.sources.map(s=>[s.key,s])),receipt:new Map(receipt.documents.map(d=>[d.key,d]))};}
function checkedSource(key,issuer,m){
  const source=m.review.get(key),doc=m.receipt.get(key);
  requireThat(source&&doc,"missing_reconciliation_source:"+key);
  requireThat(source.url===doc.source_url&&source.projection_sha256===doc.projection_sha256,"reconciliation_source_receipt_mismatch:"+key);
  requireThat(issuerKey(source.projection?.issuer)===issuerKey(issuer),"reconciliation_source_issuer_mismatch:"+key);
  return{source,doc};
}
function descriptor(key,issuer,m){
  const {source,doc}=checkedSource(key,issuer,m);
  return{url:source.url,document_type:source.document_type,document_identity:`${source.document_type} — ${issuer} [${key}]`,
    publication_date:source.publication_date??null,page:source.page??null,collected_at:doc.collected_at,document_sha256:doc.response_sha256,evidence_locator:source.evidence_locator??null};
}
function publicEvidence(source){return{url:source.url,document_type:source.document_type,document_identity:source.document_identity,publication_date:source.publication_date??null,page:source.page??null,collected_at:source.collected_at};}
function correction(previous,replacement,reason,sources,at){
  return{corrected_at:at,previous_value:previous,replacement_value:replacement,reason,evidence:sources.map(publicEvidence)};
}
function field(value,sourceValue,key,issuer,m,corrections=[]){
  const source=descriptor(key,issuer,m);return{value,source_value:sourceValue??value,status:"verified",page:source.page??null,source,corrections};
}
function addDocument(record,source){
  record.documents??=[];
  if(!record.documents.some(d=>d.url===source.url&&d.identity===source.document_identity)){
    record.documents.push({type:source.document_type,identity:source.document_identity,url:source.url,publication_date:source.publication_date,collected_at:source.collected_at,document_sha256:source.document_sha256});
  }
}
function addEvidence(record,key,source){
  record[key]??=[];
  if(!record[key].some(e=>e.url===source.url&&e.document_identity===source.document_identity))record[key].push({...source});
}
function maxStamp(a,b){return[a,b].filter(Boolean).sort().at(-1);}
function findRecords(recovery,predicate){
  const hits=[];for(const [year,data] of Object.entries(recovery))for(const record of data.records||[])if(predicate(record))hits.push({year,record});return hits;
}
function getAuditFact(audit,issuer){
  const hits=(audit.high_priority_reconciliation||[]).filter(x=>issuerKey(x.issuer_name)===issuerKey(issuer));
  requireThat(hits.length===1,"missing_or_ambiguous_bse_audit_fact:"+issuer);return hits[0];
}
function projectValue(source,key){return source.projection?.[key];}

export function validateManifest(manifest,review,receipt,audit,reviewBytes){
  validateReceipt(receipt,review,reviewBytes);
  requireThat(manifest?.schema_version==="1.0.0"&&manifest.importer_version==="1.0.0"&&manifest.status==="approved_bse_high_priority_reconciliation"&&
    manifest.review_path===REVIEW_PATH&&manifest.receipt_path===RECEIPT_PATH&&manifest.audit_path===AUDIT_PATH&&
    Array.isArray(manifest.actions)&&manifest.actions.length===5,"invalid_bse_reconciliation_manifest");
  requireThat(receipt.workflow_artifact?.artifact_id&&/^sha256:[a-f0-9]{64}$/.test(receipt.workflow_artifact?.artifact_digest||""),"missing_reconciliation_artifact_identity");
  requireThat(audit?.schema_version==="1.0.0"&&audit.status==="complete_read_only_bse_issue_summary_coverage_audit"&&audit.reconciliation?.auto_imported===0,"invalid_bse_reconciliation_audit");
  const reviewActions=new Map(review.actions.map(a=>[issuerKey(a.issuer_name),a])),m=maps(review,receipt),seen=new Set();
  for(const action of manifest.actions){
    requireThat(!seen.has(action.key),"duplicate_reconciliation_action");seen.add(action.key);
    const reviewed=reviewActions.get(issuerKey(action.target.issuer_name));
    requireThat(reviewed&&reviewed.decision===action.action.replace("move_and_correct_preserve_secondary_listing","move_and_correct_historical_ipo_preserve_secondary_listing")
      .replace("move_and_correct","move_and_correct_historical_ipo")
      .replace("add_distinct","add_distinct_historical_ipo")
      .replace("rename_preserve_id","correct_legal_name_preserve_stable_id") ||
      (reviewed&&action.key==="kronox"&&reviewed.decision==="correct_legal_name_spacing_preserve_stable_id"),"review_manifest_action_mismatch:"+action.key);
    const auditFact=getAuditFact(audit,action.target.issuer_name);
    requireThat(Number(auditFact.source_year)===Number(action.target.year)&&auditFact.bse_listing_date===
      (action.fields?.listing_date?.value??action.current?.listing_date),"audit_target_mismatch:"+action.key);
    if(action.target.bse_scrip_code)requireThat(auditFact.bse_scrip_code===action.target.bse_scrip_code,"audit_scrip_mismatch:"+action.key);
    for(const [fieldName,spec] of Object.entries(action.fields||{})){
      requireThat(validDate(spec.value)||typeof spec.value==="number","invalid_reconciliation_field:"+action.key+":"+fieldName);
      const src=checkedSource(spec.source,action.target.issuer_name,m).source;
      const projectionKey=fieldName==="open_date"?"offer_open":fieldName==="close_date"?"offer_close":fieldName==="issue_price"?"issue_price_inr":fieldName;
      requireThat(same(projectValue(src,projectionKey),spec.value),"reconciliation_projection_mismatch:"+action.key+":"+fieldName);
    }
    if(action.identity_source)checkedSource(action.identity_source,action.target.issuer_name,m);
  }
  const cleanrooms=checkedSource("fabtech_cleanrooms_identity","Fabtech Technologies Cleanrooms Limited",m).source.projection;
  requireThat(cleanrooms.bse_scrip_code==="544332","cleanrooms_identity_mismatch");
  return{m};
}
function marker(manifest,receipt,audit,action){
  return{manifest:MANIFEST_PATH,review:REVIEW_PATH,receipt:RECEIPT_PATH,audit:AUDIT_PATH,importer_version:manifest.importer_version,action:action.key,
    workflow_run_id:receipt.workflow_run_id,artifact_id:receipt.workflow_artifact.artifact_id,artifact_digest:receipt.workflow_artifact.artifact_digest,
    audit_workflow_run_id:audit.workflow_run_id,audit_artifact_id:audit.workflow_artifact?.artifact_id??null};
}
function updateGenerated(recovery,years,stamp){for(const y of years)recovery[y].generated_at=maxStamp(recovery[y].generated_at,stamp);}

function applyMove(recovery,action,m,receipt,audit,manifest){
  const already=findRecords(recovery,r=>r.id===action.target.id&&r.bse_high_priority_reconciliation?.manifest===MANIFEST_PATH);
  if(already.length){requireThat(already.length===1&&already[0].year===String(action.target.year),"applied_move_wrong_year:"+action.key);return{changed:[],already:true};}
  const hits=findRecords(recovery,r=>r.id===action.current.id);
  requireThat(hits.length===1&&hits[0].year===String(action.current.year),"move_current_record_mismatch:"+action.key);
  const source=hits[0].record;
  requireThat(source.issuer_name===action.current.issuer_name&&source.listing_date?.value===action.current.listing_date&&
    (action.current.issue_price==null||source.issue_price?.value===action.current.issue_price),"move_current_facts_mismatch:"+action.key);
  requireThat(!recovery[String(action.target.year)].records.some(r=>r.id===action.target.id),"target_id_collision:"+action.key);
  const record=structuredClone(source),at=receipt.collection_completed_at;
  recovery[hits[0].year].records=recovery[hits[0].year].records.filter(r=>r!==hits[0].record);
  record.issuer_name=action.target.issuer_name;record.board=action.target.board;record.nse_symbol=action.target.nse_symbol;record.nse_series=action.target.nse_series;
  record.bse_scrip_code=action.target.bse_scrip_code;record.isin=action.target.isin;record.last_collected_at=maxStamp(record.last_collected_at,at);
  const oldListing=source.listing_date,listingSpec=action.fields.listing_date,listingSource=descriptor(listingSpec.source,action.target.issuer_name,m);
  record.listing_date=field(listingSpec.value,listingSpec.value,listingSpec.source,action.target.issuer_name,m,[
    correction(oldListing?.value,listingSpec.value,action.key==="protean"?"Replace later NSE secondary-listing date with original IPO listing date.":"Replace superseded NSE observation with original IPO listing date.",[oldListing?.source??listingSource,listingSource].filter(Boolean),at)
  ]);
  for(const name of ["open_date","close_date","issue_price","minimum_bid_quantity"]){
    const spec=action.fields[name];if(!spec)continue;
    const previous=record[name];
    const corrections=previous&&previous.value!==spec.value?[correction(previous.value,spec.value,"Replace non-IPO/superseded historical field with original IPO evidence.",[previous.source,descriptor(spec.source,action.target.issuer_name,m)].filter(Boolean),at)]:[];
    record[name]=field(spec.value,spec.value,spec.source,action.target.issuer_name,m,corrections);
  }
  for(const key of [...new Set(Object.values(action.fields).map(x=>x.source))]){const d=descriptor(key,action.target.issuer_name,m);addDocument(record,d);}
  addEvidence(record,"status_evidence",listingSource);addEvidence(record,"board_evidence",listingSource);
  if(action.key==="protean"){
    const secondary=descriptor(action.secondary_listing.source,action.target.issuer_name,m);
    addDocument(record,secondary);
    record.secondary_listing_events=[...(record.secondary_listing_events||[]),{date:action.secondary_listing.date,exchange:action.secondary_listing.exchange,source:secondary,note:"Later exchange admission retained separately from original IPO listing."}];
    record.bse_source={...listingSource};
  }
  if(action.key==="cams")record.nse_source={...listingSource};
  record.bse_high_priority_reconciliation=marker(manifest,receipt,audit,action);
  recovery[String(action.target.year)].records.push(record);
  return{changed:[hits[0].year,String(action.target.year)],already:false};
}
function applyFabtech(recovery,action,m,receipt,audit,manifest){
  const existing=findRecords(recovery,r=>r.id===action.target.id);
  if(existing.length){requireThat(existing.length===1&&existing[0].year==="2025"&&existing[0].record.bse_high_priority_reconciliation?.manifest===MANIFEST_PATH,"fabtech_existing_conflict");return{changed:[],already:true};}
  const clean=findRecords(recovery,r=>r.id===action.preserve_distinct.id);
  requireThat(clean.length===1&&clean[0].year==="2025"&&clean[0].record.issuer_name===action.preserve_distinct.issuer_name&&
    clean[0].record.bse_scrip_code===action.preserve_distinct.bse_scrip_code&&clean[0].record.listing_date?.value===action.preserve_distinct.listing_date,"cleanrooms_preservation_mismatch");
  const at=receipt.collection_completed_at,listing=descriptor(action.fields.listing_date.source,action.target.issuer_name,m);
  const record={id:action.target.id,issuer_name:action.target.issuer_name,board:action.target.board,sector:null,status:"listed",
    nse_symbol:action.target.nse_symbol,nse_series:action.target.nse_series,nse_source:{...listing},bse_scrip_code:action.target.bse_scrip_code,isin:action.target.isin,
    terms:{price_band:null,market_lot:null,minimum_bid_quantity:null,open_date:null,close_date:null},documents:[],first_observed_at:at,last_collected_at:at,
    board_evidence:[{...listing}],status_evidence:[{...listing}],bse_high_priority_reconciliation:marker(manifest,receipt,audit,action)};
  for(const [name,spec] of Object.entries(action.fields))record[name]=field(spec.value,spec.value,spec.source,action.target.issuer_name,m);
  for(const key of [...new Set(Object.values(action.fields).map(x=>x.source))])addDocument(record,descriptor(key,action.target.issuer_name,m));
  const cleanroomsEvidence=descriptor("fabtech_cleanrooms_identity","Fabtech Technologies Cleanrooms Limited",m);
  record.distinct_issuer_evidence={issuer_name:"Fabtech Technologies Cleanrooms Limited",bse_scrip_code:"544332",source:cleanroomsEvidence,note:"Retained only to prove the audit prefix match was a different legal issuer; not published as a Fabtech Technologies document."};
  recovery["2025"].records.push(record);return{changed:["2025"],already:false};
}
function applyRename(recovery,action,m,receipt,audit,manifest){
  const hits=findRecords(recovery,r=>r.id===action.target.id);
  requireThat(hits.length===1&&hits[0].year===String(action.target.year),"rename_record_mismatch:"+action.key);
  const record=hits[0].record;
  if(record.bse_high_priority_reconciliation?.manifest===MANIFEST_PATH){requireThat(record.issuer_name===action.target.issuer_name,"renamed_record_drift:"+action.key);return{changed:[],already:true};}
  requireThat(record.issuer_name===action.current.issuer_name&&record.listing_date?.value===action.current.listing_date,"rename_current_facts_mismatch:"+action.key);
  const source=descriptor(action.identity_source,action.target.issuer_name,m),previous=record.issuer_name;
  record.issuer_name=action.target.issuer_name;record.last_collected_at=maxStamp(record.last_collected_at,receipt.collection_completed_at);addDocument(record,source);addEvidence(record,"board_evidence",source);
  if(action.target.bse_scrip_code){record.bse_scrip_code=action.target.bse_scrip_code;record.bse_source={...source};}
  record.identity_corrections=[...(record.identity_corrections||[]),{corrected_at:receipt.collection_completed_at,previous_issuer_name:previous,replacement_issuer_name:record.issuer_name,reason:"Correct legal issuer name from independent official evidence.",source}];
  record.bse_high_priority_reconciliation=marker(manifest,receipt,audit,action);return{changed:[hits[0].year],already:false};
}

export function applyReviewedReconciliation(recoveryInput,published,manifest,review,receipt,audit,reviewBytes){
  const {m}=validateManifest(manifest,review,receipt,audit,reviewBytes),recovery=structuredClone(recoveryInput);
  const cleanBefore=JSON.stringify(findRecords(recovery,r=>r.id==="fabtech-technologies-cleanrooms-limited")[0]?.record??null);
  const stats={moved:0,added:0,renamed:0,already_present:0};const changed=new Set();
  for(const action of manifest.actions){
    let result;
    if(action.action.startsWith("move_and_correct"))result=applyMove(recovery,action,m,receipt,audit,manifest);
    else if(action.action==="add_distinct")result=applyFabtech(recovery,action,m,receipt,audit,manifest);
    else result=applyRename(recovery,action,m,receipt,audit,manifest);
    if(result.already)stats.already_present++;
    else if(action.action.startsWith("move_and_correct"))stats.moved++;
    else if(action.action==="add_distinct")stats.added++;
    else stats.renamed++;
    result.changed.forEach(y=>changed.add(y));
  }
  const cleanAfter=JSON.stringify(findRecords(recovery,r=>r.id==="fabtech-technologies-cleanrooms-limited")[0]?.record??null);
  requireThat(cleanBefore===cleanAfter,"cleanrooms_record_changed");
  const all=Object.values(recovery).flatMap(x=>x.records||[]),ids=new Set();
  for(const record of all){requireThat(!ids.has(record.id),"duplicate_recovery_id_after_reconciliation:"+record.id);ids.add(record.id);}
  for(const id of ["computer-age-management-services-limited","protean-egov-technologies-limited","fabtech-technologies-limited"]){
    requireThat(all.filter(r=>r.id===id).length===1,"reconciled_identity_count_invalid:"+id);
  }
  const publicNames=new Map((published.records||[]).map(r=>[issuerKey(r.issuer_name),r]));
  requireThat(publicNames.has(issuerKey("Computer Age Management Services Limited"))&&publicNames.has(issuerKey("Protean eGov Technologies Limited")),"expected_public_records_missing");
  updateGenerated(recovery,[...changed],receipt.collection_completed_at);
  for(const y of changed)recovery[y].records.sort((a,b)=>a.issuer_name.localeCompare(b.issuer_name));
  return{recovery,stats,changed_years:[...changed].sort()};
}
export function loadRecovery(root=ROOT){
  const result={};for(const entry of fs.readdirSync(path.join(root,"data","recovery"),{withFileTypes:true}).filter(e=>e.isDirectory()&&/^20\d{2}$/.test(e.name))){
    const file=path.join(root,"data","recovery",entry.name,"nse-issue-information.json");if(fs.existsSync(file))result[entry.name]=JSON.parse(fs.readFileSync(file,"utf8"));
  }return result;
}
function load(){
  const rb=fs.readFileSync(path.join(ROOT,REVIEW_PATH));
  return{reviewBytes:rb,review:JSON.parse(rb),receipt:JSON.parse(fs.readFileSync(path.join(ROOT,RECEIPT_PATH),"utf8")),
    audit:JSON.parse(fs.readFileSync(path.join(ROOT,AUDIT_PATH),"utf8")),manifest:JSON.parse(fs.readFileSync(path.join(ROOT,MANIFEST_PATH),"utf8")),
    recovery:loadRecovery(ROOT),published:JSON.parse(fs.readFileSync(path.join(ROOT,"data","ipos.json"),"utf8"))};
}
function run(){
  requireThat(process.argv.slice(2).every(x=>x==="--check"),"only_--check_supported");
  const x=load(),plan=applyReviewedReconciliation(x.recovery,x.published,x.manifest,x.review,x.receipt,x.audit,x.reviewBytes);
  if(process.argv.includes("--check")){console.log(JSON.stringify({bse_high_priority_reconciliation:plan.stats,changed_years:plan.changed_years}));return;}
  for(const y of plan.changed_years)fs.writeFileSync(path.join(RECOVERY_ROOT,y,"nse-issue-information.json"),JSON.stringify(plan.recovery[y],null,2)+"\n");
  console.log(JSON.stringify({bse_high_priority_reconciliation:plan.stats,changed_years:plan.changed_years}));
}
if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url){try{run();}catch(e){console.error(e);process.exit(1);}}
