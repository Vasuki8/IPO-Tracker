import assert from 'node:assert/strict';
import fs from 'node:fs';
import { applyApprovedBatches, loadApprovedBatches, validateApprovedPaths } from './apply-verified-bse-listings.mjs';

const batches = loadApprovedBatches();
assert.equal(batches.length, 2);
assert.equal(batches[0].manifest.entries.length, 15);
assert.equal(batches[1].manifest.entries.length, 12);
const base = { 2026: { generated_at: '2026-09-24T10:00:00Z', records: [
  { id: 'unrelated', issuer_name: 'Unrelated Limited', terms: { price_band: null }, corrections: [{ reason: 'keep' }] }
] } };
const before = structuredClone(base);
const first = applyApprovedBatches(base, batches);
assert.equal(first.stats.added, 27);
assert.deepEqual(base, before);
assert.equal(first.recovery[2026].generated_at, base[2026].generated_at);
for (const batch of batches) for (const entry of batch.manifest.entries) {
  const found = first.recovery[2026].records.find((r) => r.bse_scrip_code === entry.bse_scrip_code);
  assert.equal(found.bse_verified_listing_batch.manifest, batch.manifest_path);
  assert.equal(found.last_collected_at, entry.collected_at);
  assert.equal(found.bse_verified_listing_batch.verifier_version, batch.manifest.verifier_version);
  for (const field of ['listing_date', 'market_lot', 'issue_price']) assert.equal(found[field].value, entry.facts[field].value);
  assert.equal(found.terms.minimum_bid_quantity, null);
  assert.equal(found.terms.price_band, null);
  assert.equal(found.issue_size_inr, undefined);
}
const second = applyApprovedBatches(first.recovery, batches);
assert.equal(second.stats.added, 0); assert.equal(second.stats.already_present, 27);
assert.deepEqual(second.recovery, first.recovery); assert.deepEqual(second.changed_years, []);
const priorOnly = applyApprovedBatches(base, [batches[0]]);
const next = applyApprovedBatches(priorOnly.recovery, batches);
assert.equal(next.stats.added, 12); assert.equal(next.stats.already_present, 15);
for (const record of priorOnly.recovery[2026].records) assert.deepEqual(next.recovery[2026].records.find((r) => r.id === record.id), record);
const invalid = structuredClone(batches); invalid[1].manifest.entries[0].facts.issue_price.value++;
assert.throws(() => applyApprovedBatches(base, invalid)); assert.deepEqual(base, before);
assert.throws(() => applyApprovedBatches(base, [batches[0], batches[0]]), /cross_batch_identity_conflict/);
for (const pair of [
  { manifest: '../unexpected.json', discovery: 'unexpected.json' },
  { manifest: batches[0].manifest_path, discovery: batches[1].manifest.discovery_batch }
]) assert.throws(() => validateApprovedPaths({ schema_version: '1.0.0', batches: [pair] }));
const pair = { manifest: batches[0].manifest_path, discovery: batches[0].manifest.discovery_batch };
assert.throws(() => validateApprovedPaths({ schema_version: '1.0.0', batches: [pair, pair] }));
// Unknown future verifier versions are never accepted by accident.
const future = structuredClone(batches); future[1].manifest.verifier_version = '99.0.0';
assert.throws(() => applyApprovedBatches(base, future));
const crossCode = structuredClone(base); crossCode[2026].records[0].bse_scrip_code = '544807';
const protectedCode = applyApprovedBatches(crossCode, batches);
assert.equal(protectedCode.stats.held_identity_conflict, 1); assert.equal(protectedCode.stats.added, 26);
assert.deepEqual(protectedCode.recovery[2026].records.find((r) => r.id === 'unrelated'), crossCode[2026].records[0]);
console.log('Approved BSE batches: path binding, atomic validation, provenance, conflicts and idempotency passed.');
