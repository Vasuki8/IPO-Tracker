import assert from 'node:assert/strict';
import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
import {apply,context,expected,loadRecovery,validate,FIELDS,REVIEW,RECEIPT,MANIFEST,QUEUE,TARGET,jsonBytes} from './apply-reviewed-bse-2023-four.mjs';
import {expectedPublic,verifyFour2023Publication} from './verify-bse-2023-four.mjs';
import {sha256} from './verify-bse-listing-candidates.mjs';
const ctx=context(),targets=expected(ctx),before=loadRecovery(),now='2026-09-28T05:00:00.000Z';
for(const m of Object.values(before))m.records=m.records.filter(r=>!targets.some(t=>t.id===r.id));
const saved=structuredClone(before),x=apply(before,ctx,now),rerun=apply(x.recovery,ctx,now);
assert.deepEqual(before,saved);assert.deepEqual(x.stats,{records:4,added:4,skipped:0,changed:true});
assert.deepEqual(rerun.stats,{records:4,added:0,skipped:4,changed:false});assert.deepEqual(x.recovery,rerun.recovery);
for(const [year,m] of Object.entries(before))for(const r of m.records)assert.deepEqual(x.recovery[year].records.find(n=>n.id===r.id),r,'unrelated retained record changed');
const values=[[[61,65],65,663000000,1,230,'2022-12-30','2023-01-04','2023-01-12'],[[133,140],140,1549800000,1,100,'2023-03-13','2023-03-15','2023-03-23'],[[33,35],35,660000000,1,428,'2023-03-20','2023-03-23','2023-04-03'],[[151,166],166,1530520000,1,90,'2023-08-18','2023-08-22','2023-08-29']];
for(let i=0;i<4;i++){
 const r=targets[i];assert.deepEqual(FIELDS.map(f=>f==='price_band'?[r[f].value.min,r[f].value.max]:r[f].value),values[i]);
 assert.equal(r.status,'listed');assert.equal(r.board,null);assert.deepEqual(r.board_evidence,[]);
 for(const key of ['isin','bse_scrip_code','bse_symbol','nse_symbol','sector'])assert.equal(r[key],null);
 assert.ok(r.first_observed_at<r.last_collected_at);assert.equal(r.documents.length,3);
 assert.notStrictEqual(r.market_lot,r.minimum_bid_quantity);assert.notEqual(r.market_lot.page,r.minimum_bid_quantity.page);
 assert.equal(r.issue_size_inr.status,'provisional');assert.ok(r.issue_size_inr.qualification.length>30);
 for(const f of FIELDS){assert.match(r[f].source.document_sha256,/^[a-f0-9]{64}$/);assert.equal(r[f].status,f==='issue_size_inr'?'provisional':'verified');}
 assert.equal(r.open_date.source.publication_date,null);assert.ok(ctx.review.actions[i].anchor_date<r.open_date.value);
}
assert.equal(targets[3].open_date.source.document_date,'2023-08-23');
assert.equal(ctx.review.sources.find(s=>s.key==='pyramid_landing').publication_date,'2024-08-23');
assert.equal(ctx.receipt.documents.length,12);assert.equal(ctx.receipt.total_response_bytes,37415464);
let rejected=0;
for(const t of targets)for(const mode of ['id','name','code']){
 const bad=structuredClone(before),r={id:'collision',issuer_name:'Other'};
 if(mode==='id')r.id=t.id;if(mode==='name')r.issuer_name=t.issuer_name.toUpperCase().replace(/LIMITED/,'LTD.');if(mode==='code')r.bse_scrip_code=t.bse_2023_four_import.discovery_bse_scrip_code;
 bad['2022'].records.push(r);assert.throws(()=>apply(bad,ctx,now),/identity_collision/);rejected++;
}
// Rebind deliberately malformed fixtures to test semantic guards, not only hashes.
function rebind(c){c.receipt.review_sha256=sha256(jsonBytes(c.review));c.manifest.review_sha256=c.receipt.review_sha256;c.manifest.receipt_sha256=sha256(jsonBytes(c.receipt));}
for(const mutate of [
 c=>c.review.actions.pop(),c=>c.review.auto_import_allowed=true,c=>c.manifest.target_year=2024,
 c=>c.review.actions[0].terms.issue_size_inr.status='verified',
 c=>c.review.actions[0].terms.issue_size_inr.scope='fresh_issue',
 c=>c.review.actions[0].terms.issue_size_inr.normalization_multiplier=10000000,
 c=>c.review.actions[0].terms.issue_size_inr.qualification='',
 c=>c.review.actions[0].terms.issue_size_inr.reported_amount='6630bad',
 c=>c.review.actions[0].terms.issue_size_inr.source_unit='INR crore',
 c=>c.review.actions[0].terms.market_lot.value=230,
 c=>c.review.actions[0].terms.minimum_bid_quantity.investor_category='anchor',
 c=>c.review.actions[0].terms.minimum_bid_quantity.source_value='231',
 c=>c.review.actions[0].terms.minimum_bid_quantity.page=9999,
 c=>c.review.actions[0].terms.minimum_bid_quantity.page=null,
 c=>c.review.actions[0].terms.issue_price.source_key='global_prospectus',
 c=>c.review.actions[0].terms.open_date.value=c.review.actions[0].anchor_date,
 c=>c.review.actions[0].terms.close_date.value='2023-02-30',
 c=>c.review.actions[0].terms.listing_date.value='2024-01-12',
 c=>c.review.actions[0].terms.price_band.value.min=66,
 c=>c.review.actions[0].terms.issue_price.value=-1,
 c=>c.review.actions[0].terms.minimum_application_amount_inr={value:14950},
 c=>c.review.actions[0].board='Mainboard',
 c=>c.review.actions[0].identity_sources[0]='global_landing',
 c=>c.review.sources.find(s=>s.key==='sah_prospectus').publication_date='2023-01-12',
 c=>c.review.sources[0].document_date='2023-02-30',
 c=>c.review.sources[0].url='https://evil.example/source',
 c=>c.receipt.documents[0].response_sha256='invalid',
 c=>c.receipt.documents[0].response_bytes++,
 c=>c.receipt.documents[0].http_status=404,
 c=>c.receipt.documents[0].collected_at='2020-01-01T00:00:00Z',
 c=>c.receipt.documents[0].collected_at='2026-09-28T06:00:00Z',
 c=>c.receipt.documents[0].artifact_id=1,
 c=>c.receipt.artifacts[0].sha256='bad',
 c=>c.queue.rows.pop(),
 c=>c.review.reconciliation.matched_records.push({id:'existing'})]){
 const bad=structuredClone(ctx);mutate(bad);rebind(bad);assert.throws(()=>expected(bad));rejected++;
}
const unbound=structuredClone(ctx);unbound.review.actions[0].terms.issue_price.value++;assert.throws(()=>validate(unbound),/content_binding/);rejected++;
for(const mutate of [r=>r.issue_price.value++,r=>r.issue_size_inr.status='verified',r=>r.documents[0].document_sha256='0'.repeat(64),r=>r.first_observed_at=r.last_collected_at,r=>r.status_evidence[0].page=77,r=>r.bse_2023_four_import.action_key='global',r=>r.board='Mainboard']){
 const bad=structuredClone(x.recovery);mutate(bad['2023'].records.find(r=>r.id===targets[0].id));assert.throws(()=>apply(bad,ctx,now),/changed_import_record/);rejected++;
}
assert.throws(()=>apply(before,ctx,'2020-01-01T00:00:00Z'));rejected++;
const protectedPaths=[TARGET,'data/ipos.json',REVIEW,RECEIPT,MANIFEST,QUEUE,'data/discovery/bse-retained-reconciliation-2026-09-28.json'];
const protectedBytes=protectedPaths.map(p=>fs.readFileSync(p));
const check=spawnSync(process.execPath,['scripts/apply-reviewed-bse-2023-four.mjs','--check'],{encoding:'utf8'});assert.equal(check.status,0,check.stderr);
protectedPaths.forEach((p,i)=>assert.deepEqual(fs.readFileSync(p),protectedBytes[i]));
const publicData=JSON.parse(fs.readFileSync('data/ipos.json')),expectedRows=targets.map(expectedPublic),present=publicData.records.filter(r=>targets.some(t=>t.id===r.id));
if(present.length){assert.equal(present.length,4);for(const t of expectedRows)assert.deepEqual(present.find(r=>r.id===t.id),t,'real builder projection');}
const fixture={schema_version:'1.2.0',generated_at:now,records:expectedRows};let calls=0;
const result=await verifyFour2023Publication({fetchImpl:async url=>{calls++;assert.equal(url,'https://vasuki8.github.io/IPO-Tracker/data/ipos.json');return new Response(JSON.stringify(fixture));}});
assert.equal(calls,1);assert.equal(result.ok,true);assert.equal(result.response_sha256,sha256(Buffer.from(JSON.stringify(fixture))));
for(const mutate of [s=>s.records.pop(),s=>s.records[0].issue_size_inr.status='verified',s=>s.records[0].market_lot.value=230,s=>s.records[0].open_date.value='2022-12-29',s=>s.records[0].listing_date.evidence[0].url='https://evil.example',s=>s.records.push(s.records[0])]){
 const bad=structuredClone(fixture);mutate(bad);await assert.rejects(verifyFour2023Publication({fetchImpl:async()=>new Response(JSON.stringify(bad))}));rejected++;
}
console.log(JSON.stringify({four_2023_tests:{records:4,verified_fields:28,provisional_amounts:4,rejected_mutations:rejected,unrelated_records_unchanged:true,raw_units_and_pages:true,public_anchor_dates_distinct:true,read_only:true,rerun_safe:true,real_builder_checked:present.length===4,live_contract:true}}));
