import assert from "node:assert/strict";
import fs from "node:fs";

const html=fs.readFileSync("drhp.html","utf8");
const app=fs.readFileSync("assets/drhp.js","utf8");
const index=fs.readFileSync("index.html","utf8");
const data=JSON.parse(fs.readFileSync("data/drhp-filings.json","utf8"));

assert.match(index,/href="drhp\.html"[^>]*>DRHP \/ Pre-IPO<\/a>/);
assert.match(html,/id="drhpSearch"/);
assert.match(html,/data\/drhp-filings\.json|assets\/drhp\.js/);
assert.match(html,/DRHP Filed \/ Pre-IPO/);
assert.match(html,/not yet categorized as Upcoming, Open, Closed, or Listed/);
assert.match(html,/Official SEBI source/);
assert.match(app,/fetch\("data\/drhp-filings\.json"/);
assert.match(app,/fetch\("data\/ipos\.json"/);
assert.match(app,/buildPreIpoView/);
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
console.log(JSON.stringify({drhp_ui_tests:{companies:data.companies.length,filings:data.coverage.filing_records,pages:data.coverage.pages_fetched,source_backed:true}}));
