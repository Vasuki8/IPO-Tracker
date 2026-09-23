import assert from "node:assert/strict";
import {
  extractEndpointContexts,
  extractMainScript
} from "./diagnose-bse-notice-api-context.mjs";

assert.equal(
  extractMainScript('<script src="polyfills-A.js"></script><script src="main-XYZ.js"></script>'),
  "main-XYZ.js"
);

const source =
  'abc GetLatestNotices xyz ' +
  'const u="/api/GetNoticesadvancesearch_newcomb/w";foo(StartDate,EndDate,NoticeNo); ' +
  'bar="/api/NoticesAsiaDownload/w?NoticeId=";';
const contexts = extractEndpointContexts(source, 80);
assert.ok(contexts.some((item) => item.target === "GetLatestNotices"));
assert.ok(contexts.some((item) =>
  item.target === "GetNoticesadvancesearch_newcomb" &&
  item.context.includes("StartDate")
));
assert.ok(contexts.some((item) => item.target === "NoticesAsiaDownload"));

console.log("BSE notice API context diagnostic tests passed.");
