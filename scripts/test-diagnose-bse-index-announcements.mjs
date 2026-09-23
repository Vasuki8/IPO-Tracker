import assert from "node:assert/strict";
import {
  extractAnnouncementHints,
  extractScriptSources
} from "./diagnose-bse-index-announcements.mjs";

assert.deepEqual(
  extractScriptSources('<script src="main-A.js"></script><script src="/env.js"></script><script src="main-A.js"></script>'),
  ["main-A.js", "/env.js"]
);

const hints = extractAnnouncementHints(
  'const a="https://www.bseindices.com/AsiaIndexAPI/api/NoticesAsiaDownload/w?NoticeId=";' +
  'const b="/api/NoticesAsia/list";const c="DisplayNoticescircular";'
);
assert.ok(hints.some((value) => value.includes("NoticesAsiaDownload")));
assert.ok(hints.some((value) => value.includes("/api/NoticesAsia/list")));
assert.ok(hints.some((value) => value.includes("DisplayNoticescircular")));

console.log("BSE Index announcement diagnostic tests passed.");
