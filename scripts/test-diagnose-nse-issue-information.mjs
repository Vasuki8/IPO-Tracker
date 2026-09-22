import assert from "node:assert/strict";
import { parseIssueInformationBidTerms } from "./diagnose-nse-issue-information.mjs";

const parsed = parseIssueInformationBidTerms(`
  <table>
    <tr><th>Bid Lot</th><td>8 Equity Shares and in multiples thereof</td></tr>
    <tr><th>Minimum Order Quantity</th><td>8 Equity Shares</td></tr>
  </table>
`);

assert.equal(parsed.bid_lot, 8);
assert.equal(parsed.minimum_order_quantity, 8);
assert.equal(parsed.contexts.length, 2);

const missing = parseIssueInformationBidTerms(
  "<div>Bid Lot will be decided later. Minimum Order Quantity [●]</div>"
);
assert.equal(missing.bid_lot, null);
assert.equal(missing.minimum_order_quantity, null);

console.log("NSE Issue Information diagnostic parser tests passed.");
