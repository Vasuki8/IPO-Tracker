import assert from "node:assert/strict";
import { applyBseParsedFields, parseBseEquityIssuePage, parseBseListingNotice } from "./extract-bse-ipo-fields.mjs";
const issue=`<div>Book Building - Live Security Type Equity Symbol GROWW Issue Period 04 Nov 2025 to 07 Nov 2025 Issue Size – No. of Shares 36,47,76,528 Price Band 95.00-100.00 Face Value 2.00 Market Lot 150 Minimum Bid Quantity 150 Book Running Lead Manager X</div>`;
assert.deepEqual(parseBseEquityIssuePage(issue),{symbol:"GROWW",issue_size_shares:364776528,price_band:{min:95,max:100},market_lot:150,minimum_bid_quantity:150,open_date_raw:"04 Nov 2025",close_date_raw:"07 Nov 2025"});
assert.equal(parseBseEquityIssuePage("<div>Security Type Secured Redeemable non-convertible Debentures</div>"),null);
const notice=`<div>Subject Listing of Equity Shares of 3B Films Limited Attachments Annexure I.pdf Content Trading Members are informed that effective from Friday, June 6, 2025, the Equity Shares shall be listed. Market Lot 3000 Issue Price for the current Public issue Rs. 50/- per share</div>`;
const n=parseBseListingNotice(notice); assert.equal(n.company,"3B Films Limited");assert.equal(n.listing_date_raw,"June 6, 2025");assert.equal(n.market_lot,3000);assert.equal(n.issue_price,50);
console.log("BSE detail/listing parser tests passed.");

const record={issuer_name:"3B Films Limited",listing_date:{value:null},issue_price:{value:null},market_lot:{value:null},documents:[]};
const applied=applyBseParsedFields(record,{issuer_name:"3B Films Limited",kind:"listing_notice",url:"https://www.bseindia.com/notice",publication_date:"2025-06-05"},n,"2026-09-23T16:30:00Z");
assert.equal(applied.changed,true);assert.deepEqual(applied.conflicts,[]);
assert.equal(record.listing_date.value,"2025-06-06");assert.equal(record.issue_price.value,50);assert.equal(record.market_lot.value,3000);
assert.equal(record.documents[0].type,"BSE Listing Notice");
const conflictRecord={issuer_name:"3B Films Limited",listing_date:{value:"2025-06-07"},issue_price:{value:null},market_lot:{value:null},documents:[]};
const conflicted=applyBseParsedFields(conflictRecord,{issuer_name:"3B Films Limited",kind:"listing_notice",url:"https://www.bseindia.com/notice"},n,"2026-09-23T16:30:00Z");
assert.equal(conflicted.conflicts[0].field,"listing_date");assert.equal(conflictRecord.listing_date.value,"2025-06-07");
