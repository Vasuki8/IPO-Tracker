import assert from "node:assert/strict";
import fs from "node:fs";
import {
  appendDocument,
  applySebiEntry,
  cacheBustedListingUrl,
  canonicalIssuer,
  issuerFromListingTitle,
  issuerVariants,
  issuerFromFilingUrl,
  matchIssuerRecord,
  buildSebiSearchUrl,
  hasSebiDocument,
  targetedSearchCandidates,
  searchTermForIssuer,
  parseAbridgedProspectusLinks,
  parseProspectusPdfLinks,
  parseOtherDocumentPdfLinks,
  directSebiProspectusPdf,
  parseSebiDate,
  parseSebiListingHtml,
  SEBI_PUBLIC_ISSUES_URL
} from "./sync-sebi-documents.mjs";

const listing = fs.readFileSync(new URL("./fixtures/sebi-public-issues-sample.html", import.meta.url), "utf8");
const detail = fs.readFileSync(new URL("./fixtures/sebi-rhp-detail-sample.html", import.meta.url), "utf8");
const finalDetail = fs.readFileSync(new URL("./fixtures/sebi-prospectus-detail-sample.html", import.meta.url), "utf8");
const base = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&smid=11&ssid=15";

assert.equal(parseSebiDate("Sep 21, 2026"), "2026-09-21");
assert.equal(parseSebiDate("bad date"), null);
assert.equal(
  cacheBustedListingUrl(
    "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&smid=11&ssid=15",
    "20260922070000"
  ),
  "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&smid=11&ssid=15&_fresh=20260922070000"
);
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

const allFilings = parseSebiListingHtml(listing, null, base);
assert.equal(allFilings.length, 5);

const finals = parseSebiListingHtml(listing, "final", base);
assert.equal(finals.length, 2);
assert.equal(finals[0].issuer_name, "Manipal Payment & Identity Solutions Limited");
assert.equal(canonicalIssuer(finals[1].issuer_name), "kanohar electricals");
assert.equal(
  canonicalIssuer(issuerFromFilingUrl(
    "https://www.sebi.gov.in/filings/public-issues/sep-2026/kanohar-electricals-limited-prospectus_104483.html",
    "final"
  )),
  "kanohar electricals"
);

const aps = parseAbridgedProspectusLinks(detail, rhp[0].url);
assert.equal(aps.length, 1);
assert.equal(aps[0].type, "SEBI Abridged Prospectus");
assert.ok(aps[0].url.includes("/sebi_data/commondocs/"));

const rhpPdfs = parseProspectusPdfLinks(detail, rhp[0].url).map((doc) => ({
  ...doc,
  type: "SEBI RHP PDF"
}));
assert.equal(rhpPdfs.length, 1);
assert.equal(rhpPdfs[0].type, "SEBI RHP PDF");
assert.equal(
  rhpPdfs[0].url,
  "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/1789986760331.pdf"
);

const records = [
  { record: { issuer_name: "Moneyview Limited" }, recovery: { changed: false } },
  { record: { issuer_name: "Swastika Infra Limited" }, recovery: { changed: false } },
  { record: { issuer_name: "Adroit Industries (India) Limited" }, recovery: { changed: false } },
  { record: { issuer_name: "National Stock Exchange of India Limited" }, recovery: { changed: false } }
];

const malformedLiveRhp = `
  <div>Sep 21, 2026</div>
  <a href="https://www.sebi.gov.in/filings/public-issues/sep-2026/adroit-industries-limited-rhp_104607.html">
    Adroit Industries Limited - Abridged Prospectus
  </a>
  <div>Sep 17, 2026</div>
  <a href="https://www.sebi.gov.in/filings/public-issues/sep-2026/swastika-infra-ltd-rhp_104573.html">
    Swastika Infra Ltd. - Abridged Prospectus
  </a>
  <div>Sep 11, 2026</div>
  <a href="https://www.sebi.gov.in/filings/public-issues/sep-2026/national-stock-exchange-of-india-limited-rhp_104428.html">
    NATIONAL STOCK EXCHANGE OF INDIA LIMITED - Abridged Prospectus
  </a>
`;
const malformedParsed = parseSebiListingHtml(malformedLiveRhp, "rhp", base);
assert.deepEqual(
  malformedParsed.map((entry) => canonicalIssuer(entry.issuer_name)),
  ["adroit industries", "swastika infra", "national stock exchange of india"]
);
assert.equal(matchIssuerRecord(records, malformedParsed[0].issuer_name).record.issuer_name, "Adroit Industries (India) Limited");
assert.equal(matchIssuerRecord(records, malformedParsed[1].issuer_name).record.issuer_name, "Swastika Infra Limited");
assert.equal(
  matchIssuerRecord(records, malformedParsed[2].issuer_name).record.issuer_name,
  "National Stock Exchange of India Limited"
);


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

const sparseRecords = [
  {
    record: {
      issuer_name: "New Live Limited",
      first_observed_at: "2026-09-22T04:00:00Z",
      nse_source: {
        document_type: "NSE IPO Live Feed",
        url: "https://www.nseindia.com/api/all-upcoming-issues?category=ipo"
      },
      documents: [{ type: "NSE IPO Live Feed", url: "https://www.nseindia.com/api/all-upcoming-issues?category=ipo" }]
    },
    recovery: {}
  },
  {
    record: {
      issuer_name: "Already Enriched Limited",
      first_observed_at: "2026-09-22T03:00:00Z",
      nse_source: {
        document_type: "NSE IPO Live Feed",
        url: "https://www.nseindia.com/api/all-upcoming-issues?category=ipo"
      },
      documents: [
        { type: "NSE IPO Live Feed", url: "https://www.nseindia.com/api/all-upcoming-issues?category=ipo" },
        { type: "SEBI RHP filing", url: "https://www.sebi.gov.in/filings/public-issues/sep-2026/already-enriched-limited-rhp_1.html" }
      ]
    },
    recovery: {}
  },
  {
    record: {
      issuer_name: "Manual Limited",
      first_observed_at: "2026-09-22T05:00:00Z",
      nse_source: {
        document_type: "NSE Issue Information",
        url: "https://www.nseindia.com/market-data/issue-information?series=EQ&symbol=MANUAL&type=Active"
      },
      documents: []
    },
    recovery: {}
  }
];

assert.equal(hasSebiDocument(sparseRecords[0].record), false);
assert.equal(hasSebiDocument(sparseRecords[1].record), true);
assert.deepEqual(
  targetedSearchCandidates(sparseRecords, 10).map(({ record }) => record.issuer_name),
  ["New Live Limited"]
);
assert.equal(searchTermForIssuer("Adroit Industries (India) Limited"), "adroit");
assert.equal(searchTermForIssuer("Swastika Infra Limited"), "swastika");
assert.equal(searchTermForIssuer("National Stock Exchange of India Limited"), "national");
assert.equal(
  buildSebiSearchUrl("National Stock Exchange of India Limited"),
  "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListingAll=yes&search=national"
);

assert.equal(
  SEBI_PUBLIC_ISSUES_URL,
  "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&ssid=15"
);

const viewerUrl =
  "https://www.sebi.gov.in/web/?file=https%3A%2F%2Fwww.sebi.gov.in%2Fsebi_data%2Fattachdocs%2Fsep-2026%2F1789991154046.pdf";
assert.equal(
  directSebiProspectusPdf(viewerUrl, "https://www.sebi.gov.in/"),
  "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/1789991154046.pdf"
);
assert.equal(
  directSebiProspectusPdf("https://example.com/file.pdf", "https://www.sebi.gov.in/"),
  null
);

const prospectusPdfs = parseProspectusPdfLinks(
  finalDetail,
  "https://www.sebi.gov.in/filings/public-issues/sep-2026/example-limited-prospectus_1.html"
);
assert.equal(prospectusPdfs.length, 1);
assert.equal(prospectusPdfs[0].type, "SEBI Prospectus PDF");
assert.equal(
  prospectusPdfs[0].url,
  "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/1789991154046.pdf"
);

const otherDocumentPdfs = parseOtherDocumentPdfLinks(
  finalDetail,
  "https://www.sebi.gov.in/filings/public-issues/sep-2026/qualiance-international-limited_104401.html",
  "QUALIANCE INTERNATIONAL LIMITED"
);
assert.equal(otherDocumentPdfs.length, 1);
assert.equal(otherDocumentPdfs[0].type, "SEBI Other Document PDF");
assert.equal(otherDocumentPdfs[0].identity, "QUALIANCE INTERNATIONAL LIMITED — PDF");
assert.equal(
  otherDocumentPdfs[0].url,
  "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/1789991154046.pdf"
);
