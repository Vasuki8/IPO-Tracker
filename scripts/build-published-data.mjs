import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const inputPath = path.join(ROOT, "data", "recovery", "2026", "nse-issue-information.json");
const outputPath = path.join(ROOT, "data", "ipos.json");
const CHECK = process.argv.includes("--check");

const OFFICIAL_HOSTS = new Set([
  "www.nseindia.com",
  "nseindia.com",
  "www.sebi.gov.in",
  "sebi.gov.in",
  "www.heromotors.com",
  "heromotors.com"
]);

function fail(message) {
  throw new Error(`Recovery build failed: ${message}`);
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function officialUrl(url, context) {
  if (!url) fail(`${context}: official URL is required`);
  let parsed;
  try {
    parsed = new URL(url);
  } catch {
    fail(`${context}: invalid URL ${url}`);
  }
  if (parsed.protocol !== "https:" || !OFFICIAL_HOSTS.has(parsed.hostname)) {
    fail(`${context}: unsupported source host ${parsed.hostname}`);
  }
  return url;
}

function emptyField() {
  return { value: null, status: "missing", evidence: [], corrections: [] };
}

function evidence(source, page = null) {
  return {
    url: officialUrl(source.url, source.document_identity || source.document_type),
    document_type: source.document_type,
    document_identity: source.document_identity,
    publication_date: source.publication_date ?? null,
    page,
    collected_at: source.collected_at
  };
}

function verifiedField(value, source, page = null) {
  if (value === null || value === undefined) return emptyField();
  return {
    value,
    status: "verified",
    evidence: [evidence(source, page)],
    corrections: []
  };
}

function retainedField(field, collectedAt) {
  if (!field || field.value === null || field.value === undefined) return emptyField();
  return verifiedField(
    field.value,
    { ...field.source, collected_at: collectedAt },
    field.page ?? null
  );
}

function retainedEvidence(items, collectedAt) {
  return (items || []).map((item) => evidence(
    { ...item, collected_at: collectedAt },
    item.page ?? null
  ));
}

function normalizeDocument(doc, collectedAt) {
  return {
    type: doc.type,
    identity: doc.identity ?? null,
    url: officialUrl(doc.url, doc.identity || doc.type),
    publication_date: doc.publication_date ?? null,
    collected_at: collectedAt
  };
}

function normalizeRecord(record, collectedAt) {
  const nse = {
    ...record.nse_source,
    document_type: "NSE Issue Information",
    collected_at: collectedAt
  };

  return {
    id: record.id,
    issuer_name: record.issuer_name,
    board: record.board ?? null,
    board_evidence: retainedEvidence(record.board_evidence, collectedAt),
    sector: record.sector ?? null,
    status: record.status ?? null,
    status_evidence: retainedEvidence(record.status_evidence, collectedAt),
    price_band: verifiedField(record.terms.price_band, nse),
    issue_price: retainedField(record.issue_price, collectedAt),
    issue_size_inr: retainedField(record.issue_size_inr, collectedAt),
    market_lot: verifiedField(record.terms.market_lot, nse),
    minimum_bid_quantity: verifiedField(record.terms.minimum_bid_quantity, nse),
    minimum_application_amount_inr: emptyField(),
    open_date: verifiedField(record.terms.open_date, nse),
    close_date: verifiedField(record.terms.close_date, nse),
    listing_date: retainedField(record.listing_date, collectedAt),
    documents: (record.documents || []).map((doc) => normalizeDocument(doc, collectedAt)),
    first_observed_at: record.first_observed_at ?? collectedAt,
    last_collected_at: collectedAt
  };
}

const recovery = readJson(inputPath);
if (!recovery.collection_started_at) fail("collection_started_at is required");
if (!recovery.generated_at) fail("generated_at is required");
if (!Array.isArray(recovery.records)) fail("records must be an array");

const ids = new Set();
for (const record of recovery.records) {
  if (!record.id || !record.issuer_name) fail("every recovery record needs id and issuer_name");
  if (ids.has(record.id)) fail(`duplicate recovery id: ${record.id}`);
  ids.add(record.id);
}

const published = {
  schema_version: "1.0.0",
  generated_at: recovery.generated_at,
  collection_started_at: recovery.collection_started_at,
  records: recovery.records
    .map((record) => normalizeRecord(record, recovery.generated_at))
    .sort((a, b) => a.issuer_name.localeCompare(b.issuer_name))
};

const serialized = `${JSON.stringify(published, null, 2)}\n`;

if (CHECK) {
  const current = fs.readFileSync(outputPath, "utf8");
  if (current !== serialized) {
    console.error("data/ipos.json is not synchronized with the recovery source.");
    process.exit(1);
  }
  console.log(`Recovery build is synchronized for ${published.records.length} record(s).`);
} else {
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, serialized);
  console.log(`Published ${published.records.length} recovered IPO record(s).`);
}
