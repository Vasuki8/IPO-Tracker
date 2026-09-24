import assert from "node:assert/strict";
import {
  BSE_NOTICE_RETRY_COOLDOWN_MS,
  bseNoticeProgress,
  emptyBseNoticeState,
  eligibleBseSmeAdditionNotices,
  selectBseNoticeBackfillBatch,
  validateBseNoticeState
} from "./backfill-bse-sme-addition-notices.mjs";

const row = (noticeNo, date) => ({
  notice_no: noticeNo,
  Notice_Date: date,
  Subject: "Addition to the BSE SME IPO Index",
  FileName: "https://www.bseindia.com/downloads/UploadDocs/Notices/" + noticeNo + "/" + noticeNo + ".pdf"
});
const catalog = { Table: [
  row("20260605-1", "2026-06-05"),
  row("20260604-1", "2026-06-04"),
  row("20260603-1", "2026-06-03"),
  row("20260602-1", "2026-06-02"),
  row("20260601-1", "2026-06-01"),
  { notice_no: "20260531-1", Notice_Date: "2026-05-31", Subject: "Other index notice" }
]};
const eligible = eligibleBseSmeAdditionNotices(catalog);
assert.deepEqual(eligible.map((item) => item.notice_no), [
  "20260605-1", "20260604-1", "20260603-1", "20260602-1", "20260601-1"
]);

const at = "2026-09-24T03:00:00Z";
const parsed = (noticeNo, parserVersion = "1.2.0") => ({
  notice_no: noticeNo,
  notice_date: "2026-06-01",
  subject: "Addition to the BSE SME IPO Index",
  parser_version: parserVersion,
  status: "parsed",
  attempts: 1,
  first_attempted_at: at,
  last_attempted_at: at,
  source_kind: "bse_index_notice_pdf",
  source_url: "https://www.bseindia.com/example.pdf",
  pdf_url: "https://www.bseindia.com/example.pdf",
  extracted_text_sha256: "a".repeat(64),
  parsed_entry_count: 1,
  parsed_entries: [{ listing_notice_no: "20260601-2" }],
  error: null
});
const state = emptyBseNoticeState();
state.updated_at = at;
state.notices["20260605-1"] = parsed("20260605-1");
state.notices["20260604-1"] = parsed("20260604-1");

assert.deepEqual(
  selectBseNoticeBackfillBatch(eligible, state, 2, Date.parse(at)).map((item) => item.row.notice_no),
  ["20260603-1", "20260602-1"],
  "unseen notices must advance before any retry"
);

const failure = {
  ...parsed("20260605-1"),
  status: "unparseable",
  parsed_entry_count: 0,
  parsed_entries: [],
  error: "no_parseable_listing_reference",
  last_attempted_at: new Date(Date.parse(at) - BSE_NOTICE_RETRY_COOLDOWN_MS - 1000).toISOString()
};
const withFailureAndUnseen = structuredClone(state);
withFailureAndUnseen.notices["20260605-1"] = failure;
assert.deepEqual(
  selectBseNoticeBackfillBatch(eligible, withFailureAndUnseen, 2, Date.parse(at)).map((item) => item.row.notice_no),
  ["20260603-1", "20260602-1"],
  "a retryable failure must not block older unseen progress"
);

const fullySeen = emptyBseNoticeState();
fullySeen.updated_at = at;
for (const item of eligible) fullySeen.notices[item.notice_no] = parsed(item.notice_no);
fullySeen.notices["20260603-1"] = { ...failure, notice_no: "20260603-1" };
assert.deepEqual(
  selectBseNoticeBackfillBatch(eligible, fullySeen, 2, Date.parse(at)).map((item) => item.row.notice_no),
  ["20260603-1"],
  "failed notices become retry candidates after unseen work is exhausted"
);

const compatibleParsed = structuredClone(fullySeen);
compatibleParsed.notices["20260605-1"] = parsed("20260605-1", "1.1.0");
assert.notEqual(
  selectBseNoticeBackfillBatch(eligible, compatibleParsed, 1, Date.parse(at))[0]?.row.notice_no,
  "20260605-1",
  "successfully parsed v1.1 entries remain compatible with the additive v1.2 grammar"
);

const stale = structuredClone(fullySeen);
stale.notices["20260605-1"] = { ...failure, notice_no: "20260605-1", parser_version: "1.1.0" };
const parserRepair = selectBseNoticeBackfillBatch(eligible, stale, 2, Date.parse(at));
assert.deepEqual(
  parserRepair.map((item) => [item.row.notice_no, item.reason]),
  [["20260605-1", "parser_changed_failure"]],
  "failed v1.1 entries must be requeued immediately and isolated from unseen discovery"
);

const progress = bseNoticeProgress(eligible, state);
assert.deepEqual(progress, {
  eligible_notices: 5,
  parsed_current_parser: 2,
  failed_current_parser: 0,
  unseen_or_parser_changed: 3,
  stale_parser_entries: 0,
  next_unseen_notice_no: "20260603-1",
  complete: false
});

validateBseNoticeState(state);
assert.throws(() => validateBseNoticeState({
  ...state,
  notices: { "20260605-1": { ...parsed("20260605-1"), status: "parsed", parsed_entry_count: 0 } }
}), /parsed_bse_notice_without_entries/);
assert.throws(() => validateBseNoticeState({
  ...state,
  notices: { "bad": parsed("bad") }
}), /invalid_bse_notice_state_entry/);

console.log("BSE SME addition-notice cursor selection/state tests passed.");
