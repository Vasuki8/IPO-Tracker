import assert from "node:assert/strict";
import fs from "node:fs";
import { test } from "node:test";

const read = name => fs.readFileSync(new URL(`../.github/workflows/${name}`, import.meta.url), "utf8");
const pages = read("deploy-pages.yml");

test("successful source writers trigger Pages without needing a token-generated push", () => {
  assert.match(pages, /workflow_run:\s*\n\s+workflows:/);
  for (const name of ["Sync live IPO data", "Sync Pre-IPO draft sources", "Backfill historical IPO offer dates", "Backfill historical IPO PDF fields"]) {
    assert.ok(pages.includes(`- "${name}"`), `missing writer: ${name}`);
  }
  assert.match(pages, /types: \[completed\]/);
  assert.match(pages, /branches: \[main\]/);
});

test("privileged deployment rejects failed, foreign repository and PR workflow runs", () => {
  assert.ok(pages.includes("github.event.workflow_run.conclusion == 'success'"));
  assert.ok(pages.includes("github.event.workflow_run.head_repository.full_name == github.repository"));
  assert.ok(pages.includes('contains(fromJSON(\'["push","schedule","workflow_dispatch"]\'), github.event.workflow_run.event)'));
  assert.ok(pages.includes("github.ref == 'refs/heads/main'"));
  assert.match(pages, /uses: actions\/checkout@v4\s*\n\s+with:\s*\n\s+ref: main/);
  assert.doesNotMatch(pages, /(?:token:\s*\$\{\{\s*secrets\.|download-artifact)/);
});

test("skipped upstream runs cannot cancel an active trusted deployment", () => {
  assert.doesNotMatch(pages, /^concurrency:/m, "workflow-level cancellation runs before the trusted job guard");
  assert.match(pages, /^    concurrency:\s*\n\s+group: pages\s*\n\s+cancel-in-progress: true/m, "only an eligible deployment job may join the shared cancellation group");
});

test("health receives the immutable uploaded commit and served verification result", () => {
  assert.ok(pages.includes('git rev-parse HEAD'));
  assert.ok(pages.includes('PAGES_DEPLOY_COMMIT_SHA: ${{ steps.revision.outputs.sha }}'));
  assert.ok(pages.includes('PAGES_VERIFY_OUTCOME: ${{ steps.verify.outcome }}'));
  assert.match(pages, /name: Verify served IPO dataset matches this deployment\s*\n\s+id: verify/);
});

test("DRHP live verification follows deployment so it cannot block its own workflow_run trigger", () => {
  assert.doesNotMatch(read("update-drhp.yml"), /node scripts\/verify-drhp-publication\.mjs --output-dir=/);
  assert.ok(pages.indexOf('node scripts/verify-drhp-publication.mjs --output-dir=') > pages.indexOf('uses: actions/deploy-pages@v4'));
  assert.match(pages, /uses: actions\/upload-artifact@v4/);
  assert.ok(read("update-drhp.yml").includes('published-data.json'));
});

test("BSE PR checks have separate concurrency from production cursor publication", () => {
  const bse = read("backfill-bse-sme-addition-notices.yml");
  assert.ok(bse.includes("github.event_name == 'pull_request'"));
  assert.match(bse, /group:.*github\.event\.pull_request\.number/);
  assert.match(bse, /group:.*'production'/);
});
