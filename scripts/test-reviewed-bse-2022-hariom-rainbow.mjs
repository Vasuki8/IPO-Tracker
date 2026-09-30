import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {ROOT, ID, ALIAS_ID, REVIEW, RECEIPT, MANIFEST, FIELDS,
  context, loadRecovery, expected, apply, validateContext} from './apply-reviewed-bse-2022-hariom-rainbow.mjs';
import {audit} from './verify-bse-2022-hariom-rainbow.mjs';
import {sha256} from './verify-bse-listing-candidates.mjs';
const ctx = context(), current = loadRecovery(), now = new Date().toISOString();
const before = structuredClone(current);
for (const m of Object.values(before)) m.records = m.records.filter(r => r.id !== ID);
const frozen = JSON.stringify(before), first = apply(before,ctx,now), row = expected(ctx);
assert.equal(JSON.stringify(before),frozen);
assert.deepEqual(first.stats,{added:1,already_present:0,existing_aliases:1,conflicts:1});
const rerun = apply(first.recovery,ctx,now);
assert.deepEqual(rerun.stats,{added:0,already_present:1,existing_aliases:1,conflicts:1});
assert.deepEqual(rerun.recovery,first.recovery);
for (const [year,m] of Object.entries(before)) {
  for (const old of m.records) assert.deepEqual(first.recovery[year].records.find(r => r.id === old.id),old);
  if (year !== '2022') assert.deepEqual(first.recovery[year],m);
}
assert.deepEqual(FIELDS.map(k => row[k].value),[{min:144,max:153},153,1300500000,1,98,'2022-03-30','2022-04-05','2022-04-13']);
assert.equal(row.issue_size_inr.status,'conflict');
assert.equal(row.issue_size_inr.additional_sources.length,1);
assert.equal(row.issue_size_inr.corrections[0].competing.value,130050000);
assert.equal(row.issue_size_inr.corrections[0].competing.unit,'INR million');
assert.equal(row.board,null); assert.equal(row.bse_scrip_code,null);
assert.equal(row.last_collected_at,'2026-09-27T15:18:03.936Z');
assert.notEqual(row.last_collected_at,ctx.receipt.collection_completed_at);
assert.match(row.listing_date.source.document_identity,/Waaree Energies/);
assert.equal(row.listing_date.source.page,542);
let negative = 0;
const rejects = (model,c=ctx,pattern=/./,clock=now) => {assert.throws(() => apply(model,c,clock),pattern); negative++;};
for (const [key,value] of [['id',ID],['issuer_name','Hariom Pipe Industries Ltd.'],['bse_scrip_code','543517'],['nse_symbol','HARIOMPIPE']]) {
  const all = structuredClone(before);
  all['2023'].records.push({id:'unrelated',issuer_name:'Another issuer',[key]:value});
  rejects(all,ctx,/identity_collision/);
}
for (const edit of [
  x => x.records = x.records.filter(r => r.id !== ALIAS_ID),
  x => x.records.push({...x.records.find(r => r.id === ALIAS_ID),id:'duplicate-rainbow',issuer_name:"Rainbow Children's Medicare Limited"}),
  x => x.records.find(r => r.id === ALIAS_ID).nse_symbol = 'WRONG',
  x => x.records.find(r => r.id === ALIAS_ID).issue_price.value = 543,
  x => x.records.find(r => r.id === ALIAS_ID).minimum_bid_quantity.status = 'provisional'
]) {const all = structuredClone(before); edit(all['2022']); rejects(all,ctx,/alias_/);}
const duplicate = structuredClone(before); duplicate['2022'].records.push(duplicate['2022'].records[0]);
rejects(duplicate,ctx,/duplicate_existing_id/);
for (const change of [
  r => r.issue_price.value++, r => r.issue_size_inr.status='verified',
  r => r.issue_size_inr.additional_sources=[], r => r.issue_size_inr.corrections=[],
  r => r.bse_2022_hariom_import.artifact_sha256='0'.repeat(64), r => r.board='Mainboard'
]) {const all = structuredClone(first.recovery); change(all['2022'].records.find(r => r.id === ID)); rejects(all,ctx,/changed_reviewed_record/);}
for (const mutate of [
  c => c.manifest.review_sha256='0'.repeat(64), c => c.manifest.receipt_sha256='0'.repeat(64),
  c => c.manifest.import_ids.push(ID), c => c.manifest.existing_alias_ids=[],
  c => c.manifest.target_year=2021, c => c.manifest.receipt_path='another.json',
  c => c.receipt.documents[0].response_sha256='1'.repeat(64),
  c => c.review.import.fields.issue_price.value=154
]) {const c=structuredClone(ctx); mutate(c); rejects(before,c);}
// Reject invalid source/data types even if a caller recalculates the byte hashes.
function rebind(c) {
  c.reviewBytes=Buffer.from(JSON.stringify(c.review));
  c.receipt.review_sha256=sha256(c.reviewBytes);
  c.receiptBytes=Buffer.from(JSON.stringify(c.receipt));
  c.manifest.review_sha256=sha256(c.reviewBytes); c.manifest.receipt_sha256=sha256(c.receiptBytes);
}
for (const mutate of [
  c => c.review.sources[1].key='hariom_prospectus',
  c => {for(const k of ['source_url','final_url'])c.receipt.documents[0][k]='http://www.sebi.gov.in/a.pdf';c.review.sources[0].url='http://www.sebi.gov.in/a.pdf'},
  c => {const u='https://secret@www.sebi.gov.in/a.pdf';c.review.sources[0].url=u;for(const k of ['source_url','final_url'])c.receipt.documents[0][k]=u},
  c => c.review.import.fields.listing_date.value='2022-02-30',
  c => c.review.import.fields.minimum_bid_quantity.unit='INR/share',
  c => c.review.import.fields.issue_size_inr.status='verified',
  c => c.review.import.conflicts[0].competing.unit='INR crore',
  c => c.review.import.conflicts[0].competing.value=1300500000,
  c => c.receipt.documents[0].response_bytes=0,
  c => c.receipt.documents[0].collected_at='2099-01-01T00:00:00Z',
  c => c.review.existing_alias.nse_symbol='OTHER'
]) {const c=structuredClone(ctx);mutate(c);rebind(c);rejects(before,c);}
rejects(before,ctx,/invalid_generation_clock/,'2022-01-01T00:00:00Z');
rejects(before,ctx,/invalid_generation_clock/,'not-a-date');
const dataPath=path.join(ROOT,'data/recovery/2022/nse-issue-information.json');
const original=fs.readFileSync(dataPath);
const cli=spawnSync(process.execPath,['scripts/apply-reviewed-bse-2022-hariom-rainbow.mjs','--check'],{cwd:ROOT,encoding:'utf8'});
assert.equal(cli.status,0,cli.stderr);assert.deepEqual(fs.readFileSync(dataPath),original);

// Use the real builder and schema validator in an isolated worktree. No external fetch.
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'hariom-release-test-'));
try {
  for(const name of ['scripts','data','assets'])fs.cpSync(path.join(ROOT,name),path.join(temp,name),{recursive:true});
  const writeRecovery=model=>{for(const [year,m]of Object.entries(model))fs.writeFileSync(path.join(temp,'data/recovery',year,'nse-issue-information.json'),JSON.stringify(m,null,2)+'\n');};
  const run=(file,args=[])=>{const r=spawnSync(process.execPath,[file,...args],{cwd:temp,encoding:'utf8'});assert.equal(r.status,0,r.stderr||r.stdout);return r;};
  const readPublic=()=>JSON.parse(fs.readFileSync(path.join(temp,'data/ipos.json')));
  writeRecovery(before);run('scripts/build-published-data.mjs');const baseline=readPublic();
  // Modifying the publisher alone must not alter any baseline record.
  const retained=JSON.parse(fs.readFileSync(path.join(ROOT,'data/ipos.json')));
  const retainedOld=retained.records.filter(r=>r.id!==ID);
  assert.deepEqual(baseline.records,retainedOld);
  writeRecovery(first.recovery);run('scripts/build-published-data.mjs');run('scripts/build-published-data.mjs',['--check']);
  run('scripts/validate-data.mjs');const data=readPublic();
  const good=audit({ctx,recovery:first.recovery,data,checkedAt:new Date().toISOString(),baseline});
  assert.equal(data.records.length,baseline.records.length+1);
  assert.equal(good.source_evidence_count,2);
  assert.equal(good.verified_fields,7);
  for(const mutate of [
    d=>d.records.find(r=>r.id===ID).issue_size_inr.evidence.pop(),
    d=>d.records.find(r=>r.id===ID).issue_size_inr.status='verified',
    d=>d.records.find(r=>r.id===ID).market_lot.value=98,
    d=>d.records.find(r=>r.id===ALIAS_ID).issue_price.value++,
    d=>d.records.find(r=>r.id===ID).status_evidence=[],
    d=>d.records.find(r=>r.id===ID).documents=[],
    d=>d.records.pop(), d=>d.records.push(d.records[0])
  ]) {const bad=structuredClone(data);mutate(bad);assert.throws(()=>audit({ctx,recovery:first.recovery,data:bad,checkedAt:now,baseline}));negative++;}
  const invalid=structuredClone(first.recovery);
  invalid['2022'].records.find(r=>r.id===ID).issue_size_inr.additional_sources[0].url='https://evil.test/x';
  writeRecovery(invalid);const bad=spawnSync(process.execPath,['scripts/build-published-data.mjs'],{cwd:temp,encoding:'utf8'});
  assert.notEqual(bad.status,0);assert.match(bad.stderr,/unsupported source host/);negative++;
  // Repeated identical sources do not create duplicate public evidence.
  const repeated=structuredClone(first.recovery);const f=repeated['2022'].records.find(r=>r.id===ID).issue_size_inr;
  f.additional_sources.push(structuredClone(f.additional_sources[0]));writeRecovery(repeated);run('scripts/build-published-data.mjs');
  assert.equal(readPublic().records.find(r=>r.id===ID).issue_size_inr.evidence.length,2);
  console.log(JSON.stringify({hariom_rainbow_tests:{new_issuers:1,existing_aliases:1,verified_fields:7,conflicting_fields:1,
    negative_cases:negative,original_records_unchanged:baseline.records.length,real_builder:true,read_only_check:true}}));
} finally {fs.rmSync(temp,{recursive:true,force:true});}
