/* Shared DRHP-to-IPO lifecycle reconciliation for browser UI and Node tests. */
export const NORMAL_IPO_LIFECYCLE_STATUSES = Object.freeze(["upcoming", "open", "closed", "listed"]);
const NORMAL_STATUS_SET = new Set(NORMAL_IPO_LIFECYCLE_STATUSES);

export function canonicalLifecycleIssuer(value) {
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

function identityNames(record) {
  const names = [record?.issuer_name];
  for (const key of ["issuer_aliases", "aliases", "previous_names"]) {
    if (Array.isArray(record?.[key])) names.push(...record[key].filter(value => typeof value === "string"));
  }
  return [...new Set(names.map(canonicalLifecycleIssuer).filter(Boolean))];
}

export function buildIpoLifecycleIndex(ipoData) {
  if (!ipoData || !Array.isArray(ipoData.records)) throw new Error("invalid_ipo_dataset");
  const index = new Map();
  for (const record of ipoData.records) {
    const status = String(record?.status ?? "").toLowerCase();
    if (!NORMAL_STATUS_SET.has(status)) continue;
    for (const key of identityNames(record)) {
      const matches = index.get(key) || [];
      matches.push({
        id: record.id ?? null,
        issuer_name: record.issuer_name,
        status,
        board: record.board ?? null,
        nse_symbol: record.nse_symbol ?? null,
      });
      index.set(key, matches);
    }
  }
  return index;
}

export function buildPreIpoView(drhpData, ipoData) {
  if (!drhpData || !Array.isArray(drhpData.companies)) throw new Error("invalid_drhp_dataset");
  const index = buildIpoLifecycleIndex(ipoData);
  const companies = [];
  const transitioned = [];
  for (const sourceCompany of drhpData.companies) {
    const key = canonicalLifecycleIssuer(sourceCompany?.issuer_name);
    if (!key) throw new Error("invalid_drhp_issuer_name");
    const matches = index.get(key) || [];
    if (matches.length) {
      transitioned.push({
        issuer_name: sourceCompany.issuer_name,
        latest_filing_date: sourceCompany.latest_filing_date,
        matches,
      });
      continue;
    }
    companies.push({...sourceCompany, lifecycle_stage: "drhp_filed_pre_ipo"});
  }
  return {
    companies,
    transitioned,
    counts: {
      source_companies: drhpData.companies.length,
      pre_ipo_companies: companies.length,
      transitioned_companies: transitioned.length,
      source_filings: drhpData.companies.reduce((sum, company) => sum + (company.filings?.length || 0), 0),
      pre_ipo_filings: companies.reduce((sum, company) => sum + (company.filings?.length || 0), 0),
    },
    lifecycle_statuses: NORMAL_IPO_LIFECYCLE_STATUSES,
  };
}
