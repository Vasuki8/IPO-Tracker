import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { hash, loadReviewed, loadRecovery, validateReviewedBatch, applyReviewedBatch, projectDetail } from './apply-reviewed-nse-ipos.mjs';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const b = loadReviewed(root)[0], { manifest: m, queue: q } = b;
const checked = validateReviewedBatch(m, q);
assert.equal(checked.length, 14);
assert.equal(checked.reduce((n, c) => n + Object.keys(c.facts).length, 0), 83);
assert.equal(checked.filter(c => c.facts.market_lot).length, 9);
assert.equal(checked.filter(c => c.facts.minimum_bid_quantity).length, 5);
assert.equal(checked[0].facts.open_date.value, '2025-12-26');
assert.equal(checked[0].facts.listing_date.value, '2026-01-02');
assert.equal(checked[1].facts.price_band, undefined, 'fixed price is not an invented band');
assert.equal(checked.find(c => c.candidate.nse_symbol === 'ARMOUR').issuer_name, 'Armour Security (India) Limited');

const fullMonthPeriod = structuredClone(m);
const periodItem = fullMonthPeriod.entries[0].detail.issueInfo.dataList.find(i => i.title.toLowerCase() === 'issue period');
periodItem.value = '26-December-2025 to 30-December-2025';
fullMonthPeriod.entries[0].detail_source.projection_sha256 = hash(JSON.stringify(fullMonthPeriod.entries[0].detail));
assert.equal(validateReviewedBatch(fullMonthPeriod, q)[0].facts.open_date.value, '2025-12-26', 'full month issue-period names');
const invalidFullMonth = structuredClone(fullMonthPeriod);
invalidFullMonth.entries[0].detail.issueInfo.dataList.find(i => i.title.toLowerCase() === 'issue period').value = '26-Decembruary-2025 to 30-December-2025';
invalidFullMonth.entries[0].detail_source.projection_sha256 = hash(JSON.stringify(invalidFullMonth.entries[0].detail));
assert.throws(() => validateReviewedBatch(invalidFullMonth, q), 'unknown full month names fail closed');
const editItem = (e, name, value) => { e.detail.issueInfo.dataList.find(i => i.title.toLowerCase() === name).value = value; };
let rejected = 0;
function bad(mutator, rehash = true) {
  const copy = structuredClone(m); mutator(copy.entries[0], copy);
  if (rehash) for (const e of copy.entries) { e.detail_source.projection_sha256 = hash(JSON.stringify(e.detail)); e.past_source.projection_sha256 = hash(JSON.stringify(e.past_row)); }
  assert.throws(() => validateReviewedBatch(copy, q)); rejected++;
}
bad(e => { e.detail.metaInfo.symbol = 'OTHER'; });
bad(e => { e.detail.issueInfo.symbol = 'OTHER'; });
bad(e => editItem(e, 'symbol', 'OTHER'));
bad(e => { e.detail.companyName = 'Other Limited'; });
bad(e => { e.detail.metaInfo.companyName = 'Other Limited'; });
bad(e => { e.past_row.company = 'Other Limited'; });
bad(e => { e.detail.metaInfo.isin = 'IN9423A01048'; });
bad(e => { e.detail.metaInfo.isDebtSec = true; });
bad(e => { e.detail.metaInfo.segment = 'EQUITY'; });
bad(e => { e.past_row.securityType = 'EQ'; });
bad(e => editItem(e, 'issue size', 'Further Public Offer of 100 Equity Shares'));
bad(e => editItem(e, 'issue size', 'Rights issue of equity shares'));
bad(e => editItem(e, 'issue size', 'Initial Public Offer of debentures'));
bad(e => { e.detail.issueInfo.dataList = e.detail.issueInfo.dataList.filter(i => i.title !== 'Issue Size'); });
bad(e => { e.detail.issueInfo = { symbol: null, dataList: [] }; });
bad(e => { e.detail_source.http_status = 403; });
bad(e => { e.detail_source.collected_at = '2026-02-30T00:00:00Z'; });
bad(e => { e.detail_source.url = e.detail_source.url.replace('www.nseindia.com', 'www.nseindia.com.evil.example'); });
bad(e => { e.detail_source.final_url = e.detail_source.url + '&other=1'; });
bad(e => { e.detail_source.response_sha256 = 'bad'; });
bad(e => { e.detail.metaInfo.listingDate = '2026-02-30'; });
bad(e => { e.past_row.listingDate = '03-JAN-2026'; });
bad(e => { e.detail_source.collected_at = '2025-12-25T00:00:00Z'; });
bad(e => editItem(e, 'issue period', '26-Dec-2025 to 31-Feb-2026'));
bad(e => { editItem(e, 'issue period', '31-Nov-2025 to 30-Dec-2025'); e.past_row.ipoStartDate = '31-NOV-2025'; });
bad(e => { e.past_row.issuePrice = '164 to 174'; });
bad(e => { e.past_row.issuePrice = '0'; });
bad(e => { e.past_row.issuePrice = '999'; });
bad(e => editItem(e, 'lot size', 'pending'));
bad(e => { e.detail.issueInfo.dataList.push({ title: 'Lot Size', value: '1000' }); });
bad(e => { e.detail.issueInfo.dataList.push({ title: 'Issue Size', value: 'Rights issue' }); });
bad((e, a) => { a.entries.push(structuredClone(e)); });
bad((e, a) => { a.queue_sha256 = '0'.repeat(64); });
bad(e => { e.detail.companyName += 'X'; }, false);
const raw = loadRecovery(root), pub = JSON.parse(fs.readFileSync(path.join(root, 'data/ipos.json')));
const snapshot = JSON.stringify(raw), pubBefore = JSON.stringify(pub);
// Reconstruct the pre-release state so this remains a true addition test after publication.
for (const year of Object.values(raw)) year.records = year.records.filter(r => r.nse_verified_ipo_batch?.manifest !== b.manifest_path);
const prior = { ...pub, records: pub.records.filter(r => !checked.some(c => c.issuer_name === r.issuer_name)) };
const a = applyReviewedBatch(raw, prior, m, q, b.manifest_path);
assert.deepEqual(a.stats, { added: 14, already_present: 0 });
assert.equal(JSON.stringify(pub), pubBefore);
assert.equal(JSON.stringify(loadRecovery(root)), snapshot, 'no source file changed');
for (const [y, before] of Object.entries(raw)) for (const r of before.records) assert.deepEqual(a.recovery[y].records.find(n => n.id === r.id), r);
assert.deepEqual(applyReviewedBatch(a.recovery, prior, m, q, b.manifest_path).recovery, a.recovery);
assert.deepEqual(applyReviewedBatch(a.recovery, prior, m, q, b.manifest_path).stats, { added: 0, already_present: 14 });
const newRecord = a.recovery['2026'].records.find(r => r.nse_symbol === 'E2ERAIL');
for (const collision of [
  { id: 'different-id', issuer_name: newRecord.issuer_name },
  { id: 'different-id', issuer_name: 'Another Company', nse_symbol: 'e2erail' },
  { id: 'different-id', issuer_name: 'Another Company', isin: newRecord.isin },
  { id: 'different-id', issuer_name: 'Another Company', documents: [{ url: newRecord.nse_source.url }] }
]) {
  const input = structuredClone(raw); input['2021'].records.push(collision); const bytes = JSON.stringify(input);
  assert.throws(() => applyReviewedBatch(input, prior, m, q, b.manifest_path));
  assert.equal(JSON.stringify(input), bytes, 'collision planning must be read-only');
}
assert.throws(() => applyReviewedBatch(raw, {records: [newRecord]}, m, q, b.manifest_path));
const changed = structuredClone(a.recovery); changed['2026'].records.find(r => r.id === newRecord.id).market_lot.value = 1;
assert.throws(() => applyReviewedBatch(changed, prior, m, q, b.manifest_path));
const adani = JSON.parse(fs.readFileSync(path.join(root, 'scripts/fixtures/nse-universe-held-adani.json')));
assert.deepEqual(projectDetail(adani.detail), adani.detail);
const held = { ...structuredClone(m), entries: [adani] };
held.entries[0].decision = 'verified_initial_equity_ipo';
assert.throws(() => validateReviewedBatch(held, q), 'symbol metadata without IPO terms cannot authorize publication');
console.log(JSON.stringify({ reviewed_nse_tests: { issuers: 14, facts: 83, rejected_mutations: rejected, held_issuer_rejected: true, cross_year_collisions: 4, idempotent: true } }));

await import("./test-reviewed-nse-batch3.mjs");

await import("./test-reviewed-nse-batch4.mjs");

await import("./test-reviewed-nse-batch5.mjs");
