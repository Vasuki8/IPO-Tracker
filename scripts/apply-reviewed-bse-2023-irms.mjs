import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {isDeepStrictEqual as same} from 'node:util';
import {sha256,strictDate} from './verify-bse-listing-candidates.mjs';
import {canonicalIssuer} from './sync-sebi-documents.mjs';
import {context as fieldContext,validateReview} from './check-bse-2023-irms-field-review.mjs';
export {loadRecovery} from './apply-reviewed-bse-2023-rvpe.mjs';
import {loadRecovery} from './apply-reviewed-bse-2023-rvpe.mjs';

export const ROOT=fileURLToPath(new URL('../',import.meta.url));
export const REVIEW='data/discovery/bse-2023-irms-listing-review-2026-09-29.json';
export const RECEIPT='data/evidence/bse-2023-irms-listing-source-receipt-2026-09-29.json';
export const MANIFEST='data/verified-bse-listings/2026-09-29-irms-2023.json';
export const FIELD_REVIEW='data/discovery/bse-2023-irms-field-review-2026-09-28.json';
export const TARGET='data/recovery/2023/nse-issue-information.json';
const FIELDS=['price_band','issue_price','issue_size_inr','market_lot','minimum_bid_quantity','open_date','close_date','listing_date'];
const CODES=['544026','544053','544060','543963'];
// Explicit manual-review boundary. This pin is not an automatic PDF semantic
// parser; a substantive source/field change requires a newly reviewed approval.
const APPROVED_MANIFEST_SHA256='41e3bf5c6c3d64dac84fe6f661630f3d50fb5cb9f5fb34c145c8053308d9143e';
const req=(ok,message)=>{if(!ok)throw new Error(message);};
const parse=b=>JSON.parse(Buffer.from(b).toString('utf8'));
const clock=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(s)&&Number.isFinite(Date.parse(s));
const date=s=>typeof s==='string'&&strictDate(s)===s;
const positive=n=>Number.isSafeInteger(n)&&n>0;
// Exact decimal-to-INR conversion. Binary floating point cannot represent
// 2150.22 * 10000000 exactly; do not round an unchecked financial number.
function normalizedAmount(value,multiplier){
 req(typeof value==='string'&&/^\d+(?:\.\d{1,2})?$/.test(value)&&positive(multiplier)&&multiplier%100===0,'invalid_decimal_amount');
 const [whole,fraction='']=value.split('.');
 const result=(BigInt(whole)*100n+BigInt(fraction.padEnd(2,'0')))*BigInt(multiplier)/100n;
 req(result<=BigInt(Number.MAX_SAFE_INTEGER),'amount_overflow');return Number(result);
}
export function context(root=ROOT){
 const read=p=>fs.readFileSync(path.join(root,p));
 const manifestBytes=read(MANIFEST),reviewBytes=read(REVIEW),receiptBytes=read(RECEIPT),fieldReviewBytes=read(FIELD_REVIEW);
 return{manifest:parse(manifestBytes),review:parse(reviewBytes),receipt:parse(receiptBytes),manifestBytes,reviewBytes,receiptBytes,fieldReviewBytes,fieldContext:fieldContext(root)};
}
export function validate(ctx){
 const {manifest:m,review:r,receipt:c}=ctx;
 req(sha256(ctx.manifestBytes)===APPROVED_MANIFEST_SHA256&&same(m,parse(ctx.manifestBytes)),'unapproved_manifest');
 req(m.schema_version==='1.0.0'&&m.status==='approved_bse_2023_irms_import'&&m.target_year===2023&&m.publication_import_allowed===true,'invalid_import_scope');
 req(m.review_path===REVIEW&&m.review_sha256===sha256(ctx.reviewBytes)&&same(r,parse(ctx.reviewBytes)),'review_binding_mismatch');
 req(m.receipt_path===RECEIPT&&m.receipt_sha256===sha256(ctx.receiptBytes)&&same(c,parse(ctx.receiptBytes)),'receipt_binding_mismatch');
 req(m.field_review_path===FIELD_REVIEW&&m.field_review_sha256===sha256(ctx.fieldReviewBytes)&&same(ctx.fieldContext.review,parse(ctx.fieldReviewBytes)),'prospectus_binding_mismatch');
 validateReview(ctx.fieldContext);
 req(r.status==='reviewed_actual_listings_import_approved'&&r.source_year===2023&&r.publication_import_allowed===true&&r.auto_import_allowed===false&&r.complete_indian_ipo_universe===false&&r.discovery_source_refetched===false,'unsafe_review_scope');
 req(r.prospectus_review.path===FIELD_REVIEW&&r.prospectus_review.sha256===m.field_review_sha256&&r.listing_receipt.path===RECEIPT&&r.listing_receipt.sha256===m.receipt_sha256,'source_role_binding');
 req(clock(r.reviewed_at)&&r.reviewed_at===m.reviewed_at&&clock(c.checked_at)&&c.checked_at<=r.reviewed_at,'invalid_review_clock');
 req(c.status==='original_listing_sources_retained'&&c.publication_import_allowed===false&&c.semantic_review_complete===false&&c.collections.length===2,'original_collection_scope');
 for(const collection of c.collections){
  req(positive(collection.artifact.id)&&collection.artifact.retention_days===14&&/^[a-f0-9]{64}$/.test(collection.artifact.zip_sha256),'unbound_artifact');
  req(collection.receipt_sha256===sha256(JSON.stringify(collection.receipt,null,2)+'\n'),'original_receipt_changed');
 }
 req(c.collections[0].receipt.status==='partial'&&c.collections[0].receipt.documents.every(d=>d.status===404&&d.accepted===false),'failed_history_changed');
 const collection=c.collections[1],docs=collection.receipt.documents;
 req(collection.workflow_run_id===c.selected_run&&collection.artifact.id===c.selected_artifact_id&&docs.length===4&&docs.every(d=>d.status===200&&d.accepted===true&&d.error===null),'unaccepted_listing_sources');
 req(docs.reduce((s,d)=>s+d.response_bytes,0)===c.original_pdf_bytes,'source_total_mismatch');
 req(same(r.actions.map(a=>a.discovery_bse_scrip_code),CODES)&&same(m.actions,r.actions.map(a=>({stable_id:a.stable_id,discovery_bse_scrip_code:a.discovery_bse_scrip_code}))),'unexpected_candidate_scope');
 for(let n=0;n<r.actions.length;n++){
  const a=r.actions[n],p=ctx.fieldContext.review.actions[n],d=a.document,s=docs.find(d=>d.code===a.discovery_bse_scrip_code),t=a.listing_date;
  req(a.decision==='approved_missing_ipo'&&a.stable_id===p.candidate_id&&a.issuer_name===p.issuer_name&&a.source_row_index===p.source_row_index,'issuer_identity_mismatch');
  req(d.url===s.url&&s.final_url===s.url&&d.response_sha256===s.response_sha256&&d.response_bytes===s.response_bytes&&d.evidence_file===s.file,'source_response_mismatch');
  const u=new URL(d.url);req(u.protocol==='https:'&&['www.bseindia.com','nsearchives.nseindia.com'].includes(u.hostname)&&!u.username&&!u.password&&!u.hash&&!u.search,'untrusted_original_host');
  req(d.artifact_id===collection.artifact.id&&d.workflow_run_id===collection.workflow_run_id&&d.workflow_attempt===collection.workflow_attempt,'source_archive_mismatch');
  req(d.requested_at===s.requested_at&&d.collected_at===s.collected_at&&clock(d.requested_at)&&clock(d.collected_at)&&d.requested_at<=d.collected_at&&d.collected_at<=c.checked_at,'source_clock_mismatch');
  req(d.document_type==='Exchange-hosted Annual Report PDF'&&d.document_identity===a.issuer_name+' — Annual Report FY2023-24'&&d.reporting_period==='FY2023-24'&&date(d.document_date)&&d.publication_date===null&&positive(d.pdf_pages),'invalid_document_identity');
  for(const page of [d.document_date_page,t.page,a.identifiers.bse_scrip_code.page,a.identifiers.nse_symbol?.page].filter(x=>x!==undefined))req(positive(page)&&page<=d.pdf_pages,'invalid_physical_page');
  req(t.status==='verified'&&t.source_unit==='ISO date'&&date(t.value)&&t.value.startsWith('2023-')&&t.source_value===t.value&&p.terms.close_date.value<t.value&&t.reporting_period==='2023 IPO'&&t.evidence_locator.length>20,'invalid_actual_listing');
  req(a.identifiers.bse_scrip_code.value===a.discovery_bse_scrip_code&&a.identifiers.board===null&&a.identifiers.isin===null,'unsupported_identity');
  req(n===0?a.amount_conflict?.status==='unresolved':a.amount_conflict===null,'unexpected_amount_override');
 }
 const i=r.actions[0].amount_conflict,o=i.competing_observation,p=ctx.fieldContext.review.actions[0].terms.issue_size_inr;
 req(i.preferred_value===p.value&&i.preferred_status_before_conflict===p.status&&i.preferred_source==='retained_final_prospectus'&&o.value===normalizedAmount(o.source_value,o.normalization_multiplier)&&o.source_unit==='INR crore'&&o.normalization_multiplier===10000000&&o.scope==='total_offer'&&o.value!==p.value&&o.page===38&&i.qualification.includes('Basis of Allotment'),'invalid_conflict');
 return{ok:true,records:4,verified:28,provisional:2,conflict:1,missing:1};
}
function annualSource(a,page,locator){const d=a.document;return{url:d.url,document_type:d.document_type,document_identity:d.document_identity,document_date:d.document_date,publication_date:d.publication_date,reporting_period:d.reporting_period,collected_at:d.collected_at,document_sha256:d.response_sha256,page,evidence_locator:locator};}
export function expected(ctx){
 validate(ctx);
 return ctx.review.actions.map((a,n)=>{
  const p=ctx.fieldContext.review.actions[n],d=p.document;
  const prospectus=(page=null,locator=null)=>({url:d.url,document_type:'SEBI Prospectus PDF',document_identity:p.issuer_name+' — Prospectus '+d.document_date,document_date:d.document_date,publication_date:d.publication_date,reporting_period:'2023 IPO',collected_at:d.collected_at,document_sha256:d.response_sha256,page,evidence_locator:locator});
  const annual=annualSource(a,null,null),sources=[prospectus(),annual],times=sources.map(x=>x.collected_at).sort();
  const record={id:a.stable_id,issuer_name:a.issuer_name,board:null,sector:null,status:'listed',nse_symbol:a.identifiers.nse_symbol?.value??null,nse_series:null,nse_source:null,bse_symbol:null,bse_scrip_code:a.identifiers.bse_scrip_code.value,isin:null,bse_source:null,terms:{price_band:null,market_lot:null,minimum_bid_quantity:null,open_date:null,close_date:null},documents:sources.map(s=>({type:s.document_type,identity:s.document_identity,url:s.url,publication_date:s.publication_date,collected_at:s.collected_at,document_sha256:s.document_sha256})),first_observed_at:times[0],last_collected_at:times.at(-1),board_evidence:[],status_evidence:[],identity_evidence:{bse_scrip_code:annualSource(a,a.identifiers.bse_scrip_code.page,a.identifiers.bse_scrip_code.evidence_locator),nse_symbol:a.identifiers.nse_symbol?annualSource(a,a.identifiers.nse_symbol.page,a.identifiers.nse_symbol.evidence_locator):null},bse_2023_irms_import:{manifest:MANIFEST,review:REVIEW,field_review:FIELD_REVIEW,receipt:RECEIPT,discovery_bse_scrip_code:a.discovery_bse_scrip_code,document_inconsistencies:structuredClone(a.document_inconsistencies)}};
  for(const f of FIELDS){
   const t=f==='listing_date'?a.listing_date:p.terms[f];
   if(t.value===null){record[f]={value:null,status:'missing',source:null,corrections:[],qualification:t.qualification};continue;}
   const source=f==='listing_date'?annualSource(a,t.page,t.evidence_locator):prospectus(t.evidence.page,t.evidence.locator);
   record[f]={value:structuredClone(t.value),status:t.status==='verified_stated_term'?'verified':t.status,source_value:t.source_value,source_unit:t.source_unit,reporting_period:t.reporting_period,page:source.page,source,corrections:[],qualification:t.qualification??'Actual equity listing disclosed retrospectively in the annual report; not a proposed prospectus date.'};
  }
  if(a.amount_conflict){
   const x=a.amount_conflict,other=x.competing_observation,t=p.terms.issue_size_inr;
   record.issue_size_inr.status='conflict';record.issue_size_inr.qualification=x.qualification;
   record.issue_size_inr.additional_sources=[annualSource(a,other.page,other.evidence_locator)];
   record.issue_size_inr.corrections=[{kind:'unresolved_offer_total_disagreement',status:'unresolved',note:x.qualification,preferred_candidate:{value:t.value,source_value:t.source_value,source_unit:t.source_unit,original_status:t.status,qualification:t.qualification,page:t.evidence.page},competing_observations:[{...structuredClone(other),source_url:a.document.url,document_sha256:a.document.response_sha256}]}];
  }
  record.status_evidence=[record.listing_date.source];return record;
 });
}
export function apply(all,ctx,now){
 req(clock(now),'invalid_generation_clock');const targets=expected(ctx),out=structuredClone(all);
 req(now>=ctx.review.reviewed_at&&Array.isArray(out['2023']?.records),'generation_before_review_or_missing_year');
 const rows=Object.entries(out).flatMap(([year,m])=>{req(/^20\d{2}$/.test(year)&&Array.isArray(m.records),'invalid_recovery_year');return m.records.map(record=>({year,record}));});
 req(rows.every(x=>typeof x.record.id==='string')&&new Set(rows.map(x=>x.record.id)).size===rows.length,'duplicate_existing_id');
 let added=0,skipped=0;
 for(const target of targets){
  const hits=rows.filter(({record:r})=>r.id===target.id||canonicalIssuer(r.issuer_name)===canonicalIssuer(target.issuer_name)||String(r.bse_scrip_code??'')===target.bse_scrip_code||(target.nse_symbol&&String(r.nse_symbol??'').toUpperCase()===target.nse_symbol));
  if(hits.length){req(hits.length===1&&hits[0].year==='2023'&&hits[0].record.id===target.id,'identity_collision:'+target.id);req(same(hits[0].record,target),'changed_import_record:'+target.id);skipped++;continue;}
  out['2023'].records.push(target);rows.push({year:'2023',record:target});added++;
 }
 if(added)out['2023'].generated_at=now;
 return{recovery:out,stats:{records:4,added,skipped,changed:added>0}};
}
export function verifyOriginals(ctx,dir){
 validate(ctx);let bytes=0;
 for(const a of ctx.review.actions){const d=a.document;req(/^[0-9]{6}-annual-2024\.pdf$/.test(d.evidence_file),'unsafe_original_file');const b=fs.readFileSync(path.join(dir,d.evidence_file));req(b.length===d.response_bytes&&sha256(b)===d.response_sha256&&b.subarray(0,5).toString()==='%PDF-','original_bytes_mismatch');bytes+=b.length;}
 return{ok:true,original_documents:4,response_bytes:bytes};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){try{
 req(process.argv.length===3,'use_one_explicit_mode');const arg=process.argv[2],ctx=context();
 if(arg==='--review')console.log(JSON.stringify(validate(ctx)));
 else if(arg.startsWith('--verify-originals='))console.log(JSON.stringify(verifyOriginals(ctx,arg.slice('--verify-originals='.length))));
 else{req(['--check','--apply'].includes(arg),'use_--review_--check_or_--apply');const x=apply(loadRecovery(),ctx,new Date().toISOString());if(arg==='--apply'&&x.stats.changed){const file=path.join(ROOT,TARGET);fs.writeFileSync(file+'.tmp',JSON.stringify(x.recovery['2023'],null,2)+'\n');fs.renameSync(file+'.tmp',file);}console.log(JSON.stringify({irms_import:x.stats}));}
}catch(e){console.error(e.message);process.exitCode=1;}}
