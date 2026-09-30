import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {expectedPublic} from './verify-bse-2023-rvpe.mjs';
import {sha256} from './verify-bse-listing-candidates.mjs';
const moduleUrl=new URL('./apply-reviewed-bse-2023-ssek.mjs',import.meta.url);
const {context,validate,expected,apply,loadRecovery}=await import(moduleUrl.href);
const ctx=context(),now='2026-09-30T02:00:00.000Z',raw=()=>expected(ctx),clone=()=>structuredClone(ctx);
const fixture=()=>Object.fromEntries([2020,2021,2022,2023,2024,2025,2026].map(y=>[y,{schema_version:'1.0.0',generated_at:'2026-09-29T01:00:00.000Z',records:[{id:'unrelated-'+y,issuer_name:'Other '+y+' Limited'}]}]));
test('validates separately reviewed listing approval and immutable source bindings',()=>{
 assert.deepEqual(validate(ctx),{ok:true,records:4,listing_verified:4,board_promoted:0,isin_promoted:0,nse_promoted:0});
 assert.equal(ctx.fieldContext.review.publication_import_allowed,false);
 assert.ok(ctx.fieldContext.review.actions.every(a=>a.terms.listing_date.value===null));
 assert.equal(ctx.receipt.failed_attempt.status,'partial');
 assert.equal(ctx.receipt.collection.source_documents_accepted,4);
});
test('constructs exact listing dates and BSE identities while leaving unsupported identities null',()=>{
 const r=raw();
 assert.deepEqual(r.map(x=>x.listing_date.value),['2023-12-27','2023-08-29','2023-04-17','2023-08-07']);
 assert.deepEqual(r.map(x=>x.bse_scrip_code),['544059','543970','543895','543953']);
 assert.deepEqual(r.map(x=>x.market_lot.value),[2000,3000,2000,1000]);
 assert.deepEqual(r.map(x=>x.minimum_bid_quantity.value),[2000,3000,2000,1000]);
 assert.deepEqual(r.map(x=>x.issue_price.value),[70,48,64,140]);
 assert.deepEqual(r.map(x=>x.issue_size_inr.status),['provisional','verified','provisional','verified']);
 for(const x of r){assert.equal(x.board,null);assert.equal(x.nse_symbol,null);assert.equal(x.isin,null);assert.equal(x.status,'listed');assert.equal(x.status_evidence.length,1);assert.match(x.status_evidence[0].document_type,/Annual Report PDF$/);}
 assert.equal(r[1].price_band.status,'missing');assert.equal(r[3].price_band.status,'missing');
});
test('adds exactly four, preserves unrelated records, and reruns idempotently',()=>{
 const before=fixture(),copy=structuredClone(before),first=apply(before,ctx,now);assert.deepEqual(before,copy);assert.deepEqual(first.stats,{records:4,added:4,skipped:0,changed:true});
 for(const y of Object.keys(before)){assert.deepEqual(first.recovery[y].records.filter(r=>r.id.startsWith('unrelated-')),before[y].records);if(y!=='2023')assert.deepEqual(first.recovery[y],before[y]);}
 const second=apply(first.recovery,ctx,'2026-09-30T02:01:00.000Z');assert.deepEqual(second.stats,{records:4,added:0,skipped:4,changed:false});assert.deepEqual(second.recovery,first.recovery);
});
for(const y of ['2020','2022','2024','2026'])for(const key of ['id','issuer_name','bse_scrip_code'])test('rejects '+y+' '+key+' collision',()=>{
 const all=fixture(),target=raw()[0],collision={id:'alias-record',issuer_name:'Some prior alias Limited',[key]:key==='issuer_name'?target.issuer_name.toUpperCase():target[key]};all[y].records.push(collision);assert.throws(()=>apply(all,ctx,now),/identity_collision/);
});
for(const [name,mutate] of [
 ['listing date',c=>c.review.actions[0].listing_date.value='2023-12-28'],
 ['BSE code',c=>c.review.actions[1].identifiers.bse_scrip_code.value='999999'],
 ['board promotion',c=>c.review.actions[2].identifiers.board='SME'],
 ['ISIN promotion',c=>c.review.actions[3].identifiers.isin='INE0OWC01011'],
 ['platform mapping',c=>c.review.actions[0].platform_observation.status='verified_board'],
 ['source URL',c=>c.review.actions[0].document.url='https://example.com/report.pdf'],
 ['source hash',c=>c.review.actions[2].document.response_sha256='0'.repeat(64)],
 ['review blob binding',c=>c.manifest.review_git_blob_sha='0'.repeat(40)],
 ['receipt blob binding',c=>c.manifest.receipt_git_blob_sha='0'.repeat(40)],
 ['source plan binding',c=>c.manifest.source_plan_git_blob_sha='0'.repeat(40)],
 ['prospectus review changed',c=>c.fieldContext.review.actions[0].terms.issue_size_inr.status='verified_stated_term']
])test('rejects '+name,()=>{const c=clone();mutate(c);assert.throws(()=>validate(c));});
test('current production has no conflicting target identities before import',()=>{
 const all=loadRecovery(),targets=raw();for(const t of targets){const hits=Object.entries(all).flatMap(([year,m])=>m.records.map(r=>({year,r}))).filter(x=>x.r.id===t.id||String(x.r.bse_scrip_code??'')===t.bse_scrip_code||x.r.issuer_name.toLowerCase()===t.issuer_name.toLowerCase());assert.deepEqual(hits,[]);}
});
test('public projection retains null application amounts and exact listing evidence',()=>{
 for(const record of raw().map(expectedPublic)){assert.equal(record.minimum_application_amount_inr.value,null);assert.ok(Object.values(record.application_requirements).every(x=>x.minimum_application_amount_inr.value===null));assert.equal(record.listing_date.status,'verified');assert.equal(record.documents.length,2);}
});
const verifierUrl=new URL('./verify-bse-2023-ssek.mjs',import.meta.url);
async function verifyData(data,t){
 const {verifySsekPublication}=await import(verifierUrl.href);const base=fs.mkdtempSync(path.join(os.tmpdir(),'ssek-live-test-'));t.after(()=>fs.rmSync(base,{recursive:true,force:true}));const dir=path.join(base,'snapshot'),body=Buffer.from(JSON.stringify(data));
 const result=await verifySsekPublication({ctx,outputDir:dir,clock:()=>now,fetchImpl:async(url,options)=>{assert.equal(url,'https://vasuki8.github.io/IPO-Tracker/data/ipos.json');assert.equal(options.redirect,'error');return new Response(body);}});
 assert.equal(result.response_sha256,sha256(body));return result;
}
const published=()=>({schema_version:'1.2.0',generated_at:'2026-09-30T01:59:00.000Z',records:raw().map(expectedPublic)});
test('live verifier requires exact reviewed public projections',async t=>{const r=await verifyData(published(),t);assert.equal(r.ok,true);assert.equal(r.records.length,4);});
for(const [name,change] of [
 ['missing issuer',d=>d.records.pop()],['duplicate id',d=>d.records.push(d.records[0])],['listing drift',d=>d.records[2].listing_date.value='2023-04-18'],['invented application amount',d=>d.records[0].minimum_application_amount_inr.value=140000]
])test('live verifier rejects '+name,async t=>{const d=published();change(d);await assert.rejects(()=>verifyData(d,t));});
test('bounded publisher and live verifier exist only while release is pending',()=>{
 const root=new URL('../',import.meta.url),workflow=fs.readFileSync(new URL('.github/workflows/update-ipos.yml',root),'utf8');
 const state=JSON.parse(fs.readFileSync(new URL('docs/verification/bse-2023-ssek-release-2026-09-29.json',root)));
 const live=new URL('.github/workflows/verify-bse-2023-ssek-live.yml',root);
 if(['prepared_import_pending','published_verification_pending'].includes(state.status)){
  assert.match(workflow,/reviewed_ssek:/);assert.match(workflow,/startsWith\(github\.event\.head_commit\.message, 'release\(ssek\):'\)/);
  const job=workflow.split('  reviewed_ssek:')[1].split('  sync:')[0];
  assert.match(job,/git reset --hard origin\/main/);assert.match(job,/apply-reviewed-bse-2023-ssek\.mjs --apply/);assert.match(job,/build-published-data\.mjs --check/);
  assert.match(job,/git add data\/recovery\/2023\/nse-issue-information\.json data\/ipos\.json/);assert.doesNotMatch(job,/curl |wget |sync-nse|collect-/);
  assert.match(workflow,/sync:\n    if: github\.event_name != 'push' \|\| !startsWith\(github\.event\.head_commit\.message, 'release\(ssek\):'\)/);
  assert.equal(fs.existsSync(live),true);
 }else{
  assert.equal(state.status,'verified_and_publisher_retired');assert.equal(state.new_public_records,4);
  assert.doesNotMatch(workflow,/reviewed_ssek:|apply-reviewed-bse-2023-ssek\.mjs --apply/);assert.equal(fs.existsSync(live),false);
 }
});
test('temporary listing collector workflow is not retained in final tree',()=>{assert.equal(fs.existsSync(new URL('../.github/workflows/collect-bse-2023-ssek-listing-evidence.yml',import.meta.url)),false);});
