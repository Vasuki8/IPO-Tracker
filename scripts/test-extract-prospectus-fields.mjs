import assert from "node:assert/strict";
import fs from "node:fs";
import {
  applyIssuePriceExtraction,
  applyIssueSizeExtraction,
  applyMinimumBidExtraction,
  candidateProspectusDocument,
  candidateProspectusIssueSizeDocument,
  candidateProspectusMinimumBidDocument,
  candidateRhpIssueSizeDocument,
  candidateRhpMinimumBidDocument,
  findMinimumBidMentionsInPages,
  findAggregateIssueSizeMentions,
  findIssuePriceMentions,
  parseExplicitAggregateIssueSizeFromPages,
  parseExplicitIssuePriceFromPages,
  parseExplicitMinimumBidQuantityFromPages
} from "./extract-prospectus-fields.mjs";

const fixture = JSON.parse(
  fs.readFileSync(new URL("./fixtures/prospectus-issue-price-layout.json", import.meta.url), "utf8")
);
const sizeFixture = JSON.parse(
  fs.readFileSync(new URL("./fixtures/prospectus-issue-size-layout.json", import.meta.url), "utf8")
);

for (const testCase of fixture.cases) {
  const extracted = parseExplicitIssuePriceFromPages(testCase.pages);
  assert.equal(extracted?.value ?? null, testCase.expected?.value ?? null, testCase.name);
  assert.equal(extracted?.page ?? null, testCase.expected?.page ?? null, testCase.name + " page");
  if (testCase.expected) assert.match(extracted.source_value, /^₹/);
}

for (const testCase of sizeFixture.cases) {
  const extracted = parseExplicitAggregateIssueSizeFromPages(testCase.pages);
  assert.equal(extracted?.value ?? null, testCase.expected?.value ?? null, testCase.name);
  assert.equal(extracted?.page ?? null, testCase.expected?.page ?? null, testCase.name + " page");
  if (testCase.expected) assert.match(extracted.source_value, /^₹/);
}

const explicitBidLot = parseExplicitMinimumBidQuantityFromPages([
  "Offer overview.",
  "Bid Lot 8 Equity Shares of face value of ₹1 each and in multiples of 8 Equity Shares thereafter."
]);
assert.equal(explicitBidLot.value, 8);
assert.equal(explicitBidLot.page, 2);

const explicitMinimumBid = parseExplicitMinimumBidQuantityFromPages([
  "Minimum Bid 161 Equity Shares of face value of ₹10 each."
]);
assert.equal(explicitMinimumBid.value, 161);
assert.equal(explicitMinimumBid.page, 1);

assert.equal(
  parseExplicitMinimumBidQuantityFromPages([
    "Anchor Investors may submit a minimum Bid of ₹100.00 million."
  ]),
  null
);
assert.equal(
  parseExplicitMinimumBidQuantityFromPages([
    "Bid Lot [●] Equity Shares and in multiples of [●] Equity Shares thereafter."
  ]),
  null
);

const diagnosticMentions = findIssuePriceMentions(
  "The Offer Price shall be finalised after the Book Building Process. Later, the Issue Price is ₹424 per Equity Share.",
  12
);
assert.equal(diagnosticMentions.length, 2);
assert.equal(diagnosticMentions[0].page, 12);
assert.match(diagnosticMentions[0].context, /Offer Price/);
assert.match(diagnosticMentions[1].context, /Issue Price/);

const issueSizeMentions = findAggregateIssueSizeMentions(
  "INITIAL PUBLIC OFFER AT A PRICE OF ₹93 PER EQUITY SHARE AGGREGATING UP TO ₹12,488.04 LAKHS (THE OFFER) COMPRISING A FRESH ISSUE AGGREGATING UP TO ₹9,989.27 LAKHS.",
  3
);
assert.equal(issueSizeMentions.length, 2);
assert.equal(issueSizeMentions[0].page, 3);
assert.match(issueSizeMentions[0].context, /12,488\.04 LAKHS/);

const doc = {
  type: "SEBI Prospectus PDF",
  identity: "Example Limited - Prospectus — PDF",
  url: "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/example.pdf",
  publication_date: "2026-09-21"
};

const record = {
  issuer_name: "Example Limited",
  issue_price: undefined,
  documents: [doc],
  last_collected_at: "2026-09-20T00:00:00Z"
};

assert.equal(candidateProspectusDocument(record), doc);
assert.equal(candidateProspectusIssueSizeDocument(record), doc);
assert.equal(candidateProspectusMinimumBidDocument({
  ...record,
  issue_size_inr: undefined,
  minimum_bid_quantity: undefined,
  terms: { minimum_bid_quantity: null }
}), doc);

const rhpDoc = {
  ...doc,
  type: "SEBI RHP PDF",
  identity: "Example Limited - RHP — PDF"
};
const rhpRecord = {
  issuer_name: "RHP Example Limited",
  issue_size_inr: undefined,
  documents: [rhpDoc]
};
assert.equal(candidateRhpIssueSizeDocument(rhpRecord), rhpDoc);
assert.equal(candidateRhpMinimumBidDocument(rhpRecord), rhpDoc);

const rhpMinBidMentions = findMinimumBidMentionsInPages([
  "Offer summary only.",
  "Bids can be made for a minimum of 8 Equity Shares and in multiples of 8 Equity Shares thereafter."
]);
assert.equal(rhpMinBidMentions.length, 2);
assert.equal(rhpMinBidMentions[0].page, 2);
assert.match(rhpMinBidMentions[0].context, /minimum of 8 Equity Shares/i);
assert.equal(
  applyIssuePriceExtraction(
    record,
    doc,
    { value: 93, source_value: "₹93 per Equity Share", page: 4 },
    "2026-09-22T05:00:00Z"
  ),
  true
);
assert.equal(record.issue_price.value, 93);
assert.equal(record.issue_price.page, 4);
assert.equal(record.issue_price.source.url, doc.url);
assert.equal(record.last_collected_at, "2026-09-22T05:00:00Z");

assert.equal(
  applyIssueSizeExtraction(
    record,
    doc,
    { value: 5000000000, source_value: "₹5,000.00 million", page: 3 },
    "2026-09-22T05:05:00Z"
  ),
  true
);
assert.equal(record.issue_size_inr.value, 5000000000);
assert.equal(record.issue_size_inr.page, 3);
assert.equal(record.issue_size_inr.source.url, doc.url);
assert.equal(record.last_collected_at, "2026-09-22T05:05:00Z");

assert.equal(
  applyMinimumBidExtraction(
    record,
    doc,
    { value: 8, source_value: "Bid Lot 8 Equity Shares", page: 10 },
    "2026-09-22T05:10:00Z"
  ),
  true
);
assert.equal(record.minimum_bid_quantity.value, 8);
assert.equal(record.minimum_bid_quantity.status, "verified");
assert.equal(record.minimum_bid_quantity.page, 10);
assert.equal(record.minimum_bid_quantity.source.url, doc.url);
assert.equal(record.last_collected_at, "2026-09-22T05:10:00Z");

const existing = {
  issuer_name: "Existing Limited",
  issue_price: { value: 88, source: { url: "https://example.com" } },
  issue_size_inr: { value: 1000, source: { url: "https://example.com" } },
  minimum_bid_quantity: { value: 5, source: { url: "https://example.com" } },
  documents: [doc]
};
assert.equal(candidateProspectusDocument(existing), null);
assert.equal(candidateProspectusIssueSizeDocument(existing), null);
assert.equal(candidateProspectusMinimumBidDocument({
  ...existing,
  minimum_bid_quantity: { value: 8, source: { url: "https://example.com" } },
  documents: [doc]
}), null);
assert.equal(candidateProspectusMinimumBidDocument({
  ...existing,
  minimum_bid_quantity: undefined,
  terms: { minimum_bid_quantity: 8 },
  documents: [doc]
}), null);
assert.equal(candidateRhpIssueSizeDocument({
  ...existing,
  documents: [{ ...doc, type: "SEBI RHP PDF" }]
}), null);
assert.equal(candidateRhpMinimumBidDocument({
  ...existing,
  minimum_bid_quantity: { value: 8, source: { url: "https://example.com" } },
  documents: [{ ...doc, type: "SEBI RHP PDF" }]
}), null);
assert.equal(candidateRhpMinimumBidDocument({
  ...existing,
  minimum_bid_quantity: undefined,
  terms: { minimum_bid_quantity: 8 },
  documents: [{ ...doc, type: "SEBI RHP PDF" }]
}), null);
assert.equal(
  applyIssuePriceExtraction(
    existing,
    doc,
    { value: 93, source_value: "₹93 per Equity Share", page: 4 },
    "2026-09-22T05:00:00Z"
  ),
  false
);
assert.equal(existing.issue_price.value, 88);
assert.equal(
  applyIssueSizeExtraction(
    existing,
    doc,
    { value: 5000000000, source_value: "₹5,000.00 million", page: 3 },
    "2026-09-22T05:05:00Z"
  ),
  false
);
assert.equal(existing.issue_size_inr.value, 1000);

assert.equal(
  applyMinimumBidExtraction(
    existing,
    doc,
    { value: 8, source_value: "Bid Lot 8 Equity Shares", page: 10 },
    "2026-09-22T05:10:00Z"
  ),
  false
);
assert.equal(existing.minimum_bid_quantity.value, 5);

const mirrorRecord = {
  issuer_name: "Mirror Limited",
  documents: [{ ...doc, url: "https://example.com/prospectus.pdf" }]
};
assert.equal(candidateProspectusDocument(mirrorRecord), null);

console.log("Prospectus issue-price extraction tests passed.");
