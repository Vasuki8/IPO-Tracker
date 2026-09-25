import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {hash, loadReviewed, loadRecovery, validateReviewedBatch, applyReviewedBatch, reviewedRecord} from './apply-reviewed-nse-ipos.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const manifestPath='data/verified-nse-ipos/2026-09-25-batch8.json';
const batch=loadReviewed(root).find(b=>b.manifest_path===manifestPath);
assert.ok(batch,'pinned batch8 is required');
const {manifest:m,queue:q}=batch,checked=validateReviewedBatch(m,q);
assert.equal(q.candidates.length,14);
assert.equal(checked.length,12);
assert.equal(checked.reduce((n,c)=>n+Object.keys(c.facts).length,0),71);
assert.equal(checked.filter(c=>c.facts.price_band).length,11);
assert.equal(checked.filter(c=>c.facts.market_lot).length,6);
assert.equal(checked.filter(c=>c.facts.minimum_bid_quantity).length,6);

const literal=[
  ['SUMAX','2026-08-25','2026-08-28','2026-09-02',101,95,101,1200,null],
  ['LUMINO','2026-08-27','2026-08-31','2026-09-03',82,78,82,null,182],
  ['ASHUTOSH','2026-08-31','2026-09-02','2026-09-07',92,87,92,1200,null],
  ['PERNIASPOP','2026-08-31','2026-09-02','2026-09-07',575,546,575,null,26],
  ['SHANTIINOR','2026-08-31','2026-09-02','2026-09-07',83,79,83,1600,null],
  ['DEEPA','2026-09-01','2026-09-03','2026-09-08',177,168,177,null,84],
  ['GLASSWALL','2026-09-08','2026-09-10','2026-09-16',182,172,182,null,82],
  ['PRASOLCHEM','2026-09-08','2026-09-10','2026-09-16',676,643,676,null,22],
  ['STEAMHOUSE','2026-09-09','2026-09-11','2026-09-17',81,77,81,null,185],
  ['VINOD','2026-09-09','2026-09-11','2026-09-17',94,null,null,1200,null],
  ['KHERIAAUTO','2026-09-17','2026-09-21','2026-09-24',101,96,101,1200,null],
  ['SPECTRAA','2026-09-17','2026-09-21','2026-09-24',118,112,118,1200,null]
];
for(const [symbol,open,close,listing,price,min,max,lot,bid] of literal){
  const c=checked.find(c=>c.candidate.nse_symbol===symbol);assert.ok(c,symbol);
  assert.equal(c.facts.open_date.value,open);assert.equal(c.facts.close_date.value,close);
  assert.equal(c.facts.listing_date.value,listing);assert.equal(c.facts.issue_price.value,price);
  assert.deepEqual(c.facts.price_band?.value??null,min===null?null:{min,max});
  assert.equal(c.facts.market_lot?.value??null,lot);assert.equal(c.facts.minimum_bid_quantity?.value??null,bid);
}
const expected=checked.map((c,i)=>reviewedRecord(m.entries[i],c,m,manifestPath));
for(const record of expected){
  assert.equal(record.issue_size_inr?.value??null,null);
  assert.equal(record.minimum_application_amount_inr?.value??null,null);
  assert.equal(record.status,'listed');assert.ok(record.status_evidence.length);
}
const review=JSON.parse(fs.readFileSync(path.join(root,'data/discovery/nse-universe-batch8-review-2026-09-25.json')));
assert.equal(review.held.length,0);assert.deepEqual(review.parser_changes,[]);
assert.deepEqual(review.excluded.map(e=>e.candidate.nse_symbol),['DOLLEX','13DCCL28']);
const migration=review.excluded[0],debt=review.excluded[1];
assert.equal(migration.decision,'excluded_migration_not_new_ipo');
assert.equal(migration.independent_official_evidence.isin,migration.detail.metaInfo.isin);
assert.equal(migration.independent_official_evidence.effective_date,'2026-09-11');
assert.equal(migration.original_offer_period.open,'2022-12-15');
assert.equal(debt.decision,'excluded_debt_security_not_initial_equity_ipo');
assert.equal(debt.independent_official_evidence.isin,'INE04Q907231');
assert.equal(debt.independent_official_evidence.isin,debt.detail.metaInfo.isin);
assert.equal(debt.independent_official_evidence.coupon_percent,13);
assert.equal(debt.detail.metaInfo.isDebtSec,true);
assert.equal(debt.additional_endpoint.projection.metaInfo.isin,'INE04Q901010');
assert.equal(debt.additional_endpoint.projection.metaInfo.isDebtSec,true,'do not silently clear mixed endpoint flags');
assert.equal(debt.additional_endpoint.disposition,'retained_mixed_metadata_not_equity_approval');
assert.equal(hash(JSON.stringify(debt.additional_endpoint.projection)),debt.additional_endpoint.source.projection_sha256);
for(const entry of review.excluded){
  assert.equal(entry.auto_import_allowed,false);assert.equal(entry.independent_official_evidence.http_status,200);
  assert.match(entry.independent_official_evidence.document_sha256,/^[a-f0-9]{64}$/);
}

const item=(e,t)=>e.detail.issueInfo.dataList.find(i=>String(i.title).trim().toLowerCase()===t);
const rehash=e=>{e.detail_source.projection_sha256=hash(JSON.stringify(e.detail));e.past_source.projection_sha256=hash(JSON.stringify(e.past_row));};
let rejected=0;
function bad(symbol,mutate){
  const copy=structuredClone(m),e=copy.entries.find(e=>e.candidate.nse_symbol===symbol);
  mutate(e);rehash(e);assert.throws(()=>validateReviewedBatch(copy,q));rejected++;
}
bad('VINOD',e=>{item(e,'issue type').value='Book Building';});
bad('VINOD',e=>{item(e,'price range').value='Rs. 95 per equity share';});
bad('VINOD',e=>{e.past_row.issuePrice='95';});
bad('VINOD',e=>{item(e,'price range').value='94 per equity share';});
bad('VINOD',e=>{item(e,'price range').value='Rs. 94 per equity share or revised later';});
bad('VINOD',e=>{e.detail.issueInfo.dataList.push({...item(e,'price range')});});
bad('VINOD',e=>{item(e,'issue period').value='09-Sep-2026 to 31-Sep-2026';});
bad('VINOD',e=>{item(e,'issue period').value='09-Sep-2026 to 11-Sep-2026 (The Issue may be extended)';});
bad('VINOD',e=>{item(e,'issue size').value='Further Public Offer of Equity Shares';});
bad('SUMAX',e=>{e.detail.metaInfo.isDebtSec=true;});
bad('SUMAX',e=>{e.detail.metaInfo.isin=null;});
bad('SUMAX',e=>{e.detail.companyName='Different Limited';});
bad('SUMAX',e=>{e.detail.metaInfo.segment='EQUITY';});
bad('SUMAX',e=>{e.detail_source.http_status=403;});
bad('SUMAX',e=>{e.detail_source.collected_at='2026-01-01T00:00:00Z';});
bad('SUMAX',e=>{e.past_row.ipoEndDate='27-AUG-2026';});
bad('SUMAX',e=>{e.detail.issueInfo.dataList.push({title:'Market Lot',value:'2400 Equity Shares'});});
bad('LUMINO',e=>{item(e,'minimum order quantity').value='183 Equity Shares';});
bad('SPECTRAA',e=>{e.past_row.issuePrice='119';});
for(const excluded of review.excluded){
  assert.throws(()=>validateReviewedBatch({...m,entries:[{...structuredClone(excluded),decision:'verified_initial_equity_ipo'}]},q));rejected++;
}

// Reconstruct prior inputs, so the tests work on both sides of publication.
const raw=loadRecovery(root),original=JSON.stringify(raw);
const publicBytes=fs.readFileSync(path.join(root,'data/ipos.json')),pub=JSON.parse(publicBytes);
const before=structuredClone(raw),ids=new Set(expected.map(r=>r.id));
for(const y of Object.values(before))y.records=y.records.filter(r=>r.nse_verified_ipo_batch?.manifest!==manifestPath);
const prior={...pub,records:pub.records.filter(r=>!ids.has(r.id))},saved=JSON.stringify(before);
const plan=applyReviewedBatch(before,prior,m,q,manifestPath);
assert.deepEqual(plan.stats,{added:12,already_present:0});assert.equal(JSON.stringify(before),saved);
for(const [year,data] of Object.entries(before)){
  for(const record of data.records)assert.deepEqual(plan.recovery[year].records.find(r=>r.id===record.id),record);
}
const rerun=applyReviewedBatch(plan.recovery,prior,m,q,manifestPath);
assert.deepEqual(rerun.stats,{added:0,already_present:12});assert.deepEqual(rerun.recovery,plan.recovery);
const present={...prior,records:[...prior.records,...expected]};
assert.deepEqual(applyReviewedBatch(plan.recovery,present,m,q,manifestPath).stats,{added:0,already_present:12});
const first=expected[0];
for(const duplicate of [
  {id:'prior',issuer_name:first.issuer_name},
  {id:'prior',issuer_name:'Other Limited',nse_symbol:first.nse_symbol},
  {id:'prior',issuer_name:'Other Limited',isin:first.isin},
  {id:'prior',issuer_name:'Other Limited',documents:[{url:first.nse_source.url}]}
]){
  const collision=structuredClone(before);collision['2021'].records.push(duplicate);
  const saved=JSON.stringify(collision);assert.throws(()=>applyReviewedBatch(collision,prior,m,q,manifestPath));
  assert.equal(JSON.stringify(collision),saved);
}
const corrupted=structuredClone(plan.recovery);
corrupted['2026'].records.find(r=>r.id===first.id).issue_price.value=1;
assert.throws(()=>applyReviewedBatch(corrupted,present,m,q,manifestPath));
assert.equal(JSON.stringify(loadRecovery(root)),original);
assert.deepEqual(fs.readFileSync(path.join(root,'data/ipos.json')),publicBytes);
console.log(JSON.stringify({reviewed_nse_batch8_tests:{issuers:12,facts:71,rejected_mutations:rejected,cross_year_collisions:4,migration_exclusions:1,debt_exclusions:1,holds:0,fixed_price_null_band:true,before_and_after_publication:true,preservation:true,idempotent:true,read_only:true}}));
