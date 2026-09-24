import assert from "node:assert/strict";
import fs from "node:fs";
import { createHash } from "node:crypto";
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


const legacy2025Single = `
Content Addition to the BSE SME IPO Index
MUMBAI, JULY 16, 2025: With reference to Notice No . 20250715-53,
ASSTON PHARMACEUTICALS LIMITED (Exchange ticker - 544445 ),
is being listed on the SME Platform of BSE effective Wednesday, July 16,2025 .
Effective at the open of Thursday, July 17,2025 the stock will be added to the below index.
`;
assert.deepEqual(parseBseSmeAdditionNoticeHtml(legacy2025Single), [{
  listing_notice_no: "20250715-53",
  issuer_name: "ASSTON PHARMACEUTICALS LIMITED",
  bse_scrip_code: "544445",
  listing_date: "2025-07-16",
  listing_date_raw: "July 16,2025"
}]);

const legacy2025PluralSpacedId = `
PRESS RELEASE Additions to the BSE SME IPO Index
MUMBAI, APRIL 08, 2025: With reference to Notice No. 20250407- 51
SPINAROO COMMERCIAL LIMITED (Exchange ticker- 544392 ) and Notice No. 20250407-67,
INFONATIVE SOLUTIONS LIMITED (Exchange ticker- 544393 ),
are being listed on the SME Platform of BSE effective Tuesday, April 08, 2025 .
Effective at the open of Wednesday, April 09, 2025. stocks will be added to the below index.
`;
assert.deepEqual(parseBseSmeAdditionNoticeHtml(legacy2025PluralSpacedId), [
  {
    listing_notice_no: "20250407-51",
    issuer_name: "SPINAROO COMMERCIAL LIMITED",
    bse_scrip_code: "544392",
    listing_date: "2025-04-08",
    listing_date_raw: "April 08, 2025"
  },
  {
    listing_notice_no: "20250407-67",
    issuer_name: "INFONATIVE SOLUTIONS LIMITED",
    bse_scrip_code: "544393",
    listing_date: "2025-04-08",
    listing_date_raw: "April 08, 2025"
  }
]);

const legacy2025Plural = `
PRESS RELEASE Additions to the BSE SME IPO Index
MUMBAI, MAY 12, 2025: With reference to Notice No. 20250509-44
SRIGEE DLM LIMITED (Exchange ticker-544399) and Notice No. 20250509-45,
MANOJ JEWELLERS LIMITED (Exchange ticker- 544400),
are being listed on the SME Platform of BSE effective Monday, May 12, 2025 .
`;
assert.deepEqual(parseBseSmeAdditionNoticeHtml(legacy2025Plural), [
  {
    listing_notice_no: "20250509-44",
    issuer_name: "SRIGEE DLM LIMITED",
    bse_scrip_code: "544399",
    listing_date: "2025-05-12",
    listing_date_raw: "May 12, 2025"
  },
  {
    listing_notice_no: "20250509-45",
    issuer_name: "MANOJ JEWELLERS LIMITED",
    bse_scrip_code: "544400",
    listing_date: "2025-05-12",
    listing_date_raw: "May 12, 2025"
  }
]);

const legacy2024InnerTickerSpace = `
Content Addition to the BSE SME IPO Index
MUMBAI, December 11, 2024: With reference to Notice No . 20241210-61 ,
NISUS FINANCE SERVICES CO LIMITED ( Exchange ticker - 544296),
is being listed on the SME Platform of BSE effective Wednesday, December 11, 2024 .
`;
assert.deepEqual(parseBseSmeAdditionNoticeHtml(legacy2024InnerTickerSpace), [{
  listing_notice_no: "20241210-61",
  issuer_name: "NISUS FINANCE SERVICES CO LIMITED",
  bse_scrip_code: "544296",
  listing_date: "2024-12-11",
  listing_date_raw: "December 11, 2024"
}]);

const sharedNoticeIds2024 = `
Content Additions to the BSE SME IPO Index
MUMBAI, JULY 22, 2024: With reference to Notice No:20240719-44 and 20240719-38,
Aelea Commodities Limited (Exchange ticker - 544213) and Three M Paper Boards Ltd
(Exchange ticker - 544214), are being listed on the SME Platform of BSE effective Monday, July 22, 2024 .
`;
assert.deepEqual(parseBseSmeAdditionNoticeHtml(sharedNoticeIds2024), [
  {
    listing_notice_no: "20240719-44",
    issuer_name: "Aelea Commodities Limited",
    bse_scrip_code: "544213",
    listing_date: "2024-07-22",
    listing_date_raw: "July 22, 2024"
  },
  {
    listing_notice_no: "20240719-38",
    issuer_name: "Three M Paper Boards Ltd",
    bse_scrip_code: "544214",
    listing_date: "2024-07-22",
    listing_date_raw: "July 22, 2024"
  }
]);
assert.deepEqual(
  parseBseSmeAdditionNoticeHtml(sharedNoticeIds2024.replace(/\s+and Three M Paper Boards Ltd[\s\S]*?\(Exchange ticker - 544214\)/, "")),
  [],
  "shared notice-ID clauses require one issuer/ticker pair per notice ID"
);

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

// Literal source regressions from the seven hash-matching cursor6/7 failures.
const repairedSource = JSON.parse(fs.readFileSync(new URL('./fixtures/bse-cursor7-parser-repair.json', import.meta.url), 'utf8'));
assert.equal(repairedSource.fixtures.length, 7);
let recoveredReferences = 0;
for (const fixture of repairedSource.fixtures) {
  const { text, expected, notice_no: id } = fixture;
  assert.equal(fixture.extracted_text_sha256, fixture.retained_text_sha256, id + ': unchanged official source');
  assert.equal(createHash('sha256').update(text).digest('hex'), fixture.excerpt_sha256, id + ': exact retained excerpt');
  assert.deepEqual(parseBseSmeAdditionNoticeHtml(text), expected, id);
  recoveredReferences += expected.length;
  assert.deepEqual(parseBseSmeAdditionNoticeHtml(text + ' ' + text), expected, id + ': duplicate clauses');
  for (const [label, mutated] of [
    ['missing ticker', text.replace(/\(\s*Exchange ticker[^)]+\)/i, '')],
    ['invalid ticker', text.replace(expected[0].bse_scrip_code, '12345')],
    ['wrong venue', text.replace(/\bBSE\b/g, 'NSE')],
    ['negated listing', text.replace(/(?:is|are) being listed/, 'is not being listed')],
    ['index date only', text.replace(/(?:is|are) being listed[^.]+\./, '')],
    ['invalid calendar date', text.replace(expected[0].listing_date_raw, 'February 30, 2024')],
    ['unrelated issuer prose', text.replace(/(?:is|are) being listed/, 'Unrelated issuer is being listed')]
  ]) {
    assert.notEqual(mutated, text, id + ': mutation applied: ' + label);
    assert.deepEqual(parseBseSmeAdditionNoticeHtml(mutated), [], id + ': ' + label);
  }
  if (expected.length > 1) {
    for (const [label, mutated] of [
      ['extra notice', text.replace(expected[0].listing_notice_no, expected[0].listing_notice_no + ' and 20240101-99')],
      ['duplicate notice', text.replace(expected[1].listing_notice_no, expected[0].listing_notice_no)],
      ['duplicate ticker', text.replace(expected[1].bse_scrip_code, expected[0].bse_scrip_code)],
      ['respectively repeated', text.replace('respectively,', 'respectively respectively,')],
      ['respectively inside name', text.replace(expected[0].issuer_name, expected[0].issuer_name + ' respectively')],
      ['raw notice inside name', text.replace(expected[0].issuer_name, expected[0].issuer_name + ' 20240101-99')],
      ['dangling issuer', text.replace('respectively,', 'and Missing Limited respectively,')]
    ]) {
      assert.notEqual(mutated, text);
      assert.deepEqual(parseBseSmeAdditionNoticeHtml(mutated), [], id + ': ' + label);
    }
  }
}
assert.equal(recoveredReferences, 13);
console.log('Seven retained BSE source fixtures recover 13 references; incomplete/ambiguous clauses fail closed.');
