import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { buildBseOnlyRecoveryRecord } from "./extract-bse-ipo-fields.mjs";
import { issuerKey, strictDate, validateBatch, VERIFIER_VERSION } from "./verify-bse-listing-candidates.mjs";
import { archiveProbeUrl, verifyListingPdfText } from "./retry-bse-listing-pdf.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const MANIFEST = "data/verified-bse-listings/2026-09-24.json";
const REGISTRY = "data/verified-bse-listings/approved-batches.json";
// Earlier reviewed evidence is revalidated by the current parser, not relabeled.
const COMPATIBLE_VERSIONS = new Set(["1.1.0", VERIFIER_VERSION]);
const FIELDS = ["listing_date", "market_lot", "issue_price"];
const hashValid = (value) => typeof value === "string" && /^[a-f0-9]{64}$/.test(value);
const stampValid = (value) => typeof value === "string" && /^\d{4}-\d{2}-\d{2}T[\d:.]+Z$/.test(value) && Number.isFinite(Date.parse(value));
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

// This importer accepts only a reviewed, committed evidence batch. It never
// discovers URLs, downloads data, or upgrades an index candidate on its own.
export function validateEvidenceBatch(manifest, discovery) {
  const candidates = validateBatch(discovery);
  if (manifest?.schema_version !== "1.0.0" || !COMPATIBLE_VERSIONS.has(manifest.verifier_version) ||
      !hashValid(manifest.source_artifact_sha256) || !/^\d+$/.test(manifest.source_run_id) ||
      !Number.isSafeInteger(manifest.source_artifact_id) || !Array.isArray(manifest.entries) ||
      manifest.entries.length < 1 || manifest.entries.length > 15) throw new Error("invalid_verified_evidence_batch");
  const seen = new Set();
  for (const entry of manifest.entries) {
    const candidate = candidates.find((c) => c.listing_notice_no === entry.listing_notice_no);
    if (!candidate || seen.has(entry.listing_notice_no)) throw new Error("unrecognized_or_duplicate_listing_notice");
    seen.add(entry.listing_notice_no);
    if (entry.source_url !== archiveProbeUrl(entry.listing_notice_no) || !hashValid(entry.document_sha256) ||
        !stampValid(entry.collected_at) || strictDate(entry.publication_date) !== entry.publication_date ||
        entry.document_identity !== "BSE Listing Notice " + entry.listing_notice_no ||
        issuerKey(entry.issuer_name) !== issuerKey(candidate.issuer_name) ||
        entry.bse_scrip_code !== candidate.bse_scrip_code || entry.board !== "SME" ||
        !same(Object.keys(entry.facts || {}).sort(), [...FIELDS].sort())) throw new Error("invalid_listing_evidence");
    if (!Array.isArray(entry.excerpt_pages) || entry.excerpt_pages.length < 1 || entry.excerpt_pages.length > 3 ||
        entry.excerpt_pages.some((p, i) => p.page !== i + 1 || typeof p.text !== "string" || !p.text || p.text.length > 10000)) {
      throw new Error("invalid_page_excerpts");
    }
    const checked = verifyListingPdfText(entry.excerpt_pages.map((p) => p.text).join("\f"), candidate, entry.collected_at);
    if (checked.status !== "verified" || !same(checked.facts, entry.facts) ||
        !same(checked.identity_pages, entry.identity_pages) ||
        checked.observed_identity.publication_date !== entry.publication_date ||
        entry.publication_date > entry.facts.listing_date.value ||
        Object.values(entry.identity_pages).some((p) => !Number.isSafeInteger(p) || p < 1)) {
      throw new Error("listing_evidence_revalidation_failed");
    }
  }
  return manifest.entries;
}

function recoveryRecord(entry, manifest, manifestPath) {
  const collectedAt = entry.collected_at;
  const year = Number(entry.facts.listing_date.value.slice(0, 4));
  const record = buildBseOnlyRecoveryRecord({
    kind: "listing_notice", materialize_if_missing: true, year,
    issuer_name: entry.issuer_name, url: entry.source_url, publication_date: entry.publication_date
  }, {
    company: entry.issuer_name, board: "SME", listing_date_raw: entry.facts.listing_date.value,
    market_lot: entry.facts.market_lot.value, issue_price: entry.facts.issue_price.value
  }, collectedAt);
  if (!record) throw new Error("listing_record_factory_rejected_evidence");
  const source = {
    url: entry.source_url, document_type: "BSE Listing Notice PDF",
    document_identity: entry.document_identity, document_sha256: entry.document_sha256,
    publication_date: entry.publication_date, collected_at: collectedAt
  };
  record.bse_source = source;
  record.bse_scrip_code = entry.bse_scrip_code;
  record.board_evidence = [{ ...source, page: entry.identity_pages.board }];
  record.status_evidence = [{ ...source, page: entry.facts.listing_date.page }];
  record.documents = [{ type: source.document_type, identity: source.document_identity, url: source.url,
    publication_date: source.publication_date, collected_at: collectedAt, document_sha256: entry.document_sha256 }];
  for (const field of FIELDS) record[field] = {
    value: entry.facts[field].value, source_value: entry.facts[field].source_value,
    status: "verified", page: entry.facts[field].page, source: { ...source }, corrections: []
  };
  record.bse_verified_listing_batch = {
    manifest: manifestPath, verifier_version: manifest.verifier_version,
    source_run_id: manifest.source_run_id, source_artifact_id: manifest.source_artifact_id,
    source_artifact_sha256: manifest.source_artifact_sha256, listing_notice_no: entry.listing_notice_no
  };
  return { year, record };
}

export function applyVerifiedListings(recoveryByYear, manifest, discovery, manifestPath = MANIFEST) {
  // Validate the entire batch before making even an in-memory modification.
  const entries = validateEvidenceBatch(manifest, discovery);
  const recovery = structuredClone(recoveryByYear);
  const stats = { added: 0, already_present: 0, held_existing: 0, held_identity_conflict: 0 };
  const holds = [], changedYears = new Set();
  for (const entry of entries) {
    const { year, record } = recoveryRecord(entry, manifest, manifestPath);
    const matches = Object.entries(recovery).flatMap(([y, m]) => (m.records || []).filter((r) =>
      r.id === record.id || issuerKey(r.issuer_name) === issuerKey(record.issuer_name) ||
      String(r.bse_scrip_code || "") === entry.bse_scrip_code ||
      (r.documents || []).some((d) => d.url === entry.source_url)
    ).map((r) => ({ year: Number(y), record: r })));
    if (matches.length) {
      const existing = matches.length === 1 ? matches[0].record : null;
      const sameIdentity = existing && matches[0].year === year &&
        issuerKey(existing.issuer_name) === issuerKey(entry.issuer_name) &&
        (!existing.bse_scrip_code || existing.bse_scrip_code === entry.bse_scrip_code);
      if (!sameIdentity) {
        stats.held_identity_conflict += 1; holds.push({ notice: entry.listing_notice_no, reason: "existing_identity_conflict" });
      } else if (existing.bse_verified_listing_batch?.listing_notice_no === entry.listing_notice_no &&
          FIELDS.every((f) => existing[f]?.value === entry.facts[f].value &&
            existing[f]?.source?.document_sha256 === entry.document_sha256)) stats.already_present += 1;
      else { stats.held_existing += 1; holds.push({ notice: entry.listing_notice_no, reason: "existing_record_not_overwritten" }); }
      continue;
    }
    recovery[year] ||= { source_family: "Official NSE / SEBI / BSE offer-document and exchange evidence",
      collection_started_at: entry.collected_at, generated_at: entry.collected_at, records: [] };
    recovery[year].records.push(record);
    if (!Number.isFinite(Date.parse(recovery[year].generated_at)) ||
        Date.parse(entry.collected_at) > Date.parse(recovery[year].generated_at)) recovery[year].generated_at = entry.collected_at;
    stats.added += 1; changedYears.add(year);
  }
  for (const year of changedYears) recovery[year].records.sort((a, b) => a.issuer_name.localeCompare(b.issuer_name));
  return { recovery, stats, holds, changed_years: [...changedYears] };
}

// Approved registry paths are paired and bounded; no filesystem scan can promote
// an unreviewed manifest. Validate every batch before any recovery file is written.
export function validateApprovedPaths(registry) {
  if (registry?.schema_version !== "1.0.0" || !Array.isArray(registry.batches) ||
      !registry.batches.length || registry.batches.length > 100) throw new Error("invalid_approved_batch_registry");
  const seen = new Set();
  for (const pair of registry.batches) {
    const suffix = typeof pair?.manifest === "string" && pair.manifest.match(/^data\/verified-bse-listings\/(20\d{2}-\d{2}-\d{2}(?:-batch-\d{2})?)\.json$/)?.[1];
    if (!suffix || pair.discovery !== "data/discovery/bse-listing-candidates-" + suffix + ".json" ||
        seen.has(pair.manifest)) throw new Error("unapproved_or_duplicate_batch_path");
    seen.add(pair.manifest);
  }
  return registry.batches;
}
export function loadApprovedBatches(root = ROOT) {
  const registry = JSON.parse(fs.readFileSync(path.join(root, REGISTRY), "utf8"));
  return validateApprovedPaths(registry).map((pair) => {
    const manifest = JSON.parse(fs.readFileSync(path.join(root, pair.manifest), "utf8"));
    if (manifest.discovery_batch !== pair.discovery) throw new Error("unapproved_discovery_batch_path");
    return { manifest_path: pair.manifest, manifest,
      discovery: JSON.parse(fs.readFileSync(path.join(root, pair.discovery), "utf8")) };
  });
}
export function applyApprovedBatches(recoveryByYear, batches) {
  const codes = new Set(), names = new Set(), notices = new Set();
  for (const batch of batches) {
    validateApprovedPaths({ schema_version: "1.0.0", batches: [{ manifest: batch.manifest_path, discovery: batch.manifest.discovery_batch }] });
    for (const entry of validateEvidenceBatch(batch.manifest, batch.discovery)) {
      if (codes.has(entry.bse_scrip_code) || names.has(issuerKey(entry.issuer_name)) || notices.has(entry.listing_notice_no)) {
        throw new Error("cross_batch_identity_conflict");
      }
      codes.add(entry.bse_scrip_code); names.add(issuerKey(entry.issuer_name)); notices.add(entry.listing_notice_no);
    }
  }
  let recovery = recoveryByYear;
  const stats = { added: 0, already_present: 0, held_existing: 0, held_identity_conflict: 0 };
  const changedYears = new Set(), holds = [];
  for (const batch of batches) {
    const result = applyVerifiedListings(recovery, batch.manifest, batch.discovery, batch.manifest_path);
    recovery = result.recovery;
    for (const key of Object.keys(stats)) stats[key] += result.stats[key];
    for (const year of result.changed_years) changedYears.add(year);
    holds.push(...result.holds);
  }
  return { recovery, stats, holds, changed_years: [...changedYears] };
}
function run() {
  if (process.argv.slice(2).some((arg) => arg !== "--check")) throw new Error("only --check is supported");
  const batches = loadApprovedBatches();
  if (process.argv.includes("--check")) {
    const checked = applyApprovedBatches({}, batches);
    console.log(JSON.stringify({ approved_bse_batches: batches.length, verified_bse_evidence_entries: checked.stats.added })); return;
  }
  const recoveryRoot = path.join(ROOT, "data", "recovery");
  const recovery = {};
  for (const y of fs.readdirSync(recoveryRoot).filter((name) => /^20\d{2}$/.test(name))) {
    const file = path.join(recoveryRoot, y, "nse-issue-information.json");
    if (fs.existsSync(file)) recovery[y] = JSON.parse(fs.readFileSync(file, "utf8"));
  }
  const applied = applyApprovedBatches(recovery, batches);
  for (const year of applied.changed_years) {
    const dir = path.join(recoveryRoot, String(year)); fs.mkdirSync(dir, { recursive: true });
    const file = path.join(dir, "nse-issue-information.json");
    fs.writeFileSync(file + ".tmp", JSON.stringify(applied.recovery[year], null, 2) + "\n"); fs.renameSync(file + ".tmp", file);
  }
  console.log(JSON.stringify({ verified_bse_listing_import: applied.stats, holds: applied.holds }, null, 2));
}
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) run();
