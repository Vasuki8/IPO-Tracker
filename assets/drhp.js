/* Dynamic pre-IPO company list backed by retained SEBI draft-offer evidence and current published IPO state. */
let DRHP_DATA = null;
const $ = (selector) => document.querySelector(selector);

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) =>
    ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"})[char]);
}
function safeUrl(value, prefix = "/filings/public-issues/") {
  try {
    const url = new URL(value);
    return url.protocol === "https:" && ["www.sebi.gov.in", "sebi.gov.in"].includes(url.hostname) && !url.username && !url.password && url.pathname.startsWith(prefix) ? url.href : null;
  } catch {
    return null;
  }
}
function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value + "T00:00:00Z");
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleDateString("en-GB", {
    day:"2-digit", month:"short", year:"numeric", timeZone:"UTC"
  });
}
function formatTimestamp(value) {
  if (!value) return "Unavailable";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Unavailable" : date.toLocaleString("en-GB", {
    day:"2-digit", month:"short", year:"numeric", hour:"2-digit", minute:"2-digit", timeZone:"UTC"
  }) + " UTC";
}
function visibleCompanies() {
  const query = ($("#drhpSearch")?.value || "").trim().toLowerCase();
  const companies = DRHP_DATA?.companies || [];
  return query ? companies.filter(company => company.issuer_name.toLowerCase().includes(query)) : companies;
}
function filingLink(company) {
  const url = safeUrl(company.latest_filing_url);
  return url
    ? `<a class="drhp-filing-link" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">View latest draft ↗</a>`
    : "Unavailable";
}
function render() {
  if (!DRHP_DATA) return;
  const companies = visibleCompanies();
  $("#drhpVisibleCount").textContent = companies.length;
  $("#drhpRows").innerHTML = companies.map(company => `<tr>
    <td><strong class="drhp-company-name">${escapeHtml(company.issuer_name)}</strong>${company.filings?.some(f => f.not_seen_in_latest_scan) ? '<span class="secondary">Includes earlier retained source evidence</span>' : ""}</td>
    <td><span class="status status--upcoming">DRHP filed</span></td>
    <td><span class="number">${escapeHtml(formatDate(company.latest_filing_date))}</span><span class="secondary">${escapeHtml(company.latest_filing_type)} · latest retained draft</span></td>
    <td>${filingLink(company)}</td>
  </tr>`).join("");
  $("#drhpCards").innerHTML = companies.map(company => `<article class="mobile-card drhp-card">
    <div class="mobile-card__head"><div><strong class="drhp-company-name">${escapeHtml(company.issuer_name)}</strong><div class="company-meta">DRHP filed · latest draft ${escapeHtml(formatDate(company.latest_filing_date))}</div></div><span class="status status--upcoming">DRHP filed</span></div>
    <div class="mobile-card__foot"><span>Proposed IPO · ${escapeHtml(company.latest_filing_type)} evidence</span>${filingLink(company)}</div>
  </article>`).join("");
  $("#drhpEmpty").hidden = companies.length !== 0;
}
function validateDrhpDataset(data) {
  if(data?.schema_version !== "1.0.0" || data?.coverage?.year !== 2026 ||
    data?.coverage?.stop_reason !== "first_page_strictly_older_than_year" ||
    !Array.isArray(data.companies) || !data.companies.length || data.coverage.companies !== data.companies.length) return false;
  const urls = new Set(); let filings = 0;
  for(const c of data.companies) {
    if(typeof c.issuer_name !== "string" || !c.issuer_name.trim() || !Array.isArray(c.filings) || !c.filings.length || c.filing_count !== c.filings.length) return false;
    if(c.latest_filing_url !== c.filings[0].filing_url || c.latest_filing_date !== c.filings[0].filing_date || c.latest_filing_type !== c.filings[0].filing_type) return false;
    for(const f of c.filings) {
      if(!/^(?:DRHP|UDRHP(?:-?(?:I{1,4}|V|\d+))?)$/.test(f.filing_type || "") || !safeUrl(f.filing_url) || urls.has(f.filing_url) || !/^2026-\d\d-\d\d$/.test(f.filing_date)) return false;
      urls.add(f.filing_url); filings++;
    }
  }
  return data.coverage.filing_records === filings;
}
function validateIpoDataset(data) {
  const statuses = new Set(["upcoming", "open", "closed", "listed"]);
  return Array.isArray(data?.records) && data.records.every(record =>
    record && typeof record.issuer_name === "string" && record.issuer_name.trim() &&
    statuses.has(String(record.status || "").toLowerCase()));
}
async function load() {
  $("#drhpLoading").hidden = false;
  $("#drhpError").hidden = true;
  $("#drhpResults").hidden = true;
  try {
    const [drhpResponse, ipoResponse] = await Promise.all([
      fetch("data/drhp-filings.json", {cache:"no-store"}),
      fetch("data/ipos.json", {cache:"no-store"}),
    ]);
    if (!drhpResponse.ok || !ipoResponse.ok) throw new Error("Pre-IPO lifecycle datasets request failed");
    const [sourceData, ipoData] = await Promise.all([drhpResponse.json(), ipoResponse.json()]);
    if (!validateDrhpDataset(sourceData) || !validateIpoDataset(ipoData) || !globalThis.PreIpoFilter) {
      throw new Error("Invalid pre-IPO lifecycle datasets");
    }

    const activeCompanies = PreIpoFilter.activeCompanies(sourceData.companies, ipoData.records);
    const progressedCount = sourceData.companies.length - activeCompanies.length;
    DRHP_DATA = {...sourceData, companies: activeCompanies};

    $("#drhpCompanyCount").textContent = activeCompanies.length;
    $("#drhpLatestDate").textContent = formatDate(activeCompanies.reduce((latest, company) =>
      !latest || company.latest_filing_date > latest ? company.latest_filing_date : latest, null));
    $("#drhpYear").textContent = sourceData.coverage.year;
    $("#drhpPages").textContent = sourceData.coverage.pages_fetched;
    $("#drhpGenerated").textContent = "Lifecycle state checked: " + formatTimestamp(
      [sourceData.collection_completed_at || sourceData.generated_at, ipoData.generated_at].filter(Boolean).sort().at(-1)
    );
    $("#drhpCoverageNote").textContent =
      `${activeCompanies.length} active pre-IPO companies · ${progressedCount} progressed issuer(s) hidden · ${sourceData.companies.length} draft-backed companies tracked`;

    const totals = new Set((sourceData.source_pages || []).map(p => p.observed_records));
    const retained = sourceData.companies.flatMap(c => c.filings).filter(f => f.not_seen_in_latest_scan).length;
    $("#drhpIntegrityNote").textContent =
      (totals.size > 1 ? "SEBI page totals differed during collection. " : "") +
      "The visible list is the intersection of retained draft-offer evidence and the current IPO lifecycle: exact canonical legal-name matches are removed once they are Upcoming, Open, Closed, Listed, or have an IPO open/close/listing date. " +
      (retained ? `${retained} earlier draft observation(s) not seen in the latest scan remain retained as source history. ` : "") +
      "No fuzzy issuer matching is used.";

    const sourceUrl = safeUrl(sourceData.source?.listing_url, "/sebiweb/home/");
    if (sourceUrl) $("#sebiSourceLink").href = sourceUrl;
    $("#drhpLoading").hidden = true;
    $("#drhpResults").hidden = false;
    render();

    try {
      const healthResponse = await fetch("ops/drhp-collection.json", {cache:"no-store"});
      if(!healthResponse.ok) throw new Error("health unavailable");
      const health = await healthResponse.json();
      if(health.status === "failed") $("#drhpIntegrityNote").textContent += " Latest draft-source refresh failed; the last successful evidence set is retained.";
      else if(health.status !== "success") $("#drhpIntegrityNote").textContent += " Latest draft-source refresh status is unavailable.";
    } catch { $("#drhpIntegrityNote").textContent += " Latest draft-source refresh status is unavailable."; }
  } catch (error) {
    console.error(error);
    DRHP_DATA = null;
    $("#drhpLoading").hidden = true;
    $("#drhpError").hidden = false;
  }
}
$("#drhpSearch").addEventListener("input", render);
$("#drhpRetry").addEventListener("click", load);
load();
