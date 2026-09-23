import assert from "node:assert/strict";
import { matchBseSummaryLink, parseBseIssueSummaryLinks } from "./diagnose-bse-issues.mjs";

const html = `
<table>
<tr><td>Kenrik Industries Limited</td><td><a href="/markets/publicIssues/DisplayIPO.aspx?IPONo=7058&amp;id=3912&amp;idtype=1&amp;startdt=29%2F04%2F2025&amp;status=L&amp;type=FPO">View Detail</a></td></tr>
<tr><td>Example Technologies Ltd</td><td><a href="/markets/publicIssues/DisplayIPO.aspx?IPONo=9999&amp;id=9999&amp;idtype=1">View Detail</a></td></tr>
</table>`;
const links = parseBseIssueSummaryLinks(html);
assert.equal(links.length, 2);
assert.match(links[0].url, /IPONo=7058/);
assert.equal(matchBseSummaryLink("Kenrik Industries Limited", links).match.url, links[0].url);
assert.equal(matchBseSummaryLink("Example Technologies Limited", links).match.url, links[1].url);
assert.equal(matchBseSummaryLink("Missing Limited", links).reason, "no_match");
console.log("BSE issue-summary diagnostic tests passed.");
