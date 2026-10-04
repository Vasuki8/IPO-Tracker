import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL, fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {test} from 'node:test';
import {buildNewRecoveryRecord, enrichExistingRecord, mergeFeeds} from './sync-nse-live.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const clock = '2026-10-04T12:00:00Z';
const issue = (overrides = {}) => ({companyName:'Safety Example Limited', symbol:'SAFE', series:'EQ',
  status:'Forthcoming', issueStartDate:'05-Oct-2026', issueEndDate:'07-Oct-2026', issuePrice:'Rs.100', ...overrides});
const record = (overrides = {}) => ({...buildNewRecoveryRecord(issue(), clock), ...overrides});
const manifest = records => ({collection_started_at:clock, generated_at:clock, records});
const write = (p, value) => { fs.mkdirSync(path.dirname(p),{recursive:true}); fs.writeFileSync(p,JSON.stringify(value,null,2)+'\n'); };
async function isolated(manifests, callback) {
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'live-identity-safety-'));
  try {
    for (const name of ['sync-nse-live.mjs','ipo-instrument-policy.mjs','build-published-data.mjs','publish-field-status.mjs']) {
      const source=path.join(root,'scripts',name);
      if (fs.existsSync(source)) {fs.mkdirSync(path.join(dir,'scripts'),{recursive:true});fs.copyFileSync(source,path.join(dir,'scripts',name));}
    }
    fs.mkdirSync(path.join(dir,'assets'),{recursive:true});
    fs.copyFileSync(path.join(root,'assets/ipo-order.js'),path.join(dir,'assets/ipo-order.js'));
    for (const [year,data] of Object.entries(manifests)) write(path.join(dir,'data/recovery',year,'nse-issue-information.json'),data);
    const sync=await import(pathToFileURL(path.join(dir,'scripts/sync-nse-live.mjs')));
    await callback(dir,sync);
  } finally {fs.rmSync(dir,{recursive:true,force:true});}
}

// Removing eligibility checks must admit these non-equity / unknown observations.
test('live feed admits only the existing EQ and SME instrument families', () => {
  const rows=['EQ','SME','DEBT','N1','REIT','UNKNOWN','',null].map((series,i)=>issue({symbol:`S${i}`,companyName:`Safety ${i} Limited`,series}));
  assert.deepEqual(mergeFeeds(rows,[]).map(r=>r.series),['EQ','SME']);
  assert.equal(mergeFeeds([issue({series:' eq '})],[]).length,1);
  for (const series of ['DEBT','N1','UNKNOWN','',null]) assert.throws(()=>buildNewRecoveryRecord(issue({series}),clock),/ineligible.*instrument/);
  for (const flag of ['isDebtSec','isETFSec','isMunicipalBond','isHybridSymbol']) {
    assert.equal(mergeFeeds([issue({[flag]:true})],[]).length,0,flag);
    assert.equal(mergeFeeds([issue({[flag]:false})],[]).length,1,flag);
  }
});

test('an ineligible feed cannot mutate an existing equity record', () => {
  const r=record(),before=structuredClone(r);
  assert.throws(()=>enrichExistingRecord(r,issue({series:'DEBT',status:'Active'}),clock),/ineligible.*instrument/);
  assert.deepEqual(r,before);
});

for (const [label,change] of [
  ['same symbol, different legal issuer',{companyName:'Different Entity Limited'}],
  ['same legal issuer, different symbol',{symbol:'OTHER'}],
  ['same symbol/name, contradictory series',{series:'SME'}],
  ['missing legal issuer',{companyName:''}],
]) test(`identity rejection before mutation: ${label}`, () => {
  const r=record(),before=structuredClone(r);
  assert.throws(()=>enrichExistingRecord(r,issue({...change,status:'Active'}),clock),/identity|instrument/);
  assert.deepEqual(r,before);
});

test('feed combination cannot erase conflicting legal names under one symbol', () => {
  const first=issue(),second=issue({companyName:'Different Entity Limited',status:'Active'});
  const before=structuredClone([first,second]);
  assert.throws(()=>mergeFeeds([first],[second]),/identity/);
  assert.deepEqual([first,second],before);
});

test('cosmetic name/case changes are compatible but no fuzzy match is used', () => {
  const r=record({issuer_name:'Safety & Example Limited'});
  assert.equal(enrichExistingRecord(r,issue({companyName:' SAFETY AND EXAMPLE LIMITED ',symbol:' safe ',status:'Active'}),clock),true);
  assert.equal(r.issuer_name,'Safety & Example Limited');
  assert.equal(r.status,'open');
  assert.equal(enrichExistingRecord(r,issue({companyName:'SAFETY AND EXAMPLE LIMITED',status:'Active'}),clock),false);
});

test('symbol from retained NSE URL is checked when explicit identity is absent', () => {
  const r=record();delete r.nse_symbol;
  r.nse_source.url='https://www.nseindia.com/api/ipo-detail?symbol=OTHER&series=EQ';
  const before=structuredClone(r);
  assert.throws(()=>enrichExistingRecord(r,issue({status:'Active'}),clock),/identity/);
  assert.deepEqual(r,before);
});

test('matching name may fill a genuinely missing symbol without rewriting the name', () => {
  const r=record();delete r.nse_symbol;delete r.nse_series;
  r.nse_source=null;r.board=null;r.documents=[];
  assert.equal(enrichExistingRecord(r,issue({status:'Active'}),clock),true);
  assert.equal(r.nse_symbol,'SAFE');assert.equal(r.issuer_name,'Safety Example Limited');
});

test('all feed identities are checked before any year file is written', async () => {
  await isolated({'2025':manifest([{...buildNewRecoveryRecord(issue({companyName:'Earlier Limited',symbol:'EARLIER',issueStartDate:'05-Oct-2025'}),clock),id:'earlier'}]),'2026':manifest([record()])}, async (dir,{runSync}) => {
    const paths=['2025','2026'].map(y=>path.join(dir,'data/recovery',y,'nse-issue-information.json'));
    const before=paths.map(p=>fs.readFileSync(p));
    const fixture=path.join(dir,'feed.json');
    write(fixture,{upcoming:[issue({companyName:'Earlier Limited',symbol:'EARLIER',issueStartDate:'05-Oct-2025',status:'Active'}),issue({companyName:'Contradiction Limited',status:'Active'})],current:[]});
    await assert.rejects(runSync({fixturePath:fixture,now:clock}),/identity/);
    paths.forEach((p,i)=>assert.deepEqual(fs.readFileSync(p),before[i]));
  });
});

test('split symbol/name matches cannot choose one existing issuer arbitrarily', async () => {
  await isolated({'2026':manifest([record(),record({id:'second',issuer_name:'Second Limited',nse_symbol:'SECOND'})])}, async (dir,{runSync}) => {
    const p=path.join(dir,'data/recovery/2026/nse-issue-information.json'),before=fs.readFileSync(p),fixture=path.join(dir,'feed.json');
    write(fixture,{upcoming:[issue({companyName:'Second Limited',status:'Active'})]});
    await assert.rejects(runSync({fixturePath:fixture,now:clock}),/identity/);
    assert.deepEqual(fs.readFileSync(p),before);
  });
});

test('duplicate retained identity matches require review instead of last-wins', async () => {
  await isolated({'2026':manifest([record(),record({id:'duplicate'})])},async(dir,{runSync})=>{
    const fixture=path.join(dir,'feed.json');write(fixture,{upcoming:[issue({status:'Active'})]});
    await assert.rejects(runSync({fixturePath:fixture,now:clock}),/identity/);
  });
});

test('same legal name under different new symbols is rejected before insertion', async () => {
  await isolated({'2026':manifest([])}, async(dir,{runSync})=>{
    const fixture=path.join(dir,'feed.json');write(fixture,{upcoming:[issue(),issue({symbol:'SECOND'})]});
    await assert.rejects(runSync({fixturePath:fixture,now:clock}),/identity/);
    assert.deepEqual(JSON.parse(fs.readFileSync(path.join(dir,'data/recovery/2026/nse-issue-information.json'))).records,[]);
  });
});

test('cross-year identity collision is held for review without creating a duplicate', async () => {
  await isolated({'2025':manifest([record()])},async(dir,{runSync})=>{
    const fixture=path.join(dir,'feed.json');write(fixture,{upcoming:[issue({companyName:'Different Entity Limited'})]});
    await assert.rejects(runSync({fixturePath:fixture,now:clock}),/identity/);
    assert.equal(fs.existsSync(path.join(dir,'data/recovery/2026')),false);
  });
});

test('debt-only source is observable and cannot create an empty recovery manifest', async () => {
  await isolated({},async(dir,{runSync})=>{
    const fixture=path.join(dir,'feed.json');write(fixture,{upcoming:[issue({series:'DEBT'})]});
    const result=await runSync({fixturePath:fixture,now:clock});
    assert.equal(result.added,0);assert.equal(result.excluded.length,1);
    assert.equal(result.excluded[0].issue.series,'DEBT');
    assert.equal(fs.existsSync(path.join(dir,'data/recovery/2026')),false);
  });
});

test('mixed legitimate equities and debt: dry-run preservation, import and replay', async () => {
  await isolated({'2026':manifest([record()])},async(dir,{runSync})=>{
    const p=path.join(dir,'data/recovery/2026/nse-issue-information.json'),before=fs.readFileSync(p),fixture=path.join(dir,'feed.json');
    write(fixture,{upcoming:[issue({status:'Active'}),issue({companyName:'Second Limited',symbol:'SECOND',series:'SME'}),issue({companyName:'Debt Limited',symbol:'BOND',series:'DEBT'})]});
    const dry=await runSync({fixturePath:fixture,dryRun:true,now:clock});
    assert.deepEqual(fs.readFileSync(p),before);assert.equal(dry.added,1);
    const actual=await runSync({fixturePath:fixture,now:clock});assert.equal(actual.added,1);assert.equal(actual.enriched,1);assert.equal(actual.excluded.length,1);
    const bytes=fs.readFileSync(p);assert.equal(JSON.parse(bytes).records.length,2);
    const replay=await runSync({fixturePath:fixture,now:clock});assert.equal(replay.added,0);assert.equal(replay.enriched,0);assert.deepEqual(fs.readFileSync(p),bytes);
  });
});

test('public projection excludes debt while preserving all retained evidence and unknown-board equities', async () => {
  const debt={...record(),id:'debt',issuer_name:'Debt Limited',nse_series:'DEBT',board:null};
  const unknown={...record(),id:'unknown',issuer_name:'Unknown Board Limited',board:null};delete unknown.nse_series;unknown.nse_source.document_type='Reviewed official IPO source';
  await isolated({'2026':manifest([record(),debt,unknown])},async(dir)=>{
    const p=path.join(dir,'data/recovery/2026/nse-issue-information.json'),before=fs.readFileSync(p);
    const build=()=>execFileSync(process.execPath,['scripts/build-published-data.mjs'],{cwd:dir,encoding:'utf8'});
    build();const output=fs.readFileSync(path.join(dir,'data/ipos.json')),data=JSON.parse(output);
    assert.deepEqual(data.records.map(r=>r.id).sort(),['safety-example-limited','unknown']);
    assert.equal(data.generated_at,clock);assert.deepEqual(fs.readFileSync(p),before);
    build();assert.deepEqual(fs.readFileSync(path.join(dir,'data/ipos.json')),output);
    execFileSync(process.execPath,['scripts/build-published-data.mjs','--check'],{cwd:dir});
  });
});

test('retained NSE source-URL instrument evidence is checked without inventing a board', async () => {
  const {retainedRecordIneligibility} = await import('./ipo-instrument-policy.mjs');
  assert.ok(retainedRecordIneligibility({board:null,nse_source:{url:'https://www.nseindia.com/api/ipo-detail?series=DEBT&symbol=BOND',document_type:'NSE Issue Information'}}));
  assert.equal(retainedRecordIneligibility({board:null,nse_source:{url:'https://www.nseindia.com/api/ipo-detail?series=EQ&symbol=SAFE',document_type:'NSE Issue Information'}}),null);
  assert.equal(retainedRecordIneligibility({board:null,nse_source:{url:'https://www.bseindia.com/retained-equity-source',document_type:'BSE listing notice'}}),null);
});
