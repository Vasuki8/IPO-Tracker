/* Read-only DRHP Filed / Pre-IPO directory sourced from retained SEBI filings plus the current IPO lifecycle. */
import { buildPreIpoView } from "./drhp-lifecycle.js";

let DRHP_DATA = null;
let DRHP_VIEW = null;
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
  const companies = DRHP_VIEW?.companies || [];
  return query ? companies.filter(company => company.issuer_name.toLowerCase().includes(query)) : companies;
}
function filingLink(company) {
  const url = safeUrl(company.latest_filing_url);
  return url
    ? `<a class="drhp-filing-link" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">View on SEBI ↗</a>`
    : "Unavailable";
}
function render() {
  if (!DRHP_VIEW) return;
  const companies = visibleCompanies();
  $("#drhpVisibleCount").textContent = companies.length;
  $("#drhpRows").innerHTML = companies.map(company => `<tr>
    <td><strong class="drhp-company-name">${escapeHtml(company.issuer_name)}</strong><span class="secondary">DRHP Filed / Pre-IPO</span>${company.filings?.some(f => f.not_seen_in_latest_scan) ? '<span class="secondary">Includes an earlier retained observation</span>' : ""}${company.filing_count > 1 ? `<span class="secondary">${escapeHtml(company.filing_count)} retained filings</span>` : ""}</td>
    <td><span class="source source--verified">${escapeHtml(company.latest_filing_type)}</span></td>
    <td><span class="number">${escapeHtml(formatDate(company.latest_filing_date))}</span></td>
    <td>${filingLink(company)}</td>
  </tr>`).join("");
  $("#drhpCards").innerHTML = companies.map(company => `<article class="mobile-card drhp-card">
    <div class="mobile-card__head"><div><strong class="drhp-company-name">${escapeHtml(company.issuer_name)}</strong><div class="company-meta">DRHP Filed / Pre-IPO · ${escapeHtml(company.latest_filing_type)} · ${escapeHtml(formatDate(company.latest_filing_date))}</div></div></div>
    <div class="mobile-card__foot"><span>${company.filing_count > 1 ? `${escapeHtml(company.filing_count)} filings retained` : "1 filing retained"}</span>${filingLink(company)}</div>
  </article>`).join("");
  $("#drhpEmpty").hidden = companies.length !== 0;
}
function validateDataset(data) {
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
async function load() {
  $("#drhpLoading").hidden = false;
  $("#drhpError").hidden = true;
  $("#drhpResults").hidden = true;
  try {
    const [drhpResponse, ipoResponse] = await Promise.all([
      fetch("data/drhp-filings.json", {cache:"no-store"}),
      fetch("data/ipos.json", {cache:"no-store"}),
    ]);
    if (!drhpResponse.ok) throw new Error("DRHP dataset request failed");
    if (!ipoResponse.ok) throw new Error("IPO lifecycle dataset request failed");
    const [data, ipoData] = await Promise.all([drhpResponse.json(), ipoResponse.json()]);
    if (!validateDataset(data)) throw new Error("Invalid DRHP dataset");
    const view = buildPreIpoView(data, ipoData);
    if (!view.companies.length) throw new Error("No DRHP Filed / Pre-IPO companies after lifecycle reconciliation");
    DRHP_DATA = data;
    DRHP_VIEW = view;
    $("#drhpCompanyCount").textContent = view.counts.pre_ipo_companies;
    $("#drhpFilingCount").textContent = view.counts.pre_ipo_filings;
    $("#drhpYear").textContent = data.coverage.year;
    $("#drhpPages").textContent = data.coverage.pages_fetched;
    $("#drhpGenerated").textContent = "Last successful DRHP collection: " + formatTimestamp(data.collection_completed_at || data.source_pages?.at(-1)?.collected_at || data.generated_at);
    $("#drhpCoverageNote").textContent =
      `${view.counts.pre_ipo_companies} pre-IPO companies · ${view.counts.transitioned_companies} source companies already in Upcoming/Open/Closed/Listed and hidden · ${data.coverage.pages_fetched} SEBI pages checked`;
    const totals = new Set((data.source_pages || []).map(p => p.observed_records));
    const retained = data.companies.flatMap(c => c.filings).filter(f => f.not_seen_in_latest_scan).length;
    $("#drhpIntegrityNote").textContent =
      `Lifecycle rule: show retained DRHP/UDRHP filers only while they are absent from Upcoming, Open, Closed and Listed IPO records. ${view.counts.transitioned_companies} company/companies have already entered that lifecycle and are hidden here; their draft history remains retained. ` +
      (totals.size > 1 ? "SEBI page totals differed during collection. " : "") +
      "The underlying DRHP source list is not a complete register. " +
      (retained ? `${retained} earlier filing(s) not seen in the latest scan remain retained; absence is not withdrawal evidence. ` : "") +
      "Other years, unlabelled draft filings and exchange-only filings are not included.";
    const sourceUrl = safeUrl(data.source?.listing_url, "/sebiweb/home/");
    if (sourceUrl) $("#sebiSourceLink").href = sourceUrl;
    $("#drhpLoading").hidden = true;
    $("#drhpResults").hidden = false;
    render();
    try {
      const healthResponse = await fetch("ops/drhp-collection.json", {cache:"no-store"});
      if(!healthResponse.ok) throw new Error("health unavailable");
      const health = await healthResponse.json();
      if(health.status === "failed") $("#drhpIntegrityNote").textContent += " Latest DRHP refresh failed; the last successful filing evidence is retained.";
      else if(health.status !== "success") $("#drhpIntegrityNote").textContent += " Latest DRHP refresh status is unavailable.";
    } catch { $("#drhpIntegrityNote").textContent += " Latest DRHP refresh status is unavailable."; }
  } catch (error) {
    console.error(error);
    $("#drhpLoading").hidden = true;
    $("#drhpError").hidden = false;
  }
}
$("#drhpSearch").addEventListener("input", render);
$("#drhpRetry").addEventListener("click", load);
load();
