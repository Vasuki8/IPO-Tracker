import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { hash, loadReviewed, loadRecovery, validateReviewedBatch, applyReviewedBatch } from './apply-reviewed-nse-ipos.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const manifestPath = 'data/verified-nse-ipos/2026-09-25-batch4.json';
const batch = loadReviewed(root).find(b => b.manifest_path === manifestPath);
assert.ok(batch, 'pinned batch4 manifest is required');
const { manifest: m, queue: q } = batch, checked = validateReviewedBatch(m, q);
assert.equal(checked.length, 13);
assert.equal(checked.reduce((n, c) => n + Object.keys(c.facts).length, 0), 78);
assert.equal(checked.filter(c => c.facts.market_lot).length, 10);
assert.equal(checked.filter(c => c.facts.minimum_bid_quantity).length, 3);

const bmll = checked.find(c => c.candidate.nse_symbol === 'BMLL');
assert.match(bmll.offer, /^Initial Public Issue\b/i);
const genxai = checked.find(c => c.candidate.nse_symbol === 'GENXAI');
assert.match(genxai.offer, /^Intial Public offer\b/i);
const turtlemint = checked.find(c => c.candidate.nse_symbol === 'TURTLEMINT');
assert.deepEqual(turtlemint.facts.price_band.value, { min: 144, max: 152 });
assert.equal(turtlemint.facts.minimum_bid_quantity.value, 98);
assert.equal(turtlemint.facts.market_lot, undefined);
assert.equal(checked.find(c => c.candidate.nse_symbol === 'CLAYCRAFT').facts.open_date.value, '2026-06-17');

const review = JSON.parse(fs.readFileSync(path.join(root, 'data/discovery/nse-universe-batch4-review-2026-09-25.json')));
assert.equal(review.held.length, 2);
assert.equal(review.held.find(e => e.candidate.nse_symbol === 'QMSMEDI').decision, 'excluded_migration_not_new_ipo');
assert.equal(review.held.find(e => e.candidate.nse_symbol === '12VPT28A').decision, 'excluded_debt_security_not_initial_equity_ipo');
assert.equal(review.held.find(e => e.candidate.nse_symbol === '12VPT28A').detail.metaInfo.isDebtSec, true);

const rehash = e => { e.detail_source.projection_sha256 = hash(JSON.stringify(e.detail)); e.past_source.projection_sha256 = hash(JSON.stringify(e.past_row)); };
let rejected = 0;
function bad(symbol, mutate) {
  const copy = structuredClone(m), e = copy.entries.find(e => e.candidate.nse_symbol === symbol);
  mutate(e); rehash(e); assert.throws(() => validateReviewedBatch(copy, q)); rejected++;
}
bad('BMLL', e => { e.detail.issueInfo.dataList.find(i => i.title.trim().toLowerCase() === 'issue size').value = 'Initial Public Placement of 1,000 Equity Shares'; });
bad('GENXAI', e => { const i=e.detail.issueInfo.dataList.find(i => i.title.trim().toLowerCase() === 'issue size'); i.value=i.value.replace('Intial','Initail'); });
bad('TURTLEMINT', e => { e.detail.issueInfo.dataList.find(i => i.title.trim().toLowerCase() === 'price range').value = '144 to 152 per Equity Shares'; });
bad('TURTLEMINT', e => { e.past_row.issuePrice = '999'; });
bad('RFBL', e => { e.detail.metaInfo.isDebtSec = true; });
for (const held of review.held) {
  const copy = { ...structuredClone(m), entries: [{ ...structuredClone(held), decision: 'verified_initial_equity_ipo' }] };
  assert.throws(() => validateReviewedBatch(copy, q)); rejected++;
}

const raw = loadRecovery(root), rawBefore = JSON.stringify(raw), pub = JSON.parse(fs.readFileSync(path.join(root, 'data/ipos.json')));
const plan = applyReviewedBatch(raw, pub, m, q, manifestPath);
assert.deepEqual(plan.stats, { added: 13, already_present: 0 });
assert.equal(JSON.stringify(raw), rawBefore);
for (const [year, data] of Object.entries(raw)) for (const r of data.records) assert.deepEqual(plan.recovery[year].records.find(n => n.id === r.id), r);
assert.deepEqual(applyReviewedBatch(plan.recovery, pub, m, q, manifestPath).stats, { added: 0, already_present: 13 });

const first = checked[0], collision = structuredClone(raw);
collision['2021'].records.push({ id: 'prior-batch4-collision', issuer_name: 'Different Limited', nse_symbol: first.candidate.nse_symbol });
const collisionBefore = JSON.stringify(collision);
assert.throws(() => applyReviewedBatch(collision, pub, m, q, manifestPath));
assert.equal(JSON.stringify(collision), collisionBefore);
console.log(JSON.stringify({ reviewed_nse_batch4_tests: { issuers: 13, facts: 78, rejected_inputs: rejected, preservation: true, idempotent: true } }));
