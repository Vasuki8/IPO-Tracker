import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { validateHistoricalEvidenceReceipt } from "./materialize-historical-ipo-evidence.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const REVIEW_PATH = "data/discovery/excluded-event-issuer-historical-ipo-review-2026-09-26.json";
export const RECEIPT_PATH = "data/evidence/historical-ipo-nine-source-receipt-2026-09-26.json";
export const MANIFEST_PATH = "data/verified-historical-ipos/2026-09-26-nine.json";
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");
const PUBLISHED_PATH = path.join(ROOT, "data", "ipos.json");

const PUBLICATION_HOSTS = new Set([
  "www.nseindia.com", "nseindia.com", "nsearchives.nseindia.com",
  "www.sebi.gov.in", "sebi.gov.in", "www.bseindia.com", "bseindia.com",
  "www.heromotors.com", "heromotors.com"
]);
const FIELD_PROJECTION_KEYS = {
  open_date: "offer_open",
  close_date: "offer_close",
  listing_date: "listing_date",
  issue_price: "issue_price_inr",
  market_lot: "market_lot",
  minimum_bid_quantity: "minimum_bid_quantity"
};

const norm = (value) => String(value ?? "").replace(/\s+/g, " ").trim();
const slug = (value) => norm(value).toLowerCase().replace(/&/g, " and ").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const issuerKey = (value) => norm(value).toLowerCase().replace(/&/g," and ").replace(/\bltd\.?\b/g," limited ")
  .replace(/[^a-z0-9]+/g," ").replace(/\blimited\s*$/g,"").replace(/\s+/g," ").trim();
const equal = (a,b) => JSON.stringify(a) === JSON.stringify(b);
const requireThat = (condition, reason) => { if (!condition) throw new Error(reason); };
const validDate = (value) => typeof value === "string" && /^\d{4}-\d\d-\d\d$/.test(value) &&
  Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0,10) === value;
const validIsin = (value) => typeof value === "string" && /^IN[A-Z0-9]{10}$/.test(value);
const readJson = (relative) => JSON.parse(fs.readFileSync(path.join(ROOT, relative), "utf8"));

function publicationSafeUrl(value) {
  try {
    const url = new URL(String(value));
    return url.protocol === "https:" && !url.username && !url.password && PUBLICATION_HOSTS.has(url.hostname) ? url.href : null;
  } catch {
    return null;
  }
}

function sourceMaps(review, receipt) {
  return {
    review: new Map(review.sources.map(source => [source.key, source])),
    receipt: new Map(receipt.documents.map(doc => [doc.key, doc]))
  };
}

function checkedSource(key, issuerName, maps, { publicationSafe = false } = {}) {
  const reviewSource = maps.review.get(key), receiptDoc = maps.receipt.get(key);
  requireThat(reviewSource && receiptDoc, "missing_historical_source:" + key);
  requireThat(receiptDoc.source_url === reviewSource.url && receiptDoc.projection_sha256 === reviewSource.projection_sha256,
    "historical_source_receipt_mismatch:" + key);
  requireThat(issuerKey(reviewSource.projection?.issuer) === issuerKey(issuerName), "historical_source_issuer_mismatch:" + key);
  if (publicationSafe) requireThat(publicationSafeUrl(reviewSource.url), "unsupported_publication_source_host:" + key);
  return { reviewSource, receiptDoc };
}

function descriptor(key, issuerName, maps) {
  const { reviewSource, receiptDoc } = checkedSource(key, issuerName, maps, { publicationSafe: true });
  return {
    url: reviewSource.url,
    document_type: reviewSource.document_type,
    document_identity: issuerName + " — " + reviewSource.document_type + " [" + key + "]",
    publication_date: reviewSource.publication_date ?? null,
    page: reviewSource.page ?? null,
    collected_at: receiptDoc.collected_at,
    document_sha256: receiptDoc.response_sha256,
    evidence_locator: reviewSource.evidence_locator ?? null
  };
}

function field(value, key, issuerName, maps) {
  const source = descriptor(key, issuerName, maps);
  return { value, source_value: value, status: "verified", page: source.page ?? null, source, corrections: [] };
}

function expectedHistoricalField(hist, fieldName) {
  if (fieldName === "issue_price") return hist.issue_price_inr;
  return hist[fieldName];
}

function validateFieldSource(hist, fieldName, sourceKey, issuerName, maps) {
  requireThat(Object.hasOwn(FIELD_PROJECTION_KEYS, fieldName), "unsupported_historical_field:" + fieldName);
  const { reviewSource } = checkedSource(sourceKey, issuerName, maps, { publicationSafe: true });
  const projectionKey = FIELD_PROJECTION_KEYS[fieldName];
  const expected = expectedHistoricalField(hist, fieldName);
  requireThat(expected !== undefined && expected !== null, "missing_reviewed_historical_value:" + fieldName + ":" + hist.nse_symbol);
  requireThat(equal(reviewSource.projection?.[projectionKey], expected),
    "historical_field_projection_mismatch:" + fieldName + ":" + hist.nse_symbol);
}

export function validateHistoricalImportManifest(manifest, review, receipt, reviewBytes) {
  validateHistoricalEvidenceReceipt(receipt, review, reviewBytes);
  requireThat(manifest?.schema_version === "1.0.0" && manifest.importer_version === "1.0.0" &&
    manifest.status === "approved_historical_equity_ipos_for_recovery_import" &&
    manifest.review_path === REVIEW_PATH && manifest.receipt_path === RECEIPT_PATH &&
    Array.isArray(manifest.entries) && manifest.entries.length === 9, "invalid_historical_import_manifest");
  requireThat(receipt.workflow_artifact?.artifact_id && /^sha256:[a-f0-9]{64}$/.test(receipt.workflow_artifact?.artifact_digest || ""),
    "historical_source_artifact_missing");

  const decisions = new Map(review.decisions.map(decision => [decision.excluded_event_symbol, decision]));
  const maps = sourceMaps(review, receipt);
  const seenExcluded = new Set(), seenSymbols = new Set(), seenIsins = new Set();

  return manifest.entries.map(entry => {
    requireThat(!seenExcluded.has(entry.excluded_event_symbol) && !seenSymbols.has(entry.historical_symbol),
      "duplicate_historical_import_identity");
    seenExcluded.add(entry.excluded_event_symbol); seenSymbols.add(entry.historical_symbol);

    const decision = decisions.get(entry.excluded_event_symbol);
    requireThat(decision?.decision === "historical_initial_equity_ipo_verified_import_pending", "unapproved_historical_ipo");
    const hist = decision.historical_equity;
    requireThat(hist?.nse_symbol === entry.historical_symbol && hist.board === "SME" && validIsin(hist.isin) &&
      validDate(hist.listing_date) && !seenIsins.has(hist.isin), "invalid_historical_equity_identity");
    seenIsins.add(hist.isin);

    const identity = checkedSource(entry.identity_source, decision.issuer_name, maps, { publicationSafe: true }).reviewSource.projection;
    requireThat(identity.symbol === hist.nse_symbol && identity.isin === hist.isin, "historical_identity_projection_mismatch:" + hist.nse_symbol);
    const listing = checkedSource(entry.listing_source, decision.issuer_name, maps, { publicationSafe: true }).reviewSource.projection;
    requireThat(listing.listing_date === hist.listing_date, "historical_listing_projection_mismatch:" + hist.nse_symbol);
    checkedSource(entry.offer_source, decision.issuer_name, maps);

    requireThat(entry.field_sources && typeof entry.field_sources === "object" && entry.field_sources.listing_date === entry.listing_source,
      "historical_listing_source_not_mapped:" + hist.nse_symbol);
    for (const [fieldName, sourceKey] of Object.entries(entry.field_sources)) {
      validateFieldSource(hist, fieldName, sourceKey, decision.issuer_name, maps);
    }
    return { entry, decision, hist, maps };
  });
}

export function historicalRecoveryRecord(checked, manifest, receipt) {
  const { entry, decision, hist, maps } = checked;
  const issuer = decision.issuer_name;
  const listingSource = descriptor(entry.listing_source, issuer, maps);
  const identitySource = descriptor(entry.identity_source, issuer, maps);
  const selectedSourceKeys = [...new Set([
    entry.identity_source, entry.listing_source,
    ...Object.values(entry.field_sources)
  ])];
  const documents = selectedSourceKeys.map(key => {
    const source = descriptor(key, issuer, maps);
    return {
      type: source.document_type,
      identity: source.document_identity,
      url: source.url,
      publication_date: source.publication_date,
      collected_at: source.collected_at,
      document_sha256: source.document_sha256,
      ...(source.page == null ? {} : { page: source.page })
    };
  });

  const record = {
    id: slug(issuer),
    issuer_name: issuer,
    board: "SME",
    sector: null,
    status: "listed",
    nse_symbol: hist.nse_symbol,
    nse_series: "SME",
    isin: hist.isin,
    nse_source: { ...listingSource },
    terms: { price_band:null, market_lot:null, minimum_bid_quantity:null, open_date:null, close_date:null },
    documents,
    first_observed_at: receipt.collection_completed_at,
    last_collected_at: receipt.collection_completed_at,
    board_evidence: [{ ...identitySource }],
    status_evidence: [{ ...listingSource }],
    historical_verified_ipo_review: {
      manifest: MANIFEST_PATH,
      review: REVIEW_PATH,
      receipt: RECEIPT_PATH,
      importer_version: manifest.importer_version,
      excluded_event_symbol: entry.excluded_event_symbol,
      workflow_run_id: receipt.workflow_run_id,
      artifact_id: receipt.workflow_artifact.artifact_id,
      artifact_digest: receipt.workflow_artifact.artifact_digest,
      source_hashes: Object.fromEntries([...new Set([entry.offer_source, ...selectedSourceKeys])].map(key => [
        key, checkedSource(key, issuer, maps).receiptDoc.response_sha256
      ]))
    }
  };

  for (const [fieldName, sourceKey] of Object.entries(entry.field_sources)) {
    const value = expectedHistoricalField(hist, fieldName);
    record[fieldName] = field(value, sourceKey, issuer, maps);
  }
  return record;
}

function matchesRecovery(record, candidate) {
  return record?.id === candidate.id ||
    issuerKey(record?.issuer_name) === issuerKey(candidate.issuer_name) ||
    norm(record?.nse_symbol).toUpperCase() === candidate.nse_symbol ||
    norm(record?.isin).toUpperCase() === candidate.isin;
}
function matchesPublished(record, candidate) {
  return record?.id === candidate.id || issuerKey(record?.issuer_name) === issuerKey(candidate.issuer_name);
}

export function applyReviewedHistoricalIpos(recoveryByYear, published, manifest, review, receipt, reviewBytes) {
  const checked = validateHistoricalImportManifest(manifest, review, receipt, reviewBytes);
  const recovery = structuredClone(recoveryByYear);
  const stats = { added:0, already_present:0, already_present_external:0 };
  const changedYears = new Set();

  for (const item of checked) {
    const candidate = historicalRecoveryRecord(item, manifest, receipt);
    const year = candidate.listing_date.value.slice(0,4);
    requireThat(recovery[year]?.records && Array.isArray(recovery[year].records), "missing_historical_recovery_year:" + year);

    const rawHits = Object.entries(recovery).flatMap(([y, data]) =>
      data.records.filter(record => matchesRecovery(record, candidate)).map(record => ({year:y, record}))
    );
    const publicHits = (published.records || []).filter(record => matchesPublished(record, candidate));

    if (rawHits.length) {
      requireThat(rawHits.length === 1 && rawHits[0].year === year, "historical_recovery_identity_collision:" + candidate.nse_symbol);
      const existing = rawHits[0].record;
      requireThat(existing.id === candidate.id && issuerKey(existing.issuer_name) === issuerKey(candidate.issuer_name) &&
        norm(existing.nse_symbol).toUpperCase() === candidate.nse_symbol && norm(existing.isin).toUpperCase() === candidate.isin &&
        existing.board === "SME" && existing.status === "listed" && existing.listing_date?.value === candidate.listing_date.value,
        "historical_existing_record_conflict:" + candidate.nse_symbol);
      requireThat(publicHits.length <= 1 && publicHits.every(record => record.id === candidate.id),
        "historical_published_identity_conflict:" + candidate.nse_symbol);
      if (existing.historical_verified_ipo_review?.manifest === MANIFEST_PATH) stats.already_present++;
      else stats.already_present_external++;
      continue;
    }

    requireThat(publicHits.length === 0, "historical_published_without_recovery:" + candidate.nse_symbol);
    recovery[year].records.push(candidate);
    recovery[year].records.sort((a,b)=>a.issuer_name.localeCompare(b.issuer_name));
    recovery[year].generated_at = [recovery[year].generated_at, receipt.collection_completed_at].filter(Boolean).sort().at(-1);
    changedYears.add(year);
    stats.added++;
  }

  return { recovery, stats, changed_years:[...changedYears].sort() };
}

export function loadRecovery(root = ROOT) {
  return Object.fromEntries(Array.from({length:7},(_,i)=>String(2020+i)).map(year => [
    year, JSON.parse(fs.readFileSync(path.join(root,"data","recovery",year,"nse-issue-information.json"),"utf8"))
  ]));
}

function loadInputs(root = ROOT) {
  const reviewFile = path.join(root, REVIEW_PATH);
  const reviewBytes = fs.readFileSync(reviewFile);
  return {
    reviewBytes,
    review: JSON.parse(reviewBytes),
    receipt: JSON.parse(fs.readFileSync(path.join(root, RECEIPT_PATH),"utf8")),
    manifest: JSON.parse(fs.readFileSync(path.join(root, MANIFEST_PATH),"utf8")),
    recovery: loadRecovery(root),
    published: JSON.parse(fs.readFileSync(path.join(root,"data","ipos.json"),"utf8"))
  };
}

function run() {
  requireThat(process.argv.slice(2).every(arg => arg === "--check"), "only_--check_supported");
  const input = loadInputs();
  const checked = validateHistoricalImportManifest(input.manifest,input.review,input.receipt,input.reviewBytes);
  const plan = applyReviewedHistoricalIpos(input.recovery,input.published,input.manifest,input.review,input.receipt,input.reviewBytes);
  if (process.argv.includes("--check")) {
    console.log(JSON.stringify({ reviewed_historical_ipos: checked.length, plan: plan.stats, changed_years: plan.changed_years }));
    return;
  }
  for (const year of plan.changed_years) {
    fs.writeFileSync(path.join(RECOVERY_ROOT,year,"nse-issue-information.json"),JSON.stringify(plan.recovery[year],null,2)+"\n");
  }
  console.log(JSON.stringify({ reviewed_historical_ipo_import: plan.stats, changed_years: plan.changed_years }));
}

const isMain = process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) {
  try { run(); } catch (error) { console.error(error); process.exit(1); }
}
