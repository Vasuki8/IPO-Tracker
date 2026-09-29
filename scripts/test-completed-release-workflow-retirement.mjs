import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const WORKFLOWS = path.join(ROOT, ".github", "workflows");

const retired = [
  "materialize-bse-2020-unmatched-evidence.yml",
  "materialize-bse-2021-mainboard-batch1-evidence.yml",
  "materialize-bse-audit-conflict-evidence.yml",
  "materialize-fabino-listing-evidence.yml",
  "materialize-historical-ipo-evidence.yml",
  "publish-bse-2021-sme-pair.yml",
  "publish-reviewed-bse-2021-batch2-nureca.yml",
  "publish-reviewed-bse-2021-batch3-paras.yml",
  "publish-reviewed-bse-2021-final-pair.yml",
  "publish-reviewed-bse-2021-getalong-svrl.yml",
  "publish-reviewed-bse-2021-hp-nuvoco.yml",
  "publish-reviewed-bse-2021-jetmall-brandbucket.yml",
  "publish-reviewed-bse-2021-mainboard-batch1.yml",
  "publish-reviewed-bse-2022-eighty-virtuoso.yml",
  "publish-reviewed-bse-2022-final-pair.yml",
  "publish-reviewed-bse-2022-hariom-rainbow.yml",
  "publish-reviewed-bse-2022-maagh-technopack.yml",
  "publish-reviewed-bse-2022-maruti-olatech.yml",
  "publish-reviewed-bse-2022-pace-gargi.yml",
  "publish-reviewed-bse-2022-tmb-dcx.yml",
  "publish-reviewed-bse-2022-veranda-uma.yml",
  "publish-reviewed-bse-2023-four.yml",
  "publish-reviewed-bse-2023-rvpe.yml",
  "publish-reviewed-bse-reconciliation.yml",
  "publish-reviewed-fabino.yml",
  "publish-reviewed-historical-ipos.yml",
  "publish-reviewed-bse-2020-unmatched.yml",
  "verify-reviewed-bse-reconciliation-publication.yml",
  "verify-reviewed-fabino-publication.yml",
  "verify-reviewed-historical-ipo-publication.yml"
];
const allowedWriters = new Set([
  "backfill-bse-sme-addition-notices.yml",
  "backfill-historical-offer-dates.yml",
  "backfill-historical-pdf-fields.yml",
  "deploy-pages.yml",
  "update-drhp.yml",
  "update-ipos.yml"
]);

for (const file of retired) {
  assert.equal(fs.existsSync(path.join(WORKFLOWS, file)), false, "retired workflow reintroduced: " + file);
}

const files = fs.readdirSync(WORKFLOWS).filter((file) => /\.ya?ml$/i.test(file));
const observedWriters = [];
for (const file of files) {
  const text = fs.readFileSync(path.join(WORKFLOWS, file), "utf8");
  const contentsWrite = /(^|\n)\s*contents:\s*write\s*($|\n)/m.test(text);
  const directMainPush = /git\s+push[^\n]*(?:HEAD:main|refs\/heads\/main|\sorigin\s+main\b)/m.test(text);
  if (contentsWrite || directMainPush) {
    observedWriters.push(file);
    assert.ok(allowedWriters.has(file), "unexpected workflow with production write capability: " + file);
  }
}

for (const file of allowedWriters) {
  assert.ok(files.includes(file), "approved active writer is missing: " + file);
  assert.ok(observedWriters.includes(file), "approved active writer no longer writes; remove it from the allowlist: " + file);
}


console.log(JSON.stringify({
  retired_workflows: retired.length,
  active_write_workflows: [...allowedWriters].sort(),
  workflow_files_checked: files.length
}));
