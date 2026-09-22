import fs from "node:fs";

const path = new URL("../data/ipos.json", import.meta.url);
const data = JSON.parse(fs.readFileSync(path, "utf8"));

const allowedStatuses = new Set(["verified", "provisional", "conflict", "missing"]);
const fieldNames = [
  "price_band", "issue_price", "issue_size_inr", "market_lot",
  "minimum_bid_quantity", "minimum_application_amount_inr",
  "open_date", "close_date", "listing_date"
];

function fail(message) {
  console.error(`DATA CONTRACT ERROR: ${message}`);
  process.exitCode = 1;
}

if (data.schema_version !== "1.1.0") fail("schema_version must be 1.1.0");
if (!Array.isArray(data.records)) fail("records must be an array");

const ids = new Set();
for (const [index, record] of (data.records || []).entries()) {
  const prefix = `records[${index}]`;
  if (!record.id || typeof record.id !== "string") fail(`${prefix}.id is required`);
  if (ids.has(record.id)) fail(`${prefix}.id duplicates ${record.id}`);
  ids.add(record.id);
  if (!record.issuer_name || typeof record.issuer_name !== "string") fail(`${prefix}.issuer_name is required`);
  if (!Array.isArray(record.board_evidence)) fail(`${prefix}.board_evidence must be an array`);
  if (!Array.isArray(record.status_evidence)) fail(`${prefix}.status_evidence must be an array`);
  if (record.board !== null && record.board_evidence.length === 0) {
    fail(`${prefix}.board requires retained evidence`);
  }
  if (record.status !== null && record.status_evidence.length === 0) {
    fail(`${prefix}.status requires retained evidence`);
  }

  for (const fieldName of fieldNames) {
    const field = record[fieldName];
    if (!field || typeof field !== "object") {
      fail(`${prefix}.${fieldName} must be an evidence-bearing field object`);
      continue;
    }
    if (!allowedStatuses.has(field.status)) fail(`${prefix}.${fieldName}.status is invalid`);
    if (!Array.isArray(field.evidence)) fail(`${prefix}.${fieldName}.evidence must be an array`);
    if (!Array.isArray(field.corrections)) fail(`${prefix}.${fieldName}.corrections must be an array`);
    if (field.value === null && field.status === "verified") {
      fail(`${prefix}.${fieldName} cannot be verified with a null value`);
    }
    if (field.status === "missing" && field.value !== null) {
      fail(`${prefix}.${fieldName} must keep missing values as null`);
    }
    if (field.status === "verified" && field.evidence.length === 0) {
      fail(`${prefix}.${fieldName} verified values require retained evidence`);
    }
  }
}

if (!process.exitCode) {
  console.log(`Validated ${data.records.length} IPO record(s) against core contract invariants.`);
}
