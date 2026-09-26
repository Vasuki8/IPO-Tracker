import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const html=fs.readFileSync("drhp.html","utf8");
const app=fs.readFileSync("assets/drhp.js","utf8");
const filterCode=fs.readFileSync("assets/pre-ipo-filter.js","utf8");
const index=fs.readFileSync("index.html","utf8");
const data=JSON.parse(fs.readFileSync("data/drhp-filings.json","utf8"));
const ipoData=JSON.parse(fs.readFileSync("data/ipos.json","utf8"));

assert.match(index,/href="drhp\.html"[^>]*>Pre-IPO companies<\/a>/);
assert.match(html,/Companies that have filed for an IPO\./);
assert.match(html,/progress into the published IPO pipeline are hidden automatically/i);
assert.match(html,/assets\/pre-ipo-filter\.js/);
assert.doesNotMatch(html,/Filing records/);
assert.doesNotMatch(html,/DRHP filing companies/);
assert.match(html,/id="drhpSearch"/);
assert.match(html,/Primary SEBI source/);
assert.match(html,/official lead-manager/i);
assert.match(app,/fetch\("data\/drhp-filings\.json"/);
assert.match(app,/fetch\("data\/ipos\.json"/);
assert.match(app,/PreIpoFilter\.activeCompanies/);
assert.match(app,/status status--upcoming">DRHP filed/);
assert.match(app,/No fuzzy issuer matching is used/);
assert.match(app,/stop_reason !== "first_page_strictly_older_than_year"/);
assert.match(app,/drhpIntegrityNote/);

const sandbox={};
vm.runInNewContext(filterCode,sandbox,{filename:"assets/pre-ipo-filter.js"});
const filter=sandbox.PreIpoFilter;
assert.ok(filter);
assert.equal(filter.canonicalIssuer("Example & Sons Ltd."),"example and sons");
assert.equal(filter.canonicalIssuer("EXAMPLE AND SONS LIMITED"),"example and sons");

const companies=[
  {issuer_name:"Pure Draft Limited"},
  {issuer_name:"Future & Co. Ltd."},
  {issuer_name:"Open Company Limited"},
  {issuer_name:"Closed Company Limited"},
  {issuer_name:"Listed Company Limited"},
  {issuer_name:"Date Trigger Limited"},
  {issuer_name:"Similar Company India Limited"},
];
const records=[
  {issuer_name:"Future and Co Limited",status:"upcoming",open_date:{value:null},close_date:{value:null},listing_date:{value:null}},
  {issuer_name:"Open Company Limited",status:"open",open_date:{value:"2026-10-01"},close_date:{value:null},listing_date:{value:null}},
  {issuer_name:"Closed Company Limited",status:"closed",open_date:{value:"2026-09-01"},close_date:{value:"2026-09-03"},listing_date:{value:null}},
  {issuer_name:"Listed Company Limited",status:"listed",open_date:{value:"2026-08-01"},close_date:{value:"2026-08-03"},listing_date:{value:"2026-08-10"}},
  {issuer_name:"Date Trigger Limited",status:"upcoming",open_date:{value:"2026-11-01"},close_date:{value:null},listing_date:{value:null}},
  {issuer_name:"Similar Company Limited",status:"listed",open_date:{value:"2020-01-01"},close_date:{value:"2020-01-03"},listing_date:{value:"2020-01-10"}},
];
assert.deepEqual(
  Array.from(filter.activeCompanies(companies,records),x=>x.issuer_name),
  ["Pure Draft Limited","Similar Company India Limited"],
  "hide exact canonical issuers once they progress, but do not fuzzy-match different legal names",
);
assert.equal(filter.hasProgressed({issuer_name:"X",status:"upcoming"}),true);
assert.equal(filter.hasProgressed({issuer_name:"X",status:"draft",open_date:{value:"2026-10-01"}}),true);
assert.equal(filter.hasProgressed({issuer_name:"X",status:"draft"}),false);

const currentActive=Array.from(filter.activeCompanies(data.companies,ipoData.records));
const currentProgressed=data.companies.length-currentActive.length;
assert.ok(currentActive.length<=data.companies.length);
for(const company of currentActive){
  const key=filter.canonicalIssuer(company.issuer_name);
  assert.equal(ipoData.records.some(record=>filter.canonicalIssuer(record.issuer_name)===key&&filter.hasProgressed(record)),false);
}

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
  assert.match(company.latest_filing_url,/^https:\/\/(?:www\.sebi\.gov\.in\/filings\/public-issues\/|www\.axiscapital\.co\.in\/contents\/)/);
  for(const filing of company.filings.filter(f=>f.source_kind==="official_lead_manager")){
    assert.equal(filing.source_authority,"Axis Capital Limited");
    assert.equal(filing.date_basis,"lead_manager_document_upload_timestamp");
  }
  assert.match(company.latest_filing_date,/^2026-\d\d-\d\d$/);
  assert.ok(company.filing_count>=1);
}
console.log(JSON.stringify({pre_ipo_company_ui_tests:{
  source_companies:data.companies.length,
  active_pre_ipo_companies:currentActive.length,
  progressed_hidden:currentProgressed,
  retained_source_filings:data.coverage.filing_records,
  lifecycle_filter:true,
  exact_canonical_identity:true,
  no_fuzzy_matching:true,
  source_backed:true,
  lead_manager_fallback_supported:true,
}}));
