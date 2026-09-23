import assert from "node:assert/strict";
import {
  parseBseArchiveNavigation,
  parseBseListingNoticeArchive
} from "./diagnose-bse-listing-notices.mjs";

const html = `
<html><body>
<input type="hidden" name="__VIEWSTATE" value="abc" />
<table>
<tr>
<td>20250121-40</td>
<td><a href="/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=20250121-40">Listing of Equity Shares of Rikhav Securities Limited</a></td>
<td>SME</td><td>Company related</td><td>Listing Operations</td>
</tr>
<tr>
<td>20250725-24</td>
<td><a href="/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=20250725-24">Listing of New Securities of Vishal Fabrics Limited</a></td>
<td>Equity</td><td>Company related</td><td>Listing Operations</td>
</tr>
<tr>
<td>20251119-39</td>
<td><a href="/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=20251119-39&amp;x=1">Listing of Equity Shares of Fujiyama Power Systems Limited</a></td>
<td>Equity</td><td>Company related</td><td>Listing Operations</td>
</tr>
</table>
<a href="NoticesCirculars.aspx?id=0&amp;txtscripcd=&amp;pagecont=2&amp;subject=Listing+of+Equity+Shares+of">2</a>
</body></html>`;

const notices = parseBseListingNoticeArchive(html);
assert.equal(notices.length, 2);
assert.deepEqual(notices.map((item) => item.notice_no), ["20250121-40", "20251119-39"]);
assert.equal(notices[0].company, "Rikhav Securities Limited");
assert.equal(notices[0].segment, "SME");
assert.equal(notices[1].segment, "EQUITY");
assert.match(notices[1].url, /page=20251119-39/);

const nav = parseBseArchiveNavigation(html);
assert.deepEqual(nav.pagecont_values, ["2"]);
assert.ok(nav.hidden_input_names.includes("__VIEWSTATE"));
assert.ok(nav.query_links.some((url) => url.includes("pagecont=2")));

console.log("BSE listing-notice archive diagnostic tests passed.");
