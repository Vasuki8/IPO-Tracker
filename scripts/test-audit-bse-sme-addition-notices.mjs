import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import {
  classifyAdditionNoticeAudit,
  validateNoticeBatchSize,
  isBseSmeAdditionNotice,
  officialNoticePdfUrl,
  parseBseSmeAdditionNoticeHtml,
  summarizeBseNoticeDataShape,
  summarizeBseNoticeParseFailure
} from "./audit-bse-sme-addition-notices.mjs";

assert.equal(
  isBseSmeAdditionNotice({ Subject: "Addition to the BSE SME IPO INDEX" }),
  true
);
assert.equal(
  isBseSmeAdditionNotice({ subject: "Additions to the BSE SME IPO INDEX" }),
  true
);
assert.equal(
  isBseSmeAdditionNotice({ Subject: "Additions to the BSE Indices" }),
  false
);

const gabion = `
<div>
  With reference to Notice No.&nbsp;20260112-35,
  GABION TECHNOLOGIES INDIA LIMITED
  (Exchange ticker-544675), is being listed on BSE effective
  <b>Tuesday, January 13, 2026</b>.
</div>`;
assert.deepEqual(parseBseSmeAdditionNoticeHtml(gabion), [{
  listing_notice_no: "20260112-35",
  issuer_name: "GABION TECHNOLOGIES INDIA LIMITED",
  bse_scrip_code: "544675",
  listing_date: "2026-01-13",
  listing_date_raw: "January 13, 2026"
}]);

const yashhtej = `
<p>With reference to Notice No. 20260224-17, YASHHTEJ INDUSTRIES (INDIA) LIMITED
(Exchange ticker-544708), is being listed on BSE, effective Wednesday, February 25, 2026.</p>`;
assert.equal(parseBseSmeAdditionNoticeHtml(yashhtej)[0].issuer_name, "YASHHTEJ INDUSTRIES (INDIA) LIMITED");
assert.equal(parseBseSmeAdditionNoticeHtml(yashhtej)[0].listing_date, "2026-02-25");

const productionSpacing = `
<p>With reference to Notice No. 20260224-17, YASHHTEJ INDUSTRIES (INDIA) LIMITED
(Exchange ticker- 544708 ), is being listed on BSE, effective Wednesday, February 25, 2026 .</p>`;
assert.deepEqual(parseBseSmeAdditionNoticeHtml(productionSpacing), [{
  listing_notice_no: "20260224-17",
  issuer_name: "YASHHTEJ INDUSTRIES (INDIA) LIMITED",
  bse_scrip_code: "544708",
  listing_date: "2026-02-25",
  listing_date_raw: "February 25, 2026"
}]);

const multiple = `
With reference to Notice No. 20260810-35, AEGEUS TECHNOLOGIES LIMITED
(Exchange ticker-544858), will be listed on BSE effective Tuesday, August 11, 2026.
Effective at the open of Wednesday, August 12, 2026, this stock will be added to the BSE SME IPO INDEX.
With reference to Notice No. 20260812-34, LAPL AUTOMOTIVE LIMITED
(Exchange ticker-544863), is being listed on BSE effective Thursday, August 13, 2026.
`;
const multipleRows = parseBseSmeAdditionNoticeHtml(multiple);
assert.equal(multipleRows.length, 2);
assert.equal(multipleRows[0].listing_date, "2026-08-11");
assert.equal(multipleRows[1].listing_date, "2026-08-13");
assert.equal(parseBseSmeAdditionNoticeHtml("unrelated notice").length, 0);


const failureExcerpt = summarizeBseNoticeParseFailure(`
<html><body>Header text ${"x".repeat(120)} With reference to Notice No. 20260813-16,
LAPL Automotive Limited (Exchange ticker-544863) is being listed on BSE effective Thursday,
August 13, 2026. ${"y".repeat(900)}</body></html>`, 300);
assert.ok(failureExcerpt.includes("With reference to Notice No. 20260813-16"));
assert.ok(failureExcerpt.length <= 300);


const shaped = {
  Html: "<p>With reference to Notice No. 20260813-16, Example Limited (Exchange ticker-544863) is being listed on BSE effective Thursday, August 13, 2026.</p>",
  Meta: { source: "BSE" }
};
assert.equal(summarizeBseNoticeDataShape(shaped).type, "object");
assert.ok(summarizeBseNoticeParseFailure(shaped, 300).includes("With reference"));

assert.equal(
  officialNoticePdfUrl({
    FileName: "https://www.bseindia.com/downloads/UploadDocs/Notices/20260821-22/20260821-22.pdf"
  }),
  "https://www.bseindia.com/downloads/UploadDocs/Notices/20260821-22/20260821-22.pdf"
);
assert.equal(officialNoticePdfUrl({ FileName: "https://evil.example/notice.pdf" }), null);
assert.equal(officialNoticePdfUrl({ FileName: "https://www.bseindia.com/notices/index.html" }), null);


const austereSharvaya = `
Additions to the BSE SME IPO Index
MUMBAI, SEPTEMBER 12, 2025: With reference to Notice No: 20250911-76,
AUSTERE SYSTEMS LIMITED (Exchange ticker – 544505) & Notice No:
20250911-79, SHARVAYA METALS LIMITED (Exchange ticker – 544506),
are being listed on SME platform of BSE effective Friday, September 12, 2025.
Effective at the open of Monday, September 15, 2025, the stock will be added to the below index.
INDEX ADD Exchange Ticker Stock Name EFFECTIVE DATE
BSE SME IPO 544505 AUSTERE SYSTEMS LIMITED September 15, 2025
544506 SHARVAYA METALS LIMITED
`;
assert.deepEqual(parseBseSmeAdditionNoticeHtml(austereSharvaya), [
  {
    listing_notice_no: "20250911-76",
    issuer_name: "AUSTERE SYSTEMS LIMITED",
    bse_scrip_code: "544505",
    listing_date: "2025-09-12",
    listing_date_raw: "September 12, 2025"
  },
  {
    listing_notice_no: "20250911-79",
    issuer_name: "SHARVAYA METALS LIMITED",
    bse_scrip_code: "544506",
    listing_date: "2025-09-12",
    listing_date_raw: "September 12, 2025"
  }
]);
assert.deepEqual(
  parseBseSmeAdditionNoticeHtml(austereSharvaya.replace("SME platform of BSE", "SME platform of NSE")),
  [],
  "only the demonstrated BSE SME-platform listing phrase is accepted"
);
assert.deepEqual(
  parseBseSmeAdditionNoticeHtml(austereSharvaya.replace("(Exchange ticker – 544505)", "")),
  [],
  "an ampersand must not allow a missing issuer ticker to borrow another reference"
);
assert.equal(
  parseBseSmeAdditionNoticeHtml(austereSharvaya)[0].listing_date,
  "2025-09-12",
  "the later September 15 index-admission date is never the listing date"
);

const pluralProduction = `
PRESS RELEASE Additions to the BSE SME IPO Index
MUMBAI, AUGUST 21, 2026: With reference to Notice No: 20260820-37,
ENS ENTERPRISES LIMITED (Exchange ticker – 544876),
Notice No: 20260820-35, TECHNOCRATS PLASMA SYSTEMS LIMITED
(Exchange ticker - 544877) are being listed on BSE effective Friday, August 21, 2026.
Effective at the open of Monday, August 24, 2026, these stocks will be added to the below index.
`;
assert.deepEqual(parseBseSmeAdditionNoticeHtml(pluralProduction), [
  {
    listing_notice_no: "20260820-37",
    issuer_name: "ENS ENTERPRISES LIMITED",
    bse_scrip_code: "544876",
    listing_date: "2026-08-21",
    listing_date_raw: "August 21, 2026"
  },
  {
    listing_notice_no: "20260820-35",
    issuer_name: "TECHNOCRATS PLASMA SYSTEMS LIMITED",
    bse_scrip_code: "544877",
    listing_date: "2026-08-21",
    listing_date_raw: "August 21, 2026"
  }
]);

// Synthetic safety fixtures: punctuation must be accepted in BOTH parser stages.
for (const label of ["No", "No.", "No:", "No.:", "No. :"]) {
  for (const dash of ["-", "–", "—", "&ndash;", "&mdash;"]) {
    const text = gabion.replace("No.", label).replace("ticker-", "ticker" + dash);
    assert.equal(parseBseSmeAdditionNoticeHtml(text).length, 1, label + " / " + dash);
  }
}
assert.deepEqual(parseBseSmeAdditionNoticeHtml(pluralProduction + pluralProduction),
  parseBseSmeAdditionNoticeHtml(pluralProduction), "duplicate clauses must be idempotent");
assert.equal(parseBseSmeAdditionNoticeHtml(multiple)[0].listing_date, "2026-08-11",
  "later index addition date is not listing date");
assert.deepEqual(parseBseSmeAdditionNoticeHtml(gabion.replace("January 13, 2026", "February 30, 2026")), []);
assert.deepEqual(parseBseSmeAdditionNoticeHtml(gabion.replace("January 13, 2026", "February 29, 2026")), []);
assert.equal(parseBseSmeAdditionNoticeHtml(gabion.replace("January 13, 2026", "February 29, 2024"))[0].listing_date, "2024-02-29");
assert.deepEqual(parseBseSmeAdditionNoticeHtml(gabion.replace("is being listed on BSE", "will be added to the index")), []);
assert.deepEqual(parseBseSmeAdditionNoticeHtml(gabion.replace("is being listed", "is not being listed")), []);
assert.deepEqual(parseBseSmeAdditionNoticeHtml(gabion.replace("(Exchange ticker-544675)", "(Exchange ticker-[pending])")), []);
assert.deepEqual(parseBseSmeAdditionNoticeHtml(gabion.replace("is being listed", "Unrelated issuer is being listed")), []);
assert.deepEqual(parseBseSmeAdditionNoticeHtml(gabion + gabion.replace("January 13, 2026", "January 14, 2026")), [],
  "conflicting listing dates must not silently use last-wins");
const overlong = gabion.replace("is being listed", "x".repeat(2000) + " is being listed");
assert.deepEqual(parseBseSmeAdditionNoticeHtml(overlong + gabion), parseBseSmeAdditionNoticeHtml(gabion),
  "every clause must remain bounded even if another reference follows");
const missingTicker = pluralProduction.replace("(Exchange ticker – 544876)", "");
assert.deepEqual(parseBseSmeAdditionNoticeHtml(missingTicker), [], "do not borrow another issuer's ticker");
assert.equal(officialNoticePdfUrl({ FileName: "http://www.bseindia.com/notice.pdf" }), null);
assert.equal(officialNoticePdfUrl({ FileName: "https://u:p@www.bseindia.com/notice.pdf" }), null);
assert.equal(officialNoticePdfUrl({ FileName: "https://www.bseindia.com.evil.example/notice.pdf" }), null);
assert.equal(validateNoticeBatchSize(1), 1);
assert.equal(validateNoticeBatchSize(20), 20);
for (const invalid of [0, -1, 1.5, 21, NaN, Infinity, "20"]) {
  assert.throws(() => validateNoticeBatchSize(invalid), /integer between/);
}
const good = { stats: { catalog_rows: 100, eligible_sme_addition_notices: 10,
  attempted_notices: 10, parsed_entries: 12, parse_failures: 0, fetch_errors: 0 }, failures: [] };
assert.equal(classifyAdditionNoticeAudit(good), "complete");
assert.equal(classifyAdditionNoticeAudit({ stats: null, failures: [{}] }), "failed");
assert.equal(classifyAdditionNoticeAudit({ ...good, stats: { ...good.stats, catalog_rows: 0 } }), "failed");
assert.equal(classifyAdditionNoticeAudit({ ...good, stats: { ...good.stats, parsed_entries: 0 } }), "failed");
assert.equal(classifyAdditionNoticeAudit({ ...good, stats: { ...good.stats, parse_failures: 1 } }), "partial");
assert.equal(classifyAdditionNoticeAudit({ ...good, stats: { ...good.stats, fetch_errors: 1 } }), "partial");
assert.equal(classifyAdditionNoticeAudit({ ...good, stats: { ...good.stats, eligible_sme_addition_notices: 0, attempted_notices: 0, parsed_entries: 0 } }), "no_eligible_notices");
// Exercise the real CLI failure path without an external network request.
const temp = fs.mkdtempSync(path.join(os.tmpdir(), "bse-notice-cli-test-"));
try {
  const target = fileURLToPath(new URL("./audit-bse-sme-addition-notices.mjs", import.meta.url));
  const output = path.join(temp, "audit.json");
  const child = spawnSync(process.execPath, ["--input-type=module", "-e", `
    globalThis.fetch = async () => { throw new Error("fixture source unavailable"); };
    process.argv = [process.execPath, ${JSON.stringify(target)}, "--batch=1", ${JSON.stringify("--output=" + output)}];
    await import(${JSON.stringify(new URL("./audit-bse-sme-addition-notices.mjs", import.meta.url).href)});
  `], { encoding: "utf8", timeout: 10000 });
  assert.equal(child.status, 1, child.stderr);
  const report = JSON.parse(fs.readFileSync(output, "utf8")).bse_sme_addition_notice_audit;
  assert.equal(report.status, "failed");
  assert.equal(report.batch_limit, 1);
  assert.deepEqual(report.candidates, []);
  assert.match(report.failures[0].error, /fixture source unavailable/);
} finally {
  fs.rmSync(temp, { recursive: true, force: true });
}
console.log("BSE SME addition notice parser, safety and audit-status tests passed.");
