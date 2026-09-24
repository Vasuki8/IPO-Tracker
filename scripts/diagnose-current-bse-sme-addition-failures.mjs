import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import {
  BSE_INDEX_NOTICE_DETAIL_URL,
  parseBseSmeAdditionNoticeHtml,
  summarizeBseNoticeDataShape,
  summarizeBseNoticeParseFailure
} from "./audit-bse-sme-addition-notices.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const state = JSON.parse(fs.readFileSync(path.join(ROOT, "ops", "bse-sme-addition-notices.json"), "utf8"));
const failures = Object.values(state.notices || {})
  .filter((entry) => entry?.status === "unparseable")
  .sort((a, b) => String(b.notice_no).localeCompare(String(a.notice_no)));

const headers = {
  "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
  "accept": "application/json,*/*",
  "accept-language": "en-US,en;q=0.9",
  "referer": "https://www.bseindices.com/notices"
};

const diagnostics = [];
for (const entry of failures) {
  const url = BSE_INDEX_NOTICE_DETAIL_URL + encodeURIComponent(entry.notice_no);
  try {
    const response = await fetch(url, { headers, signal: AbortSignal.timeout(20000) });
    const raw = await response.text();
    if (!response.ok) throw new Error("HTTP " + response.status + " " + raw.slice(0, 200));
    const detail = JSON.parse(raw);
    const text = typeof detail?.Data === "string" ? detail.Data : "";
    const actualHash = createHash("sha256").update(text, "utf8").digest("hex");
    diagnostics.push({
      notice_no: entry.notice_no,
      source_url: url,
      expected_text_sha256: entry.extracted_text_sha256,
      actual_text_sha256: actualHash,
      hash_matches_retained_cursor: actualHash === entry.extracted_text_sha256,
      data_shape: summarizeBseNoticeDataShape(detail),
      excerpt: summarizeBseNoticeParseFailure(detail, 1000),
      parsed_rows: parseBseSmeAdditionNoticeHtml(text)
    });
  } catch (error) {
    diagnostics.push({
      notice_no: entry.notice_no,
      source_url: url,
      error: String(error?.message || error)
    });
  }
}

console.log(JSON.stringify({
  diagnostic_only: true,
  cursor_parser_version: state.parser_version,
  retained_failure_count: failures.length,
  diagnostics
}, null, 2));
