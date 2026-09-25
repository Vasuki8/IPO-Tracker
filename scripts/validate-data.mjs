import fs from "node:fs";

const path = new URL("../data/ipos.json", import.meta.url);
const data = JSON.parse(fs.readFileSync(path, "utf8"));

const allowedStatuses = new Set(["verified", "provisional", "conflict", "missing"]);
const allowedRecordStatuses = new Set(["open", "upcoming", "closed", "listed"]);
const fieldNames = [
  "price_band", "issue_price", "issue_size_inr", "market_lot",
  "minimum_bid_quantity", "minimum_application_amount_inr",
  "open_date", "close_date", "listing_date"
];
const applicationCategories = ["retail", "non_institutional", "anchor_investor"];
const applicationRequirementFields = ["minimum_application_amount_inr", "minimum_bid_quantity"];

function fail(message) {
  console.error(`DATA CONTRACT ERROR: ${message}`);
  process.exitCode = 1;
}

function validateField(field, prefix) {
  if (!field || typeof field !== "object" || Array.isArray(field)) {
    fail(`${prefix} must be an evidence-bearing field object`);
    return;
  }
  if (!allowedStatuses.has(field.status)) fail(`${prefix}.status is invalid`);
  if (!Array.isArray(field.evidence)) fail(`${prefix}.evidence must be an array`);
  if (!Array.isArray(field.corrections)) fail(`${prefix}.corrections must be an array`);
  if (field.value === null && field.status === "verified") {
    fail(`${prefix} cannot be verified with a null value`);
  }
  if (field.status === "missing" && field.value !== null) {
    fail(`${prefix} must keep missing values as null`);
  }
  if (field.status === "verified" && field.evidence.length === 0) {
    fail(`${prefix} verified values require retained evidence`);
  }
}

if (data.schema_version !== "1.2.0") fail("schema_version must be 1.2.0");
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
  if (!allowedRecordStatuses.has(record.status)) fail(`${prefix}.status must be one of open, upcoming, closed, listed`);
  if (record.board !== null && record.board_evidence.length === 0) {
    fail(`${prefix}.board requires retained evidence`);
  }
  if (record.status_evidence.length === 0) {
    fail(`${prefix}.status requires retained evidence`);
  }

  for (const fieldName of fieldNames) {
    validateField(record[fieldName], `${prefix}.${fieldName}`);
  }

  const requirements = record.application_requirements;
  if (!requirements || typeof requirements !== "object" || Array.isArray(requirements)) {
    fail(`${prefix}.application_requirements must be an object`);
    continue;
  }

  const categoryKeys = Object.keys(requirements).sort();
  const expectedCategoryKeys = [...applicationCategories].sort();
  if (JSON.stringify(categoryKeys) !== JSON.stringify(expectedCategoryKeys)) {
    fail(`${prefix}.application_requirements must contain exactly ${applicationCategories.join(", ")}`);
  }

  for (const category of applicationCategories) {
    const requirement = requirements[category];
    const categoryPrefix = `${prefix}.application_requirements.${category}`;
    if (!requirement || typeof requirement !== "object" || Array.isArray(requirement)) {
      fail(`${categoryPrefix} must be an object`);
      continue;
    }

    const requirementKeys = Object.keys(requirement).sort();
    const expectedRequirementKeys = [...applicationRequirementFields].sort();
    if (JSON.stringify(requirementKeys) !== JSON.stringify(expectedRequirementKeys)) {
      fail(`${categoryPrefix} must contain exactly ${applicationRequirementFields.join(", ")}`);
    }

    for (const fieldName of applicationRequirementFields) {
      validateField(requirement[fieldName], `${categoryPrefix}.${fieldName}`);
    }
  }
}

if (!process.exitCode) {
  console.log(`Validated ${data.records.length} IPO record(s) against schema 1.2.0 core contract invariants.`);
}
