import { retainedFieldStatus } from "./publish-field-status.mjs";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const recoveryRoot = path.join(ROOT, "data", "recovery");
const outputPath = path.join(ROOT, "data", "ipos.json");
const CHECK = process.argv.includes("--check");

const OFFICIAL_HOSTS = new Set([
  "www.nseindia.com",
  "nseindia.com",
  "www.sebi.gov.in",
  "sebi.gov.in",
  "www.heromotors.com",
  "heromotors.com",
  "nsearchives.nseindia.com",
  "www.bseindia.com",
  "bseindia.com"
]);

function fail(message) {
  throw new Error(`Recovery build failed: ${message}`);
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function recoveryFiles() {
  if (!fs.existsSync(recoveryRoot)) return [];
  return fs.readdirSync(recoveryRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && /^\d{4}$/.test(entry.name))
    .map((entry) => path.join(recoveryRoot, entry.name, "nse-issue-information.json"))
    .filter((file) => fs.existsSync(file))
    .sort();
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
  return {
    value: field.value,
    status: retainedFieldStatus(field),
    evidence: [evidence(
      { ...field.source, collected_at: field.source.collected_at ?? collectedAt },
      field.page ?? null
    )],
    corrections: Array.isArray(field.corrections) ? field.corrections : []
  };
}

function applicationRequirement(category, collectedAt) {
  return {
    minimum_application_amount_inr: retainedField(category?.minimum_application_amount_inr, collectedAt),
    minimum_bid_quantity: retainedField(category?.minimum_bid_quantity, collectedAt)
  };
}

function applicationRequirements(record, collectedAt) {
  const requirements = record.application_requirements ?? {};
  return {
    retail: applicationRequirement(requirements.retail, collectedAt),
    non_institutional: applicationRequirement(requirements.non_institutional, collectedAt),
    anchor_investor: applicationRequirement(requirements.anchor_investor, collectedAt)
  };
}

function retainedEvidence(items, collectedAt) {
  return (items || []).map((item) => evidence(
    { ...item, collected_at: item.collected_at ?? collectedAt },
    item.page ?? null
  ));
}

function normalizeDocument(doc, collectedAt) {
  return {
    type: doc.type,
    identity: doc.identity ?? null,
    url: officialUrl(doc.url, doc.identity || doc.type),
    publication_date: doc.publication_date ?? null,
    collected_at: doc.collected_at ?? collectedAt
  };
}

function normalizeRecord(record, collectedAt) {
  const nse = {
    ...record.nse_source,
    document_type: record.nse_source?.document_type ?? "NSE Issue Information",
    collected_at: record.nse_source?.collected_at ?? collectedAt
  };

  return {
    id: record.id,
    issuer_name: record.issuer_name,
    board: record.board ?? null,
    board_evidence: retainedEvidence(record.board_evidence, collectedAt),
    sector: record.sector ?? null,
    status: record.status ?? null,
    status_evidence: retainedEvidence(record.status_evidence, collectedAt),
    price_band: record.price_band?.value !== null && record.price_band?.value !== undefined
      ? retainedField(record.price_band, collectedAt)
      : verifiedField(record.terms?.price_band ?? null, nse),
    issue_price: retainedField(record.issue_price, collectedAt),
    issue_size_inr: retainedField(record.issue_size_inr, collectedAt),
    market_lot: record.market_lot?.value !== null && record.market_lot?.value !== undefined
      ? retainedField(record.market_lot, collectedAt)
      : verifiedField(record.terms?.market_lot ?? null, nse),
    minimum_bid_quantity: record.minimum_bid_quantity?.value !== null && record.minimum_bid_quantity?.value !== undefined
      ? retainedField(record.minimum_bid_quantity, collectedAt)
      : verifiedField(record.terms?.minimum_bid_quantity ?? null, nse),
    minimum_application_amount_inr: emptyField(),
    application_requirements: applicationRequirements(record, collectedAt),
    open_date: verifiedField(record.terms?.open_date ?? null, nse),
    close_date: verifiedField(record.terms?.close_date ?? null, nse),
    listing_date: retainedField(record.listing_date, collectedAt),
    documents: (record.documents || []).map((doc) => normalizeDocument(doc, collectedAt)),
    first_observed_at: record.first_observed_at ?? collectedAt,
    last_collected_at: record.last_collected_at ?? collectedAt
  };
}

const files = recoveryFiles();
if (files.length === 0) fail("no recovery manifests found");

const recoveries = files.map((file) => ({ file, data: readJson(file) }));
for (const { file, data } of recoveries) {
  if (!data.collection_started_at) fail(`${file}: collection_started_at is required`);
  if (!data.generated_at) fail(`${file}: generated_at is required`);
  if (!Array.isArray(data.records)) fail(`${file}: records must be an array`);
}

const ids = new Set();
const normalizedRecords = [];
for (const { file, data } of recoveries) {
  for (const record of data.records) {
    if (!record.id || !record.issuer_name) fail(`${file}: every recovery record needs id and issuer_name`);
    if (ids.has(record.id)) fail(`duplicate recovery id across manifests: ${record.id}`);
    ids.add(record.id);
    normalizedRecords.push(normalizeRecord(record, data.generated_at));
  }
}

const published = {
  schema_version: "1.2.0",
  generated_at: recoveries.map(({ data }) => data.generated_at).sort().at(-1),
  collection_started_at: recoveries.map(({ data }) => data.collection_started_at).sort().at(0),
  records: normalizedRecords.sort((a, b) => {
    const openA = a.open_date?.value ?? "";
    const openB = b.open_date?.value ?? "";
    if (openA !== openB) return openB.localeCompare(openA);

    const closeA = a.close_date?.value ?? "";
    const closeB = b.close_date?.value ?? "";
    if (closeA !== closeB) return closeB.localeCompare(closeA);

    const listingA = a.listing_date?.value ?? "";
    const listingB = b.listing_date?.value ?? "";
    if (listingA !== listingB) return listingB.localeCompare(listingA);

    return a.issuer_name.localeCompare(b.issuer_name);
  })
};

const serialized = `${JSON.stringify(published, null, 2)}\n`;

if (CHECK) {
  const current = fs.readFileSync(outputPath, "utf8");
  if (current !== serialized) {
    console.error("data/ipos.json is not synchronized with the recovery sources.");
    process.exit(1);
  }
  console.log(`Recovery build is synchronized for ${published.records.length} record(s) across ${files.length} year manifest(s).`);
} else {
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, serialized);
  console.log(`Published ${published.records.length} recovered IPO record(s) across ${files.length} year manifest(s).`);
}
