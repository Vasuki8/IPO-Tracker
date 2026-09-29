import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {isDeepStrictEqual as same} from 'node:util';
import {sha256,strictDate} from './verify-bse-listing-candidates.mjs';
import {canonicalIssuer} from './sync-sebi-documents.mjs';

const ROOT=fileURLToPath(new URL('../',import.meta.url));
export const REVIEW='data/discovery/bse-2023-ssek-field-review-2026-09-29.json';
const RECEIPT='data/evidence/bse-2023-ssek-source-receipt-2026-09-29.json';
const PLAN='data/discovery/bse-2023-ssek-source-plan-2026-09-29.json';
const QUEUE='data/discovery/bse-2023-review-queue-2026-09-28.json';
const CODES=['544059','543970','543895','543953'];
const FIXED=new Set(['543970','543953']);
const PROVISIONAL_AMOUNT=new Set(['544059','543895']);
const BOOK_BUILT=new Set(['544059','543895']);
const FIELDS=['price_band','issue_price','issue_size_inr','market_lot','minimum_bid_quantity','open_date','close_date','listing_date'];
const REVIEWED_PAGES={
  '544059':{price_band:10,issue_price:2,issue_size_inr:2,market_lot:9,minimum_bid_quantity:7,open_date:1,close_date:1},
  '543970':{price_band:2,issue_price:2,issue_size_inr:2,market_lot:8,minimum_bid_quantity:201,open_date:1,close_date:1},
  '543895':{price_band:2,issue_price:2,issue_size_inr:2,market_lot:189,minimum_bid_quantity:7,open_date:1,close_date:1},
  '543953':{price_band:1,issue_price:1,issue_size_inr:1,market_lot:9,minimum_bid_quantity:216,open_date:1,close_date:1}
};
const REVIEWED_GIT_BLOB='279facba3105465d832799c2983d22ccbb3cdc09';
const RECEIPT_GIT_BLOB='31c1e99c8c71dfd1dd53119a3247c0c5343dc19f';
const req=(ok,message)=>{if(!ok)throw new Error(message);};
const parse=b=>JSON.parse(Buffer.from(b).toString('utf8'));
const stamp=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(s)&&Number.isFinite(Date.parse(s));
const date=s=>typeof s==='string'&&strictDate(s)===s;
const positive=n=>Number.isSafeInteger(n)&&n>0;
const gitBlob=bytes=>createHash('sha1').update(Buffer.from('blob '+bytes.length+'\0')).update(bytes).digest('hex');

export function context(root=ROOT){
 const read=p=>fs.readFileSync(path.join(root,p));
 return {reviewBytes:read(REVIEW),review:parse(read(REVIEW)),receiptBytes:read(RECEIPT),planBytes:read(PLAN),queueBytes:read(QUEUE)};
}

export function validateReview(ctx){
 req(gitBlob(ctx.reviewBytes)===REVIEWED_GIT_BLOB,'reviewed_projection_changed');
 req(gitBlob(ctx.receiptBytes)===RECEIPT_GIT_BLOB,'source_receipt_changed');
 const r=ctx.review,b=parse(ctx.receiptBytes),p=parse(ctx.planBytes),q=parse(ctx.queueBytes);
 req(r?.schema_version==='1.0.0'&&r.status==='reviewed_prospectus_terms_listing_evidence_pending'&&r.source_year===2023,'invalid_review');
 req(r.prospectus_terms_reviewed===true&&r.ipo_release_review_complete===false&&r.publication_import_allowed===false&&r.auto_import_allowed===false&&r.source_refetched===false&&r.complete_indian_ipo_universe===false,'unsafe_review_scope');
 req(r.source_receipt?.path===RECEIPT&&r.source_receipt.git_blob_sha===RECEIPT_GIT_BLOB,'source_receipt_binding_mismatch');
 req(r.source_plan?.path===PLAN&&r.source_plan.sha256===sha256(ctx.planBytes),'source_plan_binding_mismatch');
 req(r.source_queue?.path===QUEUE&&r.source_queue.sha256===sha256(ctx.queueBytes),'source_queue_binding_mismatch');
 req(b.status==='retained_source_set_complete'&&b.source_set_complete===true&&b.single_collection_complete===true&&b.publication_import_allowed===false&&b.semantic_review_complete===false,'invalid_source_receipt');
 req(b.collection?.workflow_run_id===36601106741&&b.collection.workflow_attempt===1&&b.collection.artifact?.id===11048768865&&b.collection.artifact.digest==='sha256:938d65dbc230e0f0a3264a80dff8fa772d9d99695a7347db0b54a60fd914fcda','artifact_identity_mismatch');
 req(b.collection.raw_receipt_sha256==='704b090187ce88ffe8fbc3d76c41f36c498b2a398afcb89a4239ad1c5c77aa22'&&b.collection.identity_preflight_sha256==='8123287afe2966af1b5dc88bcd8c870e584c476585c160a9567fa4cb39e5e8a8','artifact_receipt_hash_mismatch');
 req(b.collection.identity_preflight?.identity_holds===0&&b.collection.identity_preflight.publication_import_allowed===false&&same(b.collection.identity_preflight.next_bounded_review_codes,CODES),'invalid_identity_preflight');
 req(b.unique_source_documents===8&&b.unique_response_bytes===16817590&&Array.isArray(b.documents)&&b.documents.length===8&&b.documents.every(d=>d.accepted===true&&d.http_status===200&&/^[a-f0-9]{64}$/.test(d.response_sha256)&&positive(d.response_bytes)),'incomplete_source_set');
 req(Array.isArray(b.landing_pdf_bindings)&&b.landing_pdf_bindings.length===4&&b.landing_pdf_bindings.every(x=>x.link_found===true),'source_link_binding_missing');
 req(stamp(b.independently_checked_at)&&stamp(r.reviewed_at)&&r.reviewed_at>=b.independently_checked_at&&r.discovery_source_collected_at===q.source_collected_at&&r.discovery_source_collected_at===p.discovery_source_collected_at,'invalid_review_clock');
 req(Array.isArray(r.actions)&&same(r.actions.map(a=>a.discovery_bse_scrip_code),CODES),'invalid_candidate_scope');

 const expectedInconsistency={544059:'definition_typo',543970:'archive_date_mismatch',543895:'offer_date_definition_conflict',543953:null};
 const counts={ok:true,issuers:4,field_dispositions:0,verified_stated_terms:0,provisional:0,not_applicable:0,missing:0,publication_import_allowed:false};
 for(const a of r.actions){
   const code=a.discovery_bse_scrip_code,d=a.document;
   const original=q.rows.filter(x=>x.bse_scrip_code===code),planned=p.issuers.find(x=>x.discovery_bse_scrip_code===code);
   req(original.length===1&&original[0].source_row_index===a.source_row_index&&canonicalIssuer(original[0].issuer_name)===canonicalIssuer(a.issuer_name)&&planned?.issuer_name===a.issuer_name,'candidate_identity_mismatch');
   req(/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(a.candidate_id)&&same(Object.keys(a.terms).sort(),FIELDS.slice().sort()),'invalid_field_scope');
   req(a.unverified_identifiers&&Object.values(a.unverified_identifiers).every(v=>v===null)&&same(Object.keys(a.unverified_identifiers).sort(),['board','bse_scrip_code','isin','nse_symbol']),'unverified_identity_promoted');

   const response=b.documents.find(x=>x.code===code&&x.kind==='prospectus'),cover=b.document_identity_observations.find(x=>x.code===code);
   req(response?.accepted===true&&d.url===response.url&&d.url===planned.prospectus_url&&d.response_sha256===response.response_sha256&&d.response_bytes===response.response_bytes&&d.evidence_file===response.evidence_file,'document_source_mismatch');
   req(d.workflow_run_id===36601106741&&d.workflow_attempt===1&&d.artifact_id===11048768865&&d.document_type==='prospectus','document_collection_identity_mismatch');
   req(date(d.document_date)&&d.document_date===cover?.cover_date_observed&&d.pdf_pages===cover?.pdf_pages&&d.response_sha256===cover?.source_response_sha256,'document_identity_mismatch');
   req(d.publication_date===null&&d.landing_displayed_date===planned.landing_displayed_date,'publication_date_laundered');
   req(d.requested_at===response.requested_at&&d.collected_at===response.collected_at&&stamp(d.requested_at)&&stamp(d.collected_at)&&d.collected_at<=r.reviewed_at,'document_clock_mismatch');

   req(Array.isArray(a.source_inconsistencies),'invalid_inconsistency_record');
   const kind=expectedInconsistency[code];
   req(kind?a.source_inconsistencies.length===1&&a.source_inconsistencies[0].kind===kind:a.source_inconsistencies.length===0,'source_inconsistency_changed');
   if(kind)req(typeof a.source_inconsistencies[0].observation==='string'&&a.source_inconsistencies[0].observation.length>50&&typeof a.source_inconsistencies[0].disposition==='string'&&a.source_inconsistencies[0].disposition.length>50,'source_inconsistency_qualification_missing');

   for(const field of FIELDS){
     const t=a.terms[field];counts.field_dispositions++;
     req(typeof t?.qualification==='string'&&t.qualification.length>25,'missing_qualification:'+code+':'+field);
     if(field==='listing_date'){req(t.status==='missing'&&t.value===null&&t.evidence===null,'actual_listing_evidence_missing');counts.missing++;continue;}
     req(t.reporting_period==='2023 IPO'&&typeof t.source_value==='string'&&t.source_value.length>0,'missing_field_scope');
     const e=t.evidence;req(e&&e.document_sha256===d.response_sha256&&positive(e.page)&&e.page<=d.pdf_pages&&(e.printed_page===null||typeof e.printed_page==='string')&&typeof e.locator==='string'&&e.locator.length>12,'invalid_field_evidence');
     req(e.page===REVIEWED_PAGES[code][field],'reviewed_evidence_page_changed:'+code+':'+field);

     const expectedStatus=field==='price_band'&&FIXED.has(code)?'not_applicable':field==='issue_size_inr'&&PROVISIONAL_AMOUNT.has(code)?'provisional':'verified_stated_term';
     req(t.status===expectedStatus,'unsafe_field_status:'+code+':'+field);counts[t.status==='verified_stated_term'?'verified_stated_terms':t.status]++;
     if(field==='price_band'){
       req(t.source_unit==='INR/share','invalid_band_unit');
       req(FIXED.has(code)?t.value===null&&t.source_value==='fixed price':t.value&&positive(t.value.min)&&positive(t.value.max)&&t.value.min<t.value.max&&t.source_value===t.value.min+'–'+t.value.max,'invalid_price_band');
     }else if(field==='issue_size_inr'){
       const multiplier={'INR thousand':1000,'INR lakh':100000}[t.source_unit];
       req(multiplier&&t.normalization_multiplier===multiplier&&/^\d+(?:\.\d{1,2})?$/.test(t.source_value)&&positive(t.value)&&Number(t.source_value)*multiplier===t.value&&t.scope==='total_offer'&&t.realised_proceeds_verified===false,'invalid_amount_unit_or_scope');
     }else if(field.endsWith('_date')){
       req(t.source_unit==='ISO date'&&date(t.value)&&t.source_value===t.value,'invalid_offer_date');
     }else{
       req(positive(t.value)&&Number(t.source_value)===t.value&&t.source_unit===(field==='issue_price'?'INR/share':'shares'),'invalid_price_or_quantity');
       if(field==='minimum_bid_quantity')req(t.investor_category==='retail individual','minimum_bid_scope_missing');
     }
   }

   req(a.terms.open_date.value<=a.terms.close_date.value,'inverted_offer_window');
   if(BOOK_BUILT.has(code))req(date(a.anchor_bid_date.value)&&a.anchor_bid_date.value<a.terms.open_date.value&&positive(a.anchor_bid_date.page),'anchor_is_not_public_opening');
   else req(a.anchor_bid_date.value===null&&a.anchor_bid_date.page===null,'fixed_price_anchor_invented');
   if(!FIXED.has(code))req(a.terms.price_band.value.min<=a.terms.issue_price.value&&a.terms.issue_price.value<=a.terms.price_band.value.max,'issue_price_outside_band');
 }
 req(same(r.disposition_counts,{issuers:4,field_dispositions:32,verified_stated_terms:24,provisional:2,not_applicable:2,missing:4}),'review_counts_mismatch');
 return counts;
}

export function reconcileIdentities(actions,recoveryByYear,published){
 const matches=[];let records=0;
 for(const [year,manifest] of Object.entries(recoveryByYear).sort()){
   req(/^20\d{2}$/.test(year)&&Array.isArray(manifest?.records),'invalid_recovery_year');
   for(const record of manifest.records){records++;
     for(const a of actions){const reasons=[];if(record.id===a.candidate_id)reasons.push('candidate_id');if(canonicalIssuer(record.issuer_name)===canonicalIssuer(a.issuer_name))reasons.push('canonical_legal_name');if(String(record.bse_scrip_code??'')===a.discovery_bse_scrip_code)reasons.push('bse_scrip_code');if(reasons.length)matches.push({surface:'recovery',year:Number(year),candidate_code:a.discovery_bse_scrip_code,id:record.id,issuer_name:record.issuer_name,reasons});}
   }
 }
 for(const record of published?.records||[])for(const a of actions){const reasons=[];if(record.id===a.candidate_id)reasons.push('candidate_id');if(canonicalIssuer(record.issuer_name)===canonicalIssuer(a.issuer_name))reasons.push('canonical_legal_name');if(String(record.bse_scrip_code??'')===a.discovery_bse_scrip_code)reasons.push('bse_scrip_code');if(reasons.length)matches.push({surface:'public',candidate_code:a.discovery_bse_scrip_code,id:record.id,issuer_name:record.issuer_name,reasons});}
 return {records_checked:records,public_records_checked:(published?.records||[]).length,matches,clearance_for_import:false,scope:'Exact current stable-id, canonical legal-name and BSE-code matches only; not fuzzy matching, permanent alias clearance or publication approval.'};
}

export function checkReview(root=ROOT){
 const ctx=context(root),review=validateReview(ctx),dir=path.join(root,'data/recovery'),all={};
 for(const year of fs.readdirSync(dir).filter(y=>/^20\d{2}$/.test(y)&&fs.existsSync(path.join(dir,y,'nse-issue-information.json'))))all[year]=parse(fs.readFileSync(path.join(dir,year,'nse-issue-information.json')));
 const reconciliation=reconcileIdentities(ctx.review.actions,all,parse(fs.readFileSync(path.join(root,'data/ipos.json'))));
 req(reconciliation.matches.length===0,'current_identity_collision_requires_review');
 return {review,reconciliation};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
 try{req(process.argv.length===2,'read-only checker accepts no arguments');console.log(JSON.stringify({bse_2023_ssek_field_review:checkReview()},null,2));}
 catch(e){console.error(e.message);process.exitCode=1;}
}
