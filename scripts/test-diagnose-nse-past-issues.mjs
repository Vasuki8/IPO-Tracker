import assert from "node:assert/strict";
import {
  indexPastIssues,
  parsePastIssuePrice
} from "./diagnose-nse-past-issues.mjs";

assert.equal(parsePastIssuePrice(139), 139);
assert.equal(parsePastIssuePrice("139"), 139);
assert.equal(parsePastIssuePrice("Rs.139"), 139);
assert.equal(parsePastIssuePrice("₹139 per Equity Share"), 139);
assert.equal(parsePastIssuePrice("Rs.132 to Rs.139"), null);
assert.equal(parsePastIssuePrice("[●]"), null);
assert.equal(parsePastIssuePrice("N/A"), null);

const index = indexPastIssues([
  { symbol: "ARCIL", issuePrice: 139 },
  { symbol: "QUALIANCE", issuePrice: "127" }
]);
assert.equal(index.get("ARCIL").length, 1);
assert.equal(index.get("QUALIANCE")[0].issuePrice, "127");

console.log("NSE public-past-issues diagnostic tests passed.");
