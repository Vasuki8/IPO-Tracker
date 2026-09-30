import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
import {sha256} from './verify-bse-listing-candidates.mjs';
import {context,validateReview,reconcileIdentities,checkReview} from './check-bse-2023-ssek-field-review.mjs';

const original=context(),clone=()=>structuredClone(original);
test('reviews exactly 32 dispositions without approving publication',()=>{
 const r=validateReview(original);
 assert.deepEqual(r,{ok:true,issuers:4,field_dispositions:32,verified_stated_terms:24,provisional:2,not_applicable:2,missing:4,publication_import_allowed:false});
 const [shanti,shoora,exhicon,khazanchi]=original.review.actions;
 assert.deepEqual(shanti.terms.price_band.value,{min:66,max:70});assert.equal(shanti.terms.issue_price.value,70);assert.equal(shanti.terms.issue_size_inr.value,312480000);assert.equal(shanti.terms.market_lot.value,2000);assert.equal(shanti.terms.minimum_bid_quantity.value,2000);
 assert.equal(shoora.terms.price_band.status,'not_applicable');assert.equal(shoora.terms.issue_price.value,48);assert.equal(shoora.terms.issue_size_inr.value,20304000);assert.equal(shoora.terms.market_lot.value,3000);
 assert.deepEqual(exhicon.terms.price_band.value,{min:61,max:64});assert.equal(exhicon.terms.issue_price.value,64);assert.equal(exhicon.terms.issue_size_inr.status,'provisional');assert.equal(exhicon.terms.open_date.value,'2023-03-31');assert.equal(exhicon.terms.close_date.value,'2023-04-05');
 assert.equal(khazanchi.terms.price_band.status,'not_applicable');assert.equal(khazanchi.terms.issue_price.value,140);assert.equal(khazanchi.terms.issue_size_inr.value,967400000);assert.equal(khazanchi.terms.minimum_bid_quantity.value,1000);
});
for(const [name,mutate] of [
 ['import permission',r=>r.publication_import_allowed=true],
 ['completed release',r=>r.ipo_release_review_complete=true],
 ['listing date from discovery',r=>{r.actions[0].terms.listing_date.value='2023-12-27';r.actions[0].terms.listing_date.status='verified_stated_term';}],
 ['Shanti cut-off typo promoted',r=>r.actions[0].terms.issue_price.value=80],
 ['Shanti inconsistency removed',r=>r.actions[0].source_inconsistencies=[]],
 ['Shoora archive date laundered',r=>r.actions[1].document.document_date='2024-04-04'],
 ['Shoora gets a fabricated band',r=>r.actions[1].terms.price_band.value={min:47,max:48}],
 ['Exhicon definitions override cover',r=>r.actions[2].terms.open_date.value='2023-04-05'],
 ['Exhicon amount promoted',r=>r.actions[2].terms.issue_size_inr.status='verified_stated_term'],
 ['Exhicon inconsistency removed',r=>r.actions[2].source_inconsistencies=[]],
 ['Khazanchi amount changed',r=>r.actions[3].terms.issue_size_inr.value=918960000],
 ['minimum application amount invented',r=>r.actions[3].terms.minimum_application_amount_inr={value:140000}],
 ['wrong evidence page',r=>r.actions[1].terms.minimum_bid_quantity.evidence.page=202],
 ['unverified board promoted',r=>r.actions[2].unverified_identifiers.board='SME'],
 ['source receipt substitution',r=>r.source_receipt.git_blob_sha='0'.repeat(40)]
])test('rejects '+name,()=>{const c=clone();mutate(c.review);assert.throws(()=>validateReview(c));});

test('raw source receipt and review are content-pinned',()=>{
 const c=clone();c.receiptBytes=Buffer.from('{}');assert.throws(()=>validateReview(c));
 const d=clone();d.reviewBytes=Buffer.from(JSON.stringify(d.review));assert.throws(()=>validateReview(d));
});

test('exact identity matching warns but never authorizes an import',()=>{
 const actions=original.review.actions;
 const rec={'2020':{records:[{id:actions[0].candidate_id,issuer_name:'Different name'}]},'2024':{records:[{id:'x',issuer_name:actions[1].issuer_name}]}};
 const pub={records:[{id:'p',issuer_name:'Other Limited',bse_scrip_code:'543895'}]};
 const r=reconcileIdentities(actions,rec,pub);assert.equal(r.matches.length,3);assert.equal(r.clearance_for_import,false);
});

test('current all-year and public identities remain clear at review time',()=>{
 const r=checkReview();assert.deepEqual(r.reconciliation.matches,[]);assert.equal(r.reconciliation.clearance_for_import,false);assert.ok(r.reconciliation.records_checked>=1383);assert.ok(r.reconciliation.public_records_checked>=1383);
});

test('CLI is read-only and temporary source workflow is retired',()=>{
 const root=new URL('../',import.meta.url),moduleUrl=new URL('./check-bse-2023-ssek-field-review.mjs',import.meta.url);
 const paths=['data/ipos.json','data/discovery/bse-2023-review-progress-2026-09-28.json'];
 const before=paths.map(p=>sha256(fs.readFileSync(new URL(p,root))));
 const r=spawnSync(process.execPath,[moduleUrl.pathname,'--apply'],{encoding:'utf8'});assert.notEqual(r.status,0);assert.match(r.stderr,/read-only/);
 assert.deepEqual(paths.map(p=>sha256(fs.readFileSync(new URL(p,root)))),before);
 assert.equal(fs.existsSync(new URL('.github/workflows/collect-bse-2023-ssek-evidence.yml',root)),false,'temporary source collector workflow must not remain');
 const ci=fs.readFileSync(new URL('.github/workflows/validate-data.yml',root),'utf8');assert.match(ci,/test-bse-2023-ssek-field-review\.mjs/);
});
