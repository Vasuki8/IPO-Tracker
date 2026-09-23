import assert from "node:assert/strict";
import { parseBseEquityIssuePage, parseBseListingNotice } from "./extract-bse-ipo-fields.mjs";
const issue=`<div>Book Building - Live Security Type Equity Symbol GROWW Issue Period 04 Nov 2025 to 07 Nov 2025 Issue Size – No. of Shares 36,47,76,528 Price Band 95.00-100.00 Face Value 2.00 Market Lot 150 Minimum Bid Quantity 150 Book Running Lead Manager X</div>`;
assert.deepEqual(parseBseEquityIssuePage(issue),{symbol:"GROWW",issue_size_shares:364776528,price_band:{min:95,max:100},market_lot:150,minimum_bid_quantity:150,open_date_raw:"04 Nov 2025",close_date_raw:"07 Nov 2025"});
assert.equal(parseBseEquityIssuePage("<div>Security Type Secured Redeemable non-convertible Debentures</div>"),null);
const notice=`<div>Subject Listing of Equity Shares of 3B Films Limited Attachments Annexure I.pdf Content Trading Members are informed that effective from Friday, June 6, 2025, the Equity Shares shall be listed. Market Lot 3000 Issue Price for the current Public issue Rs. 50/- per share</div>`;
const n=parseBseListingNotice(notice); assert.equal(n.company,"3B Films Limited");assert.equal(n.listing_date_raw,"June 6, 2025");assert.equal(n.market_lot,3000);assert.equal(n.issue_price,50);
console.log("BSE detail/listing parser tests passed.");
