import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { hash, loadReviewed, loadRecovery, validateReviewedBatch, applyReviewedBatch, reviewedRecord } from './apply-reviewed-nse-ipos.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const manifestPath='data/verified-nse-ipos/2026-09-25-batch9.json';
const batch=loadReviewed(root).find(b=>b.manifest_path===manifestPath);
assert.ok(batch,'batch9 required');
const checked=validateReviewedBatch(batch.manifest,batch.queue);
assert.equal(checked.length,2);
assert.equal(checked.reduce((n,c)=>n+Object.keys(c.facts).length,0),12);
const amir=checked.find(c=>c.candidate.nse_symbol==='AMIRCHAND');
const leap=checked.find(c=>c.candidate.nse_symbol==='LEAP');
assert.equal(amir.nse_symbol,'AMIRCHAND');
assert.equal(amir.isin,'INE05TO01019');
assert.equal(leap.nse_symbol,'LEAPIND');
assert.equal(leap.isin,'INE00GO01025');
assert.equal(leap.facts.issue_price.value,159);
assert.deepEqual(leap.facts.price_band.value,{min:151,max:159});
assert.equal(leap.facts.minimum_bid_quantity.value,94);
assert.equal(leap.facts.market_lot,undefined);
assert.equal(reviewedRecord(batch.manifest.entries[1],leap,batch.manifest,manifestPath).nse_symbol,'LEAPIND');

let rejected=0;
function bad(symbol,mutate){
  const m=structuredClone(batch.manifest), e=m.entries.find(e=>e.candidate.nse_symbol===symbol);
  mutate(e); assert.throws(()=>validateReviewedBatch(m,batch.queue)); rejected++;
}
bad('LEAP',e=>{e.identity_fallback.nse_symbol='LEAP';});
bad('LEAP',e=>{e.identity_fallback.isin='INE00GO01026';});
bad('LEAP',e=>{e.detail.metaInfo.symbol='LEAPIND'; e.detail_source.projection_sha256=hash(JSON.stringify(e.detail));});
bad('LEAP',e=>{e.identity_fallback.sources[0].projection.nse_symbol='FAKE'; e.identity_fallback.sources[0].projection_sha256=hash(JSON.stringify(e.identity_fallback.sources[0].projection));});
bad('AMIRCHAND',e=>{e.identity_fallback.sources[1].projection.listing_date='2026-04-03'; e.identity_fallback.sources[1].projection_sha256=hash(JSON.stringify(e.identity_fallback.sources[1].projection));});
bad('AMIRCHAND',e=>{e.identity_fallback.sources[0].url='https://example.com/fake';e.identity_fallback.sources[0].final_url=e.identity_fallback.sources[0].url;});

const raw=loadRecovery(root), pub=JSON.parse(fs.readFileSync(path.join(root,'data/ipos.json')));
const pre=structuredClone(raw);
for(const year of Object.values(pre)) year.records=year.records.filter(r=>!['amir-chand-jagdish-kumar-exports-limited','leap-india-limited'].includes(r.id));
const prior={...pub,records:pub.records.filter(r=>!['amir-chand-jagdish-kumar-exports-limited','leap-india-limited'].includes(r.id))};
const before=JSON.stringify(pre), plan=applyReviewedBatch(pre,prior,batch.manifest,batch.queue,manifestPath);
assert.deepEqual(plan.stats,{added:2,already_present:0});
assert.equal(JSON.stringify(pre),before);
assert.deepEqual(applyReviewedBatch(plan.recovery,prior,batch.manifest,batch.queue,manifestPath).stats,{added:0,already_present:2});

for(const symbol of ['LEAP','LEAPIND']){
  const collision=structuredClone(pre);
  collision['2021'].records.push({id:'collision-'+symbol.toLowerCase(),issuer_name:'Different Limited',nse_symbol:symbol});
  assert.throws(()=>applyReviewedBatch(collision,prior,batch.manifest,batch.queue,manifestPath)); rejected++;
}
const isinCollision=structuredClone(pre);
isinCollision['2022'].records.push({id:'collision-isin',issuer_name:'Other Limited',isin:'INE00GO01025'});
assert.throws(()=>applyReviewedBatch(isinCollision,prior,batch.manifest,batch.queue,manifestPath)); rejected++;

console.log(JSON.stringify({reviewed_nse_batch9_tests:{issuers:2,facts:12,rejected_inputs:rejected,lookup_and_listed_symbol_collisions:true,preservation:true,idempotent:true}}));
