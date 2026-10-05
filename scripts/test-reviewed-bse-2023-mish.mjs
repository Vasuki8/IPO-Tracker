import assert from 'node:assert/strict';
import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
import {
  apply,context,expected,loadRecovery,validate,
  PUBLICATION_REVIEW,FIELD_REVIEW,RECEIPT,MANIFEST,TARGET
} from './apply-reviewed-bse-2023-mish.mjs';
import {expectedPublic,verifyMishPublication} from './verify-bse-2023-mish.mjs';

const ctx=context();
assert.deepEqual(validate(ctx),{
  ok:true,
  records:1,
  public_source_host:'www.bseindia.com',
  held_research_fields:2,
  source_allowlist_expanded:false,
});

const target=expected(ctx)[0];
assert.equal(target.id,'mish-designs-limited');
assert.equal(target.issuer_name,'Mish Designs Limited');
assert.equal(target.status,'listed');
assert.equal(target.board,null);
assert.equal(target.bse_scrip_code,'544015');
assert.equal(target.price_band.value,null);
assert.equal(target.price_band.status,'missing');
assert.equal(target.issue_price.value,122);
assert.equal(target.issue_price.status,'verified');
assert.equal(target.issue_size_inr.value,97600000);
assert.equal(target.issue_size_inr.status,'verified');
assert.equal(target.market_lot.value,null);
assert.equal(target.minimum_bid_quantity.value,null);
assert.equal(target.open_date.value,'2023-10-31');
assert.equal(target.close_date.value,'2023-11-02');
assert.equal(target.listing_date.value,'2023-11-07');
assert.equal(target.documents.length,1);
assert.equal(new URL(target.documents[0].url).hostname,'www.bseindia.com');
assert.equal(target.status_evidence.length,1);
assert.equal(new URL(target.status_evidence[0].url).hostname,'www.bseindia.com');
assert.equal(new URL(target.identity_evidence.bse_scrip_code.url).hostname,'www.bseindia.com');
for(const name of ['issue_price','issue_size_inr','open_date','close_date','listing_date']){
  assert.equal(new URL(target[name].source.url).hostname,'www.bseindia.com');
}
assert.equal(JSON.stringify(target).includes('mishindia.com'),false);
assert.equal(target.open_date.corrections.length,1);
assert.equal(target.open_date.corrections[0].competing_observation.value,'2023-11-02');
assert.equal(target.close_date.corrections.length,1);
assert.equal(target.close_date.corrections[0].competing_observation.value,'2023-10-31');
assert.deepEqual(target.bse_2023_mish_import.held_research_fields,['market_lot','minimum_bid_quantity']);

const fixture=()=>Object.fromEntries([2020,2021,2022,2023,2024,2025,2026].map(year=>[
  String(year),
  {schema_version:'1.0.0',collection_started_at:'2026-10-05T18:00:00.000Z',generated_at:'2026-10-05T18:01:00.000Z',records:[{id:'unrelated-'+year,issuer_name:'Unrelated '+year+' Limited'}]}
]));
const now='2026-10-05T20:30:00.000Z';
const before=fixture(),saved=structuredClone(before);
const first=apply(before,ctx,now);
assert.deepEqual(before,saved,'apply must not mutate caller recovery');
assert.deepEqual(first.stats,{records:1,added:1,skipped:0,changed:true});
assert.deepEqual(first.recovery['2023'].records.find(r=>r.id===target.id),target);
for(const year of Object.keys(saved)){
  assert.deepEqual(
    first.recovery[year].records.filter(r=>r.id.startsWith('unrelated-')),
    saved[year].records
  );
}
const second=apply(first.recovery,ctx,now);
assert.deepEqual(second.stats,{records:1,added:0,skipped:1,changed:false});
assert.deepEqual(second.recovery,first.recovery);

for(const [year,key] of [['2020','id'],['2021','issuer_name'],['2022','bse_scrip_code'],['2024','id'],['2025','issuer_name'],['2026','bse_scrip_code']]){
  const bad=fixture();
  const collision={id:'collision-record',issuer_name:'Other Limited'};
  if(key==='id')collision.id=target.id;
  if(key==='issuer_name')collision.issuer_name=target.issuer_name.toUpperCase();
  if(key==='bse_scrip_code')collision.bse_scrip_code='544015';
  bad[year].records.push(collision);
  assert.throws(()=>apply(bad,ctx,now),/identity_collision/);
}
const drift=fixture();
drift['2023'].records.push({...structuredClone(target),issue_price:{...structuredClone(target.issue_price),value:123}});
assert.throws(()=>apply(drift,ctx,now),/changed_import_record/);
assert.throws(()=>apply(fixture(),ctx,'2026-10-05T19:00:00.000Z'),/generation_before_approval/);

let rejected=0;
for(const mutate of [
  x=>x.manifest.publication_import_allowed=false,
  x=>x.publicationReview.publication_import_allowed=false,
  x=>x.publicationReview.publication_source_policy.allowed_source_keys.push('issuer_final_prospectus'),
  x=>x.fieldReview.fields.market_lot={value:1000,status:'verified',source_key:'issuer_final_prospectus'},
  x=>x.fieldReview.fields.minimum_bid_quantity={value:1000,status:'verified',source_key:'issuer_final_prospectus'},
  x=>x.fieldReview.fields.minimum_application_amount_inr={value:122000,status:'verified'},
  x=>x.fieldReview.fields.issue_price.value=123,
  x=>x.fieldReview.fields.board.value='SME',
  x=>x.receipt.documents.find(d=>d.key==='bse_annual_report_2023_24').response_sha256='0'.repeat(64)
]){
  const bad=structuredClone(ctx);mutate(bad);assert.throws(()=>validate(bad));rejected++;
}

const protectedPaths=[TARGET,'data/ipos.json',PUBLICATION_REVIEW,FIELD_REVIEW,RECEIPT,MANIFEST,'scripts/build-published-data.mjs'];
const protectedBytes=protectedPaths.map(p=>fs.readFileSync(p));
const check=spawnSync(process.execPath,['scripts/apply-reviewed-bse-2023-mish.mjs','--check'],{encoding:'utf8'});
assert.equal(check.status,0,check.stderr);
protectedPaths.forEach((p,i)=>assert.deepEqual(fs.readFileSync(p),protectedBytes[i],'read-only check changed '+p));

const current=loadRecovery(),currentRows=Object.entries(current).flatMap(([year,m])=>(m.records||[]).map(r=>({year,r})));
const currentHits=currentRows.filter(({r})=>r.id===target.id||String(r.bse_scrip_code??'')==='544015'||String(r.issuer_name??'').toLowerCase()==='mish designs limited');
if(currentHits.length){
  assert.equal(currentHits.length,1);
  assert.equal(currentHits[0].year,'2023');
  assert.deepEqual(currentHits[0].r,target,'existing Mish record must be exact approved projection');
}

const publicTarget=expectedPublic(target);
assert.equal(publicTarget.market_lot.value,null);
assert.equal(publicTarget.minimum_bid_quantity.value,null);
assert.equal(publicTarget.minimum_application_amount_inr.value,null);
assert.equal(publicTarget.application_requirements.retail.minimum_bid_quantity.value,null);
assert.equal(publicTarget.application_requirements.retail.minimum_application_amount_inr.value,null);
assert.equal(JSON.stringify(publicTarget).includes('mishindia.com'),false);
assert.equal(publicTarget.documents.length,1);
assert.equal(new URL(publicTarget.documents[0].url).hostname,'www.bseindia.com');

const fixturePublic={schema_version:'1.2.0',generated_at:now,records:[publicTarget]};
let calls=0;
const result=await verifyMishPublication({ctx,fetchImpl:async url=>{
  calls++;assert.equal(url,'https://vasuki8.github.io/IPO-Tracker/data/ipos.json');
  return new Response(JSON.stringify(fixturePublic));
}});
assert.equal(calls,1);
assert.equal(result.ok,true);
assert.deepEqual(result.records,['mish-designs-limited']);

for(const mutate of [
  d=>d.records.pop(),
  d=>d.records[0].issue_price.value=123,
  d=>d.records[0].market_lot={value:1000,status:'verified',evidence:[],corrections:[]},
  d=>d.records[0].minimum_bid_quantity={value:1000,status:'verified',evidence:[],corrections:[]},
  d=>d.records[0].minimum_application_amount_inr={value:122000,status:'verified',evidence:[],corrections:[]},
  d=>d.records[0].open_date.corrections=[],
  d=>d.records[0].issue_price.evidence[0].url='https://mishindia.com/not-allowed.pdf',
  d=>d.records.push(d.records[0])
]){
  const bad=structuredClone(fixturePublic);mutate(bad);
  await assert.rejects(()=>verifyMishPublication({ctx,fetchImpl:async()=>new Response(JSON.stringify(bad))}));
  rejected++;
}

console.log(JSON.stringify({mish_publication_approval_tests:{
  approved_records:1,
  verified_bse_public_fields:6,
  bse_identity_fields:1,
  held_research_fields:2,
  fixed_price_no_band:true,
  application_amount_not_inferred:true,
  source_allowlist_expanded:false,
  unrelated_records_unchanged:true,
  read_only_check:true,
  live_contract:true,
  rejected_mutations:rejected
}}));
