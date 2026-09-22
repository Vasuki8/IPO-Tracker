import assert from "node:assert/strict";
import fs from "node:fs";
import {
  applyIssuePriceExtraction,
  candidateProspectusDocument,
  findIssuePriceMentions,
  parseExplicitIssuePriceFromPages
} from "./extract-prospectus-fields.mjs";

const fixture = JSON.parse(
  fs.readFileSync(new URL("./fixtures/prospectus-issue-price-layout.json", import.meta.url), "utf8")
);

for (const testCase of fixture.cases) {
  const extracted = parseExplicitIssuePriceFromPages(testCase.pages);
  assert.equal(extracted?.value ?? null, testCase.expected?.value ?? null, testCase.name);
  assert.equal(extracted?.page ?? null, testCase.expected?.page ?? null, testCase.name + " page");
  if (testCase.expected) assert.match(extracted.source_value, /^₹/);
}

const diagnosticMentions = findIssuePriceMentions(
  "The Offer Price shall be finalised after the Book Building Process. Later, the Issue Price is ₹424 per Equity Share.",
  12
);
assert.equal(diagnosticMentions.length, 2);
assert.equal(diagnosticMentions[0].page, 12);
assert.match(diagnosticMentions[0].context, /Offer Price/);
assert.match(diagnosticMentions[1].context, /Issue Price/);

const doc = {
  type: "SEBI Prospectus PDF",
  identity: "Example Limited - Prospectus — PDF",
  url: "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/example.pdf",
  publication_date: "2026-09-21"
};

const record = {
  issuer_name: "Example Limited",
  issue_price: undefined,
  documents: [doc],
  last_collected_at: "2026-09-20T00:00:00Z"
};

assert.equal(candidateProspectusDocument(record), doc);
assert.equal(
  applyIssuePriceExtraction(
    record,
    doc,
    { value: 93, source_value: "₹93 per Equity Share", page: 4 },
    "2026-09-22T05:00:00Z"
  ),
  true
);
assert.equal(record.issue_price.value, 93);
assert.equal(record.issue_price.page, 4);
assert.equal(record.issue_price.source.url, doc.url);
assert.equal(record.last_collected_at, "2026-09-22T05:00:00Z");

const existing = {
  issuer_name: "Existing Limited",
  issue_price: { value: 88, source: { url: "https://example.com" } },
  documents: [doc]
};
assert.equal(candidateProspectusDocument(existing), null);
assert.equal(
  applyIssuePriceExtraction(
    existing,
    doc,
    { value: 93, source_value: "₹93 per Equity Share", page: 4 },
    "2026-09-22T05:00:00Z"
  ),
  false
);
assert.equal(existing.issue_price.value, 88);

const mirrorRecord = {
  issuer_name: "Mirror Limited",
  documents: [{ ...doc, url: "https://example.com/prospectus.pdf" }]
};
assert.equal(candidateProspectusDocument(mirrorRecord), null);

console.log("Prospectus issue-price extraction tests passed.");
