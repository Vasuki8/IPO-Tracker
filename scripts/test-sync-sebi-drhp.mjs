import assert from "node:assert/strict";
import {
  DRHP_LIST_URL, DRHP_AJAX_URL, parseSebiDate, canonicalIssuer, parseDrhpRows,
  listingStats, parseAjaxFragment, paginationBody, buildCompanies
} from "./sync-sebi-drhp.mjs";

assert.equal(parseSebiDate("Sep 25, 2026"), "2026-09-25");
assert.equal(parseSebiDate("Sep 31, 2026"), null);
assert.equal(canonicalIssuer("Madhur Iron & Steel India Ltd."), "madhur iron and steel india");

const html = `
<input type='hidden' name='totalpage' value='89'/>
<input type='hidden' name='nextValue' value='1'/>
<div><p>1 to 25 of 2,214 records</p></div>
<table><tbody>
<tr><td>Sep 25, 2026</td><td><a href="https://www.sebi.gov.in/filings/public-issues/sep-2026/anjali-labtech-limited-udrhp-i_104737.html" title="Anjali Labtech Limited - UDRHP-I<br><a href='https://www.sebi.gov.in/sebi_data/commondocs/sep-2026/anjali-dap.pdf'>Draft Abridged Prospectus</a>">Anjali</a></td></tr>
<tr><td>Sep 22, 2026</td><td><a href="https://www.sebi.gov.in/filings/public-issues/sep-2026/vardaan-biotech-limited-drhp_104652.html" title="VARDAAN BIOTECH LIMITED - DRHP">Vardaan</a></td></tr>
<tr><td>Sep 17, 2026</td><td><a href="https://www.sebi.gov.in/filings/public-issues/sep-2026/rayzon-solar-limited-addendum-to-the-drhp_104532.html" title="Rayzon Solar Limited - Addendum to the DRHP">Addendum</a></td></tr>
<tr><td>Sep 10, 2026</td><td><a href="https://www.sebi.gov.in/filings/public-issues/sep-2026/incred-holdings-limited-corrigendum-to-udrhp_104399.html" title="Incred Holdings Limited - Corrigendum to UDRHP">Corrigendum</a></td></tr>
<tr><td>Sep 04, 2026</td><td><a href="https://www.sebi.gov.in/filings/public-issues/sep-2026/india-exposition-mart-limited_104273.html" title="India Exposition Mart Limited">Unlabelled</a></td></tr>
</tbody></table>`;

const rows = parseDrhpRows(html);
assert.equal(rows.length, 2);
assert.deepEqual(rows.map(r => [r.issuer_name,r.filing_type,r.filing_date]), [
  ["Anjali Labtech Limited","UDRHP-I","2026-09-25"],
  ["VARDAAN BIOTECH LIMITED","DRHP","2026-09-22"]
]);
assert.equal(rows[0].draft_abridged_url, "https://www.sebi.gov.in/sebi_data/commondocs/sep-2026/anjali-dap.pdf");
const variantHtml = `
<table><tbody>
<tr><td>Feb 04, 2026</td><td><a href="https://www.sebi.gov.in/filings/public-issues/feb-2026/turtlemint-fintech-solutions-limited-udrhp-1_999901.html" title="Turtlemint Fintech Solutions Limited - UDRHP 1">Turtlemint</a></td></tr>
<tr><td>Jan 23, 2026</td><td><a href="https://www.sebi.gov.in/filings/public-issues/jan-2026/phonepe-limited-udrhp-i_999902.html" title="PhonePe Limited UDRHP - I">PhonePe</a></td></tr>
</tbody></table>`;
const variantRows = parseDrhpRows(variantHtml);
assert.deepEqual(variantRows.map(r => [r.issuer_name,r.filing_type]), [
  ["Turtlemint Fintech Solutions Limited","UDRHP-1"],
  ["PhonePe Limited","UDRHP-I"]
]);

assert.deepEqual(listingStats(html), {total_records:2214,page:1,total_pages:89});

const fragment = "<input type='hidden' name='nextValue' value='2'/><p>26 to 50 of 2212 records</p><table></table>#@#<div>crumb</div>";
assert.ok(parseAjaxFragment(fragment).includes("26 to 50"));
assert.equal(listingStats(parseAjaxFragment(fragment)).page, 2);
const body = paginationBody(2);
assert.equal(body.get("sid"), "3");
assert.equal(body.get("ssid"), "15");
assert.equal(body.get("smid"), "10");
assert.equal(body.get("doDirect"), "1");
assert.equal(DRHP_LIST_URL.includes("smid=10"), true);
assert.equal(DRHP_AJAX_URL.endsWith("/getnewslistinfo.jsp"), true);

const companies = buildCompanies([
  ...rows,
  {...rows[1], filing_type:"UDRHP-1", filing_date:"2026-09-24", filing_url:"https://www.sebi.gov.in/filings/public-issues/sep-2026/vardaan-biotech-limited-udrhp-1_104700.html"},
  {issuer_name:"Vardaan Biotech Ltd.",filing_type:"UDRHP-2",filing_date:"2026-09-26",filing_url:"https://www.sebi.gov.in/filings/public-issues/sep-2026/vardaan-biotech-limited-udrhp-2_104800.html",draft_abridged_url:null}
]);
assert.equal(companies.length, 2);
const vardaan = companies.find(c => canonicalIssuer(c.issuer_name) === "vardaan biotech");
assert.equal(vardaan.filing_count, 3);
assert.equal(vardaan.latest_filing_type, "UDRHP-2");
assert.equal(vardaan.latest_filing_date, "2026-09-26");

console.log(JSON.stringify({drhp_parser_tests:{rows:rows.length,companies:companies.length,addenda_and_corrigenda_excluded:true,pagination_contract:true}}));
