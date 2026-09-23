import assert from "node:assert/strict";
import {
  extractBundleHints,
  matchIndexCompany,
  mergeIndexRows,
  normalizeIssuerName,
  pageFingerprint,
  parseBseSmeIpoIndex
} from "./audit-bse-sme-ipo-index.mjs";

const legacyHtml = `
<table>
<tr><th>Scrip Code</th><th>Company</th><th>ISIN No.</th><th>Close Price</th></tr>
<tr><td>544412</td><td>3B FILMS LIMITED</td><td>INE0TE101010</td><td>30</td></tr>
<tr><td>544535</td><td>BHARATROHAN AIRBORNE INNOVATIONS LIMITED</td><td>INE0QMV01017</td><td>97.12</td></tr>
<tr><td>544546</td><td>Chatterbox Technologies Limite</td><td>INE1B4801017</td><td>142.2</td></tr>
<tr><td>noise</td><td>Not a constituent</td><td>NA</td><td>0</td></tr>
</table>`;

const legacyRows = parseBseSmeIpoIndex(legacyHtml);
assert.equal(legacyRows.length, 3);
assert.equal(legacyRows[0].scrip_code, "544412");
assert.equal(legacyRows[1].isin, "INE0QMV01017");
assert.equal(legacyRows[0].row_format, "legacy_index_watch");
assert.equal(normalizeIssuerName("3B Films Limited"), "3b films");

const fingerprint = pageFingerprint(`
<html>
<head><title>BSE SME IPO - Index Details</title><script src="/assets/app.js"></script></head>
<body><div id="root"></div></body>
</html>`);
assert.equal(fingerprint.title, "BSE SME IPO - Index Details");
assert.equal(fingerprint.table_count, 0);
assert.equal(fingerprint.row_count, 0);
assert.deepEqual(fingerprint.script_sources, ["/assets/app.js"]);

assert.deepEqual(
  extractBundleHints('const a="/api/index/constituents";const b="plain";const c="https://x/api/indices";'),
  ["/api/index/constituents", "https://x/api/indices"]
);

const indexServicesHtml = `
<table>
<tr><th>Constituent</th><th>Scrip Code</th><th>Macro-Economic Sector</th></tr>
<tr><td>ABRIL PAPER TECH LIMITED</td><td>544500</td><td>Industrials</td></tr>
<tr><td>ACCORD TRANSFORMER &amp; SWITCHGEAR LIMITED</td><td>544710</td><td>Industrials</td></tr>
<tr><td>ADVANCE TECHNOFORGE LIMITED</td><td>544843</td><td>Industrials</td></tr>
</table>`;

const indexRows = parseBseSmeIpoIndex(indexServicesHtml);
assert.equal(indexRows.length, 3);
assert.equal(indexRows[0].company, "ABRIL PAPER TECH LIMITED");
assert.equal(indexRows[1].scrip_code, "544710");
assert.equal(indexRows[1].macro_sector, "Industrials");
assert.equal(indexRows[0].isin, null);
assert.equal(indexRows[0].row_format, "index_services");

const merged = mergeIndexRows([
  {
    name: "bse_index_services",
    url: "https://www.bseindices.com/constituents/code/76",
    rows: [
      {
        scrip_code: "544546",
        company: "Chatterbox Technologies Limited",
        isin: null,
        close_price: null,
        macro_sector: "Consumer Discretionary",
        row_format: "index_services"
      }
    ]
  },
  {
    name: "bse_legacy_index_watch",
    url: "https://www.bseindia.com/example",
    rows: [
      {
        scrip_code: "544546",
        company: "Chatterbox Technologies Limite",
        isin: "INE1B4801017",
        close_price: "142.2",
        macro_sector: null,
        row_format: "legacy_index_watch"
      }
    ]
  }
]);

assert.equal(merged.length, 1);
assert.equal(merged[0].company, "Chatterbox Technologies Limited");
assert.equal(merged[0].isin, "INE1B4801017");
assert.equal(merged[0].macro_sector, "Consumer Discretionary");
assert.equal(merged[0].official_sources.length, 2);
assert.equal(merged[0].row_format, "merged_official_formats");

const records = [
  { year: 2025, record: { issuer_name: "3B Films Limited" } },
  { year: 2025, record: { issuer_name: "Chatterbox Technologies Limited" } }
];
assert.equal(matchIndexCompany("3B FILMS LIMITED", records).match_type, "exact");
assert.equal(matchIndexCompany("Chatterbox Technologies Limite", records).match_type, "prefix");
assert.equal(matchIndexCompany("Missing SME Limited", records).match_type, "none");

console.log("BSE SME IPO index audit tests passed.");
