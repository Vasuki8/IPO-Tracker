import assert from "node:assert/strict";
import {
  applyOfferDates,
  candidateOfferDateDocument,
  offerDateCandidates,
  offerDateExtractionPassesCurrentRules,
  parseExplicitOfferDate,
  parseExplicitOfferDatesFromPages
} from "./backfill-historical-offer-dates.mjs";

assert.equal(parseExplicitOfferDate("Bid/Issue Opening Date December 3, 2025"), "2025-12-03");
assert.equal(parseExplicitOfferDate("Issue Closing Date 5 December 2025"), "2025-12-05");
assert.equal(parseExplicitOfferDate("No date here"), null);
assert.equal(parseExplicitOfferDate("Bid Opening Date February 31, 2025"), null);

const pages = [
  "Key dates Bid/Issue Opening Date December 3, 2025 Bid/Issue Closing Date December 5, 2025",
  "Other information"
];
const parsed = parseExplicitOfferDatesFromPages(pages, "2025-12-10");
assert.equal(parsed.reason, null);
assert.equal(parsed.open_date.value, "2025-12-03");
assert.equal(parsed.close_date.value, "2025-12-05");
assert.equal(parsed.open_date.page, 1);

const burgerKingStyle = parseExplicitOfferDatesFromPages([
  "Offer Opening Date Except in relation to any Bids received from the Anchor Investors, December 2, 2020 Offer Closing Date Except in relation to any Bids received from the Anchor Investors, December 4, 2020"
], "2020-12-14");
assert.equal(burgerKingStyle.open_date.value, "2020-12-02");
assert.equal(burgerKingStyle.close_date.value, "2020-12-04");

const arihantStyle = parseExplicitOfferDatesFromPages([
  "ISSUE OPENS ON: DECEMBER 16, 2022 ISSUE CLOSES ON: DECEMBER 21, 2022"
], "2022-12-29");
assert.equal(arihantStyle.open_date.value, "2022-12-16");
assert.equal(arihantStyle.close_date.value, "2022-12-21");

const parkStyle = parseExplicitOfferDatesFromPages([
  "Offer Opening Date i.e December 10, 2025, all editions of Financial Express"
], "2025-12-17");
assert.equal(parkStyle.open_date.value, "2025-12-10");

const unimechFalsePositive = parseExplicitOfferDatesFromPages([
  "Offer Closing Date. F&S has, through its letter dated December 5, 2024 accorded its consent to use the F&S Report in this Prospectus."
], "2024-12-31");
assert.equal(unimechFalsePositive.close_date, null);

const nephroAnchorFalsePositive = parseExplicitOfferDatesFromPages([
  "Offer Opening Date, being Tuesday, December 9, 2025 on which Bids by Anchor Investors were submitted, prior to and after which BRLMs did not accept any Bids from Anchor Investors."
], "2025-12-17");
assert.equal(nephroAnchorFalsePositive.open_date, null);

const coronaAnchorFalsePositive = parseExplicitOfferDatesFromPages([
  "Anchor Investor Offer Opening Date, on which Bids by Anchor Investors were submitted, and allocation to Anchor Investors was completed, i.e., Friday, December 5, 2025."
], "2025-12-15");
assert.equal(coronaAnchorFalsePositive.open_date, null);

const ventiveStyle = parseExplicitOfferDatesFromPages([
  "Bid/Issue Opening Date Except in relation to any Bids received from the Anchor Investors, Friday, December 20, 2024 Bid/Issue Closing Date Except in relation to any Bids received from the Anchor Investors, Tuesday, December 24, 2024"
], "2024-12-30");
assert.equal(ventiveStyle.open_date.value, "2024-12-20");
assert.equal(ventiveStyle.close_date.value, "2024-12-24");

const conflict = parseExplicitOfferDatesFromPages([
  "Bid Opening Date December 3, 2025",
  "Bid Opening Date December 4, 2025"
], "2025-12-10");
assert.equal(conflict.reason, "official_date_conflict");

const invalid = parseExplicitOfferDatesFromPages([
  "Issue Opening Date December 6, 2025 Issue Closing Date December 5, 2025"
], "2025-12-10");
assert.equal(invalid.reason, "invalid_offer_chronology");

const record = {
  id: "example-limited",
  issuer_name: "Example Limited",
  listing_date: { value: "2025-12-10" },
  terms: { open_date: null, close_date: null },
  documents: [{
    type: "SEBI Prospectus PDF",
    identity: "Example Limited - Prospectus — PDF",
    url: "https://www.sebi.gov.in/sebi_data/attachdocs/dec-2025/example.pdf",
    publication_date: "2025-12-08"
  }]
};
assert.ok(candidateOfferDateDocument(record, 2026));
assert.equal(offerDateCandidates([{record}], {issuers:{}}, 2026, 10).length, 1);
assert.equal(applyOfferDates(record, record.documents[0], parsed, "2026-09-23T20:00:00Z"), true);
assert.equal(record.open_date.value, "2025-12-03");
assert.equal(record.close_date.value, "2025-12-05");
assert.equal(record.open_date.status, "verified");
assert.equal(record.open_date.source.document_type, "SEBI Prospectus PDF");
assert.equal(candidateOfferDateDocument(record, 2026), null);

console.log("Historical SEBI offer-date backfill tests passed.");

assert.equal(
  offerDateExtractionPassesCurrentRules(
    { value: "2025-12-10", source_value: "Offer Opening Date i.e December 10, 2025", page: 1 },
    "open",
    "2025-12-17"
  ),
  true
);
assert.equal(
  offerDateExtractionPassesCurrentRules(
    { value: "2025-12-05", source_value: "Offer Closing Date. F&S has, through its letter dated December 5, 2024", page: 29 },
    "close",
    "2024-12-31"
  ),
  false
);
