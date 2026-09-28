// One new IPO plus an explicitly approved alias/term repair. No network or fuzzy auto-import.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {isDeepStrictEqual as same} from 'node:util';
import {sha256,strictDate} from './verify-bse-listing-candidates.mjs';
export const ROOT=fileURLToPath(new URL('../',import.meta.url));
export const REVIEW='data/discovery/bse-2022-final-pair-review-2026-09-28.json';
export const RECEIPT='data/evidence/bse-2022-final-pair-source-receipt-2026-09-28.json';
export const MANIFEST='data/verified-bse-listings/2026-09-28-final-pair.json';
export const ID='droneacharya-aerial-innovations-limited',ALIAS_ID='fivestar-business-finance-limited';
export const FIELDS=['price_band','issue_price','issue_size_inr','market_lot','minimum_bid_quantity','open_date','close_date','listing_date'];
export const REPAIRS=['price_band','market_lot','open_date','close_date','issue_size_inr'];
const KEYS=['drone_prospectus','fivestar_prospectus','drone_listing_corroboration'];
const req=(ok,msg)=>{if(!ok)throw Error(msg);};
const integer=v=>Number.isSafeInteger(v)&&v>0;
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const timestamp=v=>typeof v==='string'&&/^\d{4}-\d{2}-\d{2}T[\d:.]+Z$/.test(v)&&Number.isFinite(Date.parse(v));
const keys=(a,b)=>same([...a].sort(),[...b].sort());
const nameKey=s=>String(s??'').toLowerCase().replace(/\blimited\b|\bltd\b/g,'').replace(/[^a-z0-9]/g,'');
function official(url){const u=new URL(url);req(u.protocol==='https:'&&u.hostname==='www.sebi.gov.in'&&!u.port&&!u.username&&!u.password,'unsafe_source_url');}
export function context(root=ROOT){
 const read=p=>fs.readFileSync(path.join(root,p));
 const reviewBytes=read(REVIEW),receiptBytes=read(RECEIPT);
 const ctx={reviewBytes,receiptBytes,review:JSON.parse(reviewBytes),receipt:JSON.parse(receiptBytes),manifest:JSON.parse(read(MANIFEST))};
 validateContext(ctx);return ctx;
}
export function validateContext(c){
 const {review:r,receipt:t,manifest:m}=c;
 req(same(JSON.parse(Buffer.from(c.reviewBytes)),r)&&same(JSON.parse(Buffer.from(c.receiptBytes)),t),'parsed_evidence_changed');
 req(m.schema_version==='1.0.0'&&m.status==='approved_final_bse_2022_pair'&&m.target_year===2022&&m.review_path===REVIEW&&m.receipt_path===RECEIPT&&m.review_sha256===sha256(c.reviewBytes)&&m.receipt_sha256===sha256(c.receiptBytes)&&t.review_sha256===m.review_sha256&&t.review_path===REVIEW,'unbound_evidence');
 req(same(m.import_ids,[ID])&&same(m.existing_alias_ids,[ALIAS_ID])&&keys(m.repair_fields,REPAIRS)&&m.no_inference===true&&m.minimum_application_amount==='out_of_scope','invalid_manifest_scope');
 req(r.schema_version==='1.0.0'&&r.status==='reviewed_final_bse_2022_pair'&&r.source_year===2022&&r.auto_import_allowed===false,'invalid_review_scope');
 req(t.schema_version==='1.0.0'&&t.status==='reviewed_original_official_documents'&&integer(t.artifact_id)&&hash(t.artifact_sha256)&&t.artifact_id===m.source_artifact_id&&t.artifact_sha256===m.source_artifact_sha256&&/^\d+$/.test(t.workflow_run_id)&&timestamp(t.collection_completed_at),'invalid_receipt_scope');
 req(keys(r.sources.map(s=>s.key),KEYS)&&keys(t.documents.map(s=>s.key),[...KEYS,...KEYS.map(k=>k+'_landing')]),'source_membership');
 req(t.documents.reduce((n,d)=>n+d.response_bytes,0)===t.total_response_bytes,'receipt_byte_mismatch');
 for(const d of t.documents){official(d.source_url);req(d.final_url===d.source_url&&d.http_status===200&&integer(d.response_bytes)&&hash(d.response_sha256)&&timestamp(d.collected_at)&&Date.parse(d.collected_at)<=Date.parse(t.collection_completed_at),'invalid_response_receipt');}
 for(const s of r.sources){
  const d=t.documents.find(d=>d.key===s.key),l=t.documents.find(d=>d.key===s.landing_key);
  req(d.source_url===s.url&&integer(d.pdf_pages)&&s.document_identity&&s.document_type&&strictDate(s.document_date)===s.document_date&&s.publication_date===null&&strictDate(s.landing_page_date)===s.landing_page_date&&l&&s.document_date<=d.collected_at.slice(0,10),'invalid_document_descriptor');
 }
 const a=r.import_record,b=r.existing_alias;
 req(a.stable_id===ID&&a.issuer_name==='Droneacharya Aerial Innovations Limited'&&a.discovery_bse_scrip_code==='543713'&&a.issue_type==='IPO'&&a.pricing_method==='book built'&&a.board.value==='SME'&&a.board.source_key==='drone_prospectus'&&keys(Object.keys(a.fields),FIELDS),'invalid_new_identity');
 req(b.stable_id===ALIAS_ID&&b.discovery_bse_scrip_code==='543663'&&b.nse_symbol==='FIVESTAR'&&b.discovery_issuer_name==='Five-Star Business Finance Ltd.'&&b.recovery_issuer_name==='FiveStar Business Finance Limited'&&b.identity_source_key==='fivestar_prospectus'&&b.identity_pdf_page===1&&b.decision==='reviewed_existing_alias_and_bounded_term_repair'&&keys(Object.keys(b.fields),REPAIRS),'invalid_alias_approval');
 const old=b.baseline_record;
 req(sha256(JSON.stringify(old))===t.baseline_record_sha256&&old.id===ALIAS_ID&&old.issuer_name===b.recovery_issuer_name&&old.nse_symbol==='FIVESTAR'&&old.listing_date.value==='2022-11-21'&&old.issue_price.value===474&&old.minimum_bid_quantity.value===31,'invalid_alias_baseline');
 for(const k of REPAIRS.filter(k=>k!=='issue_size_inr'))req(old[k]?.value==null&&old.terms?.[k]==null,'repair_must_fill_missing');
 req(same(b.conflict.previous,old.issue_size_inr)&&old.issue_size_inr.value===19600050000&&old.issue_size_inr.status==='verified'&&b.conflict.status==='unresolved'&&b.conflict.field==='issue_size_inr'&&b.conflict.preferred_candidate==='fivestar_prospectus'&&b.conflict.note.length>100,'invalid_conflict_baseline');
 const verifyFact=(name,f,allowed)=>{
  const d=t.documents.find(d=>d.key===f.source_key);
  req(allowed.includes(f.source_key)&&integer(f.pdf_page)&&f.pdf_page<=d?.pdf_pages&&typeof f.source_value==='string'&&f.source_value.length>2&&typeof f.evidence_locator==='string'&&f.evidence_locator.length>12&&f.reporting_period==='2022 IPO','invalid_fact_evidence:'+name);
  if(name.endsWith('_date'))req(strictDate(f.value)===f.value&&f.source_unit==='calendar date','invalid_date_fact');
  else if(name==='price_band')req(integer(f.value?.min)&&integer(f.value?.max)&&f.value.min<f.value.max&&f.source_unit==='INR per share','invalid_bookbuilt_band');
  else if(name==='board')req(f.value==='SME'&&f.source_unit==='exchange segment','invalid_board_fact');
  else if(name==='issue_size_inr')req(integer(f.value)&&['INR lakh','INR million'].includes(f.source_unit)&&f.normalization_multiplier===(f.source_unit==='INR lakh'?100000:1000000)&&Math.round(Number(f.reported_amount)*f.normalization_multiplier)===f.value,'invalid_amount_normalization');
  else req(integer(f.value)&&f.source_unit===(name==='issue_price'?'INR per share':'equity shares'),'invalid_quantity_fact');
 };
 verifyFact('board',a.board,['drone_prospectus']);
 for(const [n,f]of Object.entries(a.fields)){verifyFact(n,f,n==='listing_date'?['drone_listing_corroboration']:['drone_prospectus']);req(!f.status||f.status==='verified','invalid_new_fact_status');}
 for(const [n,f]of Object.entries(b.fields)){verifyFact(n,f,['fivestar_prospectus']);req(n==='issue_size_inr'?f.status==='conflict'&&f.qualification?.includes('Basis of Allotment'):!f.status||f.status==='verified','invalid_repair_status');}
 for(const x of [a,b]){const f=x.fields;req(strictDate(x.anchor_date)===x.anchor_date&&x.anchor_date<f.open_date.value&&f.open_date.value<=f.close_date.value&&f.open_date.investor_scope==='public, excluding anchor','anchor_public_chronology');}
 req(a.fields.close_date.value<a.fields.listing_date.value&&a.fields.listing_date.value.startsWith('2022-')&&b.fields.close_date.value<old.listing_date.value,'invalid_listing_chronology');
 req(a.fields.issue_price.value>=a.fields.price_band.value.min&&a.fields.issue_price.value<=a.fields.price_band.value.max&&old.issue_price.value>=b.fields.price_band.value.min&&old.issue_price.value<=b.fields.price_band.value.max,'price_outside_band');
}
function source(c,f){const s=c.review.sources.find(s=>s.key===f.source_key),d=c.receipt.documents.find(d=>d.key===f.source_key);return{url:s.url,document_type:s.document_type,document_identity:s.document_identity,document_date:s.document_date,publication_date:s.publication_date,reporting_period:s.reporting_period,page:f.pdf_page??null,evidence_locator:f.evidence_locator??null,collected_at:d.collected_at,document_sha256:d.response_sha256};}
const field=(c,f)=>({value:f.value,source_value:f.source_value,source_unit:f.source_unit,reporting_period:f.reporting_period,status:f.status??'verified',page:f.pdf_page,source:source(c,f),corrections:[]});
function document(c,key){const s=source(c,{source_key:key});return{type:s.document_type,identity:s.document_identity,url:s.url,publication_date:s.publication_date,collected_at:s.collected_at,document_sha256:s.document_sha256};}
const metadata=c=>({manifest:MANIFEST,review:REVIEW,receipt:RECEIPT,artifact_id:c.receipt.artifact_id,artifact_sha256:c.receipt.artifact_sha256});
export function expected(c){
 validateContext(c);const a=c.review.import_record,b=c.review.existing_alias;
 const docs=['drone_prospectus','drone_listing_corroboration'].map(k=>document(c,k));
 const times=docs.map(d=>d.collected_at).sort();
 const drone={id:ID,issuer_name:a.issuer_name,board:'SME',sector:null,status:'listed',nse_symbol:null,nse_series:null,nse_source:null,bse_symbol:null,bse_scrip_code:null,isin:null,bse_source:null,terms:{price_band:null,market_lot:null,minimum_bid_quantity:null,open_date:null,close_date:null},documents:docs,first_observed_at:times[0],last_collected_at:times.at(-1),board_evidence:[source(c,a.board)],status_evidence:[source(c,a.fields.listing_date)],bse_2022_final_pair_import:{...metadata(c),discovery_bse_scrip_code:'543713'}};
 for(const n of FIELDS)drone[n]=field(c,a.fields[n]);
 const five=structuredClone(b.baseline_record);
 for(const n of REPAIRS)five[n]=field(c,b.fields[n]);
 const prev=b.conflict.previous;
 five.issue_size_inr.additional_sources=[{...prev.source,page:prev.page??null},...(prev.additional_sources??[])];
 five.issue_size_inr.corrections=[...(prev.corrections??[]),{kind:'unresolved_source_scope_conflict',status:'unresolved',note:b.conflict.note,preferred_candidate:{value:five.issue_size_inr.value,source_value:b.fields.issue_size_inr.source_value,unit:'INR million',qualification:b.fields.issue_size_inr.qualification,source_key:'fivestar_prospectus',pdf_page:1},previous_observation:{value:prev.value,source_value:prev.source_value,unit:'INR million',status:prev.status,source:prev.source}}];
 five.documents.push(document(c,'fivestar_prospectus'));five.last_collected_at=document(c,'fivestar_prospectus').collected_at;
 five.bse_2022_final_pair_repair={...metadata(c),discovery_bse_scrip_code:'543663',preserved_stable_id:ALIAS_ID,filled_missing_fields:REPAIRS.filter(k=>k!=='issue_size_inr'),conflicting_fields:['issue_size_inr']};
 return[drone,five];
}
export function loadRecovery(root=ROOT){return Object.fromEntries(fs.readdirSync(path.join(root,'data/recovery')).filter(y=>/^20\d{2}$/.test(y)&&fs.existsSync(path.join(root,'data/recovery',y,'nse-issue-information.json'))).map(y=>[y,JSON.parse(fs.readFileSync(path.join(root,'data/recovery',y,'nse-issue-information.json')))]));}
export function apply(all,c,now){
 const targets=expected(c);req(timestamp(now)&&Date.parse(now)>=Date.parse(c.receipt.collection_completed_at),'invalid_generation_clock');
 const out=structuredClone(all),existing=Object.entries(out).flatMap(([year,m])=>(m.records??[]).map(record=>({year,record})));
 req(Array.isArray(out['2022']?.records),'missing_2022_recovery');req(new Set(existing.map(x=>x.record.id)).size===existing.length,'duplicate_existing_id');
 let added=0,repaired=0,unchanged=0;
 for(const next of targets){const code=next.id===ID?'543713':'543663';const hits=existing.filter(({record:r})=>r.id===next.id||nameKey(r.issuer_name)===nameKey(next.issuer_name)||String(r.bse_scrip_code??'')===code||(next.id===ALIAS_ID&&r.nse_symbol==='FIVESTAR'));
  if(next.id===ALIAS_ID){req(hits.length===1&&hits[0].year==='2022'&&hits[0].record.id===ALIAS_ID,'alias_identity_collision_or_missing');
   const old=hits[0].record;if(same(old,next)){unchanged++;continue;}req(same(old,c.review.existing_alias.baseline_record),'changed_alias_baseline');
   out['2022'].records[out['2022'].records.indexOf(old)]=next;repaired++;
  }else if(hits.length){req(hits.length===1&&hits[0].year==='2022'&&hits[0].record.id===ID,'identity_collision');req(same(hits[0].record,next),'changed_reviewed_record');unchanged++;
  }else{out['2022'].records.push(next);added++;}
 }
 if(added||repaired)out['2022'].generated_at=now;
 return{recovery:out,stats:{added,repaired,unchanged,existing_aliases:1,conflicts:1,changed:Boolean(added||repaired)}};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){try{req(['--check','--apply'].includes(process.argv[2]),'use_--check_or_--apply');const x=apply(loadRecovery(),context(),new Date().toISOString());if(process.argv[2]==='--apply'&&x.stats.changed)fs.writeFileSync(path.join(ROOT,'data/recovery/2022/nse-issue-information.json'),JSON.stringify(x.recovery['2022'],null,2)+'\n');console.log(JSON.stringify({final_bse_2022_pair:x.stats}));}catch(e){console.error(e.message);process.exitCode=1;}}
