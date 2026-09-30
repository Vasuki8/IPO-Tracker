import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {ROOT,REVIEW,RECEIPT,ID,ALIAS_ID,FIELDS,REPAIRS,context,expected,loadRecovery,apply} from './apply-reviewed-bse-2022-final-pair.mjs';
import {expectedPublic,verifyFinalPairPublication} from './verify-bse-2022-final-pair.mjs';
import {sha256} from './verify-bse-listing-candidates.mjs';
const c=context(),current=loadRecovery(),before=structuredClone(current),now=new Date().toISOString();
for(const m of Object.values(before))m.records=m.records.filter(r=>r.id!==ID);
before['2022'].records=before['2022'].records.map(r=>r.id===ALIAS_ID?structuredClone(c.review.existing_alias.baseline_record):r);
const frozen=structuredClone(before),first=apply(before,c,now),[drone,five]=expected(c);
assert.deepEqual(before,frozen);assert.deepEqual(first.stats,{added:1,repaired:1,unchanged:0,existing_aliases:1,conflicts:1,changed:true});
assert.deepEqual(apply(first.recovery,c,now),{recovery:first.recovery,stats:{added:0,repaired:0,unchanged:2,existing_aliases:1,conflicts:1,changed:false}});
let preserved=0;
for(const [y,m]of Object.entries(before)){if(y!=='2022')assert.deepEqual(first.recovery[y],m);for(const r of m.records)if(r.id!==ALIAS_ID){assert.deepEqual(first.recovery[y].records.find(x=>x.id===r.id),r);preserved++;}}
assert.deepEqual(FIELDS.map(k=>drone[k].value),[{min:52,max:54},54,339660000,2000,2000,'2022-12-13','2022-12-15','2022-12-23']);
assert.deepEqual([drone.market_lot.page,drone.minimum_bid_quantity.page],[226,2]);
assert.equal(drone.board,'SME');assert.equal(drone.nse_symbol,null);assert.equal(drone.bse_scrip_code,null);
assert.equal(drone.first_observed_at,c.receipt.documents.find(d=>d.key==='drone_prospectus').collected_at);
assert.equal(drone.last_collected_at,c.receipt.documents.find(d=>d.key==='drone_listing_corroboration').collected_at);
assert.deepEqual(REPAIRS.map(k=>five[k].value),[{min:450,max:474},1,'2022-11-09','2022-11-11',15934490000]);
for(const k of ['id','issuer_name','board','board_evidence','status','status_evidence','nse_symbol','nse_series','nse_source','terms','issue_price','listing_date','minimum_bid_quantity','first_observed_at'])assert.deepEqual(five[k],c.review.existing_alias.baseline_record[k],k+' preserved');
assert.equal(five.minimum_bid_quantity.value,31);assert.equal(five.market_lot.value,1);
assert.equal(five.issue_size_inr.status,'conflict');assert.equal(five.issue_size_inr.additional_sources.length,1);
assert.deepEqual(five.issue_size_inr.additional_sources[0],{...c.review.existing_alias.baseline_record.issue_size_inr.source,page:null});
assert.equal(five.issue_size_inr.corrections[0].previous_observation.value,19600050000);
assert.match(five.issue_size_inr.corrections[0].preferred_candidate.qualification,/Basis of Allotment/);
assert.equal(five.documents.length,c.review.existing_alias.baseline_record.documents.length+1);
assert.deepEqual(five.documents.slice(0,-1),c.review.existing_alias.baseline_record.documents);
let negatives=0;
const reject=(model,ctx=c)=>{assert.throws(()=>apply(model,ctx,now));negatives++;};
for(const id of [ID,ALIAS_ID])for(const kind of ['id','name','code']){const bad=structuredClone(before),r={id:'collision',issuer_name:'Unrelated'};if(kind==='id')r.id=id;if(kind==='name')r.issuer_name=id===ID?drone.issuer_name:'Five-Star Business Finance Limited';if(kind==='code')r.bse_scrip_code=id===ID?'543713':'543663';bad['2023'].records.push(r);reject(bad);}
for(const edit of [r=>r.nse_symbol='OTHER',r=>r.issue_price.value++,r=>r.listing_date.value='2021-11-21',r=>r.documents.pop(),r=>r.first_observed_at=now]){const b=structuredClone(before);edit(b['2022'].records.find(r=>r.id===ALIAS_ID));reject(b);}
const absent=structuredClone(before);absent['2022'].records=absent['2022'].records.filter(r=>r.id!==ALIAS_ID);reject(absent);
for(const id of [ID,ALIAS_ID])for(const edit of [r=>r.market_lot.value++,r=>r.documents.pop(),r=>r.first_observed_at=now]){const b=structuredClone(first.recovery);edit(b['2022'].records.find(r=>r.id===id));reject(b);}
for(const mutate of [x=>x.manifest.review_sha256='0'.repeat(64),x=>x.manifest.existing_alias_ids=[],x=>x.manifest.import_ids.push(ALIAS_ID),x=>x.review.import_record.fields.issue_price.value++,x=>x.receipt.documents[0].response_bytes++]){const bad=structuredClone(c);mutate(bad);reject(before,bad);}
function rebind(x){x.reviewBytes=Buffer.from(JSON.stringify(x.review));x.receipt.review_sha256=sha256(x.reviewBytes);x.receiptBytes=Buffer.from(JSON.stringify(x.receipt));x.manifest.review_sha256=sha256(x.reviewBytes);x.manifest.receipt_sha256=sha256(x.receiptBytes);}
for(const mutate of [
 x=>x.review.import_record.fields.price_band.value=null,
 x=>x.review.import_record.fields.price_band.value={min:54,max:54},
 x=>x.review.import_record.fields.open_date.value='2022-12-12',
 x=>x.review.existing_alias.fields.open_date.value='2022-11-07',
 x=>x.review.import_record.fields.listing_date.value='2022-02-30',
 x=>x.review.import_record.fields.issue_price.value=999,
 x=>x.review.import_record.fields.issue_size_inr.normalization_multiplier=10000000,
 x=>x.review.existing_alias.fields.issue_size_inr.status='verified',
 x=>x.review.existing_alias.fields.issue_size_inr.qualification='',
 x=>x.review.existing_alias.conflict.previous.value++,
 x=>x.review.existing_alias.fields.market_lot.pdf_page=999,
 x=>x.review.import_record.fields.minimum_bid_quantity.source_unit='INR',
 x=>x.review.sources[0].publication_date='2022-12-19',
 x=>x.receipt.documents[0].collected_at='2099-01-01T00:00:00Z',
 x=>x.review.import_record.fields.minimum_application_amount_inr={value:108000},
 x=>x.review.existing_alias.nse_symbol='DRONE'
]){const bad=structuredClone(c);mutate(bad);rebind(bad);reject(before,bad);}
const dataPath=path.join(ROOT,'data/recovery/2022/nse-issue-information.json'),original=fs.readFileSync(dataPath);
const cli=spawnSync(process.execPath,['scripts/apply-reviewed-bse-2022-final-pair.mjs','--check'],{cwd:ROOT,encoding:'utf8'});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(fs.readFileSync(dataPath),original);
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'final-pair-test-'));
try{
 for(const dir of ['data','scripts','assets'])fs.cpSync(path.join(ROOT,dir),path.join(temp,dir),{recursive:true});
 const write=model=>{for(const [y,m]of Object.entries(model))fs.writeFileSync(path.join(temp,'data/recovery',y,'nse-issue-information.json'),JSON.stringify(m,null,2)+'\n');};
 const run=(name,args=[])=>{const r=spawnSync(process.execPath,[name,...args],{cwd:temp,encoding:'utf8'});assert.equal(r.status,0,r.stderr||r.stdout);};
 const read=()=>JSON.parse(fs.readFileSync(path.join(temp,'data/ipos.json')));
 write(before);run('scripts/build-published-data.mjs');const old=read();
 write(first.recovery);run('scripts/build-published-data.mjs');run('scripts/build-published-data.mjs',['--check']);run('scripts/validate-data.mjs');const data=read();
 assert.equal(data.records.length,old.records.length+1);
 for(const r of old.records)if(r.id!==ALIAS_ID)assert.deepEqual(data.records.find(x=>x.id===r.id),r);
 for(const target of [drone,five].map(expectedPublic))assert.deepEqual(data.records.find(r=>r.id===target.id),target,'real public projection');
 const fixture={schema_version:'1.2.0',generated_at:now,records:[drone,five].map(expectedPublic)};
 let calls=0;const bytes=JSON.stringify(fixture);
 const good=await verifyFinalPairPublication({fetchImpl:async url=>{calls++;assert.equal(url,'https://vasuki8.github.io/IPO-Tracker/data/ipos.json');return new Response(bytes,{status:200});}});
 assert.equal(calls,1);assert.equal(good.response_sha256,sha256(Buffer.from(bytes)));
 for(const mutate of [d=>d.records.pop(),d=>d.records.push(d.records[0]),d=>d.records[0].open_date.value='2022-12-12',d=>d.records[1].issue_size_inr.status='verified',d=>d.records[1].issue_size_inr.evidence.pop(),d=>d.records[1].issue_size_inr.corrections=[],d=>d.records[1].market_lot.value=31]){const bad=structuredClone(fixture);mutate(bad);await assert.rejects(verifyFinalPairPublication({fetchImpl:async()=>new Response(JSON.stringify(bad),{status:200})}));negatives++;}
 console.log(JSON.stringify({final_pair_tests:{new_issuers:1,existing_aliases:1,filled_fields:4,conflicts_retained:1,unchanged_other_records:preserved,negative_cases:negatives,bookbuilt_band:true,anchor_distinction:true,lot_bid_distinction:true,real_builder:true,read_only:true,rerun_safe:true}}));
}finally{fs.rmSync(temp,{recursive:true,force:true});}
