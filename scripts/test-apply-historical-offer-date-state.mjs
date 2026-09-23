import assert from "node:assert/strict";
import { mergeOfferDateProposal } from "./apply-historical-offer-date-state.mjs";

const record = {
  id: "alpha-limited",
  issuer_name: "Alpha Limited",
  listing_date: { value: "2025-12-10" },
  terms: { open_date: null, close_date: null },
  documents: []
};
const groups = [{ recovery: { records: [record] }, changed: false }];
const proposal = {
  schema_version: "1.0.0",
  issuers: {
    "2025|alpha-limited": {
      issuer_name: "Alpha Limited",
      listing_date: "2025-12-10",
      last_attempted_at: "2026-09-23T20:40:00Z",
      parser_version: "1.0.0",
      status: "extracted",
      open_extraction: {
        value: "2025-12-03",
        source_value: "Bid Opening Date December 3, 2025",
        page: 2
      },
      close_extraction: {
        value: "2025-12-05",
        source_value: "Bid Closing Date December 5, 2025",
        page: 2
      },
      document: {
        type: "SEBI Prospectus PDF",
        identity: "Alpha Limited - Prospectus — PDF",
        url: "https://www.sebi.gov.in/sebi_data/attachdocs/dec-2025/alpha.pdf",
        publication_date: "2025-12-08"
      }
    }
  }
};
const current = { schema_version: "1.0.0", issuers: {} };
const stats = mergeOfferDateProposal(groups, current, proposal);
assert.equal(stats.extracted_records, 1);
assert.equal(stats.open_dates, 1);
assert.equal(stats.close_dates, 1);
assert.equal(groups[0].changed, true);
assert.equal(record.open_date.value, "2025-12-03");
assert.equal(record.close_date.value, "2025-12-05");
assert.equal(record.open_date.status, "verified");
assert.equal(record.open_date.source.document_type, "SEBI Prospectus PDF");
assert.equal(current.issuers["2025|alpha-limited"].status, "extracted");

const concurrentRecord = {
  id: "beta-limited",
  issuer_name: "Beta Limited",
  listing_date: { value: "2025-11-10" },
  terms: { open_date: "2025-11-01", close_date: "2025-11-03" },
  documents: []
};
const concurrentGroups = [{ recovery: { records: [concurrentRecord] }, changed: false }];
const concurrentProposal = {
  issuers: {
    "2025|beta-limited": {
      issuer_name: "Beta Limited",
      listing_date: "2025-11-10",
      last_attempted_at: "2026-09-23T20:45:00Z",
      parser_version: "1.0.0",
      status: "extracted",
      open_extraction: { value: "2025-11-01", source_value: "Issue Opening Date November 1, 2025", page: 1 },
      close_extraction: { value: "2025-11-03", source_value: "Issue Closing Date November 3, 2025", page: 1 },
      document: { type: "SEBI RHP PDF", identity: "Beta RHP", url: "https://www.sebi.gov.in/sebi_data/attachdocs/nov-2025/beta.pdf", publication_date: "2025-10-30" }
    }
  }
};
const concurrentStats = mergeOfferDateProposal(concurrentGroups, { issuers: {} }, concurrentProposal);
assert.equal(concurrentStats.extracted_records, 0);
assert.equal(concurrentStats.already_present, 1);
assert.equal(concurrentGroups[0].changed, false);

console.log("Historical offer-date semantic merge tests passed.");
