import assert from "node:assert/strict";
import {
  applyOfferDates,
  candidateOfferDateDocument,
  offerDateCandidates,
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
