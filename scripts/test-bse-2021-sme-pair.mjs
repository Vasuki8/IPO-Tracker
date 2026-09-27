import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {loadPair, readRecovery, planPair, MANIFEST, DISCOVERY, RECEIPT, ROOT} from './release-bse-2021-sme-pair.mjs';
import {auditPublishedRelease} from './verify-bse-publication.mjs';
const pair = loadPair(), current = readRecovery();
const codes = new Set(pair.manifest.entries.map(e => e.bse_scrip_code));
const before = structuredClone(current);
for (const m of Object.values(before)) m.records = m.records.filter(r => !codes.has(r.bse_scrip_code));
const frozen = JSON.stringify(before), first = planPair(before,pair);
assert.equal(JSON.stringify(before),frozen,'planner mutates no input');
assert.deepEqual(first.stats,{added:2,already_present:0,held_existing:0,held_identity_conflict:0});
assert.deepEqual(first.changed_years,[2021]);
for (const [year,m] of Object.entries(before)) {
  if (year !== '2021') assert.deepEqual(first.recovery[year],m);
  for (const r of m.records) assert.deepEqual(first.recovery[year].records.find(x => x.id === r.id),r);
}
const rerun = planPair(first.recovery,pair);
assert.deepEqual(rerun.recovery,first.recovery);
assert.equal(rerun.stats.already_present,2);
const rows = first.recovery[2021].records.filter(r => codes.has(r.bse_scrip_code));
for (const [code,price,lot,date] of [['543284',102,1200,'2021-04-07'],['543324',170,800,'2021-08-09']]) {
  const r = rows.find(r => r.bse_scrip_code === code);
  assert.equal(r.board,'SME'); assert.equal(r.status,'listed');
  assert.equal(r.issue_price.value,price); assert.equal(r.market_lot.value,lot); assert.equal(r.listing_date.value,date);
  for (const f of ['price_band','minimum_bid_quantity','open_date','close_date']) assert.equal(r.terms[f],null);
  assert.equal(r.issue_size_inr,undefined,'never calculate issue size from listed securities');
}
let negativeCases = 0;
const reject = fn => {assert.throws(fn); negativeCases++;};
for (const identity of [{issuer_name:rows[0].issuer_name},{bse_scrip_code:'543284'},{documents:[{url:rows[0].documents[0].url}]}]) {
  const r = structuredClone(before);r[2022].records.push({id:'collision-fixture',issuer_name:'Other',...identity});
  reject(() => planPair(r,pair));
}
const changed = structuredClone(first.recovery);
changed[2021].records.find(r => r.bse_scrip_code === '543284').issue_price.value++;
reject(() => planPair(changed,pair));
const duplicate = structuredClone(before);duplicate[2021].records.push(structuredClone(duplicate[2021].records[0]));
reject(() => planPair(duplicate,pair));
for (const edit of [
 p => p.manifest.entries[0].facts.issue_price.value++,
 p => p.manifest.entries[0].issuer_name='Unrelated Limited',
 p => p.manifest.entries[0].board='Mainboard',
 p => p.manifest.entries[0].source_url='https://evil.test/notice',
 p => p.manifest.entries[0].document_sha256='invalid',
 p => p.manifest.entries[0].facts.minimum_bid_quantity={value:1200},
]) {const p=structuredClone(pair);edit(p);reject(() => planPair(before,p));}
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'bse-pair-test-'));
try {
  for (const p of [MANIFEST,DISCOVERY,RECEIPT]) {fs.mkdirSync(path.dirname(path.join(dir,p)),{recursive:true});fs.copyFileSync(path.join(ROOT,p),path.join(dir,p));}
  const p=path.join(dir,RECEIPT), receipt=JSON.parse(fs.readFileSync(p));receipt.documents[0].response_sha256='0'.repeat(64);fs.writeFileSync(p,JSON.stringify(receipt));
  reject(() => loadPair(dir));
} finally {fs.rmSync(dir,{recursive:true,force:true});}
const evidence=s=>({url:s.url,document_type:s.document_type,document_identity:s.document_identity,publication_date:s.publication_date,page:null,collected_at:s.collected_at});
const missing=()=>({value:null,status:'missing',evidence:[],corrections:[]});
const publicRows=rows.map(r=>({id:r.id,issuer_name:r.issuer_name,board:r.board,status:r.status,
  board_evidence:r.board_evidence.map(evidence),status_evidence:r.status_evidence.map(evidence),documents:r.documents,
  first_observed_at:r.first_observed_at,last_collected_at:r.last_collected_at,
  ...Object.fromEntries(['listing_date','market_lot','issue_price'].map(f=>[f,{value:r[f].value,status:'verified',evidence:[evidence(r[f].source)],corrections:[]} ])),
  ...Object.fromEntries(['price_band','open_date','close_date','issue_size_inr','minimum_bid_quantity','minimum_application_amount_inr'].map(f=>[f,missing()]))}));
const data={schema_version:'1.2.0',generated_at:new Date().toISOString(),records:publicRows};
const audit=d=>auditPublishedRelease({batches:[{manifest_path:MANIFEST,...pair}],recoveryByYear:first.recovery,data:d,checkedAt:new Date().toISOString()});
assert.equal(audit(data).status,'verified');
for (const edit of [d=>d.records.pop(),d=>d.records[0].market_lot.value=1,d=>d.records[0].issue_price.evidence=[],d=>d.records[0].issue_size_inr.value=0]) {
 const d=structuredClone(data);edit(d);assert.equal(audit(d).status,'failed');negativeCases++;
}
const snapshot=fs.readFileSync(path.join(ROOT,'data/recovery/2021/nse-issue-information.json'));
const cli=spawnSync(process.execPath,['scripts/release-bse-2021-sme-pair.mjs','--check'],{cwd:ROOT,encoding:'utf8'});
assert.equal(cli.status,0,cli.stderr);assert.deepEqual(fs.readFileSync(path.join(ROOT,'data/recovery/2021/nse-issue-information.json')),snapshot);
console.log(JSON.stringify({bse_2021_sme_pair_tests:{issuers:2,fields:6,negative_cases:negativeCases,idempotent:true,nulls_preserved:true,unrelated_records_unchanged:true,publication_comparison:true}}));
