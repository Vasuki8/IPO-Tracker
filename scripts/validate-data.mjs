import fs from "node:fs";

const path = new URL("../data/ipos.json", import.meta.url);
const data = JSON.parse(fs.readFileSync(path, "utf8"));
const schema = JSON.parse(fs.readFileSync(new URL("../data/ipo-schema.json", import.meta.url), "utf8"));

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

function validDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(value + "T00:00:00Z");
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value;
}

function validTimestamp(value) {
  const match = value.match(/^(\d{4}-\d{2}-\d{2})[Tt](\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:[Zz]|[+-](\d{2}):(\d{2}))$/);
  return Boolean(match && validDate(match[1]) && Number(match[2]) < 24 &&
    Number(match[3]) < 60 && Number(match[4]) < 60 &&
    (match[5] === undefined || (Number(match[5]) < 24 && Number(match[6]) < 60)) &&
    Number.isFinite(Date.parse(value)));
}

// The repository has no runtime package dependencies. Enforce the assertions
// used by its local schema, including retained correction representations.
// Reject unsupported assertions so future schema changes cannot silently pass.
const schemaKeywords = new Set(["$schema", "$id", "title", "description", "$defs", "$ref", "type", "required", "properties", "additionalProperties", "items", "format", "minLength", "minItems", "const", "enum", "anyOf", "exclusiveMinimum", "maximum"]);
function checkSchema(definition) {
  for (const key of Object.keys(definition)) {
    if (!schemaKeywords.has(key)) throw new Error(`unsupported schema assertion: ${key}`);
  }
  for (const child of Object.values(definition.properties || {})) checkSchema(child);
  for (const child of Object.values(definition.$defs || {})) checkSchema(child);
  if (definition.items) checkSchema(definition.items);
  for (const child of definition.anyOf || []) checkSchema(child);
}

function schemaErrors(value, definition, prefix = "dataset") {
  const errors = [];
  if (definition.$ref) {
    const match = definition.$ref.match(/^#\/\$defs\/([^/]+)$/);
    if (!match || !schema.$defs[match[1]]) throw new Error(`unsupported schema reference: ${definition.$ref}`);
    // Draft 2020-12 applies sibling assertions as well as the referenced schema.
    errors.push(...schemaErrors(value, schema.$defs[match[1]], prefix));
  }
  const object = value !== null && typeof value === "object" && !Array.isArray(value);
  const types = Array.isArray(definition.type) ? definition.type : [definition.type];
  const matchesType = type => type === "null" ? value === null
    : type === "object" ? object : type === "array" ? Array.isArray(value)
    : type === "integer" ? Number.isInteger(value)
    : type === "number" ? typeof value === "number" && Number.isFinite(value)
    : typeof value === type;
  if (definition.type && !types.some(matchesType)) return [...errors, `${prefix} must have type ${types.join(" or ")}`];
  if (Object.hasOwn(definition, "const") && value !== definition.const) errors.push(`${prefix} must equal ${JSON.stringify(definition.const)}`);
  if (definition.enum && !definition.enum.includes(value)) errors.push(`${prefix} must be one of ${JSON.stringify(definition.enum)}`);
  if (definition.anyOf && !definition.anyOf.some(option => schemaErrors(value, option, prefix).length === 0)) errors.push(`${prefix} does not match an allowed representation`);
  if (typeof value === "number") {
    if (definition.exclusiveMinimum !== undefined && !(value > definition.exclusiveMinimum)) errors.push(`${prefix} must be greater than ${definition.exclusiveMinimum}`);
    if (definition.maximum !== undefined && value > definition.maximum) errors.push(`${prefix} must not exceed ${definition.maximum}`);
  }
  if (typeof value === "string") {
    if (definition.minLength !== undefined && [...value].length < definition.minLength) errors.push(`${prefix} must not be empty`);
    if (definition.format === "date" && !validDate(value)) errors.push(`${prefix} must be a valid calendar date`);
    if (definition.format === "date-time" && !validTimestamp(value)) errors.push(`${prefix} must be a valid timestamp`);
  }
  if (object) {
    for (const name of definition.required || []) {
      if (!Object.hasOwn(value, name)) errors.push(`${prefix}.${name} is required`);
    }
    for (const [name, child] of Object.entries(value)) {
      if (Object.hasOwn(definition.properties || {}, name)) errors.push(...schemaErrors(child, definition.properties[name], `${prefix}.${name}`));
      else if (definition.additionalProperties === false) errors.push(`${prefix}.${name} is not allowed`);
    }
  }
  if (Array.isArray(value)) {
    if (definition.minItems !== undefined && value.length < definition.minItems) errors.push(`${prefix} must contain at least ${definition.minItems} item(s)`);
    if (definition.items) value.forEach((item, index) => errors.push(...schemaErrors(item, definition.items, `${prefix}[${index}]`)));
  }
  return errors;
}

checkSchema(schema);
const structuralErrors = schemaErrors(data, schema);
for (const error of structuralErrors) fail(error);
// Structural failures are already actionable; do not crash in semantic checks.
if (structuralErrors.length) process.exit(1);

function latestAttachedEvidence(value, prefix = "record") {
  let latest = null;
  function visit(node, path) {
    if (Array.isArray(node)) {
      node.forEach((item, index) => visit(item, `${path}[${index}]`));
      return;
    }
    if (!node || typeof node !== "object") return;
    for (const [key, child] of Object.entries(node)) {
      const childPath = `${path}.${key}`;
      if (key === "collected_at" && child !== null) {
        const time = Date.parse(child);
        if (Number.isFinite(time) && (!latest || time > latest.time)) {
          latest = { time, value: child, path: childPath };
        }
      } else {
        visit(child, childPath);
      }
    }
  }
  visit(value, prefix);
  return latest;
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

  const latestEvidence = latestAttachedEvidence(record, prefix);
  const lastCollectedTime = Date.parse(record.last_collected_at || "");
  if (latestEvidence && (!Number.isFinite(lastCollectedTime) || lastCollectedTime < latestEvidence.time)) {
    fail(`${prefix} (${record.id}).last_collected_at must not predate attached evidence at ${latestEvidence.path} (${latestEvidence.value})`);
  }

  const band = record.price_band.value;
  if (band !== null && band.min > band.max) fail(`${prefix}.price_band minimum must not exceed maximum`);
  for (const [earlier, later] of [["open_date", "close_date"], ["open_date", "listing_date"], ["close_date", "listing_date"]]) {
    const a = record[earlier], b = record[later];
    // Retain qualified source contradictions. Do not publish an unlabelled
    // reversal as verified/provisional, or repair dates by inference.
    if (a.value !== null && b.value !== null && a.value > b.value && a.status !== "conflict" && b.status !== "conflict") {
      fail(`${prefix}.${earlier} must not follow ${later} unless the date relationship is explicitly marked conflict`);
    }
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
