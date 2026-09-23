import assert from "node:assert/strict";
import fs from "node:fs";
import {
  applyIssuePriceExtraction,
  applyIssueSizeExtraction,
  applyMarketLotExtraction,
  applyPriceBandExtraction,
  applyMinimumBidExtraction,
  applyNiiMinimumApplicationExtraction,
  candidateProspectusDocument,
  candidateProspectusIssueSizeDocument,
  candidateProspectusMinimumBidDocument,
  candidateProspectusRetailMinimumApplicationDocument,
  candidateRhpIssueSizeDocument,
  candidateRhpMinimumBidDocument,
  candidateRhpMinimumApplicationDocument,
  candidateRhpNiiMinimumApplicationDocument,
  candidateRhpNiiMinimumBidDocument,
  findMinimumBidMentionsInPages,
  findMinimumApplicationAmountMentionsInPages,
  findExplicitNiiMinimumApplicationAmountsInPages,
  findExplicitRetailMinimumApplicationAmountsInPages,
  findExplicitNiiMinimumBidQuantitiesInPages,
  findAggregateIssueSizeMentions,
  findIssuePriceMentions,
  parseExplicitAggregateIssueSizeFromPages,
  parseExplicitIssuePriceFromPages,
  parseExplicitMarketLotFromPages,
  parseExplicitMinimumBidQuantityFromPages,
  parseExplicitPriceBandFromPages,
  shouldDeferHeavyHistoricalPdf
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

const explicitBand = parseExplicitPriceBandFromPages([
  "Price Band: ₹120 to ₹125 per Equity Share."
]);
assert.deepEqual(explicitBand.value, { min: 120, max: 125 });
assert.equal(explicitBand.page, 1);

assert.equal(
  parseExplicitPriceBandFromPages([
    "Price Band: ₹120 to ₹125 per Equity Share.",
    "Price Band: ₹121 to ₹125 per Equity Share."
  ]),
  null
);

assert.equal(
  parseExplicitPriceBandFromPages([
    "Issue Price ₹125 per Equity Share."
  ]),
  null
);

const explicitMarketLot = parseExplicitMarketLotFromPages([
  "Market Lot: 1,200 Equity Shares."
]);
assert.equal(explicitMarketLot.value, 1200);

assert.equal(
  parseExplicitMarketLotFromPages([
    "Bid Lot 1,200 Equity Shares."
  ]),
  null
);

assert.equal(
  parseExplicitMarketLotFromPages([
    "Market Lot: 1,200 Equity Shares.",
    "Lot Size: 1,000 Equity Shares."
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
  price_band: undefined,
  market_lot: undefined,
  terms: { price_band: null, market_lot: null },
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
assert.equal(candidateProspectusRetailMinimumApplicationDocument(record), doc);

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

assert.equal(candidateRhpMinimumApplicationDocument(rhpRecord), rhpDoc);
assert.equal(candidateRhpNiiMinimumApplicationDocument(rhpRecord), rhpDoc);
assert.equal(candidateRhpNiiMinimumBidDocument(rhpRecord), rhpDoc);

const rhpMinApplicationMentions = findMinimumApplicationAmountMentionsInPages([
  "Offer summary only.",
  "For Retail Individual Bidders, the Minimum Application Amount is ₹14,850.",
  "Minimum amount of application: INR 15,120 for Eligible Employees."
]);
assert.equal(rhpMinApplicationMentions.length, 2);
assert.equal(rhpMinApplicationMentions[0].page, 2);
assert.match(rhpMinApplicationMentions[0].context, /₹14,850/);
assert.equal(rhpMinApplicationMentions[1].page, 3);
assert.match(rhpMinApplicationMentions[1].context, /INR 15,120/i);

assert.deepEqual(
  findMinimumApplicationAmountMentionsInPages([
    "Anchor Investors may submit a minimum Bid of ₹100.00 million.",
    "Minimum Order Quantity is 40 Equity Shares.",
    "Maximum Application Amount is ₹2,00,000."
  ]),
  []
);

const retailMinimumApplications = findExplicitRetailMinimumApplicationAmountsInPages([
  "For Retail Individual Bidders, the Minimum Application Amount is ₹14,850.",
  "The Minimum Amount of Application: INR 15,120 for Retail Individual Investors."
]);
assert.equal(retailMinimumApplications.length, 2);
assert.equal(retailMinimumApplications[0].value, 14850);
assert.equal(retailMinimumApplications[0].page, 1);
assert.equal(retailMinimumApplications[1].value, 15120);
assert.equal(retailMinimumApplications[1].page, 2);

assert.deepEqual(
  findExplicitRetailMinimumApplicationAmountsInPages([
    "Retail Individual Bidders shall not submit applications above ₹200,000.",
    "The maximum application amount for Retail Individual Bidders is ₹200,000.",
    "Non-Institutional Investors shall have a minimum application size viz. ₹2.00 Lakhs."
  ]),
  []
);

const niiMinimumApplications = findExplicitNiiMinimumApplicationAmountsInPages([
  "Offer summary.",
  "The allocation to each Non-Institutional Investor shall not be less than the minimum application size viz. ₹ 0.20 million, subject to availability of Equity Shares.",
  "The Allotment to each Non-Institutional Investor shall not be less than the minimum application size viz. ₹2.00 Lakhs."
]);
assert.equal(niiMinimumApplications.length, 2);
assert.equal(niiMinimumApplications[0].value, 200000);
assert.equal(niiMinimumApplications[0].page, 2);
assert.equal(niiMinimumApplications[1].value, 200000);
assert.equal(niiMinimumApplications[1].page, 3);

const niiForwardContext = findExplicitNiiMinimumApplicationAmountsInPages([
  "shall not be less than the minimum application size viz. ₹ 0.20 million, subject to availability of Equity Shares in the Non-Institutional Portion and the remaining Equity Shares, if any, shall be allocated on a proportionate basis."
]);
assert.equal(niiForwardContext.length, 1);
assert.equal(niiForwardContext[0].value, 200000);
assert.equal(niiForwardContext[0].page, 1);

assert.deepEqual(
  findExplicitNiiMinimumApplicationAmountsInPages([
    "In case of a Mutual Fund, separate Bids will be aggregated to determine the minimum application size of ₹100 million.",
    "The PLI scheme requires minimum investment of Rs. 300 crore.",
    "Retail Individual Bidders may bid for the minimum Bid Lot."
  ]),
  []
);

const niiMinimumBidQuantities = findExplicitNiiMinimumBidQuantitiesInPages([
  "Offer summary.",
  "Non-Institutional Bidders shall submit a Minimum Bid of 1,200 Equity Shares and in multiples thereafter.",
  "The minimum application size is 2,400 Equity Shares for Non-Institutional Investors."
]);
assert.equal(niiMinimumBidQuantities.length, 2);
assert.equal(niiMinimumBidQuantities[0].value, 1200);
assert.equal(niiMinimumBidQuantities[0].page, 2);
assert.equal(niiMinimumBidQuantities[1].value, 2400);
assert.equal(niiMinimumBidQuantities[1].page, 3);

assert.deepEqual(
  findExplicitNiiMinimumBidQuantitiesInPages([
    "Bid Lot 40 Equity Shares and in multiples of 40 Equity Shares thereafter.",
    "Retail Individual Bidders may submit a Minimum Bid of 40 Equity Shares.",
    "Non-Institutional Bidders shall have an application amount above ₹200,000."
  ]),
  []
);

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

assert.equal(
  applyNiiMinimumApplicationExtraction(
    record,
    rhpDoc,
    { value: 200000, source_value: "minimum application size viz. ₹2.00 Lakhs", page: 77 },
    "2026-09-22T05:15:00Z"
  ),
  true
);
assert.equal(record.application_requirements.non_institutional.minimum_application_amount_inr.value, 200000);
assert.equal(record.application_requirements.non_institutional.minimum_application_amount_inr.page, 77);
assert.equal(record.application_requirements.non_institutional.minimum_application_amount_inr.status, "verified");
assert.equal(record.application_requirements.non_institutional.minimum_application_amount_inr.source.url, rhpDoc.url);
assert.equal(record.last_collected_at, "2026-09-22T05:15:00Z");

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
assert.equal(candidateProspectusRetailMinimumApplicationDocument({
  ...existing,
  application_requirements: {
    retail: {
      minimum_application_amount_inr: { value: 14850, source: { url: "https://example.com" } }
    }
  },
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
assert.equal(candidateRhpMinimumApplicationDocument({
  ...existing,
  minimum_application_amount_inr: { value: 14850, source: { url: "https://example.com" } },
  documents: [{ ...doc, type: "SEBI RHP PDF" }]
}), null);
assert.equal(candidateRhpNiiMinimumApplicationDocument({
  ...existing,
  application_requirements: {
    non_institutional: {
      minimum_application_amount_inr: { value: 200000, source: { url: "https://example.com" } }
    }
  },
  documents: [{ ...doc, type: "SEBI RHP PDF" }]
}), null);
assert.equal(candidateRhpNiiMinimumBidDocument({
  ...existing,
  application_requirements: {
    non_institutional: {
      minimum_bid_quantity: { value: 1200, source: { url: "https://example.com" } }
    }
  },
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

const existingNii = {
  ...existing,
  application_requirements: {
    non_institutional: {
      minimum_application_amount_inr: {
        value: 250000,
        status: "verified",
        source: { url: "https://example.com" }
      }
    }
  }
};
assert.equal(
  applyNiiMinimumApplicationExtraction(
    existingNii,
    rhpDoc,
    { value: 200000, source_value: "minimum application size viz. ₹2.00 Lakhs", page: 77 },
    "2026-09-22T05:15:00Z"
  ),
  false
);
assert.equal(existingNii.application_requirements.non_institutional.minimum_application_amount_inr.value, 250000);

const mirrorRecord = {
  issuer_name: "Mirror Limited",
  documents: [{ ...doc, url: "https://example.com/prospectus.pdf" }]
};
assert.equal(candidateProspectusDocument(mirrorRecord), null);

console.log("Prospectus issue-price extraction tests passed.");
assert.equal(
  shouldDeferHeavyHistoricalPdf(
    { listing_date: { value: "2025-08-01" } },
    2026,
    false
  ),
  true
);
assert.equal(
  shouldDeferHeavyHistoricalPdf(
    { listing_date: { value: "2026-08-01" } },
    2026,
    false
  ),
  false
);
assert.equal(
  shouldDeferHeavyHistoricalPdf(
    { listing_date: { value: "2025-08-01" } },
    2026,
    true
  ),
  false
);

const bandRecord = {
  issuer_name: "Band Example Limited",
  price_band: { value: null },
  terms: { price_band: null },
  documents: [doc]
};
assert.equal(applyPriceBandExtraction(
  bandRecord,
  doc,
  explicitBand,
  "2026-09-23T22:00:00Z"
), true);
assert.deepEqual(bandRecord.price_band.value, { min: 120, max: 125 });
assert.equal(bandRecord.price_band.status, "verified");

const lotRecord = {
  issuer_name: "Lot Example Limited",
  market_lot: { value: null },
  terms: { market_lot: null },
  documents: [doc]
};
assert.equal(applyMarketLotExtraction(
  lotRecord,
  doc,
  explicitMarketLot,
  "2026-09-23T22:00:00Z"
), true);
assert.equal(lotRecord.market_lot.value, 1200);
assert.equal(lotRecord.market_lot.status, "verified");
