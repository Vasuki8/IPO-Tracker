import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {
  BSE_ISSUE_SUMMARY_URL,buildBseIssueSummaryAudit,buildPostBackBody,chooseNextPagerEvent,
  collectBseIssueSummary,parseAspNetState,parseBseIssueSummaryRows
} from "./audit-bse-issue-summary-coverage.mjs";

const page=(rows,pager="",view="v1")=>`<html><form>
<input type="hidden" name="__VIEWSTATE" value="${view}">
<input type="hidden" name="__EVENTVALIDATION" value="ev">
<table><tr><th>Company Name</th><th>In-Principle Stage</th><th>Listing Stage</th></tr>
${rows.join("\n")}</table>${pager}</form></html>`;
const row=(name,issue,start,type="IPO",status="H")=>`<tr><td>${name}</td>
<td><a href="/markets/publicIssues/DisplayIPO.aspx?IPONo=${issue}&amp;id=${issue}1&amp;idtype=1&amp;startdt=${encodeURIComponent(start)}&amp;status=${status}&amp;type=${type}">View Detail</a></td>
<td><a href="/markets/publicIssues/DisplayIPO.aspx?IPONo=${issue}&amp;id=${issue}2&amp;idtype=2&amp;startdt=${encodeURIComponent(start)}&amp;status=${status}&amp;type=${type}">View Detail</a></td></tr>`;
const pager2=`<a href="javascript:__doPostBack('ctl00$Main$Grid','Page$2')">2</a><a href="javascript:__doPostBack('ctl00$Main$Grid','Page$Next')">Next</a>`;
const html1=page([row("Example Technologies Limited","7001","29/04/2025"),row("Cross Year Limited","7002","31/12/2021","FPO")],pager2,"v1");
const parsed=parseBseIssueSummaryRows(html1);
assert.equal(parsed.length,2);
assert.equal(parsed[0].issuer_name,"Example Technologies Limited");
assert.equal(parsed[0].issue_no,"7001");
assert.deepEqual(parsed[0].issue_start_dates,["2025-04-29"]);
assert.equal(parsed[0].stage_links.length,2);
assert.deepEqual(parsed[1].issue_types,["FPO"]);
assert.equal(chooseNextPagerEvent(html1,1).argument,"Page$2");
assert.equal(parseAspNetState(html1).hidden.__VIEWSTATE,"v1");
const body=buildPostBackBody(html1,{target:"ctl00$Main$Grid",argument:"Page$2"});
assert.equal(body.get("__VIEWSTATE"),"v1");
assert.equal(body.get("__EVENTTARGET"),"ctl00$Main$Grid");
assert.equal(body.get("__EVENTARGUMENT"),"Page$2");

const html2=page([row("Missing Industries Limited","7003","15-03-2020")],"","v2");
const dir=fs.mkdtempSync(path.join(os.tmpdir(),"bse-summary-"));
try{
 let calls=0;
 const fetchImpl=async(url,opts={})=>{
   if(url==="https://www.bseindia.com/")return new Response("<html>home</html>",{status:200,headers:{"set-cookie":"session=x; Path=/"}});
   calls++;
   if(calls===1){
     assert.equal(opts.method,undefined);
     const response=new Response(html1,{status:200,headers:{"content-type":"text/html"}});
     Object.defineProperty(response,"url",{value:BSE_ISSUE_SUMMARY_URL});return response;
   }
   assert.equal(opts.method,"POST");
   assert.match(String(opts.body),/__EVENTARGUMENT=Page%242/);
   const response=new Response(html2,{status:200,headers:{"content-type":"text/html"}});
   Object.defineProperty(response,"url",{value:BSE_ISSUE_SUMMARY_URL});return response;
 };
 let tick=0;
 const collection=await collectBseIssueSummary({outputDir:dir,fetchImpl,clock:()=>`2026-09-26T16:20:${String(tick++).padStart(2,"0")}.000Z`,maxPages:5});
 assert.equal(collection.pages_fetched,2);
 assert.equal(collection.exhausted,true);
 assert.equal(collection.observations.length,3);
 assert.equal(fs.readdirSync(path.join(dir,"raw")).length,2);
 const recovery=[
  {year:2025,record:{id:"example-technologies-limited",issuer_name:"Example Technologies Limited",listing_date:{value:"2025-05-10"},board:"SME"}},
  {year:2022,record:{id:"cross-year-limited",issuer_name:"Cross Year Limited",listing_date:{value:"2022-01-10"},board:"SME"}}
 ];
 const report=buildBseIssueSummaryAudit(collection,recovery);
 assert.equal(report.coverage.unique_issue_groups,3);
 assert.deepEqual(report.coverage.issue_start_year_counts,{"2020":1,"2021":1,"2025":1});
 assert.equal(report.reconciliation.exact_matches,2);
 assert.equal(report.reconciliation.unmatched,1);
 assert.equal(report.reconciliation.cross_year_offer_listing,1);
 assert.equal(report.coverage.exhausted,true);
 assert.equal(report.coverage.full_historical_universe_complete,false);

 let repeat=0;
 await assert.rejects(()=>collectBseIssueSummary({
   outputDir:path.join(dir,"repeat"),
   fetchImpl:async(url)=>{
     if(url==="https://www.bseindia.com/")return new Response("home",{status:200});
     repeat++;
     const response=new Response(html1,{status:200,headers:{"content-type":"text/html"}});
     Object.defineProperty(response,"url",{value:BSE_ISSUE_SUMMARY_URL});return response;
   },maxPages:3
 }),/did_not_advance/);
}finally{fs.rmSync(dir,{recursive:true,force:true});}
console.log(JSON.stringify({bse_issue_summary_audit_tests:{rows:true,query_dates:true,pagination_postback:true,exhaustion:true,hash_ready:true,reconciliation:true,cross_year_semantics:true,non_advancing_guard:true}}));
