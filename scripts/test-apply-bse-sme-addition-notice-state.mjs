import assert from "node:assert/strict";
import { emptyBseNoticeState } from "./backfill-bse-sme-addition-notices.mjs";
import { mergeBseNoticeStates } from "./apply-bse-sme-addition-notice-state.mjs";

function entry(noticeNo, attemptedAt, attempts = 1, status = "parsed") {
  return {
    notice_no: noticeNo,
    notice_date: "2026-06-01",
    subject: "Addition to the BSE SME IPO Index",
    parser_version: "1.2.0",
    status,
    attempts,
    first_attempted_at: "2026-09-24T00:00:00Z",
    last_attempted_at: attemptedAt,
    source_kind: "bse_index_notice_pdf",
    source_url: "https://www.bseindia.com/" + noticeNo + ".pdf",
    pdf_url: "https://www.bseindia.com/" + noticeNo + ".pdf",
    extracted_text_sha256: status === "parsed" ? "a".repeat(64) : null,
    parsed_entry_count: status === "parsed" ? 1 : 0,
    parsed_entries: status === "parsed" ? [{ listing_notice_no: "20260601-2" }] : [],
    error: status === "parsed" ? null : "fixture_error"
  };
}

const current = emptyBseNoticeState();
current.updated_at = "2026-09-24T01:00:00Z";
current.bootstrap = { source_run_id: "bootstrap" };
current.catalog = { observed_at: "2026-09-24T01:00:00Z", eligible_count: 236 };
current.notices["20260605-1"] = entry("20260605-1", "2026-09-24T01:00:00Z", 1);

const proposal = emptyBseNoticeState();
proposal.updated_at = "2026-09-24T02:00:00Z";
proposal.catalog = { observed_at: "2026-09-24T02:00:00Z", eligible_count: 236 };
proposal.notices["20260605-1"] = entry("20260605-1", "2026-09-24T02:00:00Z", 2);
proposal.notices["20260604-1"] = entry("20260604-1", "2026-09-24T02:00:00Z", 1);

const merged = mergeBseNoticeStates(current, proposal);
assert.equal(merged.notices["20260605-1"].attempts, 2);
assert.ok(merged.notices["20260604-1"]);
assert.deepEqual(merged.bootstrap, current.bootstrap);
assert.equal(merged.catalog.observed_at, "2026-09-24T02:00:00Z");

const staleProposal = structuredClone(proposal);
staleProposal.updated_at = "2026-09-24T00:30:00Z";
staleProposal.catalog.observed_at = "2026-09-24T00:30:00Z";
staleProposal.notices["20260605-1"] = entry("20260605-1", "2026-09-24T00:30:00Z", 9, "unparseable");
const notRegressed = mergeBseNoticeStates(merged, staleProposal);
assert.equal(notRegressed.notices["20260605-1"].status, "parsed");
assert.equal(notRegressed.notices["20260605-1"].attempts, 2);
assert.equal(notRegressed.catalog.observed_at, "2026-09-24T02:00:00Z");

const migratedProposal = structuredClone(proposal);
migratedProposal.parser_version = "1.3.0";
migratedProposal.updated_at = "2026-09-24T03:00:00Z";
migratedProposal.notices["20260605-1"] = {
  ...entry("20260605-1", "2026-09-24T03:00:00Z", 1, "parsed"),
  parser_version: "1.3.0"
};
const migrated = mergeBseNoticeStates(merged, migratedProposal);
assert.equal(migrated.notices["20260605-1"].parser_version, "1.3.0");
assert.equal(migrated.notices["20260605-1"].status, "parsed");

assert.deepEqual(
  mergeBseNoticeStates(merged, proposal),
  merged,
  "reapplying the same proposal must be idempotent"
);

console.log("BSE SME addition-notice semantic state merge tests passed.");
