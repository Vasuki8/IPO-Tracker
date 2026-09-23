import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RECOVERY = path.join(ROOT, "data", "recovery");
const MANIFEST = path.join(ROOT, "data", "bse-ipo-sources.json");

function fieldPresent(record, key) {
  if (key === "price_band") return record.price_band?.value != null || record.terms?.price_band != null;
  if (key === "market_lot") return record.market_lot?.value != null || record.terms?.market_lot != null;
  if (key === "minimum_bid_quantity") {
    return record.minimum_bid_quantity?.value != null || record.terms?.minimum_bid_quantity != null;
  }
  if (key === "open_date") return record.open_date?.value != null || record.terms?.open_date != null;
  if (key === "close_date") return record.close_date?.value != null || record.terms?.close_date != null;
  return record[key]?.value != null;
}

function hasDocument(record, pattern) {
  return (record.documents || []).some((doc) =>
    pattern.test(String(doc.type || "")) || pattern.test(String(doc.url || ""))
  );
}

export function summarizeHistoricalYear(year, manifest, bseSourceCount = 0) {
  if (!manifest) {
    return {
      year,
      recovery_present: false,
      status: "universe_not_materialized",
      records: 0,
      mainboard: 0,
      sme: 0,
      board_unknown: 0,
      bse_verified_sources: bseSourceCount,
      bse_attached_records: 0,
      sebi_attached_records: 0,
      coverage: {}
    };
  }

  const records = Array.isArray(manifest.records) ? manifest.records : [];
  const fields = [
    "price_band",
    "issue_price",
    "issue_size_inr",
    "market_lot",
    "minimum_bid_quantity",
    "open_date",
    "close_date",
    "listing_date"
  ];
  const coverage = Object.fromEntries(
    fields.map((field) => [field, records.filter((record) => fieldPresent(record, field)).length])
  );

  return {
    year,
    recovery_present: true,
    status: "materialized",
    records: records.length,
    mainboard: records.filter((record) => record.board === "Mainboard").length,
    sme: records.filter((record) => record.board === "SME").length,
    board_unknown: records.filter((record) => !["Mainboard", "SME"].includes(record.board)).length,
    bse_verified_sources: bseSourceCount,
    bse_attached_records: records.filter((record) => hasDocument(record, /BSE|bseindia\.com/i)).length,
    sebi_attached_records: records.filter((record) => hasDocument(record, /SEBI|sebi\.gov\.in/i)).length,
    coverage
  };
}

export function buildHistoricalCoverageAudit(years, recoveryByYear, sources) {
  return years.map((year) =>
    summarizeHistoricalYear(
      year,
      recoveryByYear.get(year) || null,
      sources.filter((source) => source.year === year).length
    )
  );
}

function loadRecoveryByYear() {
  const result = new Map();
  if (!fs.existsSync(RECOVERY)) return result;

  for (const entry of fs.readdirSync(RECOVERY, { withFileTypes: true })) {
    if (!entry.isDirectory() || !/^20\d{2}$/.test(entry.name)) continue;
    const year = Number(entry.name);
    const file = path.join(RECOVERY, entry.name, "nse-issue-information.json");
    if (!fs.existsSync(file)) continue;
    result.set(year, JSON.parse(fs.readFileSync(file, "utf8")));
  }
  return result;
}

function run() {
  const recoveryByYear = loadRecoveryByYear();
  const sources = fs.existsSync(MANIFEST)
    ? JSON.parse(fs.readFileSync(MANIFEST, "utf8")).sources || []
    : [];
  const historicalCoverage = buildHistoricalCoverageAudit(
    [2026, 2025, 2024, 2023, 2022, 2021, 2020],
    recoveryByYear,
    sources
  );
  console.log(JSON.stringify({
    total_records: historicalCoverage.reduce((sum, row) => sum + row.records, 0),
    historical_coverage: historicalCoverage
  }, null, 2));
}

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run();
