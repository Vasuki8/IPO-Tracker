import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { hash, loadReviewed, loadRecovery, validateReviewedBatch, applyReviewedBatch, reviewedRecord } from './apply-reviewed-nse-ipos.mjs';
import { parsePriceBandFromIpoDetail, parseMinimumBidFromIpoDetail, parseMarketLotFromIpoDetail } from './extract-nse-ipo-detail-fields.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const manifestPath='data/verified-nse-ipos/2026-09-25-batch6.json';
const batch=loadReviewed(root).find(b=>b.manifest_path===manifestPath);
assert.ok(batch,'pinned batch6 is required');
const {manifest:m,queue:q}=batch,checked=validateReviewedBatch(m,q);
assert.equal(checked.length,12);
assert.equal(checked.reduce((n,c)=>n+Object.keys(c.facts).length,0),72);
assert.equal(checked.filter(c=>c.facts.market_lot).length,4);
assert.equal(checked.filter(c=>c.facts.minimum_bid_quantity).length,8);
const ardee=checked.find(c=>c.candidate.nse_symbol==='ARDEE');
assert.equal(ardee.facts.issue_price.value,53);
assert.deepEqual(ardee.facts.price_band.value,{min:50,max:53});
assert.equal(ardee.facts.price_band.source_value,'Rs. 50/- per equity share to Rs. 53/- equity share');
assert.equal(ardee.facts.minimum_bid_quantity.value,281);
assert.equal(ardee.facts.minimum_bid_quantity.source_value,'Minimum 281 Equity Shares');
assert.equal(ardee.facts.market_lot,undefined,'minimum is not a market lot');
assert.equal(checked.find(c=>c.candidate.nse_symbol==='ANAWIL').facts.market_lot.value,400);
assert.equal(checked.find(c=>c.candidate.nse_symbol==='ANAWIL').facts.minimum_bid_quantity,undefined);
assert.equal(checked.find(c=>c.candidate.nse_symbol==='SHIPROCKET').facts.minimum_bid_quantity.value,154);
const expected=checked.map((c,i)=>reviewedRecord(m.entries[i],c,m,manifestPath));
for(const r of expected){
  assert.equal(r.issue_size_inr?.value??null,null);
  assert.equal(r.minimum_application_amount_inr?.value??null,null);
  assert.equal(r.status,'listed');assert.ok(r.status_evidence.length);
}
const review=JSON.parse(fs.readFileSync(path.join(root,'data/discovery/nse-universe-batch6-review-2026-09-25.json')));
assert.equal(review.excluded.length,2);assert.equal(review.held.length,1);
assert.deepEqual(review.excluded.map(e=>e.candidate.nse_symbol),['ANNAPURNA','SWARAJ']);
assert.equal(review.held[0].candidate.nse_symbol,'LEAP');
assert.equal(review.held[0].detail.metaInfo.isin,null);
for(const e of review.excluded){assert.equal(e.decision,'excluded_migration_not_new_ipo');assert.equal(e.independent_official_evidence.http_status,200);assert.equal(e.independent_official_evidence.reviewed_pages.includes(2),true);}
const item=(e,t)=>e.detail.issueInfo.dataList.find(i=>i.title.trim().toLowerCase()===t);
let rejected=0;
function bad(symbol,mutate){const copy=structuredClone(m),e=copy.entries.find(e=>e.candidate.nse_symbol===symbol);mutate(e);e.detail_source.projection_sha256=hash(JSON.stringify(e.detail));e.past_source.projection_sha256=hash(JSON.stringify(e.past_row));assert.throws(()=>validateReviewedBatch(copy,q));rejected++;}
bad('ARDEE',e=>{item(e,'price range').value='Rs. 50/- per equity share to USD 53/- equity share';});
bad('ARDEE',e=>{item(e,'price range').value='Rs. 53/- per equity share to Rs. 50/- equity share';});
bad('ARDEE',e=>{item(e,'price range').value+=' or Rs. 55 per share';});
bad('ARDEE',e=>{e.past_row.issuePrice='54';});
bad('ARDEE',e=>{item(e,'minimum order quantity').value='Minimum 282 Equity Shares';});
bad('ARDEE',e=>{item(e,'minimum order quantity').value='Maximum 281 Equity Shares';item(e,'bid lot').value='Maximum 281 Equity Shares';});
bad('ARDEE',e=>{item(e,'issue size').value='Further Public Offer of Equity Shares';});
bad('ARDEE',e=>{e.detail.metaInfo.isDebtSec=true;});
bad('ARDEE',e=>{e.detail.metaInfo.isin=null;});
bad('ARDEE',e=>{e.detail.companyName='Other Limited';});
bad('ANAWIL',e=>{item(e,'issue period').value='03-Aug-2026 to 32-Aug-2026';});
bad('ANAWIL',e=>{e.past_row.ipoEndDate='06-AUG-2026';});
bad('ANAWIL',e=>{e.detail.issueInfo.dataList.push({title:'Market Lot',value:'200 Equity Shares'});});
bad('SHIPROCKET',e=>{e.detail_source.collected_at='2026-01-01T00:00:00Z';});
bad('SHIPROCKET',e=>{e.detail_source.http_status=403;});
for(const e of [...review.excluded,...review.held]){assert.throws(()=>validateReviewedBatch({...m,entries:[{...structuredClone(e),decision:'verified_initial_equity_ipo'}]},q));rejected++;}
// Reconstruct cloned pre-release inputs so the same tests work after publication.
const raw=loadRecovery(root),original=JSON.stringify(raw),publicBytes=fs.readFileSync(path.join(root,'data/ipos.json')),pub=JSON.parse(publicBytes);
const before=structuredClone(raw),ids=new Set(expected.map(r=>r.id));
for(const y of Object.values(before))y.records=y.records.filter(r=>r.nse_verified_ipo_batch?.manifest!==manifestPath);
const beforeBytes=JSON.stringify(before),prior={...pub,records:pub.records.filter(r=>!ids.has(r.id))};
const plan=applyReviewedBatch(before,prior,m,q,manifestPath);
assert.deepEqual(plan.stats,{added:12,already_present:0});assert.equal(JSON.stringify(before),beforeBytes);
for(const [year,data]of Object.entries(before))for(const r of data.records)assert.deepEqual(plan.recovery[year].records.find(n=>n.id===r.id),r);
const rerun=applyReviewedBatch(plan.recovery,prior,m,q,manifestPath);
assert.deepEqual(rerun.stats,{added:0,already_present:12});assert.deepEqual(rerun.recovery,plan.recovery);
const present={...prior,records:[...prior.records,...expected]};
assert.deepEqual(applyReviewedBatch(plan.recovery,present,m,q,manifestPath).stats,{added:0,already_present:12});
for(const duplicate of [
  {id:'prior',issuer_name:expected[0].issuer_name},
  {id:'prior',issuer_name:'Other Limited',nse_symbol:expected[0].nse_symbol},
  {id:'prior',issuer_name:'Other Limited',isin:expected[0].isin},
  {id:'prior',issuer_name:'Other Limited',documents:[{url:expected[0].nse_source.url}]}
]){const collision=structuredClone(before);collision['2021'].records.push(duplicate);const saved=JSON.stringify(collision);assert.throws(()=>applyReviewedBatch(collision,prior,m,q,manifestPath));assert.equal(JSON.stringify(collision),saved);}
const corrupted=structuredClone(plan.recovery);corrupted['2026'].records.find(r=>r.id===expected[0].id).issue_price.value=1;
assert.throws(()=>applyReviewedBatch(corrupted,present,m,q,manifestPath));
assert.equal(JSON.stringify(loadRecovery(root)),original);assert.deepEqual(fs.readFileSync(path.join(root,'data/ipos.json')),publicBytes);
console.log(JSON.stringify({reviewed_nse_batch6_tests:{issuers:12,facts:72,rejected_mutations:rejected,cross_year_collisions:4,exclusions:2,identity_holds:1,before_and_after_publication:true,idempotent:true,read_only:true}}));

// Repeated share units: both explicit INR endpoints are mandatory for this form.
const bandPayload = value => ({issueInfo:{dataList:[{title:'Price Range',value}]}});
for(const value of ['Rs. 50/- per equity share to Rs. 53/- equity share','INR 50 per Equity Share to INR 53 per Equity Share']){
  const parsed=parsePriceBandFromIpoDetail(bandPayload(value));
  assert.deepEqual(parsed.value,{min:50,max:53});assert.equal(parsed.source_value,value);
}
for(const value of ['50 per equity share to Rs. 53 equity share','Rs. 50 per equity share to 53 equity share','Rs. 50 per equity share to USD 53 equity share','Rs. 53 per equity share to Rs. 50 equity share','Rs. 0 per equity share to Rs. 53 equity share','Rs. 50 per equity share to Rs. 53 equity share or Rs. 55']){
  assert.equal(parsePriceBandFromIpoDetail(bandPayload(value)).value,null,value);
}
const minPayload = (a,b=a) => ({issueInfo:{dataList:[{title:'Minimum Order Quantity',value:a},{title:'Bid Lot',value:b}]}});
const prefixedMinimum=parseMinimumBidFromIpoDetail(minPayload('Minimum 281 Equity Shares','Minimum 281 Equity shares and in multiples thereof'));
assert.equal(prefixedMinimum.value,281);assert.equal(prefixedMinimum.source_value,'Minimum 281 Equity Shares');
assert.equal(parseMinimumBidFromIpoDetail(minPayload('Minimum 282 Equity Shares','Minimum 281 Equity Shares')).reason,'official_term_conflict');
for(const value of ['Maximum 281 Equity Shares','Minimum 0 Equity Shares','Minimum 281 Rupees','Minimum 281 Equity Shares or 282','At least 281 Equity Shares'])assert.equal(parseMinimumBidFromIpoDetail(minPayload(value)).value,null,value);
assert.equal(parseMarketLotFromIpoDetail({issueInfo:{dataList:[{title:'Market Lot',value:'Minimum 281 Equity Shares'}]}}).value,null,'minimum qualifier must not become a market lot');
console.log('Repeated per-share band and minimum-qualified bid tests passed.');
