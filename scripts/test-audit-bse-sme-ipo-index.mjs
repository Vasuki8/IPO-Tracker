import assert from "node:assert/strict";
import { matchIndexCompany, normalizeIssuerName, parseBseSmeIpoIndex } from "./audit-bse-sme-ipo-index.mjs";

const html = `
<table>
<tr><th>Scrip Code</th><th>Company</th><th>ISIN No.</th><th>Close Price</th></tr>
<tr><td>544412</td><td>3B FILMS LIMITED</td><td>INE0TE101010</td><td>30</td></tr>
<tr><td>544535</td><td>BHARATROHAN AIRBORNE INNOVATIONS LIMITED</td><td>INE0QMV01017</td><td>97.12</td></tr>
<tr><td>544546</td><td>Chatterbox Technologies Limite</td><td>INE1B4801017</td><td>142.2</td></tr>
<tr><td>noise</td><td>Not a constituent</td><td>NA</td><td>0</td></tr>
</table>`;

const rows = parseBseSmeIpoIndex(html);
assert.equal(rows.length, 3);
assert.equal(rows[0].scrip_code, "544412");
assert.equal(rows[1].isin, "INE0QMV01017");
assert.equal(normalizeIssuerName("3B Films Limited"), "3b films");

const records = [
  { year: 2025, record: { issuer_name: "3B Films Limited" } },
  { year: 2025, record: { issuer_name: "Chatterbox Technologies Limited" } }
];
assert.equal(matchIndexCompany("3B FILMS LIMITED", records).match_type, "exact");
assert.equal(matchIndexCompany("Chatterbox Technologies Limite", records).match_type, "prefix");
assert.equal(matchIndexCompany("Missing SME Limited", records).match_type, "none");

console.log("BSE SME IPO index audit tests passed.");
