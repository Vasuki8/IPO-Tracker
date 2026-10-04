import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import assert from "node:assert/strict";
import { applyBseParsedFields, buildBseOnlyRecoveryRecord, parseBseEquityIssuePage, parseBseListingNotice } from "./extract-bse-ipo-fields.mjs";
const issue=`<div>Book Building - Live Security Type Equity Symbol GROWW Issue Period 04 Nov 2025 to 07 Nov 2025 Issue Size – No. of Shares 36,47,76,528 Price Band 95.00-100.00 Face Value 2.00 Market Lot 150 Minimum Bid Quantity 150 Book Running Lead Manager X</div>`;
assert.deepEqual(parseBseEquityIssuePage(issue),{symbol:"GROWW",issue_size_shares:364776528,price_band:{min:95,max:100},issue_price:null,market_lot:150,minimum_bid_quantity:150,open_date_raw:"04 Nov 2025",close_date_raw:"07 Nov 2025"});
assert.equal(parseBseEquityIssuePage("<div>Security Type Secured Redeemable non-convertible Debentures</div>"),null);
const notice=`<div>Category Company related Segment SME Subject Listing of Equity Shares of 3B Films Limited Attachments Annexure I.pdf Content Trading Members are informed that effective from Friday, June 6, 2025, the Equity Shares shall be listed. Market Lot 3000 Issue Price for the current Public issue Rs. 50/- per share</div>`;
const n=parseBseListingNotice(notice); assert.equal(n.company,"3B Films Limited");assert.equal(n.listing_date_raw,"June 6, 2025");assert.equal(n.market_lot,3000);assert.equal(n.issue_price,50);assert.equal(n.board,"SME");
console.log("BSE detail/listing parser tests passed.");

const record={issuer_name:"3B Films Limited",listing_date:{value:null},issue_price:{value:null},market_lot:{value:null},documents:[]};
const applied=applyBseParsedFields(record,{issuer_name:"3B Films Limited",kind:"listing_notice",url:"https://www.bseindia.com/notice",publication_date:"2025-06-05"},n,"2026-09-23T16:30:00Z");
assert.equal(applied.changed,true);assert.deepEqual(applied.conflicts,[]);
assert.equal(record.listing_date.value,"2025-06-06");assert.equal(record.issue_price.value,50);assert.equal(record.market_lot.value,3000);
assert.equal(record.documents[0].type,"BSE Listing Notice");
const conflictRecord={issuer_name:"3B Films Limited",listing_date:{value:"2025-06-07"},issue_price:{value:null},market_lot:{value:null},documents:[]};
const conflicted=applyBseParsedFields(conflictRecord,{issuer_name:"3B Films Limited",kind:"listing_notice",url:"https://www.bseindia.com/notice"},n,"2026-09-23T16:30:00Z");
assert.equal(conflicted.conflicts[0].field,"listing_date");assert.equal(conflictRecord.listing_date.value,"2025-06-07");

const fixedIssue = parseBseEquityIssuePage(`<div>Fixed Price - Historical Security Type Equity Symbol KENRIK Issue Period 29 Apr 2025 to 06 May 2025 Issue Size (No. of Shares) 3498000 Issue Price 25.00 Market Lot 6000 Minimum Bid Quantity 6000</div>`);
assert.equal(fixedIssue.issue_price,25);
assert.equal(fixedIssue.issue_size_shares,3498000);

const bseOnlyFromIssueDetail = buildBseOnlyRecoveryRecord(
  {year:2025,issuer_name:"Kenrik Industries Limited",kind:"issue_detail",materialize_if_missing:true,url:"https://www.bseindia.com/markets/publicIssues/DisplayIPO.aspx?IPONo=7058",publication_date:null},
  fixedIssue,
  "2026-09-23T20:30:00Z"
);
assert.equal(bseOnlyFromIssueDetail,null);

const bseOnlyListing = buildBseOnlyRecoveryRecord(
  {year:2025,issuer_name:"3B Films Limited",kind:"listing_notice",materialize_if_missing:true,url:"https://www.bseindia.com/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=20250605-49",publication_date:"2025-06-05"},
  n,
  "2026-09-23T20:30:00Z"
);
assert.equal(bseOnlyListing.status,"listed");assert.equal(bseOnlyListing.board,"SME");
assert.equal(bseOnlyListing.status_evidence.length,1);
assert.equal(bseOnlyListing.listing_date.value,"2025-06-06");

assert.equal(
  buildBseOnlyRecoveryRecord(
    {year:2025,issuer_name:"Wrong Limited",kind:"listing_notice",materialize_if_missing:true,url:"https://www.bseindia.com/x"},
    n,
    "2026-09-23T20:30:00Z"
  ),
  null
);
assert.equal(
  buildBseOnlyRecoveryRecord(
    {year:2025,issuer_name:"3B Films Limited",kind:"listing_notice",materialize_if_missing:false,url:"https://www.bseindia.com/x"},
    n,
    "2026-09-23T20:30:00Z"
  ),
  null
);

const nseTermsRecord={issuer_name:"Example Limited",nse_source:{url:"https://www.nseindia.com/api/ipo-detail?symbol=EXAMPLE&series=EQ",document_type:"NSE Issue Information API",document_identity:"NSE Issue Information — EXAMPLE",publication_date:null,collected_at:"2026-09-01T00:00:00Z"},terms:{market_lot:100,price_band:{min:90,max:100},open_date:"2026-09-01"},documents:[]};
const competingSource={issuer_name:"Example Limited",kind:"issue_detail",url:"https://www.bseindia.com/markets/publicIssues/DisplayIPO.aspx?IPONo=1",publication_date:null};
const competingParsed={market_lot:200,price_band:{min:110,max:120},open_date_raw:"02 Sep 2026"};
const competingResult=applyBseParsedFields(nseTermsRecord,competingSource,competingParsed,"2026-09-30T00:00:00Z");
assert.equal(nseTermsRecord.market_lot.value,100,"BSE enrichment must retain existing NSE terms on disagreement");
assert.equal(nseTermsRecord.market_lot.status,"conflict");
assert.equal(nseTermsRecord.market_lot.source.url,nseTermsRecord.nse_source.url);
assert.equal(nseTermsRecord.market_lot.additional_sources[0].url,competingSource.url);
assert.equal(nseTermsRecord.market_lot.corrections[0].competing.value,200);
assert.deepEqual(nseTermsRecord.price_band.value,{min:90,max:100});
assert.equal(nseTermsRecord.open_date.value,"2026-09-01");
assert.equal(competingResult.conflicts.length,3);
const competingSnapshot=structuredClone(nseTermsRecord);
assert.equal(applyBseParsedFields(nseTermsRecord,competingSource,competingParsed,"2026-10-01T00:00:00Z").changed,false,"Repeated competing disclosure must be idempotent");
assert.deepEqual(nseTermsRecord,competingSnapshot);
const matchingRecord={issuer_name:"Example Limited",nse_source:structuredClone(nseTermsRecord.nse_source),terms:{market_lot:100},documents:[]};
assert.equal(applyBseParsedFields(matchingRecord,competingSource,{market_lot:100},"2026-09-30T00:00:00Z").changed,true);
assert.equal(matchingRecord.market_lot.value,100);
assert.equal(matchingRecord.market_lot.status,"verified");
assert.equal(matchingRecord.market_lot.source.url,matchingRecord.nse_source.url);
assert.equal(matchingRecord.market_lot.additional_sources[0].url,competingSource.url);
const retainedConflict={issuer_name:"Example Limited",market_lot:{value:100,status:"provisional",page:4,source:structuredClone(nseTermsRecord.nse_source),corrections:[{kind:"prior_review"}]},documents:[]};
applyBseParsedFields(retainedConflict,competingSource,{market_lot:200},"2026-09-30T00:00:00Z");
assert.equal(retainedConflict.market_lot.status,"conflict");
assert.equal(retainedConflict.market_lot.value,100);
assert.equal(retainedConflict.market_lot.page,4);
assert.equal(retainedConflict.market_lot.corrections[0].kind,"prior_review");
console.log("BSE terms fallback, competing evidence, corroboration and rerun tests passed.");

const previouslyMissing={issuer_name:"Example Limited",nse_source:structuredClone(nseTermsRecord.nse_source),terms:{market_lot:100},market_lot:{value:null,status:"missing",corrections:[{kind:"retained_prior_review"}]},documents:[]};
applyBseParsedFields(previouslyMissing,competingSource,{market_lot:200},"2026-09-30T00:00:00Z");
assert.equal(previouslyMissing.market_lot.corrections[0].kind,"retained_prior_review","Fallback materialization must preserve correction history");
const projectionRoot=fs.mkdtempSync(path.join(os.tmpdir(),"bse-competing-projection-"));
try {
 fs.mkdirSync(path.join(projectionRoot,"scripts"));
 for(const script of ["build-published-data.mjs","publish-field-status.mjs","ipo-instrument-policy.mjs","validate-data.mjs"])fs.copyFileSync(new URL(script,import.meta.url),path.join(projectionRoot,"scripts",script));
 fs.mkdirSync(path.join(projectionRoot,"assets"));
 fs.copyFileSync(new URL("../assets/ipo-order.js",import.meta.url),path.join(projectionRoot,"assets/ipo-order.js"));
 fs.mkdirSync(path.join(projectionRoot,"data/recovery/2026"),{recursive:true});
 fs.copyFileSync(new URL("../data/ipo-schema.json",import.meta.url),path.join(projectionRoot,"data/ipo-schema.json"));
 const projectedRecord={...structuredClone(nseTermsRecord),id:"example-limited",board:null,status:"listed",board_evidence:[],status_evidence:[nseTermsRecord.nse_source],first_observed_at:"2026-09-01T00:00:00Z"};
 fs.writeFileSync(path.join(projectionRoot,"data/recovery/2026/nse-issue-information.json"),JSON.stringify({collection_started_at:"2026-09-01T00:00:00Z",generated_at:"2026-09-30T00:00:00Z",records:[projectedRecord]}));
 execFileSync(process.execPath,["scripts/build-published-data.mjs"],{cwd:projectionRoot});
 execFileSync(process.execPath,["scripts/validate-data.mjs"],{cwd:projectionRoot});
 const publicRecord=JSON.parse(fs.readFileSync(path.join(projectionRoot,"data/ipos.json"))).records[0];
 assert.equal(publicRecord.market_lot.value,100);
 assert.equal(publicRecord.market_lot.status,"conflict");
 assert.deepEqual(publicRecord.market_lot.evidence.map(e=>e.url),[nseTermsRecord.nse_source.url,competingSource.url]);
 assert.equal(publicRecord.market_lot.corrections[0].competing.value,200);
} finally {fs.rmSync(projectionRoot,{recursive:true,force:true});}
console.log("Real publisher retains competing field evidence and validates the public contract.");
