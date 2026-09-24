import assert from "node:assert/strict";
import {
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

console.log("BSE SME addition notice audit parser tests passed.");

const failureExcerpt = summarizeBseNoticeParseFailure(`
<html><body>Header text xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx With reference to Notice No. 20260813-16,
LAPL Automotive Limited (Exchange ticker-544863) is being listed on BSE effective Thursday,
August 13, 2026. yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy</body></html>`, 300);
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
