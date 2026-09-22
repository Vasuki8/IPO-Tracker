import assert from "node:assert/strict";
import fs from "node:fs";
import {
  applyIssueSizeExtraction,
  candidateAbridgedDocument,
  candidateAbridgedMinimumBidDocument,
  findMinimumBidMentions,
  parseExplicitTotalIssueSize
} from "./extract-abridged-fields.mjs";

const fixture = JSON.parse(
  fs.readFileSync(new URL("./fixtures/abridged-issue-size-layout.json", import.meta.url), "utf8")
);

for (const testCase of fixture.cases) {
  const extracted = parseExplicitTotalIssueSize(testCase.layout);
  assert.equal(extracted?.value ?? null, testCase.expected, testCase.name);
  if (testCase.expected !== null) {
    assert.equal(extracted.page, 1);
    assert.match(extracted.source_value, /^₹/);
  }
}

const doc = {
  type: "SEBI Abridged Prospectus",
  identity: "Example Limited - Abridged Prospectus",
  url: "https://www.sebi.gov.in/sebi_data/commondocs/sep-2026/example-ap.pdf",
  publication_date: "2026-09-01"
};

const record = {
  issuer_name: "Example Limited",
  issue_size_inr: undefined,
  documents: [doc],
  last_collected_at: "2026-09-20T00:00:00Z"
};

assert.equal(candidateAbridgedDocument(record), doc);
assert.equal(candidateAbridgedMinimumBidDocument(record), doc);

const minBidMentions = findMinimumBidMentions(
  "BIDS CAN BE MADE FOR A MINIMUM OF 100 EQUITY SHARES AND IN MULTIPLES OF 100 EQUITY SHARES THEREAFTER."
);
assert.equal(minBidMentions.length, 1);
assert.match(minBidMentions[0], /MINIMUM OF 100 EQUITY SHARES/i);
assert.equal(
  applyIssueSizeExtraction(
    record,
    doc,
    { value: 8750000000, source_value: "₹8,750.00 million", page: 1 },
    "2026-09-22T04:30:00Z"
  ),
  true
);
assert.equal(record.issue_size_inr.value, 8750000000);
assert.equal(record.issue_size_inr.page, 1);
assert.equal(record.issue_size_inr.source.url, doc.url);
assert.equal(record.last_collected_at, "2026-09-22T04:30:00Z");

const existing = {
  issuer_name: "Existing Limited",
  issue_size_inr: { value: 123, source: { url: "https://example.com" } },
  documents: [doc]
};
assert.equal(candidateAbridgedDocument(existing), null);
assert.equal(candidateAbridgedMinimumBidDocument({
  ...existing,
  issue_size_inr: undefined,
  minimum_bid_quantity: { value: 50, source: { url: "https://example.com" } }
}), null);
assert.equal(candidateAbridgedMinimumBidDocument({
  ...existing,
  issue_size_inr: undefined,
  minimum_bid_quantity: undefined,
  terms: { minimum_bid_quantity: 75 }
}), null);
assert.equal(
  applyIssueSizeExtraction(
    existing,
    doc,
    { value: 8750000000, source_value: "₹8,750.00 million", page: 1 },
    "2026-09-22T04:30:00Z"
  ),
  false
);
assert.equal(existing.issue_size_inr.value, 123);

console.log("Abridged Prospectus issue-size extraction tests passed.");
