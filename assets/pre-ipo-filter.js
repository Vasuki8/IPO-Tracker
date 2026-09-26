(function (root) {
  "use strict";

  const PROGRESSED_STATUSES = new Set(["upcoming", "open", "closed", "listed"]);

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

  root.PreIpoFilter = Object.freeze({
    canonicalIssuer,
    hasProgressed,
    progressedIssuerKeys,
    activeCompanies,
  });
})(globalThis);
