import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {reconcileRows,verifiedYearBlocks,run,PIN} from './reconcile-retained-bse-universe.mjs';
import {sha256,parseBseYearRows,parseBseYearSummary} from './audit-bse-issue-summary-coverage.mjs';
const time='2026-09-28T03:00:00Z',source='2026-09-26T16:40:00Z';
const sourceRows=[{issuer_name:'Alpha Limited',bse_scrip_code:'543100',source_row_index:0,listing_date:'2022-06-01',issue_price:10},{issuer_name:'Five-Star Business Finance Ltd.',bse_scrip_code:'543663',source_row_index:1,listing_date:'2022-11-21',issue_price:474},{issuer_name:'Not Reviewed Limited',bse_scrip_code:'543102',source_row_index:2,listing_date:'2022-09-01',issue_price:20}];
const recovery=[{year:2022,record:{id:'alpha',issuer_name:'Alpha Limited',listing_date:{value:'2022-06-01'}}},{year:2022,record:{id:'fivestar',issuer_name:'FiveStar Business Finance Limited',listing_date:{value:'2022-11-21'}}}];
const alias={year:2022,code:'543663',id:'fivestar',source_name:'Five-Star Business Finance Ltd.',retained_name:'FiveStar Business Finance Limited',approval_path:'data/discovery/bse-2022-unmatched-disposition-2026-09-27.json',disposition:'existing_recovery_alias'};
const fixture={yearBlocks:[{year:2022,total:3,rows:sourceRows}],recovery,aliases:[alias],reconciledAt:time,sourceCollectedAt:source};
const before=structuredClone(fixture),good=reconcileRows(fixture);
assert.deepEqual(fixture,before);assert.deepEqual(good.totals,{source_rows:3,recovery_records:2,exact_matches:1,reviewed_aliases:1,awaiting_review:1});assert.equal(good.source_refetched,false);assert.equal(good.full_indian_ipo_universe_complete,false);
const without=reconcileRows({...fixture,aliases:[]});assert.equal(without.totals.awaiting_review,2);assert.deepEqual(without.years[0].rows[1].candidate_hints,[{id:'fivestar',year:2022}]);
let negatives=0;for(const mutate of [x=>x.recovery.push(x.recovery[0]),x=>x.aliases.push(x.aliases[0]),x=>x.aliases[0].source_name='Another',x=>x.aliases[0].id='missing',x=>x.aliases[0].retained_name='wrong',x=>x.aliases[0].year=2023,x=>x.yearBlocks[0].total=9,x=>x.yearBlocks[0].rows[1].source_row_index=0,x=>x.reconciledAt='2020-01-01',x=>x.sourceCollectedAt='invalid']){const b=structuredClone(fixture);mutate(b);assert.throws(()=>reconcileRows(b));negatives++;}
for(const change of [x=>x.yearBlocks[0].rows[0].listing_date='2022-06-02',x=>x.recovery[0].year=2021,x=>x.yearBlocks[0].rows[0].bse_scrip_code=null,x=>x.yearBlocks[0].rows[2].bse_scrip_code='543100']){const b=structuredClone(fixture);change(b);const out=reconcileRows(b);assert.equal(out.years[0].rows[0].disposition,'awaiting_review');}
const empty=reconcileRows({...fixture,yearBlocks:[],aliases:[]});assert.equal(empty.totals.source_rows,0);
// Synthetic archive exercises byte checks and proves derived projections cannot be forged.
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'retained-universe-'));
try{
 fs.mkdirSync(path.join(dir,'raw'));const collection={schema_version:'2.0.0',completed_at:source,run_id:123,source_commit_sha:'a'.repeat(40),yearly:[]};
 const pin={workflow_run_id:123,source_commit_sha:'b'.repeat(40),generated_at:source,source_receipts:[]};
 for(const year of [2020,2021,2022,2023,2024,2025,2026]){
  const raw={Table:[{CompanyName:'Alpha Limited',IssuePrice:10,ListedOn:`${year}-06-01`,IMAGE:'https://www.bseindia.com/stock-share-price/alpha/ALPHA/543100/'}]};
  const tracker={Table:[{TotalIPO:1,NoOfIpo:1,NoOfSMEIpo:0,IPOWithPositiveListingGain:1,IPOWithListingLosses:0,IPOWithPositiveListingDayGains:1,IPOWithListingDayLosses:0}]};
  for(const [file,value]of [[`raw/ipo-year-${year}.json`,raw],[`raw/ipo-tracker-${year}.json`,tracker]]){const bytes=Buffer.from(JSON.stringify(value));fs.writeFileSync(path.join(dir,file),bytes);pin.source_receipts.push({file,bytes:bytes.length,sha256:sha256(bytes),collected_at:source});}
  collection.yearly.push({year,rows:parseBseYearRows(raw,year),summary:parseBseYearSummary(tracker,year)});
 }
 const cp=path.join(dir,'collection.json'),save=()=>fs.writeFileSync(cp,JSON.stringify(collection));save();assert.equal(verifiedYearBlocks({inputDir:dir,pin}).blocks.length,7);
 const initial=fs.readFileSync(cp);collection.yearly[0].rows[0].issuer_name='Forged';save();assert.throws(()=>verifiedYearBlocks({inputDir:dir,pin}),/projection/);negatives++;fs.writeFileSync(cp,initial);
 const file=path.join(dir,'raw/ipo-year-2020.json'),bytes=fs.readFileSync(file);fs.appendFileSync(file,' ');assert.throws(()=>verifiedYearBlocks({inputDir:dir,pin}),/hash/);negatives++;fs.writeFileSync(file,bytes);
 const unsafe=structuredClone(pin);unsafe.source_receipts[0].file='../outside';assert.throws(()=>verifiedYearBlocks({inputDir:dir,pin:unsafe}),/unsafe/);negatives++;
 const clock=JSON.parse(initial);clock.completed_at='2099-01-01T00:00:00Z';fs.writeFileSync(cp,JSON.stringify(clock));assert.throws(()=>verifiedYearBlocks({inputDir:dir,pin}),/clock/);negatives++;fs.writeFileSync(cp,initial);
 // File-backed run uses synthetic recovery and verifies only the requested report is written.
 fs.mkdirSync(path.join(dir,'repo/data/discovery'),{recursive:true});const root=path.join(dir,'repo');fs.writeFileSync(path.join(root,PIN),JSON.stringify(pin));
 fs.mkdirSync(path.join(root,'data/recovery/2022'),{recursive:true});fs.writeFileSync(path.join(root,'data/recovery/2022/nse-issue-information.json'),JSON.stringify({records:recovery.map(x=>x.record)}));
 for(const year of [2021,2022])fs.writeFileSync(path.join(root,`data/discovery/bse-${year}-unmatched-disposition-2026-09-27.json`),JSON.stringify({rows:[]}));
 const output=path.join(dir,'report.json'),result=run({inputDir:dir,output,root,reconciledAt:time});assert.equal(result.source_pin.source_commit_labels_disagree,true);assert.deepEqual(fs.readFileSync(cp),initial);assert.deepEqual(fs.readFileSync(file),bytes);
 for(const protectedFile of [file,cp,path.join(root,PIN),path.join(root,'data/ipos.json'),path.join(root,'data/recovery/2022/nse-issue-information.json')]){assert.throws(()=>run({inputDir:dir,output:protectedFile,root,reconciledAt:time}),/overwrites/);negatives++;}
}finally{fs.rmSync(dir,{recursive:true,force:true});}
console.log(JSON.stringify({retained_universe_tests:{negative_cases:negatives,explicit_alias_only:true,no_fuzzy_auto_import:true,raw_byte_binding:true,projection_tampering_rejected:true,source_clock_preserved:true,missing_codes_held:true,source_commit_disagreement_preserved:true,read_only:true}}));
