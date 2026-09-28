import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {isDeepStrictEqual as same} from 'node:util';
import {sha256,strictDate} from './verify-bse-listing-candidates.mjs';
import {canonicalIssuer} from './sync-sebi-documents.mjs';
export const ROOT=fileURLToPath(new URL('../',import.meta.url));
export const REVIEW='data/discovery/bse-2023-four-review-2026-09-28.json';
export const RECEIPT='data/evidence/bse-2023-four-source-receipt-2026-09-28.json';
export const MANIFEST='data/verified-bse-listings/2026-09-28-four-2023.json';
export const QUEUE='data/discovery/bse-2023-review-queue-2026-09-28.json';
export const TARGET='data/recovery/2023/nse-issue-information.json';
export const FIELDS=['price_band','issue_price','issue_size_inr','market_lot','minimum_bid_quantity','open_date','close_date','listing_date'];
const SCOPE=[['sah','sah-polymers-limited','543743'],['global','global-surfaces-limited','543829'],['uday','udayshivakumar-infra-limited','543861'],['pyramid','pyramid-technoplast-limited','543969']];
const req=(x,m)=>{if(!x)throw Error(m);};
export const jsonBytes=x=>Buffer.from(JSON.stringify(x)+'\n');
const hash=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const clock=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(x)&&Number.isFinite(Date.parse(x));
const read=(root,p)=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
export function context(root=ROOT){const ctx={review:read(root,REVIEW),receipt:read(root,RECEIPT),manifest:read(root,MANIFEST),queue:read(root,QUEUE),queueBytes:fs.readFileSync(path.join(root,QUEUE))};req(sha256(fs.readFileSync(path.join(root,REVIEW)))===ctx.manifest.review_sha256&&sha256(fs.readFileSync(path.join(root,RECEIPT)))===ctx.manifest.receipt_sha256,'raw_file_binding_mismatch');return ctx;}
export function validate(ctx){
 const {review:r,receipt:c,manifest:m,queue:q}=ctx;
 req(r?.schema_version==='1.0.0'&&r.status==='reviewed_bse_2023_four'&&r.source_year===2023&&r.auto_import_allowed===false,'invalid_review');
 req(c?.schema_version==='1.0.0'&&c.status==='reviewed_original_official_documents','invalid_receipt');
 req(m?.schema_version==='1.0.0'&&m.status==='approved_bse_2023_four_import'&&m.target_year===2023,'invalid_manifest');
 req(same(r.actions.map(a=>[a.key,a.stable_id,a.discovery_bse_scrip_code]),SCOPE)&&same(m.actions,r.actions.map(({key,stable_id})=>({key,stable_id}))),'invalid_batch_scope');
 req(c.review_path===REVIEW&&m.review_path===REVIEW&&m.receipt_path===RECEIPT&&c.review_sha256===sha256(jsonBytes(r))&&m.review_sha256===c.review_sha256&&m.receipt_sha256===sha256(jsonBytes(c)),'content_binding_mismatch');
 req(r.source_queue===QUEUE&&r.source_queue_sha256===sha256(ctx.queueBytes)&&same(q,JSON.parse(Buffer.from(ctx.queueBytes)))&&q.source_year===2023&&q.auto_import_allowed===false,'queue_binding_mismatch');
 req(r.reconciliation.all_recovery_years_checked===true&&r.reconciliation.matched_records.length===0&&/^[a-f0-9]{40}$/.test(r.reconciliation.repository_commit),'invalid_baseline_reconciliation');
 req(c.documents.length===12&&r.sources.length===12&&c.artifacts.length===2,'invalid_source_scope');
 req(new Set(c.documents.map(d=>d.key)).size===12&&new Set(r.sources.map(s=>s.key)).size===12,'duplicate_source_key');
 req(new Set(c.artifacts.map(a=>a.id)).size===2&&c.artifacts.every(a=>Number.isSafeInteger(a.id)&&a.id>0&&hash(a.sha256)&&/^\d+$/.test(a.workflow_run_id)),'invalid_artifacts');
 req(c.total_response_bytes===c.documents.reduce((n,d)=>n+d.response_bytes,0)&&clock(c.collection_completed_at),'receipt_totals');
 const docs=new Map(c.documents.map(d=>[d.key,d])),sources=new Map(r.sources.map(s=>[s.key,s]));
 for(const [key,s] of sources){
  const d=docs.get(key),u=new URL(s.url);
  req(d&&d.source_url===s.url&&d.final_url===s.url&&d.http_status===200&&Number.isSafeInteger(d.response_bytes)&&d.response_bytes>0&&hash(d.response_sha256),'source_receipt_mismatch:'+key);
  req(u.protocol==='https:'&&['www.sebi.gov.in','www.bseindia.com'].includes(u.hostname)&&!u.username&&!u.password,'source_host');
  req(c.artifacts.some(a=>a.id===d.artifact_id&&a.workflow_run_id===d.workflow_run_id),'unbound_source_artifact');
  req(clock(d.requested_at)&&clock(d.collected_at)&&Date.parse(d.requested_at)<=Date.parse(d.collected_at)&&Date.parse(d.collected_at)<=Date.parse(c.collection_completed_at),'invalid_source_clock');
  req(strictDate(s.document_date)===s.document_date&&(s.publication_date===null||strictDate(s.publication_date)===s.publication_date),'invalid_document_clock');
  req(typeof s.document_identity==='string'&&s.document_identity.length>12&&typeof s.reporting_period==='string','invalid_document_identity');
  if(d.file.endsWith('.pdf')){req(Number.isSafeInteger(d.pdf_pages)&&d.pdf_pages>0,'invalid_pdf_pages');req(s.publication_date===null,'unknown_pdf_publication_date_must_stay_null');}
 }
 for(const a of r.actions){
  req(a.decision==='approved_missing_ipo'&&a.board===null,'unreviewed_board_or_decision');
  const candidates=q.rows.filter(row=>row.bse_scrip_code===a.discovery_bse_scrip_code);
  req(candidates.length===1&&canonicalIssuer(candidates[0].issuer_name)===canonicalIssuer(a.issuer_name),'candidate_identity_mismatch');
  req(same(Object.keys(a.terms),FIELDS)&&a.identity_sources.length===3&&new Set(a.identity_sources).size===3,'invalid_terms_scope');
  for(const key of a.identity_sources)req(sources.has(key)&&canonicalIssuer(sources.get(key).issuer_name)===canonicalIssuer(a.issuer_name),'identity_source_mismatch');
  for(const f of FIELDS){
   const t=a.terms[f],d=docs.get(t.source_key),s=sources.get(t.source_key);
   req(d&&s&&a.identity_sources.includes(t.source_key)&&canonicalIssuer(s.issuer_name)===canonicalIssuer(a.issuer_name),'field_source_issuer_mismatch');
   req(typeof t.source_value==='string'&&t.source_value.length>0&&t.reporting_period==='2023 IPO'&&typeof t.evidence_locator==='string'&&t.evidence_locator.length>12,'missing_field_observation');
   req(d.file.endsWith('.pdf')?Number.isSafeInteger(t.page)&&t.page>0&&t.page<=d.pdf_pages:t.page===null,'field_page_out_of_bounds');
   req(t.status===(f==='issue_size_inr'?'provisional':'verified'),'unsafe_field_status');
   req(f==='listing_date'?t.source_key.endsWith('_notice')||t.source_key.endsWith('_annual'):t.source_key===a.key+'_prospectus','wrong_document_role');
   if(f.endsWith('_date'))req(t.source_unit==='ISO date'&&strictDate(t.value)===t.value&&t.source_value===t.value,'invalid_date');
   else if(f==='price_band')req(t.source_unit==='INR/share'&&same(Object.keys(t.value),['min','max'])&&Number.isFinite(t.value.min)&&Number.isFinite(t.value.max)&&t.value.min>0&&t.value.min<t.value.max&&t.source_value===`${t.value.min}–${t.value.max}`,'invalid_band');
   else req(Number.isFinite(t.value)&&t.value>0,'invalid_positive_field');
   if(f==='issue_price')req(t.source_unit==='INR/share'&&Number(t.source_value)===t.value,'issue_price_unit');
   if(f==='market_lot')req(t.source_unit==='shares'&&t.value===1&&t.source_value==='one Equity Share','trading_lot_not_bid');
   if(f==='minimum_bid_quantity')req(t.source_unit==='shares'&&Number.isSafeInteger(t.value)&&Number(t.source_value)===t.value&&t.investor_category==='retail individual','bid_quantity_scope');
   if(f==='issue_size_inr')req(t.scope==='total_offer'&&t.source_value===t.reported_amount&&/^[0-9]+(?:\.[0-9]+)?$/.test(t.reported_amount)&&t.normalization_multiplier===({'INR lakh':100000,'INR million':1000000}[t.source_unit])&&Number(t.reported_amount)*t.normalization_multiplier===t.value&&typeof t.qualification==='string'&&t.qualification.length>30,'offer_size_scope_or_unit');
  }
  const t=a.terms;
  req(t.price_band.value.min<=t.issue_price.value&&t.issue_price.value<=t.price_band.value.max,'price_outside_band');
  req(strictDate(a.anchor_date)===a.anchor_date&&a.anchor_date<t.open_date.value&&t.open_date.value<=t.close_date.value&&t.close_date.value<t.listing_date.value&&t.listing_date.value.startsWith('2023-'),'offer_chronology_or_anchor');
 }
 return{docs,sources};
}
export function expected(ctx){
 const {docs,sources}=validate(ctx);
 const descriptor=(key,page=null,locator=null)=>{const d=docs.get(key),s=sources.get(key);return{url:s.url,document_type:s.document_type,document_identity:s.document_identity,document_date:s.document_date,reporting_period:s.reporting_period,publication_date:s.publication_date,page,collected_at:d.collected_at,document_sha256:d.response_sha256,evidence_locator:locator};};
 return ctx.review.actions.map(a=>{
  const retained=a.identity_sources.map(k=>descriptor(k)),times=retained.map(d=>d.collected_at).sort();
  const r={id:a.stable_id,issuer_name:a.issuer_name,board:null,sector:null,status:'listed',nse_symbol:null,nse_series:null,nse_source:null,bse_symbol:null,bse_scrip_code:null,isin:null,bse_source:null,terms:{price_band:null,market_lot:null,minimum_bid_quantity:null,open_date:null,close_date:null},documents:retained.map(s=>({type:s.document_type,identity:s.document_identity,url:s.url,publication_date:s.publication_date,collected_at:s.collected_at,document_sha256:s.document_sha256})),first_observed_at:times[0],last_collected_at:times.at(-1),board_evidence:[],status_evidence:[],bse_2023_four_import:{manifest:MANIFEST,review:REVIEW,receipt:RECEIPT,action_key:a.key,discovery_bse_scrip_code:a.discovery_bse_scrip_code}};
  for(const f of FIELDS){const t=a.terms[f];r[f]={value:structuredClone(t.value),source_value:t.source_value,source_unit:t.source_unit,reporting_period:t.reporting_period,status:t.status,page:t.page,source:descriptor(t.source_key,t.page,t.evidence_locator),corrections:[]};if(t.qualification)r[f].qualification=t.qualification;}
  r.status_evidence=[r.listing_date.source];return r;
 });
}
export function loadRecovery(root=ROOT){const p=path.join(root,'data/recovery');return Object.fromEntries(fs.readdirSync(p).filter(y=>/^20\d{2}$/.test(y)&&fs.existsSync(path.join(p,y,'nse-issue-information.json'))).map(y=>[y,read(root,`data/recovery/${y}/nse-issue-information.json`)]));}
export function apply(all,ctx,now){
 req(clock(now),'invalid_generation_clock');const targets=expected(ctx),out=structuredClone(all);
 req(Date.parse(now)>=Date.parse(ctx.receipt.collection_completed_at)&&Array.isArray(out['2023']?.records),'generation_before_collection_or_missing_year');
 const records=Object.entries(out).flatMap(([year,m])=>(m.records||[]).map(record=>({year,record})));
 req(new Set(records.map(x=>x.record.id)).size===records.length,'duplicate_existing_id');let added=0,skipped=0;
 for(const target of targets){
  const code=target.bse_2023_four_import.discovery_bse_scrip_code;
  const hits=records.filter(({record:r})=>r.id===target.id||canonicalIssuer(r.issuer_name)===canonicalIssuer(target.issuer_name)||String(r.bse_scrip_code??'')===code);
  if(hits.length){req(hits.length===1&&hits[0].year==='2023'&&hits[0].record.id===target.id,'identity_collision:'+target.id);req(same(hits[0].record,target),'changed_import_record:'+target.id);skipped++;continue;}
  out['2023'].records.push(target);records.push({year:'2023',record:target});added++;
 }
 if(added)out['2023'].generated_at=now;
 return{recovery:out,stats:{records:4,added,skipped,changed:added>0}};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){try{req(['--check','--apply'].includes(process.argv[2]),'use_--check_or_--apply');const x=apply(loadRecovery(),context(),new Date().toISOString());if(process.argv[2]==='--apply'&&x.stats.changed)fs.writeFileSync(path.join(ROOT,TARGET),JSON.stringify(x.recovery['2023'],null,2)+'\n');console.log(JSON.stringify({bse_2023_four:x.stats}));}catch(e){console.error(e.message);process.exitCode=1;}}
