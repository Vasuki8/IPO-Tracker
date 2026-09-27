// Bounded release gate: reuse the existing reviewed-BSE importer, never infer facts.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {applyVerifiedListings, validateEvidenceBatch} from './apply-verified-bse-listings.mjs';
import {sha256} from './verify-bse-listing-candidates.mjs';

export const ROOT = fileURLToPath(new URL('../', import.meta.url));
export const MANIFEST = 'data/verified-bse-listings/2026-09-27.json';
export const DISCOVERY = 'data/discovery/bse-listing-candidates-2026-09-27.json';
export const RECEIPT = 'data/evidence/bse-2021-sme-pair-source-receipt-2026-09-27.json';
const assert = (ok, message) => {if (!ok) throw new Error(message);};
export function loadPair(root = ROOT) {
  const bytes = fs.readFileSync(path.join(root, MANIFEST));
  const manifest = JSON.parse(bytes);
  const discovery = JSON.parse(fs.readFileSync(path.join(root, DISCOVERY)));
  const receipt = JSON.parse(fs.readFileSync(path.join(root, RECEIPT)));
  assert(receipt.schema_version === '1.0.0' && receipt.status === 'reviewed_original_notices' &&
    receipt.reviewed_manifest === MANIFEST && receipt.manifest_sha256 === sha256(bytes), 'unbound_pair_manifest');
  assert(manifest.discovery_batch === DISCOVERY && receipt.original_documents === 2 &&
    receipt.documents?.length === 2 && manifest.entries?.length === 2 &&
    receipt.workflow_run_id === manifest.source_run_id && receipt.artifact_id === manifest.source_artifact_id &&
    receipt.artifact_sha256 === manifest.source_artifact_sha256, 'unbound_pair_receipt');
  assert(manifest.entries.map(e => e.bse_scrip_code).sort().join(',') === '543284,543324', 'unexpected_pair_issuers');
  const documents = new Map(receipt.documents.map(d => [d.notice, d]));
  assert(documents.size === 2, 'duplicate_pair_receipt_document');
  for (const e of validateEvidenceBatch(manifest, discovery)) {
    const d = documents.get(e.listing_notice_no);
    assert(d && d.source_url === e.source_url && d.response_sha256 === e.document_sha256 &&
      d.collected_at === e.collected_at && d.http_status === 200 &&
      d.normalized_excerpt_sha256 === e.normalized_text_sha256 &&
      Number.isSafeInteger(d.response_bytes) && d.response_bytes > 0, 'pair_source_binding_mismatch');
  }
  assert(receipt.documents.reduce((n,d) => n + d.response_bytes, 0) === receipt.total_response_bytes, 'pair_receipt_byte_mismatch');
  return {manifest, discovery};
}
export function readRecovery(root = ROOT) {
  const dir = path.join(root, 'data/recovery');
  return Object.fromEntries(fs.readdirSync(dir).filter(y => /^20\d{2}$/.test(y))
    .map(y => [y, path.join(dir,y,'nse-issue-information.json')]).filter(([,f]) => fs.existsSync(f))
    .map(([y,f]) => [y,JSON.parse(fs.readFileSync(f))]));
}
export function planPair(recovery, pair) {
  const ids = Object.values(recovery).flatMap(m => m.records.map(r => r.id));
  assert(new Set(ids).size === ids.length, 'duplicate_existing_recovery_id');
  const result = applyVerifiedListings(recovery, pair.manifest, pair.discovery, MANIFEST);
  assert(result.holds.length === 0 && result.stats.held_existing === 0 && result.stats.held_identity_conflict === 0, 'pair_publication_held');
  assert(result.stats.added + result.stats.already_present === 2 && result.changed_years.every(y => y === 2021), 'unexpected_pair_scope');
  return result;
}
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  try {
    const args = process.argv.slice(2);
    assert(args.length === 1 && ['--check','--apply'].includes(args[0]), 'use_--check_or_--apply');
    const result = planPair(readRecovery(), loadPair());
    if (args[0] === '--apply' && result.changed_years.length) {
      const file = path.join(ROOT,'data/recovery/2021/nse-issue-information.json');
      fs.writeFileSync(file + '.tmp', JSON.stringify(result.recovery[2021],null,2) + '\n');
      fs.renameSync(file + '.tmp',file);
    }
    console.log(JSON.stringify({reviewed_bse_2021_sme_pair: result.stats, changed_years: result.changed_years}));
  } catch (e) {console.error(e.message); process.exitCode = 1;}
}
