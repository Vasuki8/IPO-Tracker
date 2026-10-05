(function (root) {
  "use strict";

  const PROGRESSED_STATUSES = new Set(["upcoming", "open", "closed", "listed"]);
  const LIFECYCLE_SCHEMA_VERSION = "1.2.0";

  function canonicalIssuer(value) {
    return String(value ?? "")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase()
      .replace(/&/g, " and ")
      .replace(/\bltd\.?\b/g, " limited ")
      .replace(/[^a-z0-9]+/g, " ")
      .replace(/\blimited\s*$/g, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function fieldValue(field) {
    return field && typeof field === "object" ? field.value ?? null : null;
  }

  function hasProgressed(record) {
    const status = String(record?.status ?? "").trim().toLowerCase();
    return (
      PROGRESSED_STATUSES.has(status) ||
      fieldValue(record?.open_date) != null ||
      fieldValue(record?.close_date) != null ||
      fieldValue(record?.listing_date) != null
    );
  }

  function progressedIssuerKeys(records) {
    const keys = new Set();
    for (const record of records || []) {
      if (!record || typeof record.issuer_name !== "string" || !hasProgressed(record)) continue;
      const key = canonicalIssuer(record.issuer_name);
      if (key) keys.add(key);
    }
    return keys;
  }

  function activeCompanies(companies, records) {
    const progressed = progressedIssuerKeys(records);
    return (companies || []).filter((company) => {
      const key = canonicalIssuer(company?.issuer_name);
      return key && !progressed.has(key);
    });
  }

  function validTimestamp(value) {
    return typeof value === "string" && value.trim() &&
      Number.isFinite(Date.parse(value));
  }

  function validateLifecycleDataset(data) {
    if (!data || data.schema_version !== LIFECYCLE_SCHEMA_VERSION ||
        !validTimestamp(data.generated_at) ||
        !Array.isArray(data.records) || data.records.length === 0) return false;

    const ids = new Set();
    for (const record of data.records) {
      if (!record || typeof record.id !== "string" || !record.id.trim() ||
          ids.has(record.id) ||
          typeof record.issuer_name !== "string" || !record.issuer_name.trim() ||
          !PROGRESSED_STATUSES.has(String(record.status ?? "").trim().toLowerCase())) {
        return false;
      }
      ids.add(record.id);
    }
    return true;
  }

  root.PreIpoFilter = Object.freeze({
    canonicalIssuer,
    hasProgressed,
    progressedIssuerKeys,
    activeCompanies,
    validateLifecycleDataset,
  });
})(globalThis);
