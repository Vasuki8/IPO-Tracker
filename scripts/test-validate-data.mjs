import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const root = fileURLToPath(new URL("../", import.meta.url));
const temp = fs.mkdtempSync(path.join(os.tmpdir(), "ipo-validation-"));
const published = JSON.parse(fs.readFileSync(path.join(root, "data/ipos.json")));
const fixture = { ...published, records: [published.records[0]] };
try {
  fs.mkdirSync(path.join(temp, "scripts"));
  fs.mkdirSync(path.join(temp, "data"));
  fs.copyFileSync(path.join(root, "scripts/validate-data.mjs"), path.join(temp, "scripts/validate-data.mjs"));
  fs.copyFileSync(path.join(root, "data/ipo-schema.json"), path.join(temp, "data/ipo-schema.json"));
  function run(data) {
    fs.writeFileSync(path.join(temp, "data/ipos.json"), JSON.stringify(data));
    return spawnSync(process.execPath, ["scripts/validate-data.mjs"], { cwd: temp, encoding: "utf8" });
  }
  const good = run(published);
  assert.equal(good.status, 0, good.stderr);

  const invalidCases = [
    ["missing documents", data => { delete data.records[0].documents; }],
    ["unknown board", data => { data.records[0].board = "invalid-board"; }],
    ["missing field value", data => { delete data.records[0].open_date.value; }],
    ["empty verified evidence", data => { data.records[0].issue_price = { value: 100, status: "verified", evidence: [{}], corrections: [] }; }],
    ["wrong documents type", data => { data.records[0].documents = {}; }],
    ["incomplete document", data => { data.records[0].documents = [{ type: "Prospectus" }]; }],
    ["unexpected record property", data => { data.records[0].unreviewed = true; }],
    ["malformed timestamp", data => { data.generated_at = "yesterday"; }],
    ["malformed evidence date", data => { data.records[0].status_evidence[0].publication_date = "2026-02-30"; }],
    ["wrong page type", data => { data.records[0].status_evidence[0].page = {}; }],
    ["empty issuer", data => { data.records[0].issuer_name = ""; }],
    ["empty correction", data => { data.records[0].open_date.corrections = [{}]; }],
    ["duplicate issuer ID", data => { data.records.push(structuredClone(data.records[0])); }],
    ["non-array records", data => { data.records = {}; }],
    ["null record", data => { data.records = [null]; }],
    ["null dataset", () => null],
    ["missing verified value", data => { data.records[0].issue_price = { status: "verified", evidence: [data.records[0].status_evidence[0]], corrections: [] }; }],
    ["record clock predates status evidence", data => {
      data.records[0].last_collected_at = "2026-10-04T00:00:00Z";
      data.records[0].status_evidence[0].collected_at = "2026-10-05T00:00:00Z";
    }],
    ["record clock predates document evidence", data => {
      data.records[0].last_collected_at = "2026-10-04T00:00:00Z";
      data.records[0].documents[0].collected_at = "2026-10-05T00:00:00Z";
    }],
  ];
  for (const [label, mutate] of invalidCases) {
    const data = structuredClone(fixture);
    const replacement = mutate(data);
    const result = run(replacement === null ? null : data);
    assert.notEqual(result.status, 0, label + " must fail validation");
    assert.match(result.stderr, /DATA CONTRACT ERROR:/, label + " must give a useful contract error");
    assert.doesNotMatch(result.stderr, /TypeError|ReferenceError/, label + " must not crash the validator");
  }
  const equalEvidenceClock = structuredClone(fixture);
  equalEvidenceClock.records[0].last_collected_at = "2099-01-01T00:00:00Z";
  equalEvidenceClock.records[0].status_evidence[0].collected_at = "2099-01-01T00:00:00Z";
  const equalClock = run(equalEvidenceClock);
  assert.equal(equalClock.status, 0, "record clock equal to latest attached evidence is valid: " + equalClock.stderr);

  const standardCorrection = structuredClone(fixture);
  standardCorrection.records[0].open_date.corrections = [{ recorded_at: "2026-09-30T00:00:00Z", previous_value: null, new_value: "2026-09-01", reason: "Official-source correction" }];
  const standard = run(standardCorrection);
  assert.equal(standard.status, 0, standard.stderr);

  // BUG-002: validate domain values, not only the evidence-bearing envelope.
  // Removing typed schema constraints or chronology checks must fail these cases.
  const observed = value => ({value,status:"verified",evidence:[structuredClone(fixture.records[0].status_evidence[0])],corrections:[]});
  const domainCases = [];
  for (const name of ["issue_price","issue_size_inr","minimum_application_amount_inr"]) {
    for (const value of ["100",-1,0,true,{},[]]) domainCases.push([`${name} ${JSON.stringify(value)}`, record => {record[name]=observed(value);}]);
  }
  for (const name of ["market_lot","minimum_bid_quantity"]) {
    for (const value of ["100",-5,0,1.5,9007199254740992,true,{}]) domainCases.push([`${name} ${JSON.stringify(value)}`,record=>{record[name]=observed(value);}]);
  }
  for (const value of [{min:110,max:100},{min:0,max:100},{min:"100",max:110},{min:100},{min:100,max:110,extra:1},[100,110],100]) {
    domainCases.push([`price_band ${JSON.stringify(value)}`,record=>{record.price_band=observed(value);}]);
  }
  for (const name of ["open_date","close_date","listing_date"]) {
    for (const value of ["2026-02-30","2026-13-01","2026-01-01T00:00:00Z",20260101,{},[]]) domainCases.push([`${name} ${JSON.stringify(value)}`,record=>{record[name]=observed(value);}]);
  }
  for (const category of ["retail","non_institutional","anchor_investor"]) {
    domainCases.push([`${category} negative amount`,record=>{record.application_requirements[category].minimum_application_amount_inr=observed(-1);}]);
    domainCases.push([`${category} fractional shares`,record=>{record.application_requirements[category].minimum_bid_quantity=observed(1.5);}]);
  }
  domainCases.push(["closing before opening",record=>{record.open_date=observed("2026-10-07");record.close_date=observed("2026-10-05");}]);
  domainCases.push(["listing before closing",record=>{record.open_date=observed("2026-10-01");record.close_date=observed("2026-10-07");record.listing_date=observed("2026-10-05");}]);
  domainCases.push(["listing before opening with missing close",record=>{record.open_date=observed("2026-10-07");record.close_date={value:null,status:"missing",evidence:[],corrections:[]};record.listing_date=observed("2026-10-05");}]);
  const domainFailures = [];
  for (const [label, mutate] of domainCases) {
    const data = structuredClone(fixture); mutate(data.records[0]);
    const result = run(data);
    if (result.status===0) domainFailures.push(label);
    else {
      assert.match(result.stderr,/DATA CONTRACT ERROR:/,label);
      assert.doesNotMatch(result.stderr,/TypeError|ReferenceError/,label);
    }
  }
  assert.deepEqual(domainFailures,[],"invalid domain values must be rejected");
  const validCases = [
    ["fractional INR",record=>{record.issue_price=observed(10.25);record.issue_size_inr=observed(1000000.5);} ],
    ["equal positive band endpoints",record=>{record.price_band=observed({min:10.25,max:10.25});}],
    ["explicitly labelled date conflict",record=>{record.open_date=observed("2026-10-07");record.close_date={...observed("2026-10-05"),status:"conflict"};}],
    ["cleared conflict keeps history",record=>{record.close_date={value:null,status:"conflict",evidence:observed(1).evidence,corrections:[{recorded_at:"2026-10-04T12:00:00Z",previous_value:"invalid original text",new_value:null,reason:"Under review"}]};}],
    ["zero or invalid source text may remain in correction history",record=>{record.issue_price={...observed(10.25),corrections:[{recorded_at:"2026-10-04T12:00:00Z",previous_value:-100,new_value:10.25,reason:"Corrected source basis"}]};}],
  ];
  for (const [label, mutate] of validCases) {
    const data=structuredClone(fixture); mutate(data.records[0]);
    const result=run(data); assert.equal(result.status,0,label+": "+result.stderr);
  }
  console.log(`Domain validation regressions passed: ${domainCases.length} invalid cases rejected, ${validCases.length} legitimate fractional/null/conflict/history cases retained.`);
  console.log(`Published schema validation tests passed: ${invalidCases.length} malformed datasets rejected, current correction histories and standard corrections preserved.`);
} finally {
  fs.rmSync(temp, { recursive: true, force: true });
}
