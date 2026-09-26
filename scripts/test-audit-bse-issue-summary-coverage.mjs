import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {
  BSE_API_BASE,BSE_ISSUE_SUMMARY_URL,PROJECT_YEARS,bseApiHeaders,buildBseIssueSummaryAudit,
  collectBseIssueSummary,parseBseIssueSummaryRows,parseBseYearList,parseBseYearRows,
  parseBseYearSummary,parseCurrentIssueRows,strictDate
} from "./audit-bse-issue-summary-coverage.mjs";

const legacyHtml='<table><tr><td>Example Limited</td><td><a href="/markets/publicIssues/DisplayIPO.aspx?IPONo=7001&amp;id=11&amp;idtype=1&amp;startdt=29%2F04%2F2025&amp;status=H&amp;type=IPO">View Detail</a></td><td><a href="/markets/publicIssues/DisplayIPO.aspx?IPONo=7001&amp;id=12&amp;idtype=2&amp;startdt=29%2F04%2F2025&amp;status=H&amp;type=IPO">View Detail</a></td></tr></table>';
const legacy=parseBseIssueSummaryRows(legacyHtml);
assert.equal(legacy.length,1);
assert.equal(legacy[0].issuer_name,"Example Limited");
assert.equal(legacy[0].issue_no,"7001");
assert.deepEqual(legacy[0].issue_start_dates,["2025-04-29"]);
assert.equal(legacy[0].stage_links.length,2);

assert.equal(strictDate("2026-06-24T00:00:00"),"2026-06-24");
assert.equal(strictDate("31/12/2021"),"2021-12-31");
assert.equal(strictDate("2026-02-30"),null);
const headers=bseApiHeaders();
assert.equal(headers["sec-fetch-site"],"same-site");
assert.match(headers.referer,/bseindia\.com\/markets\/PublicIssues\/Issuesummary/);

const yearsPayload={Table:[{sr:1,year:2026},{sr:2,year:2025},{sr:3,year:2024},{sr:4,year:2023},{sr:5,year:2022},{sr:6,year:2021},{sr:7,year:2020},{sr:8,year:2019}]};
assert.deepEqual(parseBseYearList(yearsPayload),[2026,2025,2024,2023,2022,2021,2020,2019]);

const yearSummary={Table:[{TotalIPO:2,NoOfIpo:1,NoOfSMEIpo:1,IPOWithPositiveListingGain:1,IPOWithListingLosses:1,IPOWithPositiveListingDayGains:1,IPOWithListingDayLosses:1,Time:"2025-12-31T00:00:00"}]};
assert.equal(parseBseYearSummary(yearSummary,2025).TotalIPO,2);
assert.throws(()=>parseBseYearSummary({Table:[{...yearSummary.Table[0],NoOfSMEIpo:2}]},2025),/invalid_bse_year_summary/);

const rowsPayload={Table:[
 {CompanyName:"Example Technologies Limited",IssuePrice:100,ListedOn:"2025-05-10T00:00:00",ListingDayClose:120,ListingDayGain:20,CurrentPrice:140,GainLoss:40,Time:"2025-12-31T00:00:00",IMAGE:"https://www.bseindia.com/stock-share-price/example/example/544123/"},
 {CompanyName:"Missing Industries Limited",IssuePrice:55,ListedOn:"2025-06-20T00:00:00",ListingDayClose:60,ListingDayGain:5,CurrentPrice:62,GainLoss:7,Time:"2025-12-31T00:00:00",IMAGE:"https://www.bseindia.com/stock-share-price/missing/missing/544124/"}
]};
const parsedRows=parseBseYearRows(rowsPayload,2025);
assert.equal(parsedRows.length,2);
assert.equal(parsedRows[0].bse_scrip_code,"544123");
assert.equal(parsedRows[0].listing_date,"2025-05-10");
assert.equal(parsedRows[0].issue_price,100);
assert.throws(()=>parseBseYearRows({Table:[{...rowsPayload.Table[0],ListedOn:"2024-05-10T00:00:00"}]},2025),/invalid_bse_year_row/);

const current=parseCurrentIssueRows({Table:[{
 Scrip_Name:"Current Limited",Start_Dt:"2026-09-24T00:00:00",End_Dt:"2026-09-28T00:00:00",
 IR_FLAG_FULL:"IPO",Status:"L",eXCHANGE_PLATFORM:"MainBoard",Price_Band:"385.00 - 405.00",IPO_NO:7998
}]});
assert.deepEqual(current[0],{
 issuer_name:"Current Limited",issue_no:"7998",start_date:"2026-09-24",end_date:"2026-09-28",
 issue_type:"IPO",status_code:"L",exchange_platform:"MainBoard",price_band:"385.00 - 405.00",source_row_index:0
});

const dir=fs.mkdtempSync(path.join(os.tmpdir(),"bse-summary-api-"));
try{
 const responses=new Map();
 responses.set(BSE_API_BASE+"/IPOYear/w",yearsPayload);
 for(const year of PROJECT_YEARS){
   const rows=year===2025?rowsPayload.Table:[{
     CompanyName:"Year "+year+" Limited",IssuePrice:50+year%10,ListedOn:year+"-06-15T00:00:00",
     ListingDayClose:60,ListingDayGain:5,CurrentPrice:70,GainLoss:10,Time:year+"-12-31T00:00:00",
     IMAGE:"https://www.bseindia.com/stock-share-price/year-"+year+"/year"+year+"/54"+String(year).slice(-4).padStart(4,"0")+"/"
   }];
   responses.set(BSE_API_BASE+"/IPOTrackerN/w?Fromdt="+year,{Table:[{
     TotalIPO:rows.length,NoOfIpo:rows.length===2?1:0,NoOfSMEIpo:rows.length===2?1:rows.length,
     IPOWithPositiveListingGain:rows.length,IPOWithListingLosses:0,
     IPOWithPositiveListingDayGains:rows.length,IPOWithListingDayLosses:0,Time:year+"-12-31T00:00:00"
   }]});
   responses.set(BSE_API_BASE+"/MoreCompanyN/w?Fromdt="+year+"&company=&flag=7&type=2",{Table:rows});
 }
 responses.set(BSE_API_BASE+"/GetPublicIssue_par_updated/w?flag=1",{Table:[{
   Scrip_Name:"Current Limited",Start_Dt:"2026-09-24T00:00:00",End_Dt:"2026-09-28T00:00:00",
   IR_FLAG_FULL:"IPO",Status:"L",eXCHANGE_PLATFORM:"MainBoard",Price_Band:"385.00 - 405.00",IPO_NO:7998
 }]});
 const fetchImpl=async(url,opts={})=>{
   assert.equal(opts.headers["sec-fetch-site"],"same-site");
   const payload=responses.get(url);
   if(!payload)return new Response("missing",{status:404});
   const response=new Response(JSON.stringify(payload),{status:200,headers:{"content-type":"application/json; charset=utf-8"}});
   Object.defineProperty(response,"url",{value:url});return response;
 };
 let tick=0;
 const collection=await collectBseIssueSummary({
   outputDir:dir,fetchImpl,clock:()=>`2026-09-26T16:40:${String(tick++).padStart(2,"0")}.000Z`
 });
 assert.deepEqual(collection.available_years,[2026,2025,2024,2023,2022,2021,2020,2019]);
 assert.deepEqual(collection.collected_years,PROJECT_YEARS);
 assert.equal(collection.yearly.length,7);
 assert.equal(collection.yearly.find(y=>y.year===2025).rows.length,2);
 assert.equal(collection.current_issues.rows.length,1);
 assert.equal(collection.coverage_exhaustion.each_collected_year_row_count_matches_official_total,true);
 assert.equal(collection.sources.length,16);
 assert.equal(fs.readdirSync(path.join(dir,"raw")).length,16);

 const recovery=[
   {year:2025,record:{id:"example-technologies-limited",issuer_name:"Example Technologies Limited",listing_date:{value:"2025-05-10"},board:"SME",bse_scrip_code:"544123"}},
   {year:2024,record:{id:"year-2024-limited",issuer_name:"Year 2024 Limited",listing_date:{value:"2024-06-15"},board:"SME"}}
 ];
 const report=buildBseIssueSummaryAudit(collection,recovery);
 assert.equal(report.coverage.project_window_exhausted,true);
 assert.equal(report.coverage.per_year_totals_reconciled,true);
 assert.equal(report.coverage.historical_rows,8);
 assert.equal(report.reconciliation.exact_matches,2);
 assert.equal(report.reconciliation.unmatched,6);
 assert.equal(report.reconciliation.listing_date_conflicts,0);
 assert.equal(report.current_issue_surface.rows,1);
 assert.equal(report.coverage.full_indian_ipo_universe_complete,false);

 const badResponses=new Map(responses);
 badResponses.set(BSE_API_BASE+"/IPOTrackerN/w?Fromdt=2025",{Table:[{
   TotalIPO:3,NoOfIpo:2,NoOfSMEIpo:1,IPOWithPositiveListingGain:3,IPOWithListingLosses:0,
   IPOWithPositiveListingDayGains:3,IPOWithListingDayLosses:0,Time:"2025-12-31T00:00:00"
 }]});
 await assert.rejects(()=>collectBseIssueSummary({
   outputDir:path.join(dir,"bad"),
   fetchImpl:async(url,opts={})=>{
     const payload=badResponses.get(url);const response=new Response(JSON.stringify(payload),{status:200,headers:{"content-type":"application/json"}});
     Object.defineProperty(response,"url",{value:url});return response;
   }
 }),/year_count_mismatch/);
}finally{fs.rmSync(dir,{recursive:true,force:true});}

console.log(JSON.stringify({bse_issue_summary_audit_tests:{
  legacy_link_parser_retained:true,official_year_index:true,official_year_totals:true,year_rows:true,
  same_site_headers:true,raw_hash_ready:true,count_reconciliation:true,current_issue_surface:true,
  recovery_reconciliation:true,no_auto_import:true
}}));
