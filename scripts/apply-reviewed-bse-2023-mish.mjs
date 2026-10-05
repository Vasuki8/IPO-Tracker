import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {isDeepStrictEqual as same} from 'node:util';
import {canonicalIssuer} from './sync-sebi-documents.mjs';
import {checkRepository as checkFieldReview} from './check-bse-2023-mish-field-review.mjs';

export const ROOT=fileURLToPath(new URL('../',import.meta.url));
export const PUBLICATION_REVIEW='data/discovery/bse-2023-mish-publication-review-2026-10-05.json';
export const FIELD_REVIEW='data/discovery/bse-2023-mish-field-review-2026-10-05.json';
export const RECEIPT='data/evidence/bse-2023-mish-source-receipt-2026-10-05.json';
export const MANIFEST='data/verified-bse-listings/2026-10-05-mish-2023.json';
export const TARGET='data/recovery/2023/nse-issue-information.json';
const APPROVED_MANIFEST_GIT_BLOB='4776a79a839d385f99ef1b1aa6831bc6e5a26ca3';
const req=(ok,message)=>{if(!ok)throw new Error(message);};
const parse=b=>JSON.parse(Buffer.from(b).toString('utf8'));
const gitBlob=b=>{const x=Buffer.from(b);return createHash('sha1').update(Buffer.from('blob '+x.length+'\0')).update(x).digest('hex');};
const stamp=v=>typeof v==='string'&&/^\d{4}-\d{2}-\d{2}T.*Z$/.test(v)&&Number.isFinite(Date.parse(v));

export function loadRecovery(root=ROOT){
 const dir=path.join(root,'data/recovery'),out={};
 for(const e of fs.readdirSync(dir,{withFileTypes:true})){
   if(!e.isDirectory()||!/^20\d{2}$/.test(e.name))continue;
   const p=path.join(dir,e.name,'nse-issue-information.json');
   if(fs.existsSync(p))out[e.name]=JSON.parse(fs.readFileSync(p,'utf8'));
 }
 return out;
}
export function context(root=ROOT){
 const read=p=>fs.readFileSync(path.join(root,p));
 const manifestBytes=read(MANIFEST),publicationReviewBytes=read(PUBLICATION_REVIEW),fieldReviewBytes=read(FIELD_REVIEW),receiptBytes=read(RECEIPT);
 return{
   manifestBytes,publicationReviewBytes,fieldReviewBytes,receiptBytes,
   manifest:parse(manifestBytes),publicationReview:parse(publicationReviewBytes),fieldReview:parse(fieldReviewBytes),receipt:parse(receiptBytes),
   fieldReviewCheck:checkFieldReview(root)
 };
}
export function validate(ctx){
 const {manifest:m,publicationReview:r,fieldReview:f,receipt:c}=ctx;
 req(same(parse(ctx.manifestBytes),m)&&same(parse(ctx.publicationReviewBytes),r)&&same(parse(ctx.fieldReviewBytes),f)&&same(parse(ctx.receiptBytes),c),'parsed_bytes_mismatch');
 req(gitBlob(ctx.manifestBytes)===APPROVED_MANIFEST_GIT_BLOB,'unapproved_manifest_blob');
 req(m?.schema_version==='1.0.0'&&m.status==='approved_bse_2023_mish_import'&&m.target_year===2023&&m.publication_import_allowed===true&&m.auto_import_allowed===false,'invalid_manifest_scope');
 req(m.publication_review_path===PUBLICATION_REVIEW&&m.publication_review_git_blob_sha===gitBlob(ctx.publicationReviewBytes)&&m.publication_review_git_blob_sha==='cd2eb5475b398356ff962bbffb42f3de3f41639f','publication_review_binding');
 req(m.field_review_path===FIELD_REVIEW&&m.field_review_git_blob_sha===gitBlob(ctx.fieldReviewBytes)&&m.field_review_git_blob_sha==='2ba6d540d985a3414df23b778121ba116cc33e4d','field_review_binding');
 req(m.source_receipt_path===RECEIPT&&m.source_receipt_git_blob_sha===gitBlob(ctx.receiptBytes)&&m.source_receipt_git_blob_sha==='0c18a8f88427f55ab4ba184c529a0a35048863de','receipt_binding');
 req(stamp(m.reviewed_at)&&m.reviewed_at===r.reviewed_at,'review_clock_mismatch');
 req(same(m.actions,[{stable_id:'mish-designs-limited',discovery_bse_scrip_code:'544015'}]),'manifest_action_scope');

 req(ctx.fieldReviewCheck?.ok===true&&ctx.fieldReviewCheck.issuer==='mish-designs-limited'&&ctx.fieldReviewCheck.publication_import_allowed===false&&ctx.fieldReviewCheck.recovery_identity_hits===0,'field_review_not_clean');
 req(r?.schema_version==='1.0.0'&&r.status==='reviewed_bse_2023_mish_publication_approved'&&r.batch_id==='bse-2023-mish'&&r.source_year===2023,'invalid_publication_review');
 req(r.publication_import_allowed===true&&r.auto_import_allowed===false&&r.complete_indian_ipo_universe===false,'unsafe_publication_review');
 req(r.candidate?.stable_id==='mish-designs-limited'&&r.candidate.issuer_name==='Mish Designs Limited'&&r.candidate.discovery_bse_scrip_code==='544015'&&r.candidate.source_row_index===27&&r.candidate.decision==='approved_missing_ipo','publication_candidate_identity');
 req(r.field_review?.path===FIELD_REVIEW&&r.field_review.git_blob_sha===m.field_review_git_blob_sha&&r.source_receipt?.path===RECEIPT&&r.source_receipt.git_blob_sha===m.source_receipt_git_blob_sha,'publication_source_binding');
 req(same(r.approved_public_fields,['status','issue_price','issue_size_inr','open_date','close_date','listing_date']),'unexpected_public_field_scope');
 req(same(r.approved_identity_fields,['bse_scrip_code']),'unexpected_identity_scope');
 req(same(r.publication_source_policy?.allowed_source_keys,['bse_annual_report_2023_24'])&&same(r.publication_source_policy?.disallowed_for_public_evidence,['issuer_final_prospectus'])&&r.publication_source_policy.source_allowlist_expansion===false,'unsafe_source_policy');
 req(r.rules?.fixed_price_semantics===true&&r.rules.market_lot_distinct_from_minimum_bid===true&&r.rules.no_application_amount_inference===true&&r.rules.preserve_date_conflict_history===true&&r.rules.exact_served_verification_required_after_publication===true,'missing_publication_rules');

 req(f?.status==='reviewed_bse_2023_mish_semantic'&&f.publication_import_allowed===false&&f.issuer?.stable_id==='mish-designs-limited','unexpected_field_review');
 const annual=f.sources?.bse_annual_report_2023_24,issuer=f.sources?.issuer_final_prospectus;
 req(annual?.authority==='BSE Limited'&&new URL(annual.url).hostname==='www.bseindia.com'&&annual.publication_role==='approved_publication_source','annual_not_publishable');
 req(issuer?.authority==='Mish Designs Limited'&&new URL(issuer.url).hostname==='mishindia.com'&&issuer.publication_role==='semantic_review_only_host_outside_current_builder_allowlist','issuer_source_policy_changed');
 const annualReceipt=c?.documents?.find(x=>x.key==='bse_annual_report_2023_24');
 req(c.status==='complete_source_collection_only'&&c.publication_import_allowed===false&&c.semantic_review_complete===false,'unsafe_receipt_scope');
 req(annualReceipt?.authority==='BSE Limited'&&annualReceipt.url===annual.url&&annualReceipt.response_sha256===annual.document_sha256&&annualReceipt.collected_at===annual.collected_at&&annualReceipt.pdf_pages===annual.pdf_pages,'annual_receipt_mismatch');

 const fields=f.fields;
 req(fields.status.value==='listed'&&fields.status.status==='verified'&&fields.status.source_key==='bse_annual_report_2023_24','status_not_approved');
 req(fields.bse_scrip_code.value==='544015'&&fields.bse_scrip_code.status==='verified'&&fields.bse_scrip_code.source_key==='bse_annual_report_2023_24','bse_code_not_approved');
 for(const name of ['issue_price','issue_size_inr','open_date','close_date','listing_date'])req(fields[name].status==='verified'&&fields[name].source_key==='bse_annual_report_2023_24','field_not_bse_approved:'+name);
 req(fields.price_band.value===null&&fields.price_band.status==='missing_fixed_price','price_band_must_stay_missing');
 req(fields.board.value===null&&fields.board.status==='unapproved','board_must_stay_null');
 req(fields.market_lot.value===null&&fields.market_lot.status==='held_research_only','market_lot_must_stay_null');
 req(fields.minimum_bid_quantity.value===null&&fields.minimum_bid_quantity.status==='held_research_only','minimum_bid_must_stay_null');
 req(fields.minimum_application_amount_inr.value===null&&fields.minimum_application_amount_inr.status==='missing','minimum_amount_must_stay_null');
 req(fields.nse_symbol.value===null&&fields.isin.value===null&&fields.sector.value===null,'unsupported_fields_must_stay_null');
 return{ok:true,records:1,public_source_host:'www.bseindia.com',held_research_fields:2,source_allowlist_expanded:false};
}
function annualSource(ctx,page=null,locator=null){
 const a=ctx.fieldReview.sources.bse_annual_report_2023_24;
 return{
   url:a.url,
   document_type:a.document_type,
   document_identity:a.document_identity,
   document_date:a.document_date,
   publication_date:null,
   reporting_period:a.reporting_period,
   collected_at:a.collected_at,
   document_sha256:a.document_sha256,
   page,
   evidence_locator:locator
 };
}
function publicationCorrections(ctx,name){
 const f=ctx.fieldReview.fields[name];
 if(!['open_date','close_date'].includes(name))return [];
 const correction=f.corrections?.[0];
 req(correction?.kind==='intradocument_date_label_conflict'&&correction.status==='resolved_by_bse_post_ipo_source','missing_date_conflict:'+name);
 return [{
   recorded_at:ctx.manifest.reviewed_at,
   previous_value:correction.competing_observation.value,
   new_value:f.value,
   reason:correction.note
 }];
}
function retainedFieldFromReview(ctx,name){
 const f=ctx.fieldReview.fields[name],s=annualSource(ctx,f.page??null,f.evidence_locator??null);
 const out={
   value:structuredClone(f.value),
   status:f.status,
   source_value:f.source_value,
   source_unit:f.source_unit,
   reporting_period:f.reporting_period,
   page:s.page,
   source:s,
   corrections:publicationCorrections(ctx,name)
 };
 if(f.qualification)out.qualification=f.qualification;
 return out;
}
const missing=(qualification)=>({value:null,status:'missing',source:null,corrections:[],qualification});
export function expected(ctx){
 validate(ctx);
 const f=ctx.fieldReview.fields,a=ctx.fieldReview.sources.bse_annual_report_2023_24;
 const source=annualSource(ctx);
 const record={
   id:'mish-designs-limited',
   issuer_name:'Mish Designs Limited',
   board:null,
   sector:null,
   status:'listed',
   nse_symbol:null,
   nse_series:null,
   nse_source:null,
   bse_symbol:null,
   bse_scrip_code:'544015',
   isin:null,
   bse_source:null,
   terms:{price_band:null,market_lot:null,minimum_bid_quantity:null,open_date:null,close_date:null},
   documents:[{type:a.document_type,identity:a.document_identity,url:a.url,publication_date:null,collected_at:a.collected_at,document_sha256:a.document_sha256}],
   first_observed_at:a.collected_at,
   last_collected_at:a.collected_at,
   board_evidence:[],
   status_evidence:[annualSource(ctx,f.status.page,f.status.evidence_locator)],
   identity_evidence:{bse_scrip_code:annualSource(ctx,f.bse_scrip_code.page,f.bse_scrip_code.evidence_locator)},
   price_band:missing(f.price_band.reason),
   issue_price:retainedFieldFromReview(ctx,'issue_price'),
   issue_size_inr:retainedFieldFromReview(ctx,'issue_size_inr'),
   market_lot:missing(f.market_lot.reason),
   minimum_bid_quantity:missing(f.minimum_bid_quantity.reason),
   open_date:retainedFieldFromReview(ctx,'open_date'),
   close_date:retainedFieldFromReview(ctx,'close_date'),
   listing_date:retainedFieldFromReview(ctx,'listing_date'),
   bse_2023_mish_import:{
     manifest:MANIFEST,
     publication_review:PUBLICATION_REVIEW,
     field_review:FIELD_REVIEW,
     receipt:RECEIPT,
     discovery_bse_scrip_code:'544015',
     platform_observation:structuredClone(f.board.platform_observation),
     held_research_fields:['market_lot','minimum_bid_quantity']
   }
 };
 req(new URL(record.documents[0].url).hostname==='www.bseindia.com','public_document_host');
 for(const name of ['issue_price','issue_size_inr','open_date','close_date','listing_date']){
   req(new URL(record[name].source.url).hostname==='www.bseindia.com','public_field_host:'+name);
 }
 req(JSON.stringify(record).includes('mishindia.com')===false,'issuer_source_leaked_into_record');
 return [record];
}
export function apply(all,ctx,now){
 req(stamp(now),'invalid_generation_clock');req(now>=ctx.manifest.reviewed_at,'generation_before_approval');
 const targets=expected(ctx),out=structuredClone(all);
 req(Array.isArray(out['2023']?.records),'missing_2023_recovery');
 const rows=Object.entries(out).flatMap(([year,m])=>{req(/^20\d{2}$/.test(year)&&Array.isArray(m.records),'invalid_recovery_year');return m.records.map(record=>({year,record}));});
 req(rows.every(x=>typeof x.record.id==='string'&&x.record.id)&&new Set(rows.map(x=>x.record.id)).size===rows.length,'duplicate_existing_id');
 let added=0,skipped=0;
 for(const target of targets){
   const hits=rows.filter(({record:r})=>r.id===target.id||canonicalIssuer(r.issuer_name)===canonicalIssuer(target.issuer_name)||String(r.bse_scrip_code??'')===target.bse_scrip_code);
   if(hits.length){
     req(hits.length===1&&hits[0].year==='2023'&&hits[0].record.id===target.id,'identity_collision:'+target.id);
     req(same(hits[0].record,target),'changed_import_record:'+target.id);
     skipped++;continue;
   }
   out['2023'].records.push(target);rows.push({year:'2023',record:target});added++;
 }
 if(added)out['2023'].generated_at=now;
 return{recovery:out,stats:{records:1,added,skipped,changed:added>0}};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
 try{
   req(process.argv.length===3,'use_one_explicit_mode');
   const mode=process.argv[2],ctx=context();
   if(mode==='--review')console.log(JSON.stringify({mish_publication_review:validate(ctx)}));
   else{
     req(['--check','--apply'].includes(mode),'use_--review_--check_or_--apply');
     const result=apply(loadRecovery(),ctx,new Date().toISOString());
     if(mode==='--apply'&&result.stats.changed){
       const file=path.join(ROOT,TARGET),tmp=file+'.tmp';
       fs.writeFileSync(tmp,JSON.stringify(result.recovery['2023'],null,2)+'\n');fs.renameSync(tmp,file);
     }
     console.log(JSON.stringify({mish_import:result.stats}));
   }
 }catch(e){console.error(e.message);process.exitCode=1;}
}
