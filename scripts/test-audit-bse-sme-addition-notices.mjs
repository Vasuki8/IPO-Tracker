import assert from "node:assert/strict";
import {
  isBseSmeAdditionNotice,
  parseBseSmeAdditionNoticeHtml
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
(Exchange ticker-544858), is listed on BSE effective Tuesday, August 11, 2026.
With reference to Notice No. 20260812-34, LAPL AUTOMOTIVE LIMITED
(Exchange ticker-544863), is being listed on BSE effective Thursday, August 13, 2026.
`;
assert.equal(parseBseSmeAdditionNoticeHtml(multiple).length, 2);
assert.equal(parseBseSmeAdditionNoticeHtml("unrelated notice").length, 0);

console.log("BSE SME addition notice audit parser tests passed.");
