import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';

const ROOT=fileURLToPath(new URL('../',import.meta.url));
export const REVIEW='data/discovery/bse-2023-mish-field-review-2026-10-05.json';
const QUEUE='data/discovery/bse-2023-review-queue-2026-09-28.json';
const PROGRESS='data/discovery/bse-2023-review-progress-2026-09-28.json';
const req=(ok,message)=>{if(!ok)throw new Error(message);};
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const gitBlob=bytes=>{const b=Buffer.from(bytes);return createHash('sha1').update(Buffer.from('blob '+b.length+'\0')).update(b).digest('hex');};
const read=(root,p)=>fs.readFileSync(path.join(root,p));
const json=(root,p)=>JSON.parse(read(root,p));
const canon=v=>String(v??'').toLowerCase().replace(/['’]/g,'').replace(/&/g,' and ').replace(/[^a-z0-9]+/g,' ').trim();
const date=v=>typeof v==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(v)&&Number.isFinite(Date.parse(v+'T00:00:00Z'));
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);

export function validateReview({review:r,queue,progress,sourcePlanBytes,sourceReceiptBytes,rejectionBytes,recoveryByYear,published}){
 req(r?.schema_version==='1.0.0'&&r.status==='reviewed_bse_2023_mish_semantic'&&r.source_year===2023,'invalid_review');
 req(r.publication_import_allowed===false&&r.complete_indian_ipo_universe===false,'unsafe_review_scope');
 req(r.issuer?.stable_id==='mish-designs-limited'&&r.issuer.issuer_name==='Mish Designs Limited'&&r.issuer.discovery_bse_scrip_code==='544015'&&r.issuer.source_row_index===27,'review_identity');
 req(r.issuer.decision==='semantic_review_complete_publication_not_approved','unsafe_review_decision');

 const bindings=r.source_bindings;
 req(bindings?.source_plan==='data/discovery/bse-2023-mish-source-plan-2026-10-05.json'&&bindings.source_receipt==='data/evidence/bse-2023-mish-source-receipt-2026-10-05.json'&&bindings.rejected_bse_candidate==='data/evidence/bse-2023-mish-bse-prospectus-rejection-2026-10-05.json','binding_paths');
 req(gitBlob(sourcePlanBytes)===bindings.source_plan_git_blob_sha,'source_plan_blob_mismatch');
 req(gitBlob(sourceReceiptBytes)===bindings.source_receipt_git_blob_sha,'source_receipt_blob_mismatch');
 req(gitBlob(rejectionBytes)===bindings.rejected_bse_candidate_git_blob_sha,'rejection_blob_mismatch');

 req(queue?.source_year===2023&&Array.isArray(queue.rows),'invalid_queue');
 const q=queue.rows.filter(x=>x.bse_scrip_code==='544015');
 req(q.length===1&&q[0].source_row_index===27&&q[0].issuer_name==='Mish Designs Limited','queue_identity');
 req(progress?.source_year===2023&&Array.isArray(progress.rows)&&progress.next_bounded_review_codes?.[0]==='544015','progress_scope');
 const p=progress.rows.find(x=>x.bse_scrip_code==='544015');
 req(p?.disposition==='awaiting_review'&&['stable_id','manifest','release_pr','live_receipt'].every(k=>p[k]===null),'progress_not_awaiting');

 const recoveryRows=Object.entries(recoveryByYear).flatMap(([year,m])=>{req(/^20\d{2}$/.test(year)&&Array.isArray(m.records),'invalid_recovery');return m.records.map(x=>({year,x}));});
 const hits=recoveryRows.filter(({x})=>x.id==='mish-designs-limited'||canon(x.issuer_name)===canon('Mish Designs Limited')||String(x.bse_scrip_code??'')==='544015');
 req(hits.length===0,'existing_mish_recovery_identity');
 req(published?.schema_version==='1.2.0'&&Array.isArray(published.records),'invalid_public');
 req(!published.records.some(x=>x.id==='mish-designs-limited'||canon(x.issuer_name)===canon('Mish Designs Limited')||String(x.bse_scrip_code??'')==='544015'),'existing_mish_public_identity');

 const receipt=JSON.parse(sourceReceiptBytes),rejection=JSON.parse(rejectionBytes),plan=JSON.parse(sourcePlanBytes);
 req(receipt.status==='complete_source_collection_only'&&receipt.publication_import_allowed===false&&receipt.semantic_review_complete===false,'source_receipt_scope');
 req(plan.batch_id==='bse-2023-mish'&&plan.publication_import_allowed===false,'source_plan_scope');
 req(rejection.status==='rejected_wrong_issuer_document'&&rejection.publication_import_allowed===false&&rejection.semantic_field_approval_allowed===false,'rejected_source_scope');
 req(rejection.semantic_review.cover_issuer==='ARROWHEAD SEPERATION ENGINEERING LIMITED'&&rejection.semantic_review.decision==='reject_as_mish_source','wrong_source_not_rejected');

 const annual=r.sources?.bse_annual_report_2023_24,prospectus=r.sources?.issuer_final_prospectus;
 req(annual?.authority==='BSE Limited'&&new URL(annual.url).hostname==='www.bseindia.com'&&annual.publication_role==='approved_publication_source','annual_source_policy');
 req(prospectus?.authority==='Mish Designs Limited'&&new URL(prospectus.url).hostname==='mishindia.com'&&prospectus.publication_role==='semantic_review_only_host_outside_current_builder_allowlist','prospectus_source_policy');
 const receiptAnnual=receipt.documents.find(x=>x.key==='bse_annual_report_2023_24'),receiptProspectus=receipt.documents.find(x=>x.key==='final_prospectus');
 req(receiptAnnual&&receiptAnnual.response_sha256===annual.document_sha256&&receiptAnnual.pdf_pages===annual.pdf_pages&&receiptAnnual.collected_at===annual.collected_at,'annual_receipt_binding');
 req(receiptProspectus&&receiptProspectus.response_sha256===prospectus.document_sha256&&receiptProspectus.pdf_pages===prospectus.pdf_pages&&receiptProspectus.collected_at===prospectus.collected_at,'prospectus_receipt_binding');
 req(hash(annual.document_sha256)&&hash(prospectus.document_sha256),'invalid_document_hash');

 const f=r.fields;
 req(f.status.value==='listed'&&f.status.status==='verified'&&f.status.source_key==='bse_annual_report_2023_24'&&f.status.page===20,'status_field');
 req(f.bse_scrip_code.value==='544015'&&f.bse_scrip_code.status==='verified'&&f.bse_scrip_code.page===1,'bse_identity_field');
 req(f.board.value===null&&f.board.status==='unapproved'&&f.board.platform_observation.value==='BSE SME Platform'&&f.board.platform_observation.page===20,'board_must_remain_unapproved');
 req(f.price_band.value===null&&f.price_band.status==='missing_fixed_price','fixed_price_band');
 req(f.issue_price.value===122&&f.issue_price.status==='verified'&&f.issue_price.source_key==='bse_annual_report_2023_24'&&f.issue_price.page===20&&f.issue_price.source_unit==='INR/share','issue_price');
 req(f.issue_size_inr.value===97600000&&f.issue_size_inr.status==='verified'&&f.issue_size_inr.source_value==='976.00'&&f.issue_size_inr.source_unit==='INR lakh'&&f.issue_size_inr.normalization_multiplier===100000&&f.issue_size_inr.scope==='total_issue'&&Number(f.issue_size_inr.source_value)*f.issue_size_inr.normalization_multiplier===f.issue_size_inr.value,'issue_size');

 req(f.market_lot.value===null&&f.market_lot.status==='held_research_only'&&f.market_lot.held_observation.value===1000&&f.market_lot.held_observation.source_key==='issuer_final_prospectus'&&f.market_lot.held_observation.page===191,'market_lot_hold');
 req(f.minimum_bid_quantity.value===null&&f.minimum_bid_quantity.status==='held_research_only'&&Array.isArray(f.minimum_bid_quantity.held_observations)&&f.minimum_bid_quantity.held_observations.length===2&&f.minimum_bid_quantity.held_observations.every(x=>x.value===1000&&x.source_key==='issuer_final_prospectus'),'minimum_bid_hold');
 req(f.minimum_application_amount_inr.value===null&&f.minimum_application_amount_inr.status==='missing'&&/Do not infer/i.test(f.minimum_application_amount_inr.reason),'minimum_amount_must_not_be_inferred');

 req(f.open_date.value==='2023-10-31'&&f.close_date.value==='2023-11-02'&&f.listing_date.value==='2023-11-07','historical_dates');
 req([f.open_date.value,f.close_date.value,f.listing_date.value].every(date)&&f.open_date.value<f.close_date.value&&f.close_date.value<f.listing_date.value,'date_chronology');
 for(const [field,wrong] of [[f.open_date,'2023-11-02'],[f.close_date,'2023-10-31']]){
   req(field.status==='verified'&&field.source_key==='bse_annual_report_2023_24'&&field.page===20,'date_source');
   req(Array.isArray(field.corrections)&&field.corrections.length===1&&field.corrections[0].kind==='intradocument_date_label_conflict'&&field.corrections[0].status==='resolved_by_bse_post_ipo_source','date_conflict_history');
   req(field.corrections[0].competing_observation.value===wrong&&field.corrections[0].competing_observation.source_key==='issuer_final_prospectus'&&field.corrections[0].competing_observation.page===8,'date_conflict_observation');
 }
 req(f.listing_date.status==='verified'&&f.listing_date.source_key==='bse_annual_report_2023_24'&&f.listing_date.page===20&&f.listing_date.corroboration?.[0]?.page===56,'listing_date');
 req(f.nse_symbol.value===null&&f.isin.value===null&&f.sector.value===null,'unsupported_fields_must_remain_null');

 req(r.fixed_price_semantics===true&&Array.isArray(r.publication_blockers)&&r.publication_blockers.length>=2,'review_boundaries');
 req(r.publication_blockers.some(x=>/market_lot and minimum_bid_quantity/i.test(x)),'missing_lot_blocker');
 req(r.publication_blockers.some(x=>/No publication\/import manifest/i.test(x)),'missing_manifest_blocker');
 return {ok:true,issuer:r.issuer.stable_id,verified_core_fields:7,held_research_fields:2,publication_import_allowed:false,recovery_identity_hits:0};
}

export function checkRepository(root=ROOT){
 const review=json(root,REVIEW),queue=json(root,QUEUE),progress=json(root,PROGRESS),published=json(root,'data/ipos.json');
 const sourcePlanPath=review.source_bindings.source_plan,sourceReceiptPath=review.source_bindings.source_receipt,rejectionPath=review.source_bindings.rejected_bse_candidate;
 const recoveryByYear={};
 for(const e of fs.readdirSync(path.join(root,'data/recovery'),{withFileTypes:true})){
   if(!e.isDirectory()||!/^20\d{2}$/.test(e.name))continue;
   const p=path.join(root,'data/recovery',e.name,'nse-issue-information.json');
   if(fs.existsSync(p))recoveryByYear[e.name]=JSON.parse(fs.readFileSync(p,'utf8'));
 }
 return validateReview({review,queue,progress,sourcePlanBytes:read(root,sourcePlanPath),sourceReceiptBytes:read(root,sourceReceiptPath),rejectionBytes:read(root,rejectionPath),recoveryByYear,published});
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
 try{console.log(JSON.stringify({mish_field_review:checkRepository()},null,2));}
 catch(e){console.error(e.message);process.exitCode=1;}
}
