import assert from "node:assert/strict";
import fs from "node:fs";
import {
  appendDocument,
  applySebiEntry,
  canonicalIssuer,
  issuerFromListingTitle,
  issuerVariants,
  matchIssuerRecord,
  parseAbridgedProspectusLinks,
  parseSebiDate,
  parseSebiListingHtml
} from "./sync-sebi-documents.mjs";

const listing = fs.readFileSync(new URL("./fixtures/sebi-public-issues-sample.html", import.meta.url), "utf8");
const detail = fs.readFileSync(new URL("./fixtures/sebi-rhp-detail-sample.html", import.meta.url), "utf8");
const base = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&smid=11&ssid=15";

assert.equal(parseSebiDate("Sep 21, 2026"), "2026-09-21");
assert.equal(parseSebiDate("bad date"), null);
assert.equal(canonicalIssuer("Swastika Infra Ltd."), "swastika infra");
assert.equal(issuerFromListingTitle("Moneyview Limited - RHP", "rhp"), "Moneyview Limited");
assert.equal(
  issuerFromListingTitle("Manipal Payment & Identity Solutions Limited – Prospectus", "final"),
  "Manipal Payment & Identity Solutions Limited"
);

const rhp = parseSebiListingHtml(listing, "rhp", base);
assert.equal(rhp.length, 3);
assert.equal(rhp[0].publication_date, "2026-09-21");
assert.equal(rhp[0].issuer_name, "Moneyview Limited");
assert.ok(rhp[0].url.startsWith("https://www.sebi.gov.in/filings/public-issues/"));

const finals = parseSebiListingHtml(listing, "final", base);
assert.equal(finals.length, 1);
assert.equal(finals[0].issuer_name, "Manipal Payment & Identity Solutions Limited");

const aps = parseAbridgedProspectusLinks(detail, rhp[0].url);
assert.equal(aps.length, 1);
assert.equal(aps[0].type, "SEBI Abridged Prospectus");
assert.ok(aps[0].url.includes("/sebi_data/commondocs/"));

const records = [
  { record: { issuer_name: "Moneyview Limited" }, recovery: { changed: false } },
  { record: { issuer_name: "Swastika Infra Limited" }, recovery: { changed: false } },
  { record: { issuer_name: "Adroit Industries (India) Limited" }, recovery: { changed: false } }
];

assert.equal(matchIssuerRecord(records, "Moneyview Limited").record.issuer_name, "Moneyview Limited");
assert.equal(matchIssuerRecord(records, "Swastika Infra Ltd.").record.issuer_name, "Swastika Infra Limited");
assert.ok(issuerVariants("Adroit Industries (India) Limited").includes("adroit industries"));
assert.equal(
  matchIssuerRecord(records, "Adroit Industries Limited").record.issuer_name,
  "Adroit Industries (India) Limited"
);

const ambiguous = [
  { record: { issuer_name: "Example Limited" }, recovery: {} },
  { record: { issuer_name: "Example Ltd." }, recovery: {} }
];
assert.equal(matchIssuerRecord(ambiguous, "Example Limited"), null);

const target = {
  documents: [],
  last_collected_at: "2026-09-20T00:00:00Z"
};
const match = { record: target, recovery: { changed: false } };
assert.equal(
  applySebiEntry(match, rhp[0], "2026-09-22T04:00:00Z", aps),
  true
);
assert.equal(target.documents.length, 2);
assert.equal(target.last_collected_at, "2026-09-22T04:00:00Z");
assert.equal(
  applySebiEntry(match, rhp[0], "2026-09-22T05:00:00Z", aps),
  false
);
assert.equal(target.documents.length, 2);
assert.equal(target.last_collected_at, "2026-09-22T04:00:00Z");

assert.equal(
  appendDocument(target, {
    type: "SEBI Prospectus filing",
    identity: "Unique Limited - Prospectus",
    url: "https://www.sebi.gov.in/filings/public-issues/sep-2026/unique-limited-prospectus_1.html",
    publication_date: "2026-09-21",
    collected_at: "2026-09-22T05:00:00Z"
  }),
  true
);

console.log("SEBI document discovery and matching tests passed.");
