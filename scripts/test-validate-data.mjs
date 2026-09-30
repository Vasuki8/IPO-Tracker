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
  ];
  for (const [label, mutate] of invalidCases) {
    const data = structuredClone(fixture);
    const replacement = mutate(data);
    const result = run(replacement === null ? null : data);
    assert.notEqual(result.status, 0, label + " must fail validation");
    assert.match(result.stderr, /DATA CONTRACT ERROR:/, label + " must give a useful contract error");
    assert.doesNotMatch(result.stderr, /TypeError|ReferenceError/, label + " must not crash the validator");
  }
  const standardCorrection = structuredClone(fixture);
  standardCorrection.records[0].open_date.corrections = [{ recorded_at: "2026-09-30T00:00:00Z", previous_value: null, new_value: "2026-09-01", reason: "Official-source correction" }];
  const standard = run(standardCorrection);
  assert.equal(standard.status, 0, standard.stderr);
  console.log(`Published schema validation tests passed: ${invalidCases.length} malformed datasets rejected, current correction histories and standard corrections preserved.`);
} finally {
  fs.rmSync(temp, { recursive: true, force: true });
}
