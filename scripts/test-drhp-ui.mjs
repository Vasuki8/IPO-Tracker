import assert from "node:assert/strict";
import fs from "node:fs";

const html=fs.readFileSync("drhp.html","utf8");
const app=fs.readFileSync("assets/drhp.js","utf8");
const index=fs.readFileSync("index.html","utf8");
const data=JSON.parse(fs.readFileSync("data/drhp-filings.json","utf8"));

assert.match(index,/href="drhp\.html"[^>]*>Pre-IPO companies<\/a>/);
assert.match(html,/Companies that have filed for an IPO\./);
assert.match(html,/One company per row/);
assert.doesNotMatch(html,/Filing records/);
assert.doesNotMatch(html,/DRHP filing companies/);
assert.match(html,/id="drhpSearch"/);
assert.match(html,/assets\/drhp\.js/);
assert.match(html,/draft filing shows formal IPO intent/i);
assert.match(html,/Official SEBI source/);
assert.match(app,/fetch\("data\/drhp-filings\.json"/);
assert.match(app,/status status--upcoming">DRHP filed/);
assert.match(app,/company list is backed by retained 2026 draft-offer evidence/);
assert.match(app,/stop_reason !== "first_page_strictly_older_than_year"/);
assert.match(app,/drhpIntegrityNote/);
assert.equal(data.coverage.filing_records,data.companies.reduce((n,c)=>n+c.filings.length,0));
assert.equal(data.schema_version,"1.0.0");
assert.equal(data.coverage.year,2026);
assert.equal(data.coverage.stop_reason,"first_page_strictly_older_than_year");
assert.ok(data.coverage.pages_fetched>=2);
assert.equal(data.coverage.companies,data.companies.length);
assert.ok(data.companies.length>0);
assert.equal(new Set(data.companies.map(c=>c.issuer_name.toLowerCase())).size,data.companies.length);
for(const company of data.companies){
  assert.ok(company.issuer_name);
  assert.match(company.latest_filing_type,/^(?:DRHP|UDRHP(?:-?(?:I{1,4}|V|\d+))?)$/);
  assert.match(company.latest_filing_url,/^https:\/\/www\.sebi\.gov\.in\/filings\/public-issues\//);
  assert.match(company.latest_filing_date,/^2026-\d\d-\d\d$/);
  assert.ok(company.filing_count>=1);
}
console.log(JSON.stringify({pre_ipo_company_ui_tests:{companies:data.companies.length,retained_source_filings:data.coverage.filing_records,pages:data.coverage.pages_fetched,one_company_per_row:true,source_backed:true}}));
