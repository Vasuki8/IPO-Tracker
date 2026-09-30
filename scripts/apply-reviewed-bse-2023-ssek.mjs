import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {isDeepStrictEqual as same} from 'node:util';
import {strictDate} from './verify-bse-listing-candidates.mjs';
import {canonicalIssuer} from './sync-sebi-documents.mjs';
import {context as fieldContext,validateReview as validateFieldReview} from './check-bse-2023-ssek-field-review.mjs';
import {validatePlan as validateListingPlan} from './collect-bse-2023-ssek-listing-evidence.mjs';
export {loadRecovery} from './apply-reviewed-bse-2023-rvpe.mjs';
import {loadRecovery} from './apply-reviewed-bse-2023-rvpe.mjs';

export const ROOT=fileURLToPath(new URL('../',import.meta.url));
export const REVIEW='data/discovery/bse-2023-ssek-listing-review-2026-09-29.json';
export const FIELD_REVIEW='data/discovery/bse-2023-ssek-field-review-2026-09-29.json';
export const RECEIPT='data/evidence/bse-2023-ssek-listing-source-receipt-2026-09-29.json';
export const PLAN='data/discovery/bse-2023-ssek-listing-source-plan-2026-09-29.json';
export const MANIFEST='data/verified-bse-listings/2026-09-29-ssek-2023.json';
export const TARGET='data/recovery/2023/nse-issue-information.json';
const CODES=['544059','543970','543895','543953'];
const FIELDS=['price_band','issue_price','issue_size_inr','market_lot','minimum_bid_quantity','open_date','close_date','listing_date'];
const APPROVED_MANIFEST_GIT_BLOB='b0238f570b2274b2023e6024978969bf4b99d7c5';
const req=(ok,message)=>{if(!ok)throw new Error(message);};
const parse=b=>JSON.parse(Buffer.from(b).toString('utf8'));
const stamp=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(s)&&Number.isFinite(Date.parse(s));
const date=s=>typeof s==='string'&&strictDate(s)===s;
const positive=n=>Number.isSafeInteger(n)&&n>0;
const gitBlobSha=b=>{const bytes=Buffer.from(b);return createHash('sha1').update(Buffer.from('blob '+bytes.length+'\0')).update(bytes).digest('hex');};
export function context(root=ROOT){
 const read=p=>fs.readFileSync(path.join(root,p));
 const manifestBytes=read(MANIFEST),reviewBytes=read(REVIEW),fieldReviewBytes=read(FIELD_REVIEW),receiptBytes=read(RECEIPT),planBytes=read(PLAN);
 return{manifest:parse(manifestBytes),review:parse(reviewBytes),receipt:parse(receiptBytes),plan:parse(planBytes),manifestBytes,reviewBytes,fieldReviewBytes,receiptBytes,planBytes,fieldContext:fieldContext(root)};
}
export function validate(ctx){
 const {manifest:m,review:r,receipt:c,plan:p}=ctx;
 req(gitBlobSha(ctx.manifestBytes)===APPROVED_MANIFEST_GIT_BLOB,'unapproved_manifest');
 req(m.schema_version==='1.0.0'&&m.status==='approved_bse_2023_ssek_import'&&m.target_year===2023&&m.publication_import_allowed===true&&m.auto_import_allowed===false,'invalid_import_scope');
 req(m.review_path===REVIEW&&m.review_git_blob_sha===gitBlobSha(ctx.reviewBytes)&&m.review_git_blob_sha==='f1f25a4442bca25b6daf0acd31c7ae9f1e0807d1','review_binding_mismatch');
 req(m.field_review_path===FIELD_REVIEW&&m.field_review_git_blob_sha===gitBlobSha(ctx.fieldReviewBytes)&&m.field_review_git_blob_sha==='279facba3105465d832799c2983d22ccbb3cdc09','field_review_binding_mismatch');
 req(m.receipt_path===RECEIPT&&m.receipt_git_blob_sha===gitBlobSha(ctx.receiptBytes)&&m.receipt_git_blob_sha==='39265548e1f7505e51b3139c9e30ab19079667e9','receipt_binding_mismatch');
 req(m.source_plan_path===PLAN&&m.source_plan_git_blob_sha===gitBlobSha(ctx.planBytes)&&m.source_plan_git_blob_sha==='e08d94a64e183c08b887ed173e07b147d259f3e7','plan_binding_mismatch');
 validateFieldReview(ctx.fieldContext);validateListingPlan(ctx.planBytes,{fieldReviewBytes:ctx.fieldReviewBytes});
 req(r.status==='reviewed_actual_listings_import_approved'&&r.batch_id==='bse-2023-ssek'&&r.source_year===2023&&r.publication_import_allowed===true&&r.auto_import_allowed===false&&r.complete_indian_ipo_universe===false&&r.discovery_source_refetched===false,'unsafe_review_scope');
 req(r.prospectus_review.path===FIELD_REVIEW&&r.prospectus_review.git_blob_sha===m.field_review_git_blob_sha&&r.listing_receipt.path===RECEIPT&&r.listing_receipt.git_blob_sha===m.receipt_git_blob_sha&&r.listing_source_plan.path===PLAN&&r.listing_source_plan.git_blob_sha===m.source_plan_git_blob_sha,'source_role_binding');
 req(stamp(r.reviewed_at)&&r.reviewed_at===m.reviewed_at&&stamp(c.checked_at)&&c.checked_at<=r.reviewed_at,'invalid_review_clock');
 req(c.status==='original_listing_sources_retained'&&c.batch_id==='bse-2023-ssek-listing'&&c.publication_import_allowed===false&&c.semantic_review_complete===false&&c.complete_indian_ipo_universe===false,'unsafe_receipt_scope');
 req(c.selected_run===36661649197&&c.selected_artifact_id===11075040486&&c.artifact.id===c.selected_artifact_id&&c.artifact.zip_sha256==='4d15ea1dcc130e3be3e816dff55a99b8b2df6943aca35660b8221268ba01f81e'&&c.artifact.retention_days===14,'unbound_listing_artifact');
 const docs=c.collection?.documents;req(c.collection?.status==='complete'&&c.collection.source_documents_expected===4&&c.collection.source_documents_accepted===4&&Array.isArray(docs)&&docs.length===4,'incomplete_listing_sources');
 req(docs.every(d=>d.status===200&&d.accepted===true&&d.error===null&&positive(d.response_bytes)&&/^[a-f0-9]{64}$/.test(d.response_sha256)&&positive(d.pdf_pages)),'invalid_listing_source_receipt');
 req(docs.reduce((n,d)=>n+d.response_bytes,0)===c.original_pdf_bytes&&c.original_pdf_bytes===c.collection.total_response_bytes,'listing_source_total_mismatch');
 req(same(r.actions.map(a=>a.discovery_bse_scrip_code),CODES)&&same(m.actions,r.actions.map(a=>({stable_id:a.stable_id,discovery_bse_scrip_code:a.discovery_bse_scrip_code}))),'unexpected_candidate_scope');
 const planByCode=new Map(p.issuers.map(x=>[x.discovery_bse_scrip_code,x])),docByCode=new Map(docs.map(x=>[x.code,x]));
 for(let i=0;i<r.actions.length;i++){
  const a=r.actions[i],f=ctx.fieldContext.review.actions[i],d=a.document,s=docByCode.get(a.discovery_bse_scrip_code),planned=planByCode.get(a.discovery_bse_scrip_code),t=a.listing_date;
  req(a.decision==='approved_missing_ipo'&&a.stable_id===f.candidate_id&&a.issuer_name===f.issuer_name&&a.source_row_index===f.source_row_index,'issuer_identity_mismatch');
  req(s&&planned&&planned.candidate_id===a.stable_id&&planned.issuer_name===a.issuer_name&&planned.source_url===d.url&&s.url===d.url,'listing_source_identity_mismatch');
  req(d.response_sha256===s.response_sha256&&d.response_bytes===s.response_bytes&&d.evidence_file===s.file&&d.pdf_pages===s.pdf_pages,'listing_source_response_mismatch');
  const u=new URL(d.url);req(u.protocol==='https:'&&u.hostname==='www.bseindia.com'&&!u.username&&!u.password&&!u.search&&!u.hash,'untrusted_listing_source_host');
  req(d.artifact_id===c.selected_artifact_id&&d.workflow_run_id===c.selected_run&&d.workflow_attempt===1,'listing_archive_mismatch');
  req(d.requested_at===s.requested_at&&d.collected_at===s.collected_at&&stamp(d.requested_at)&&stamp(d.collected_at)&&d.requested_at<=d.collected_at&&d.collected_at<=c.checked_at,'listing_source_clock_mismatch');
  req(d.reporting_period==='FY2023-24'&&d.publication_date===null&&positive(d.pdf_pages)&&typeof d.document_identity==='string'&&d.document_identity.length>20,'invalid_listing_document_identity');
  req(d.document_date===null||date(d.document_date),'invalid_listing_document_date');
  for(const page of [d.document_date_page,t.page,a.identifiers.bse_scrip_code.page,a.platform_observation.page].filter(x=>x!==null&&x!==undefined))req(positive(page)&&page<=d.pdf_pages,'listing_evidence_page_out_of_bounds');
  req(t.status==='verified'&&t.source_unit==='ISO date'&&date(t.value)&&t.value.startsWith('2023-')&&t.source_value===t.value&&f.terms.close_date.value<t.value&&t.reporting_period==='2023 IPO'&&t.evidence_locator.length>30,'invalid_actual_listing');
  req(a.identifiers.bse_scrip_code.value===a.discovery_bse_scrip_code&&a.identifiers.nse_symbol===null&&a.identifiers.isin===null&&a.identifiers.board===null,'unsupported_identity_promotion');
  req(a.platform_observation.value==='BSE SME'&&a.platform_observation.status==='retained_not_mapped_to_board','platform_must_not_become_board');
  req(Array.isArray(a.document_inconsistencies),'invalid_document_inconsistencies');
 }
 return{ok:true,records:4,listing_verified:4,board_promoted:0,isin_promoted:0,nse_promoted:0};
}
function annualSource(a,page,locator){
 const d=a.document;return{url:d.url,document_type:d.document_type,document_identity:d.document_identity,document_date:d.document_date,publication_date:d.publication_date,reporting_period:d.reporting_period,collected_at:d.collected_at,document_sha256:d.response_sha256,page,evidence_locator:locator};
}
export function expected(ctx){
 validate(ctx);
 return ctx.review.actions.map((a,i)=>{
  const f=ctx.fieldContext.review.actions[i],d=f.document;
  const prospectus=(page=null,locator=null)=>({url:d.url,document_type:'SEBI Prospectus PDF',document_identity:f.issuer_name+' — Prospectus '+d.document_date,document_date:d.document_date,publication_date:d.publication_date,reporting_period:'2023 IPO',collected_at:d.collected_at,document_sha256:d.response_sha256,page,evidence_locator:locator});
  const annual=annualSource(a,null,null),sources=[prospectus(),annual],times=sources.map(x=>x.collected_at).sort();
  const record={id:a.stable_id,issuer_name:a.issuer_name,board:null,sector:null,status:'listed',nse_symbol:null,nse_series:null,nse_source:null,bse_symbol:null,bse_scrip_code:a.identifiers.bse_scrip_code.value,isin:null,bse_source:null,terms:{price_band:null,market_lot:null,minimum_bid_quantity:null,open_date:null,close_date:null},documents:sources.map(s=>({type:s.document_type,identity:s.document_identity,url:s.url,publication_date:s.publication_date,collected_at:s.collected_at,document_sha256:s.document_sha256})),first_observed_at:times[0],last_collected_at:times.at(-1),board_evidence:[],status_evidence:[],identity_evidence:{bse_scrip_code:annualSource(a,a.identifiers.bse_scrip_code.page,a.identifiers.bse_scrip_code.evidence_locator)},bse_2023_ssek_import:{manifest:MANIFEST,review:REVIEW,field_review:FIELD_REVIEW,receipt:RECEIPT,source_plan:PLAN,discovery_bse_scrip_code:a.discovery_bse_scrip_code,platform_observation:structuredClone(a.platform_observation),document_inconsistencies:structuredClone(a.document_inconsistencies)}};
  for(const name of FIELDS){
   const t=name==='listing_date'?a.listing_date:f.terms[name];
   if(t.value===null){record[name]={value:null,status:'missing',source:null,corrections:[],qualification:t.qualification};continue;}
   const source=name==='listing_date'?annualSource(a,t.page,t.evidence_locator):prospectus(t.evidence.page,t.evidence.locator);
   record[name]={value:structuredClone(t.value),status:t.status==='verified_stated_term'?'verified':t.status,source_value:t.source_value,source_unit:t.source_unit,reporting_period:t.reporting_period,page:source.page,source,corrections:[],qualification:t.qualification??(name==='listing_date'?'Actual equity listing disclosed retrospectively in the annual report; not a proposed Prospectus schedule.':undefined)};
  }
  record.status_evidence=[record.listing_date.source];return record;
 });
}
export function apply(all,ctx,now){
 req(stamp(now),'invalid_generation_clock');const targets=expected(ctx),out=structuredClone(all);
 req(now>=ctx.review.reviewed_at&&Array.isArray(out['2023']?.records),'generation_before_review_or_missing_year');
 const rows=Object.entries(out).flatMap(([year,m])=>{req(/^20\d{2}$/.test(year)&&Array.isArray(m.records),'invalid_recovery_year');return m.records.map(record=>({year,record}));});
 req(rows.every(x=>typeof x.record.id==='string')&&new Set(rows.map(x=>x.record.id)).size===rows.length,'duplicate_existing_id');
 let added=0,skipped=0;
 for(const target of targets){
  const hits=rows.filter(({record:r})=>r.id===target.id||canonicalIssuer(r.issuer_name)===canonicalIssuer(target.issuer_name)||String(r.bse_scrip_code??'')===target.bse_scrip_code);
  if(hits.length){req(hits.length===1&&hits[0].year==='2023'&&hits[0].record.id===target.id,'identity_collision:'+target.id);req(same(hits[0].record,target),'changed_import_record:'+target.id);skipped++;continue;}
  out['2023'].records.push(target);rows.push({year:'2023',record:target});added++;
 }
 if(added)out['2023'].generated_at=now;
 return{recovery:out,stats:{records:4,added,skipped,changed:added>0}};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){try{
 req(process.argv.length===3,'use_one_explicit_mode');const arg=process.argv[2],ctx=context();
 if(arg==='--review')console.log(JSON.stringify(validate(ctx)));
 else{req(['--check','--apply'].includes(arg),'use_--review_--check_or_--apply');const x=apply(loadRecovery(),ctx,new Date().toISOString());if(arg==='--apply'&&x.stats.changed){const file=path.join(ROOT,TARGET);fs.writeFileSync(file+'.tmp',JSON.stringify(x.recovery['2023'],null,2)+'\n');fs.renameSync(file+'.tmp',file);}console.log(JSON.stringify({ssek_import:x.stats}));}
}catch(e){console.error(e.message);process.exitCode=1;}}
