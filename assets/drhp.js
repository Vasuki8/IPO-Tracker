/* Read-only DRHP directory sourced from SEBI's Draft Offer Documents section. */
let DRHP_DATA = null;
const $ = (selector) => document.querySelector(selector);

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) =>
    ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"})[char]);
}
function safeUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === "https:" ? url.href : null;
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
    ? `<a class="drhp-filing-link" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">View on SEBI ↗</a>`
    : "Unavailable";
}
function render() {
  if (!DRHP_DATA) return;
  const companies = visibleCompanies();
  $("#drhpVisibleCount").textContent = companies.length;
  $("#drhpRows").innerHTML = companies.map(company => `<tr>
    <td><strong class="drhp-company-name">${escapeHtml(company.issuer_name)}</strong>${company.filing_count > 1 ? `<span class="secondary">${escapeHtml(company.filing_count)} retained filings</span>` : ""}</td>
    <td><span class="source source--verified">${escapeHtml(company.latest_filing_type)}</span></td>
    <td><span class="number">${escapeHtml(formatDate(company.latest_filing_date))}</span></td>
    <td>${filingLink(company)}</td>
  </tr>`).join("");
  $("#drhpCards").innerHTML = companies.map(company => `<article class="mobile-card drhp-card">
    <div class="mobile-card__head"><div><strong class="drhp-company-name">${escapeHtml(company.issuer_name)}</strong><div class="company-meta">${escapeHtml(company.latest_filing_type)} · ${escapeHtml(formatDate(company.latest_filing_date))}</div></div></div>
    <div class="mobile-card__foot"><span>${company.filing_count > 1 ? `${escapeHtml(company.filing_count)} filings retained` : "1 filing retained"}</span>${filingLink(company)}</div>
  </article>`).join("");
  $("#drhpEmpty").hidden = companies.length !== 0;
}
function validateDataset(data) {
  return data?.schema_version === "1.0.0" &&
    data?.coverage?.year === 2026 &&
    data?.coverage?.stop_reason === "first_page_strictly_older_than_year" &&
    Array.isArray(data.companies) &&
    data.companies.every(company =>
      typeof company.issuer_name === "string" &&
      /^U?DRHP/.test(company.latest_filing_type || "") &&
      safeUrl(company.latest_filing_url));
}
async function load() {
  $("#drhpLoading").hidden = false;
  $("#drhpError").hidden = true;
  $("#drhpResults").hidden = true;
  try {
    const response = await fetch("data/drhp-filings.json", {cache:"no-store"});
    if (!response.ok) throw new Error("DRHP dataset request failed");
    const data = await response.json();
    if (!validateDataset(data)) throw new Error("Invalid DRHP dataset");
    DRHP_DATA = data;
    $("#drhpCompanyCount").textContent = data.companies.length;
    $("#drhpFilingCount").textContent = data.coverage.filing_records;
    $("#drhpYear").textContent = data.coverage.year;
    $("#drhpPages").textContent = data.coverage.pages_fetched;
    $("#drhpGenerated").textContent = "Generated " + formatTimestamp(data.generated_at);
    $("#drhpCoverageNote").textContent =
      `${data.coverage.year} coverage · ${data.coverage.pages_fetched} SEBI pages checked · explicit DRHP/UDRHP filings only`;
    const sourceUrl = safeUrl(data.source?.listing_url);
    if (sourceUrl) $("#sebiSourceLink").href = sourceUrl;
    $("#drhpLoading").hidden = true;
    $("#drhpResults").hidden = false;
    render();
  } catch (error) {
    console.error(error);
    $("#drhpLoading").hidden = true;
    $("#drhpError").hidden = false;
  }
}
$("#drhpSearch").addEventListener("input", render);
$("#drhpRetry").addEventListener("click", load);
load();
