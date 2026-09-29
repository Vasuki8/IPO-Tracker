import assert from 'node:assert/strict';
import fs from 'node:fs';

const retired = new URL('../.github/workflows/publish-reviewed-bse-2020-unmatched.yml', import.meta.url);
assert.equal(fs.existsSync(retired), false, 'completed BSE 2020 workflow must remain retired');

const consolidated = new URL('../.github/workflows/validate-completed-releases.yml', import.meta.url);
const text = fs.readFileSync(consolidated, 'utf8');
assert.match(text, /contents:\s*read\b/);
assert.doesNotMatch(text, /contents:\s*write\b/);
for (const command of [
  'scripts/test-bse-2020-unmatched-review.mjs',
  'scripts/test-reviewed-bse-2020-unmatched-import.mjs',
  'scripts/test-completed-bse-2020-workflow.mjs',
  'node scripts/build-published-data.mjs --check',
  'node scripts/validate-data.mjs'
]) assert.ok(text.includes(command), `required consolidated check missing: ${command}`);

console.log(JSON.stringify({completed_bse_2020_workflow: {
  retired_entry_point: true,
  consolidated_read_only_validation: true,
  production_replay_removed: true
}}));
