import assert from 'node:assert/strict';
import fs from 'node:fs';

const file = new URL('../.github/workflows/publish-reviewed-bse-2020-unmatched.yml', import.meta.url);
const text = fs.readFileSync(file, 'utf8');
// This release is complete. Production may now have legitimate enrichment;
// run the isolated historical lifecycle test, never replay the old importer.
assert.match(text, /contents:\s*read\b/, 'completed release must have read-only contents permission');
assert.doesNotMatch(text, /contents:\s*write\b/);
assert.doesNotMatch(text, /(?:^|\n)\s*(?:node scripts\/apply-reviewed-bse-2020-unmatched\.mjs|git (?:push|commit|reset|add)\b)/);
for (const command of [
  'node scripts/test-bse-2020-unmatched-review.mjs',
  'node scripts/test-reviewed-bse-2020-unmatched-import.mjs',
  'node scripts/test-completed-bse-2020-workflow.mjs',
  'node scripts/build-published-data.mjs --check',
  'node scripts/validate-data.mjs',
  'git diff --exit-code'
]) assert.ok(text.includes(command), `required read-only check missing: ${command}`);
assert.match(text, /timeout-minutes:\s*5\b/);
console.log(JSON.stringify({completed_bse_2020_workflow: {read_only: true, production_replay_removed: true, isolated_lifecycle_retained: true}}));
