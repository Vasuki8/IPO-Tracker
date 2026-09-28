import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {sha256} from './verify-bse-listing-candidates.mjs';
const moduleUrl=new URL('./check-bse-2023-irms-field-review.mjs',import.meta.url);
assert.ok(fs.existsSync(moduleUrl),'read-only prospectus field review validator is required');
const {context,validateReview,reconcileIdentities,checkReview}=await import(moduleUrl.href);
const original=context();
const fields=['price_band','issue_price','issue_size_inr','market_lot','minimum_bid_quantity','open_date','close_date','listing_date'];
const clone=()=>structuredClone(original);
test('reviews exactly 32 dispositions without approving publication or clearing identities',()=>{
 const result=validateReview(original);
 assert.deepEqual(result,{ok:true,issuers:4,field_dispositions:32,verified_stated_terms:24,provisional:3,not_applicable:1,missing:4,publication_import_allowed:false});
 assert.equal(original.review.actions[0].terms.market_lot.value,1);
 assert.equal(original.review.actions[0].terms.minimum_bid_quantity.value,460);
 assert.equal(original.review.actions[3].terms.market_lot.value,3000);
 assert.equal(original.review.actions[3].terms.minimum_bid_quantity.value,3000);
});
for(const [name,mutate] of [
 ['import permission',r=>r.publication_import_allowed=true],
 ['completed release',r=>r.ipo_release_review_complete=true],
 ['fresh source claim',r=>r.source_refetched=true],
 ['complete universe claim',r=>r.complete_indian_ipo_universe=true],
 ['wrong issuer',r=>r.actions[0].issuer_name='Another issuer Limited'],
 ['duplicate issuer',r=>r.actions[1]=r.actions[0]],
 ['extra application field',r=>r.actions[0].terms.minimum_application_amount={value:14720}],
 ['trading lot confused with minimum bid',r=>r.actions[0].terms.market_lot.value=460],
 ['anchor used as public opening',r=>r.actions[0].terms.open_date.value='2023-11-20'],
 ['wrong public close',r=>r.actions[1].terms.close_date.value='2023-12-21'],
 ['date copied from discovery',r=>r.actions[0].terms.listing_date.value='2023-11-29'],
 ['fabricated listing evidence',r=>{r.actions[0].terms.listing_date.status='verified_stated_term';r.actions[0].terms.listing_date.evidence={page:1};}],
 ['tentative amount called verified',r=>r.actions[2].terms.issue_size_inr.status='verified_stated_term'],
 ['lost amount qualification',r=>r.actions[0].terms.issue_size_inr.qualification=''],
 ['wrong unit multiplier',r=>r.actions[0].terms.issue_size_inr.source_unit='INR lakh'],
 ['unrelated reporting period',r=>r.actions[0].terms.issue_size_inr.reporting_period='2024 IPO'],
 ['net amount replacing gross issue',r=>r.actions[3].terms.issue_size_inr.value=152208000],
 ['fixed issue gets a band',r=>r.actions[3].terms.price_band.value={min:42,max:42}],
 ['wrong evidence page',r=>r.actions[1].terms.price_band.evidence.page=13],
 ['page beyond original PDF',r=>r.actions[2].terms.market_lot.evidence.page=10000],
 ['cross-issuer document',r=>r.actions[1].terms.issue_price.evidence.document_sha256=r.actions[0].document.response_sha256],
 ['attachment directory date',r=>r.actions[1].document.document_date='2024-05-15'],
 ['invented publication date',r=>r.actions[0].document.publication_date='2023-11-28'],
 ['altered collection clock',r=>r.actions[1].document.collected_at=r.reviewed_at],
 ['wrong source attempt',r=>r.actions[1].document.workflow_attempt=1],
 ['issuer website substituted',r=>r.actions[1].document.url='https://motisonsjewellers.com/document.pdf'],
 ['source receipt path traversal',r=>r.source_receipt.path='../receipt.json'],
 ['review before collection',r=>r.reviewed_at='2023-01-01T00:00:00.000Z'],
 ['source source-row replaced',r=>r.actions[3].source_row_index=10],
 ['field omission',r=>delete r.actions[0].terms.open_date]
])test(`rejects ${name}`,()=>{const c=clone();mutate(c.review);assert.throws(()=>validateReview(c));});
for(const field of fields.filter(f=>f!=='listing_date'))test(`all four ${field} observations are content-bound`,()=>{
 for(let i=0;i<4;i++){const c=clone();c.review.actions[i].terms[field].qualification+=' changed';assert.throws(()=>validateReview(c));}
});
test('rejects mismatched raw receipt and plan bytes rather than trusting a parsed object',()=>{
 for(const key of ['receiptBytes','planBytes','queueBytes']){const c=clone();c[key]=Buffer.from('{}');assert.throws(()=>validateReview(c));}
});
test('a rehashed forged collection receipt cannot launder a different original response',()=>{
 const c=clone(),b=JSON.parse(Buffer.from(c.receiptBytes));b.collections[1].receipt.documents.find(d=>d.code==='544053'&&d.kind==='prospectus').response_sha256='f'.repeat(64);
 c.receiptBytes=Buffer.from(JSON.stringify(b));c.review.source_receipt.sha256=sha256(c.receiptBytes);assert.throws(()=>validateReview(c));
});
test('cross-year canonical-name, stable-id and code matches warn without approving import',()=>{
 const a=original.review.actions[0],other=original.review.actions[1];
 const all={'2020':{records:[{id:'prior-alias',issuer_name:a.issuer_name.toUpperCase()}]},'2022':{records:[{id:other.candidate_id,issuer_name:'Old unrelated name'}]},'2024':{records:[{id:'different-id',issuer_name:'Other Limited',bse_scrip_code:544060}]}};
 const before=structuredClone(all),r=reconcileIdentities(original.review.actions,all);
 assert.equal(r.matches.length,3);assert.deepEqual(r.years_checked,[2020,2022,2024]);assert.equal(r.clearance_for_import,false);assert.deepEqual(all,before);
 assert.deepEqual(r.matches.map(m=>m.recovery_year),[2020,2022,2024]);
});
test('an empty match list is not an identity clearance or queue closeout',()=>{
 const r=reconcileIdentities(original.review.actions,{'2023':{records:[]}});assert.deepEqual(r.matches,[]);assert.equal(r.clearance_for_import,false);
 assert.throws(()=>reconcileIdentities(original.review.actions,{'2023':{records:'invalid'}}));
});
test('runs read-only against current recovery without pinning future collector output',()=>{
 const r=checkReview();assert.equal(r.review.field_dispositions,32);assert.equal(r.reconciliation.clearance_for_import,false);
 assert.ok(r.reconciliation.years_checked.length>=7);assert.ok(r.reconciliation.records_checked>=1375);
});
test('CLI refuses an apply flag instead of writing production data',()=>{
 const root=new URL('../',import.meta.url);const paths=['data/ipos.json','data/recovery/2023/nse-issue-information.json','data/discovery/bse-2023-review-progress-2026-09-28.json'];
 const before=paths.map(p=>sha256(fs.readFileSync(new URL(p,root))));
 const r=spawnSync(process.execPath,[moduleUrl.pathname,'--apply'],{encoding:'utf8'});assert.notEqual(r.status,0);assert.match(r.stderr,/read.only/);
 assert.deepEqual(paths.map(p=>sha256(fs.readFileSync(new URL(p,root)))),before);
});
test('field-review CI runs offline with read-only permissions and no publication path',()=>{
 const url=new URL('../.github/workflows/check-bse-2023-irms-field-review.yml',import.meta.url);
 assert.ok(fs.existsSync(url),'field-review CI is required');const text=fs.readFileSync(url,'utf8');
 assert.match(text,/permissions:\n  contents: read/);assert.match(text,/persist-credentials: false/);
 assert.match(text,/node scripts\/check-bse-2023-irms-field-review\.mjs/);
 assert.match(text,/for file in scripts\/test-\*\.mjs/);
 assert.doesNotMatch(text,/contents: write|continue-on-error|git push|git commit|curl |wget |apply-reviewed|node scripts\/collect-/);
});
