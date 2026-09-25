import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { hash, loadReviewed, loadRecovery, validateReviewedBatch, applyReviewedBatch, reviewedRecord } from './apply-reviewed-nse-ipos.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const manifestPath = 'data/verified-nse-ipos/2026-09-25-batch5.json';
const batch = loadReviewed(root).find(b => b.manifest_path === manifestPath);
assert.ok(batch, 'pinned batch5 manifest is required');
const { manifest: m, queue: q } = batch, checked = validateReviewedBatch(m, q);
assert.equal(checked.length, 15);
assert.equal(checked.reduce((n, c) => n + Object.keys(c.facts).length, 0), 89);
assert.equal(checked.filter(c => c.facts.market_lot).length, 6);
assert.equal(checked.filter(c => c.facts.minimum_bid_quantity).length, 9);
const teja = checked.find(c => c.candidate.nse_symbol === 'TEJA');
assert.equal(teja.facts.issue_price.value, 220);
assert.equal(teja.facts.price_band, undefined, 'fixed price is not an inferred range');
assert.equal(teja.facts.market_lot.value, 600);
assert.equal(teja.facts.minimum_bid_quantity, undefined);
const vmobile = checked.find(c => c.candidate.nse_symbol === 'VMOBILE');
assert.equal(vmobile.facts.open_date.value, '2026-06-30');
assert.equal(vmobile.facts.close_date.value, '2026-07-02');
assert.deepEqual(vmobile.facts.price_band.value, { min: 150, max: 158 });
assert.equal(vmobile.facts.market_lot.value, 800);
const sbi = checked.find(c => c.candidate.nse_symbol === 'SBIFUNDS');
assert.equal(sbi.facts.minimum_bid_quantity.value, 26);
assert.equal(sbi.facts.market_lot, undefined, 'Bid Lot is not market lot');
const expected = checked.map((c, i) => reviewedRecord(m.entries[i], c, m, manifestPath));
for (const r of expected) {
  assert.equal(r.issue_size_inr?.value ?? null, null);
  assert.equal(r.minimum_application_amount_inr?.value ?? null, null);
  assert.equal(r.status, 'listed');
  assert.ok(r.status_evidence.length > 0);
}
const review = JSON.parse(fs.readFileSync(path.join(root, 'data/discovery/nse-universe-batch5-review-2026-09-25.json')));
assert.equal(review.held.length, 0);
assert.equal(review.stats.verified_initial_equity_ipos, 15);
const item = (e, title) => e.detail.issueInfo.dataList.find(i => i.title.trim().toLowerCase() === title);
let rejected = 0;
function bad(symbol, mutate) {
  const copy = structuredClone(m), e = copy.entries.find(e => e.candidate.nse_symbol === symbol);
  mutate(e);
  e.detail_source.projection_sha256 = hash(JSON.stringify(e.detail));
  e.past_source.projection_sha256 = hash(JSON.stringify(e.past_row));
  assert.throws(() => validateReviewedBatch(copy, q)); rejected++;
}
bad('TEJA', e => { item(e, 'issue type').value = '100 % Book Building'; });
bad('TEJA', e => { e.past_row.issuePrice = '221'; });
bad('TEJA', e => { item(e, 'issue size').value = 'Further Public Offer of Equity Shares'; });
bad('TEJA', e => { e.detail.metaInfo.isDebtSec = true; });
bad('TEJA', e => { e.detail.metaInfo.isin = null; });
bad('TEJA', e => { e.detail.companyName = 'Other Limited'; });
bad('VMOBILE', e => { item(e, 'issue period').value = '30-June-2026 to 32-July-2026'; });
bad('VMOBILE', e => { e.past_row.ipoEndDate = '03-JUL-2026'; });
bad('VMOBILE', e => { item(e, 'price range').value = '150 to 158 per Equity Share'; });
bad('VMOBILE', e => { e.detail.issueInfo.dataList.push({ title: 'Lot Size', value: '400 Equity Shares' }); });
bad('SBIFUNDS', e => { item(e, 'minimum order quantity').value = '27 Equity Shares'; });
bad('SBIFUNDS', e => { e.detail.metaInfo.symbol = 'SBIN'; });
bad('SBIFUNDS', e => { e.detail_source.collected_at = '2026-07-01T00:00:00Z'; });
bad('SBIFUNDS', e => { e.detail_source.http_status = 403; });

// Always reconstruct pre-release copies: the tests must pass before and after
// publication, without deleting/mutating the actual recovery or public files.
const raw = loadRecovery(root), original = JSON.stringify(raw);
const publicBytes = fs.readFileSync(path.join(root, 'data/ipos.json')), pub = JSON.parse(publicBytes);
const before = structuredClone(raw), ids = new Set(expected.map(r => r.id));
for (const year of Object.values(before)) year.records = year.records.filter(r => r.nse_verified_ipo_batch?.manifest !== manifestPath);
const beforeBytes = JSON.stringify(before), prior = { ...pub, records: pub.records.filter(r => !ids.has(r.id)) };
const plan = applyReviewedBatch(before, prior, m, q, manifestPath);
assert.deepEqual(plan.stats, { added: 15, already_present: 0 });
assert.equal(JSON.stringify(before), beforeBytes, 'pure planning did not mutate input');
for (const [year, data] of Object.entries(before)) for (const r of data.records) assert.deepEqual(plan.recovery[year].records.find(n => n.id === r.id), r);
const rerun = applyReviewedBatch(plan.recovery, prior, m, q, manifestPath);
assert.deepEqual(rerun.stats, { added: 0, already_present: 15 });
assert.deepEqual(rerun.recovery, plan.recovery);
const present = { ...prior, records: [...prior.records, ...expected] };
assert.deepEqual(applyReviewedBatch(plan.recovery, present, m, q, manifestPath).stats, { added: 0, already_present: 15 });
for (const duplicate of [
  { id: 'old-issuer', issuer_name: expected[0].issuer_name },
  { id: 'old-issuer', issuer_name: 'Other Limited', nse_symbol: expected[0].nse_symbol },
  { id: 'old-issuer', issuer_name: 'Other Limited', isin: expected[0].isin },
  { id: 'old-issuer', issuer_name: 'Other Limited', documents: [{ url: expected[0].nse_source.url }] }
]) {
  const collision = structuredClone(before); collision['2021'].records.push(duplicate);
  const snapshot = JSON.stringify(collision);
  assert.throws(() => applyReviewedBatch(collision, prior, m, q, manifestPath));
  assert.equal(JSON.stringify(collision), snapshot);
}
const corrupted = structuredClone(plan.recovery);
corrupted['2026'].records.find(r => r.id === expected[0].id).issue_price.value = 1;
assert.throws(() => applyReviewedBatch(corrupted, present, m, q, manifestPath));
assert.equal(JSON.stringify(loadRecovery(root)), original, 'committed recovery unchanged');
assert.deepEqual(fs.readFileSync(path.join(root, 'data/ipos.json')), publicBytes, 'committed publication unchanged');
console.log(JSON.stringify({ reviewed_nse_batch5_tests: { issuers: 15, facts: 89, rejected_mutations: rejected, cross_year_collisions: 4, before_and_after_publication: true, fixed_price_not_band: true, idempotent: true, read_only: true } }));
