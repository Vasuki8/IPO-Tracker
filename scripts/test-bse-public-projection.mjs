import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { auditPublishedRelease, loadRelease, verifyLiveRelease } from './verify-bse-publication.mjs';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const manifests = [18, 19].map((n) => `data/verified-bse-listings/2026-09-24-batch${n}.json`);
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'bse-public-projection-'));
const output = fs.mkdtempSync(path.join(os.tmpdir(), 'bse-projection-receipt-'));
try {
  // Build actual public output. Recovery-only hashes must not be injected into fixtures.
  for (const name of ['scripts', 'data', 'ops', 'assets']) fs.cpSync(path.join(root, name), path.join(temp, name), { recursive: true });
  const run = (script) => execFileSync(process.execPath, [script], { cwd: temp, encoding: 'utf8' });
  run('scripts/apply-verified-bse-listings.mjs'); run('scripts/build-published-data.mjs');
  const dataPath = path.join(temp, 'data/ipos.json');
  const bytes = fs.readFileSync(dataPath);
  const cursorPath = path.join(temp, 'ops/bse-sme-addition-notices.json');
  const cursorBytes = fs.readFileSync(cursorPath);
  const report = await verifyLiveRelease({ root: temp, manifestPaths: manifests, outputDir: output,
    fetchImpl: async () => new Response(bytes) });
  assert.equal(report.status, 'verified', JSON.stringify(report));
  assert.equal(report.checked_issuers, 23); assert.equal(report.checked_fields, 69);
  assert.equal(report.document_hash_scope.retained_fields, 69);
  assert.equal(report.document_hash_scope.serialized_live_fields, 0);
  assert.deepEqual(fs.readFileSync(dataPath), bytes);
  assert.deepEqual(fs.readFileSync(cursorPath), cursorBytes);

  const recoveryByYear = Object.fromEntries(fs.readdirSync(path.join(temp, 'data/recovery'))
    .filter((y) => /^20\d{2}$/.test(y)).map((y) => [y, JSON.parse(fs.readFileSync(path.join(temp, 'data/recovery', y, 'nse-issue-information.json')))]));
  const fixture = { batches: loadRelease(temp, manifests), recoveryByYear, data: JSON.parse(bytes), checkedAt: new Date().toISOString() };
  const notice = fixture.batches[0].manifest.entries[0].listing_notice_no;
  const getRaw = (f) => f.recoveryByYear[2025].records.find((r) => r.bse_verified_listing_batch?.listing_notice_no === notice);
  const getLive = (f) => f.data.records.find((r) => r.id === getRaw(f).id);
  const cases = [
    (f) => delete getRaw(f).market_lot.source.document_sha256,
    (f) => getRaw(f).market_lot.source.document_sha256 = '0'.repeat(64),
    (f) => getRaw(f).market_lot.source_value = 'Unrelated source text',
    (f) => getLive(f).market_lot.evidence[0].document_sha256 = '0'.repeat(64),
    (f) => getLive(f).market_lot.evidence[0].document_sha256 = null,
    (f) => getLive(f).market_lot.evidence[0].document_type = 'BSE Index Notice',
    (f) => getLive(f).market_lot.corrections = [{ overwritten: 'history' }],
    (f) => getLive(f).open_date = { value: null, status: 'provisional', evidence: [] }
  ];
  for (const mutate of cases) {
    const changed = structuredClone(fixture); mutate(changed);
    assert.equal(auditPublishedRelease(changed).status, 'failed', mutate.toString());
  }
  const explicit = structuredClone(fixture);
  getLive(explicit).market_lot.evidence[0].document_sha256 = getRaw(explicit).market_lot.source.document_sha256;
  assert.equal(auditPublishedRelease(explicit).status, 'verified');
  assert.equal(auditPublishedRelease(explicit).document_hash_scope.serialized_live_fields, 1);
  console.log('Real publisher projection passed: 23 issuers / 69 fields; eight hash, type, history and null mutations rejected; files unchanged.');
} finally { fs.rmSync(temp, { recursive: true, force: true }); fs.rmSync(output, { recursive: true, force: true }); }

// BUG-004: an explicit retained null is a decision, not an absent legacy field.
// Reinstating value-based fallback or emptyField() for retained nulls must fail.
const nullTemp = fs.mkdtempSync(path.join(os.tmpdir(), 'retained-null-projection-'));
try {
  for (const name of ['scripts/build-published-data.mjs', 'scripts/publish-field-status.mjs', 'scripts/ipo-instrument-policy.mjs', 'assets/ipo-order.js']) {
    fs.mkdirSync(path.dirname(path.join(nullTemp, name)), {recursive:true});
    fs.copyFileSync(path.join(root, name), path.join(nullTemp, name));
  }
  const clock = '2026-10-04T12:00:00Z';
  const source = {url:'https://www.nseindia.com/retained-null-fixture',document_type:'NSE Issue Information',document_identity:'Retained null fixture',collected_at:clock};
  const correction = {recorded_at:clock,previous_value:'old observation',new_value:null,reason:'Unresolved official-source discrepancy'};
  const cleared = status => ({value:null,status,source,additional_sources:[{...source,url:'https://www.sebi.gov.in/retained-null-fixture'}],corrections:[correction]});
  const fallback = {price_band:{min:100,max:110},market_lot:100,minimum_bid_quantity:200,open_date:'2026-09-01',close_date:'2026-09-03'};
  const records = [];
  for (const [field, value] of Object.entries(fallback)) {
    for (const status of ['conflict','provisional','missing']) records.push({
      id:`${field}-${status}`,issuer_name:`${field} ${status}`,nse_source:source,
      terms:{[field]:value},[field]:cleared(status)
    });
    records.push({id:`${field}-absent`,issuer_name:`${field} absent`,nse_source:source,terms:{[field]:value}});
    records.push({id:`${field}-null`,issuer_name:`${field} null`,nse_source:source,terms:{[field]:value},[field]:null});
    records.push({id:`${field}-placeholder`,issuer_name:`${field} placeholder`,nse_source:source,terms:{[field]:value},[field]:{value:null}});
  }
  for (const field of ['issue_price','issue_size_inr','listing_date']) records.push({
    id:field,issuer_name:field,[field]:cleared('conflict')
  });
  records.push({id:'applications',issuer_name:'Applications',application_requirements:{
    retail:{minimum_bid_quantity:cleared('conflict'),minimum_application_amount_inr:cleared('conflict')}
  }});
  const manifestPath = path.join(nullTemp,'data/recovery/2026/nse-issue-information.json');
  fs.mkdirSync(path.dirname(manifestPath),{recursive:true});
  fs.writeFileSync(manifestPath,JSON.stringify({collection_started_at:clock,generated_at:clock,records}));
  execFileSync(process.execPath,['scripts/build-published-data.mjs'],{cwd:nullTemp});
  const outputPath = path.join(nullTemp,'data/ipos.json');
  const projected = JSON.parse(fs.readFileSync(outputPath)).records;
  const byId = new Map(projected.map(record=>[record.id,record]));
  function assertCleared(field,status) {
    assert.equal(field.value,null);
    assert.equal(field.status,status);
    assert.deepEqual(field.corrections,[correction]);
    assert.deepEqual(field.evidence.map(item=>item.url),[source.url,'https://www.sebi.gov.in/retained-null-fixture']);
  }
  for (const [field, value] of Object.entries(fallback)) {
    for (const status of ['conflict','provisional','missing']) assertCleared(byId.get(`${field}-${status}`)[field],status);
    assert.equal(byId.get(`${field}-absent`)[field].status,'verified');
    assert.deepEqual(byId.get(`${field}-absent`)[field].value,value);
    for (const suffix of ['null','placeholder']) assert.deepEqual(byId.get(`${field}-${suffix}`)[field],{value:null,status:'missing',evidence:[],corrections:[]});
  }
  for (const field of ['issue_price','issue_size_inr','listing_date']) assertCleared(byId.get(field)[field],'conflict');
  for (const field of Object.values(byId.get('applications').application_requirements.retail)) assertCleared(field,'conflict');
  const firstBytes = fs.readFileSync(outputPath);
  execFileSync(process.execPath,['scripts/build-published-data.mjs'],{cwd:nullTemp});
  assert.deepEqual(fs.readFileSync(outputPath),firstBytes,'null projection must be deterministic');
  console.log('Retained-null projection regressions passed: explicit decisions and source/correction histories survive all legacy fallbacks and nested requirements.');
} finally { fs.rmSync(nullTemp,{recursive:true,force:true}); }
