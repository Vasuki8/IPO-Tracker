import assert from 'node:assert/strict';
import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
import {apply,context,expected,loadRecovery,FIELDS,REVIEW,RECEIPT} from './apply-reviewed-bse-2022-maruti-olatech.mjs';
import {expectedPublic,verifyMarutiOlatechPublication} from './verify-bse-2022-maruti-olatech.mjs';
import {sha256} from './verify-bse-listing-candidates.mjs';

const ctx=context(),rows=expected(ctx),current=loadRecovery();
const before=structuredClone(current);
for(const m of Object.values(before))m.records=m.records.filter(r=>!rows.some(t=>t.id===r.id));
const saved=structuredClone(before),now=new Date().toISOString(),first=apply(before,ctx,now);
assert.deepEqual(before,saved,'input recovery must not mutate');
assert.deepEqual(first.stats,{records:2,added:2,skipped:0,changed:true});
const rerun=apply(first.recovery,ctx,now);
assert.deepEqual(rerun.stats,{records:2,added:0,skipped:2,changed:false});
assert.deepEqual(rerun.recovery,first.recovery);
for(const [year,m] of Object.entries(before)){
  if(year!=='2022')assert.deepEqual(first.recovery[year],m);
  for(const r of m.records)assert.deepEqual(first.recovery[year].records.find(x=>x.id===r.id),r);
}
const [m,o]=rows;
for(const [r,facts,pages,firstAt,lastAt] of [
 [m,[55,110000000,2000,2000,'2022-02-03','2022-02-08','2022-02-16'],[1,1,194,207,1,1,100],'2026-09-28T01:25:06.521Z','2026-09-28T01:25:07.534Z'],
 [o,[27,18900000,4000,4000,'2022-08-12','2022-08-19','2022-08-29'],[8,1,193,206,1,1,20],'2026-09-28T01:25:24.174Z','2026-09-28T01:25:24.720Z']]){
  const fields=FIELDS.filter(f=>f!=='price_band');
  assert.deepEqual(fields.map(f=>r[f].value),facts);
  assert.deepEqual(fields.map(f=>r[f].page),pages);
  assert.equal(r.board,'SME');assert.equal(r.status,'listed');
  assert.equal(r.first_observed_at,firstAt);assert.equal(r.last_collected_at,lastAt);
  assert.equal(r.price_band.value,null);assert.equal(r.price_band.status,'missing');
  for(const k of ['isin','bse_scrip_code','nse_symbol','bse_symbol'])assert.equal(r[k],null);
  assert.notStrictEqual(r.market_lot,r.minimum_bid_quantity);
  assert.notEqual(r.market_lot.page,r.minimum_bid_quantity.page);
  assert.equal(r.issue_size_inr.source_unit,'INR lakh');
  for(const f of fields){assert.equal(r[f].status,'verified');assert.equal(typeof r[f].source_value,'string');assert.match(r[f].source.document_sha256,/^[a-f0-9]{64}$/);assert.equal(r[f].source.publication_date,null);}
}
assert.equal(m.issue_size_inr.source_value,'Rs. 1100 lakhs');
assert.equal(o.issue_size_inr.source_value,'Rs. 189.00 Lakhs');
assert.equal(ctx.manifest.review_sha256,sha256(fs.readFileSync(REVIEW)));
assert.equal(ctx.manifest.receipt_sha256,sha256(fs.readFileSync(RECEIPT)));
let rejected=0;
for(const target of rows)for(const kind of ['id','name','code']){
  const all=structuredClone(before),record={id:'collision-'+kind,issuer_name:'Unrelated issuer'};
  if(kind==='id')record.id=target.id;
  if(kind==='name')record.issuer_name=target.issuer_name.toUpperCase();
  if(kind==='code')record.bse_scrip_code=target.bse_2022_maruti_olatech_import.discovery_bse_scrip_code;
  all['2023'].records.push(record);assert.throws(()=>apply(all,ctx,now),/identity_collision/);rejected++;
}
for(const mutate of [
 x=>x.sources.get('maruti_prospectus').projection.issue_price++,
 x=>x.review.actions[0].field_pages.market_lot=9999,
 x=>x.review.actions[0].field_pages.market_lot=null,
 x=>x.review.actions[0].field_observations.issue_size_inr.normalization_multiplier=10000000,
 x=>x.review.actions[0].field_observations.minimum_bid_quantity.investor_category='all investors',
 x=>x.review.actions[0].target.price_band={min:55,max:55},
 x=>x.review.actions[0].target.close_date='2022-02-20',
 x=>x.review.actions[0].field_observations.issue_price.source_value=null]){
 const bad=structuredClone(ctx);mutate(bad);assert.throws(()=>expected(bad));rejected++;
}
for(const mutate of [r=>r.issue_price.value++,r=>r.documents[0].document_sha256='0'.repeat(64),r=>r.board_evidence[0].page=2,r=>r.first_observed_at=r.last_collected_at]){
 const bad=structuredClone(first.recovery);mutate(bad['2022'].records.find(r=>r.id===m.id));assert.throws(()=>apply(bad,ctx,now),/changed_import/);rejected++;
}
const bytes=fs.readFileSync('data/recovery/2022/nse-issue-information.json');
const cli=spawnSync(process.execPath,['scripts/apply-reviewed-bse-2022-maruti-olatech.mjs','--check'],{encoding:'utf8'});
assert.equal(cli.status,0,cli.stderr);assert.deepEqual(fs.readFileSync('data/recovery/2022/nse-issue-information.json'),bytes);
const publicData=JSON.parse(fs.readFileSync('data/ipos.json','utf8'));
const expectedRows=rows.map(expectedPublic);
const present=publicData.records.filter(r=>rows.some(t=>t.id===r.id));
if(present.length){assert.equal(present.length,2);for(const target of expectedRows)assert.deepEqual(present.find(r=>r.id===target.id),target,'real builder projection');}
const fixture={schema_version:'1.2.0',generated_at:now,records:expectedRows};
let fetchCalls=0;
const positive=await verifyMarutiOlatechPublication({fetchImpl:async(url)=>{fetchCalls++;assert.equal(url,'https://vasuki8.github.io/IPO-Tracker/data/ipos.json');return new Response(JSON.stringify(fixture),{status:200});}});
assert.equal(fetchCalls,1);assert.equal(positive.ok,true);assert.equal(positive.records.length,2);
assert.equal(positive.response_sha256,sha256(Buffer.from(JSON.stringify(fixture))));
for(const mutate of [x=>x.records.pop(),x=>x.records[0].issue_price.value++,x=>x.records[0].listing_date.evidence[0].page=1,x=>x.records.push(x.records[0])]){
 const bad=structuredClone(fixture);mutate(bad);await assert.rejects(verifyMarutiOlatechPublication({fetchImpl:async()=>new Response(JSON.stringify(bad),{status:200})}));rejected++;
}
console.log(JSON.stringify({bse_2022_maruti_olatech_tests:{records:2,verified_fields:14,rejected_mutations:rejected,source_units:true,physical_pdf_pages:true,first_last_collection_distinct:true,unchanged_existing_records:true,read_only_check:true,rerun_safe:true,live_fetch_contract:true,real_builder_checked:present.length===2}}));
