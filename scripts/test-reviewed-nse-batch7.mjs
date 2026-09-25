import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {hash,loadReviewed,loadRecovery,validateReviewedBatch,applyReviewedBatch,reviewedRecord} from './apply-reviewed-nse-ipos.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const manifestPath='data/verified-nse-ipos/2026-09-25-batch7.json';
const batch=loadReviewed(root).find(b=>b.manifest_path===manifestPath);assert.ok(batch,'pinned batch7 required');
const {manifest:m,queue:q}=batch,checked=validateReviewedBatch(m,q);
assert.equal(checked.length,13);assert.equal(checked.reduce((n,c)=>n+Object.keys(c.facts).length,0),78);
assert.equal(checked.filter(c=>c.facts.market_lot).length,4);assert.equal(checked.filter(c=>c.facts.minimum_bid_quantity).length,9);
const fascinate=checked.find(c=>c.candidate.nse_symbol==='FASCINATE');
assert.equal(fascinate.facts.open_date.value,'2026-08-11');assert.equal(fascinate.facts.close_date.value,'2026-08-19');
assert.equal(fascinate.facts.issue_price.value,151);assert.deepEqual(fascinate.facts.price_band.value,{min:142,max:151});
assert.equal(fascinate.facts.market_lot.value,800);assert.equal(fascinate.facts.market_lot.source_value,'800 Equity Shares and in multiples of lot size thereof');
assert.equal(fascinate.facts.minimum_bid_quantity,undefined,'a lot is not a minimum bid');
const symbiotec=checked.find(c=>c.candidate.nse_symbol==='SYMBIOTEC');assert.equal(symbiotec.facts.minimum_bid_quantity.value,15);assert.equal(symbiotec.facts.market_lot,undefined);
const item=(e,t)=>e.detail.issueInfo.dataList.find(i=>i.title.trim().toLowerCase()===t);
assert.equal(item(m.entries.find(e=>e.candidate.nse_symbol==='FASCINATE'),'issue period').value,'11-Aug-2026 to 19-Aug-2026 (The Issue is further extended to 19-Aug-2026)');
const expected=checked.map((c,i)=>reviewedRecord(m.entries[i],c,m,manifestPath));
for(const r of expected){assert.equal(r.issue_size_inr?.value??null,null);assert.equal(r.minimum_application_amount_inr?.value??null,null);assert.equal(r.status,'listed');assert.ok(r.status_evidence.length);}
const review=JSON.parse(fs.readFileSync(path.join(root,'data/discovery/nse-universe-batch7-review-2026-09-25.json')));
assert.equal(review.held.length,0);assert.deepEqual(review.excluded.map(e=>e.candidate.nse_symbol),['1150VIES30','12AIL28']);
for(const e of review.excluded){assert.equal(e.decision,'excluded_debt_security_not_initial_equity_ipo');assert.equal(e.auto_import_allowed,false);assert.equal(e.detail.metaInfo.isDebtSec,true);assert.equal(e.detail.metaInfo.isin,e.independent_official_evidence.isin);assert.notEqual(e.detail.metaInfo.isin,e.distinct_equity_identity.isin);assert.equal(e.independent_official_evidence.http_status,200);assert.match(e.independent_official_evidence.document_sha256,/^[a-f0-9]{64}$/);assert.equal(e.distinct_equity_identity.security_class,'Equity');}
const rehash=e=>{e.detail_source.projection_sha256=hash(JSON.stringify(e.detail));e.past_source.projection_sha256=hash(JSON.stringify(e.past_row));};
let rejected=0;
function bad(symbol,mutate){const copy=structuredClone(m),e=copy.entries.find(e=>e.candidate.nse_symbol===symbol);mutate(e);rehash(e);assert.throws(()=>validateReviewedBatch(copy,q));rejected++;}
for(const value of [
 '11-Aug-2026 to 19-Aug-2026 (The Issue is further extended to 20-Aug-2026)',
 '11-Aug-2026 to 19-Aug-2026 (The Issue is further extended to 32-Aug-2026)',
 '11-Aug-2026 to 19-Aug-2026 (The Issue is further extended to 19-Aug-2026) or 20-Aug-2026',
 '11-Aug-2026 to 19-Aug-2026 (The Issue may be extended to 19-Aug-2026)',
 '11-Aug-2026 to 32-Aug-2026 (The Issue is further extended to 32-Aug-2026)',
 '20-Aug-2026 to 19-Aug-2026 (The Issue is further extended to 19-Aug-2026)'
])bad('FASCINATE',e=>{item(e,'issue period').value=value;});
bad('FASCINATE',e=>{e.past_row.ipoEndDate='13-AUG-2026';});
bad('FASCINATE',e=>{e.past_row.issuePrice='156';});
bad('FASCINATE',e=>{e.detail.issueInfo.dataList.push({...item(e,'issue period')});});
bad('FASCINATE',e=>{e.detail.issueInfo.dataList.push({title:'Revised/Extended Issue Period',value:'11-Aug-2026 to 19-Aug-2026'});});
bad('FASCINATE',e=>{e.detail.issueInfo.dataList.push({title:'Market Lot',value:'1600 Equity Shares'});});
bad('FASCINATE',e=>{item(e,'issue size').value='Further Public Offer of Equity Shares';});
bad('SKYTECH',e=>{e.detail.metaInfo.isDebtSec=true;});
bad('SKYTECH',e=>{e.detail.metaInfo.isin=null;});
bad('SKYTECH',e=>{e.detail.companyName='Different Limited';});
bad('SKYTECH',e=>{e.detail_source.collected_at='2026-01-01T00:00:00Z';});
bad('SKYTECH',e=>{e.detail_source.http_status=403;});
bad('SYMBIOTEC',e=>{item(e,'minimum order quantity').value='16 Equity Shares';});
for(const e of review.excluded){assert.throws(()=>validateReviewedBatch({...m,entries:[{...structuredClone(e),decision:'verified_initial_equity_ipo'}]},q));rejected++;}
// The extension syntax is reusable and does not depend on an issuer allowlist.
const other=structuredClone(m),sky=other.entries.find(e=>e.candidate.nse_symbol==='SKYTECH');item(sky,'issue period').value+=' (The Issue is further extended to 18-Aug-2026)';rehash(sky);assert.equal(validateReviewedBatch(other,q).find(c=>c.candidate.nse_symbol==='SKYTECH').facts.close_date.value,'2026-08-18');
// Reconstruct cloned pre-release inputs so tests remain valid after publication.
const raw=loadRecovery(root),original=JSON.stringify(raw),publicBytes=fs.readFileSync(path.join(root,'data/ipos.json')),pub=JSON.parse(publicBytes);
const before=structuredClone(raw),ids=new Set(expected.map(r=>r.id));for(const y of Object.values(before))y.records=y.records.filter(r=>r.nse_verified_ipo_batch?.manifest!==manifestPath);
const saved=JSON.stringify(before),prior={...pub,records:pub.records.filter(r=>!ids.has(r.id))};
const plan=applyReviewedBatch(before,prior,m,q,manifestPath);assert.deepEqual(plan.stats,{added:13,already_present:0});assert.equal(JSON.stringify(before),saved);
for(const [year,data]of Object.entries(before))for(const r of data.records)assert.deepEqual(plan.recovery[year].records.find(n=>n.id===r.id),r);
const rerun=applyReviewedBatch(plan.recovery,prior,m,q,manifestPath);assert.deepEqual(rerun.stats,{added:0,already_present:13});assert.deepEqual(rerun.recovery,plan.recovery);
const present={...prior,records:[...prior.records,...expected]};assert.deepEqual(applyReviewedBatch(plan.recovery,present,m,q,manifestPath).stats,{added:0,already_present:13});
for(const duplicate of [{id:'prior',issuer_name:expected[0].issuer_name},{id:'prior',issuer_name:'Other Limited',nse_symbol:expected[0].nse_symbol},{id:'prior',issuer_name:'Other Limited',isin:expected[0].isin},{id:'prior',issuer_name:'Other Limited',documents:[{url:expected[0].nse_source.url}]}]){const collision=structuredClone(before);collision['2021'].records.push(duplicate);const copy=JSON.stringify(collision);assert.throws(()=>applyReviewedBatch(collision,prior,m,q,manifestPath));assert.equal(JSON.stringify(collision),copy);}
const corrupted=structuredClone(plan.recovery);corrupted['2026'].records.find(r=>r.id===expected[0].id).issue_price.value=1;assert.throws(()=>applyReviewedBatch(corrupted,present,m,q,manifestPath));
assert.equal(JSON.stringify(loadRecovery(root)),original);assert.deepEqual(fs.readFileSync(path.join(root,'data/ipos.json')),publicBytes);
console.log(JSON.stringify({reviewed_nse_batch7_tests:{issuers:13,facts:78,rejected_mutations:rejected,cross_year_collisions:4,debt_exclusions:2,holds:0,extended_date_agreement:true,before_and_after_publication:true,preservation:true,idempotent:true,read_only:true}}));
