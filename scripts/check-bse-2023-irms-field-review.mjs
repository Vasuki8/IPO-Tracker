import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {isDeepStrictEqual as same} from 'node:util';
import {sha256,strictDate} from './verify-bse-listing-candidates.mjs';
import {canonicalIssuer} from './sync-sebi-documents.mjs';

const ROOT=fileURLToPath(new URL('../',import.meta.url));
export const REVIEW='data/discovery/bse-2023-irms-field-review-2026-09-28.json';
const RECEIPT='data/evidence/bse-2023-irms-source-receipt-2026-09-28.json';
const PLAN='data/discovery/bse-2023-irms-source-plan-2026-09-28.json';
const QUEUE='data/discovery/bse-2023-review-queue-2026-09-28.json';
const CODES=['544026','544053','544060','543963'];
const FIELDS=['price_band','issue_price','issue_size_inr','market_lot','minimum_bid_quantity','open_date','close_date','listing_date'];
// Human-reviewed historical observations, not an extraction parser or import
// manifest. Updating this pin requires a new evidence review; plausible values
// and valid page ranges alone never establish that a PDF supports a claim.
const REVIEWED_PROJECTION_SHA256='a930b9771284c045ae1fbb320130bb06d022a3d7731bdfb8f8b6badae8a55b64';
const req=(ok,message)=>{if(!ok)throw new Error(message);};
const parse=bytes=>JSON.parse(Buffer.from(bytes).toString('utf8'));
const stamp=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(s)&&Number.isFinite(Date.parse(s));
const date=s=>typeof s==='string'&&strictDate(s)===s;
const positive=n=>Number.isSafeInteger(n)&&n>0;
const keys=(o,list)=>o&&same(Object.keys(o).sort(),[...list].sort());

export function context(root=ROOT){
 const read=p=>fs.readFileSync(path.join(root,p));
 return {review:parse(read(REVIEW)),receiptBytes:read(RECEIPT),planBytes:read(PLAN),queueBytes:read(QUEUE)};
}

export function validateReview(ctx){
 const r=ctx.review;
 req(r?.schema_version==='1.0.0'&&r.status==='reviewed_prospectus_terms_listing_evidence_pending'&&r.source_year===2023,'invalid_review');
 req(r.prospectus_terms_reviewed===true&&r.ipo_release_review_complete===false&&r.publication_import_allowed===false&&r.auto_import_allowed===false&&r.source_refetched===false&&r.complete_indian_ipo_universe===false,'unsafe_review_scope');
 for(const [key,p,bytes] of [['source_receipt',RECEIPT,ctx.receiptBytes],['source_plan',PLAN,ctx.planBytes],['source_queue',QUEUE,ctx.queueBytes]]){
  req(keys(r[key],['path','sha256'])&&r[key].path===p&&r[key].sha256===sha256(bytes),'raw_source_binding_mismatch:'+key);
 }
 const b=parse(ctx.receiptBytes),p=parse(ctx.planBytes),q=parse(ctx.queueBytes);
 req(b.status==='retained_source_set_complete_across_partial_collections'&&b.source_set_complete===true&&b.single_collection_complete===false&&b.publication_import_allowed===false&&b.semantic_review_complete===false,'invalid_original_receipt');
 req(b.plan_sha256===r.source_plan.sha256&&b.source_queue_sha256===r.source_queue.sha256&&p.source_queue_sha256===r.source_queue.sha256,'source_set_binding_mismatch');
 req(q.source_year===2023&&q.auto_import_allowed===false&&p.publication_import_allowed===false,'unsafe_original_source');
 req(stamp(r.reviewed_at)&&stamp(r.discovery_source_collected_at)&&r.discovery_source_collected_at===q.source_collected_at&&r.discovery_source_collected_at===p.discovery_source_collected_at&&r.reviewed_at>=b.independently_checked_at,'invalid_review_clock');
 req(Array.isArray(r.actions)&&same(r.actions.map(a=>a.discovery_bse_scrip_code),CODES),'invalid_candidate_scope');
 req(b.collections.length===2&&b.collections.every(c=>c.receipt.status==='partial'&&c.receipt.publication_import_allowed===false&&c.receipt_sha256===sha256(JSON.stringify(c.receipt,null,2)+'\n')),'partial_history_changed');
 const counts={ok:true,issuers:4,field_dispositions:0,verified_stated_terms:0,provisional:0,not_applicable:0,missing:0,publication_import_allowed:false};
 for(const a of r.actions){
  const code=a.discovery_bse_scrip_code,d=a.document;
  const original=q.rows.filter(x=>x.bse_scrip_code===code),planned=p.issuers.find(x=>x.discovery_bse_scrip_code===code);
  req(original.length===1&&original[0].source_row_index===a.source_row_index&&canonicalIssuer(original[0].issuer_name)===canonicalIssuer(a.issuer_name)&&planned?.issuer_name===a.issuer_name,'candidate_identity_mismatch');
  req(/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(a.candidate_id)&&keys(a.terms,FIELDS),'invalid_field_scope');
  req(keys(a.unverified_identifiers,['bse_scrip_code','nse_symbol','isin','board'])&&Object.values(a.unverified_identifiers).every(v=>v===null),'unverified_identity_promoted');
  const selections=b.selected_documents.filter(s=>s.code===code&&s.kind==='prospectus');req(selections.length===1,'missing_selected_source');
  const s=selections[0],collection=b.collections.find(c=>c.workflow_attempt===s.workflow_attempt),response=collection?.receipt.documents.find(x=>x.code===code&&x.kind==='prospectus');
  const cover=b.document_identity_observations.find(x=>x.code===code);
  req(response?.accepted===true&&response.http_status===200&&s.response_sha256===response.response_sha256,'unaccepted_source');
  req(d.url===response.url&&d.url===planned.prospectus_url&&d.response_sha256===response.response_sha256&&d.response_bytes===response.response_bytes&&d.evidence_file===response.evidence_file,'document_source_mismatch');
  req(d.workflow_attempt===s.workflow_attempt&&d.workflow_run_id===collection.workflow_run_id&&d.artifact_id===collection.artifact.id,'document_attempt_mismatch');
  req(d.document_type==='prospectus'&&date(d.document_date)&&d.document_date===cover.cover_date_observed&&d.pdf_pages===cover.pdf_pages&&d.response_sha256===cover.source_response_sha256,'document_identity_mismatch');
  req(d.publication_date===null&&d.landing_displayed_date===planned.landing_displayed_date,'unknown_publication_date_promoted');
  req(d.requested_at===response.requested_at&&d.collected_at===response.collected_at&&stamp(d.requested_at)&&stamp(d.collected_at)&&d.requested_at<=d.collected_at&&d.collected_at<=r.reviewed_at,'document_clock_mismatch');
  for(const field of FIELDS){
   const t=a.terms[field];counts.field_dispositions++;
   req(typeof t.qualification==='string'&&t.qualification.length>25,'missing_qualification');
   if(field==='listing_date'){
    req(keys(t,['value','status','evidence','qualification'])&&t.status==='missing'&&t.value===null&&t.evidence===null,'actual_listing_evidence_missing');counts.missing++;continue;
   }
   const e=t.evidence;
   req(t.reporting_period==='2023 IPO'&&typeof t.source_value==='string'&&t.source_value.length>0,'missing_field_scope');
   req(e&&e.document_sha256===d.response_sha256&&positive(e.page)&&e.page<=d.pdf_pages&&(e.printed_page===null||typeof e.printed_page==='string')&&typeof e.locator==='string'&&e.locator.length>12,'invalid_field_evidence');
   const expectedStatus=field==='price_band'&&code==='543963'?'not_applicable':field==='issue_size_inr'&&code!=='543963'?'provisional':'verified_stated_term';
   req(t.status===expectedStatus,'unsafe_field_status');counts[t.status==='verified_stated_term'?'verified_stated_terms':t.status]++;
   if(field==='price_band'){
    req(t.source_unit==='INR/share','invalid_band_unit');
    req(code==='543963'?t.value===null&&t.source_value==='fixed price':keys(t.value,['min','max'])&&positive(t.value.min)&&t.value.min<t.value.max&&positive(t.value.max)&&t.source_value===`${t.value.min}–${t.value.max}`,'invalid_price_band');
   }else if(field==='issue_size_inr'){
    const multiplier={'INR million':1000000,'INR lakh':100000}[t.source_unit];
    req(multiplier&&t.normalization_multiplier===multiplier&&/^\d+(?:\.\d{1,2})?$/.test(t.source_value)&&positive(t.value)&&Number(t.source_value)*multiplier===t.value&&t.scope==='total_offer'&&t.realised_proceeds_verified===false,'invalid_amount_unit_or_scope');
   }else if(field.endsWith('_date')){
    req(t.source_unit==='ISO date'&&date(t.value)&&t.source_value===t.value,'invalid_offer_date');
   }else{
    req(positive(t.value)&&Number(t.source_value)===t.value&&t.source_unit===(field==='issue_price'?'INR/share':'shares'),'invalid_price_or_quantity');
    if(field==='minimum_bid_quantity')req(t.investor_category==='retail individual','minimum_bid_scope_missing');
   }
  }
  const terms=a.terms,anchor=a.anchor_bid_date;
  req(terms.open_date.value<=terms.close_date.value,'inverted_offer_window');
  req(code==='543963'?anchor.value===null&&anchor.page===null:date(anchor.value)&&anchor.value<terms.open_date.value&&positive(anchor.page)&&anchor.page<=d.pdf_pages,'anchor_is_not_public_opening');
  req(code==='543963'||(terms.price_band.value.min<=terms.issue_price.value&&terms.issue_price.value<=terms.price_band.value.max),'issue_price_outside_band');
 }
 const {ok,publication_import_allowed,...expectedCounts}=counts;
 req(same(r.disposition_counts,expectedCounts),'review_counts_mismatch');
 // This last binding protects exact values, specific page locators and the
 // complete qualifications. Schema validation is not semantic PDF extraction.
 req(sha256(JSON.stringify(r))===REVIEWED_PROJECTION_SHA256,'reviewed_projection_changed');
 return counts;
}

export function reconcileIdentities(actions,recoveryByYear){
 req(recoveryByYear&&typeof recoveryByYear==='object'&&!Array.isArray(recoveryByYear),'invalid_recovery');
 const years=Object.keys(recoveryByYear).sort(),matches=[];let records=0;
 for(const year of years){
  const manifest=recoveryByYear[year];req(/^20\d{2}$/.test(year)&&Array.isArray(manifest?.records),'invalid_recovery_year');
  for(const record of manifest.records){
   req(record&&typeof record.id==='string'&&typeof record.issuer_name==='string','invalid_recovery_identity');records++;
   for(const a of actions){
    const reasons=[];
    if(record.id===a.candidate_id)reasons.push('candidate_id');
    if(canonicalIssuer(record.issuer_name)===canonicalIssuer(a.issuer_name))reasons.push('canonical_legal_name');
    if(String(record.bse_scrip_code??'')===a.discovery_bse_scrip_code)reasons.push('bse_scrip_code');
    if(reasons.length)matches.push({candidate_code:a.discovery_bse_scrip_code,id:record.id,issuer_name:record.issuer_name,recovery_year:Number(year),reasons});
   }
  }
 }
 return {years_checked:years.map(Number),records_checked:records,matches,clearance_for_import:false,scope:'Exact current id, canonical legal-name and BSE-code matches only; not fuzzy matching, permanent alias clearance or publication approval.'};
}

export function checkReview(root=ROOT){
 const ctx=context(root),review=validateReview(ctx),dir=path.join(root,'data/recovery');
 const years=fs.readdirSync(dir).filter(y=>/^20\d{2}$/.test(y)&&fs.existsSync(path.join(dir,y,'nse-issue-information.json')));
 const all=Object.fromEntries(years.map(y=>[y,parse(fs.readFileSync(path.join(dir,y,'nse-issue-information.json')))]));
 return {review,reconciliation:reconcileIdentities(ctx.review.actions,all)};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
 try{req(process.argv.length===2,'read-only checker accepts no arguments');console.log(JSON.stringify(checkReview(),null,2));}
 catch(e){console.error(e.message);process.exitCode=1;}
}
