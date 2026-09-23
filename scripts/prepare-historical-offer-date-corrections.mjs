import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { HISTORICAL_OFFER_DATE_PARSER_VERSION } from "./backfill-historical-offer-dates.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const STATE_PATH = path.join(ROOT, "ops", "sebi-historical-offer-dates.json");

export const LEGACY_OFFER_DATE_CORRECTIONS = {
  "2024|unimech-aerospace-and-manufacturing-limited": {
    bad_open_date: null,
    bad_close_date: "2024-12-05",
    open_date: "2024-12-23",
    close_date: "2024-12-26",
    source_value: "Issue Period: December 23, 2024, to December 26, 2024",
    source: {
      url: "https://nsearchives.nseindia.com/corporate/UNIMECH_12022026181434_Monitoring_Agency_Report_covering_Signed.pdf",
      document_type: "NSE Monitoring Agency Report",
      document_identity: "Unimech Aerospace and Manufacturing Limited — Monitoring Agency Report",
      publication_date: "2026-02-12",
      page: 4
    }
  },
  "2025|corona-remedies-limited": {
    bad_open_date: "2025-12-05",
    bad_close_date: null,
    open_date: "2025-12-08",
    close_date: "2025-12-10",
    source_value: "Issue Period: December 08, 2025 to December 10, 2025",
    source: {
      url: "https://nsearchives.nseindia.com/annual_reports/AR_29392_CORONA_2025_2026_A_10308084_15062026212248.pdf",
      document_type: "NSE Annual Report PDF",
      document_identity: "CORONA Remedies Limited — Annual Report 2025-26",
      publication_date: "2026-06-15",
      page: 84
    }
  },
  "2025|nephrocare-health-services-limited": {
    bad_open_date: "2025-12-09",
    bad_close_date: null,
    open_date: "2025-12-10",
    close_date: "2025-12-12",
    source_value: "Issue Period: December 10, 2025, to December 12, 2025",
    source: {
      url: "https://nsearchives.nseindia.com/corporate/NEPHROCARE1_12022026130442_DisclosureofMonitoringAgencyReportdt1202026.pdf",
      document_type: "NSE Monitoring Agency Report",
      document_identity: "Nephrocare Health Services Limited — Monitoring Agency Report",
      publication_date: "2026-02-12",
      page: 5
    }
  }
};

function legacyValuesMatch(entry, correction) {
  return (
    (entry?.open_date ?? null) === correction.bad_open_date &&
    (entry?.close_date ?? null) === correction.bad_close_date
  );
}

export function prepareLegacyOfferDateCorrections(
  state,
  correctedAt = new Date().toISOString()
) {
  state ||= { schema_version: "1.0.0", issuers: {} };
  state.issuers ||= {};

  const stats = {
    candidates: Object.keys(LEGACY_OFFER_DATE_CORRECTIONS).length,
    prepared: 0,
    already_corrected: 0,
    skipped_missing_cursor: 0,
    skipped_value_mismatch: 0
  };

  for (const [key, correction] of Object.entries(LEGACY_OFFER_DATE_CORRECTIONS)) {
    const current = state.issuers[key];
    if (!current) {
      stats.skipped_missing_cursor += 1;
      continue;
    }

    if (
      current.status === "corrected_official_nse" &&
      current.parser_version === HISTORICAL_OFFER_DATE_PARSER_VERSION &&
      current.open_date === correction.open_date &&
      current.close_date === correction.close_date
    ) {
      stats.already_corrected += 1;
      continue;
    }

    if (!legacyValuesMatch(current, correction)) {
      stats.skipped_value_mismatch += 1;
      continue;
    }

    state.issuers[key] = {
      ...current,
      legacy_parser_version: current.parser_version ?? null,
      legacy_status: current.status ?? null,
      legacy_open_extraction: current.open_extraction ?? null,
      legacy_close_extraction: current.close_extraction ?? null,
      parser_version: HISTORICAL_OFFER_DATE_PARSER_VERSION,
      status: "corrected_official_nse",
      corrected_at: correctedAt,
      correction_reason: "Parser v1 false-positive date capture; replaced from explicit official NSE issue-period disclosure.",
      correction: {
        open_date: {
          previous_value: correction.bad_open_date,
          replacement_value: correction.open_date
        },
        close_date: {
          previous_value: correction.bad_close_date,
          replacement_value: correction.close_date
        },
        source_value: correction.source_value,
        source: correction.source
      },
      open_date: correction.open_date,
      close_date: correction.close_date,
      open_extraction: null,
      close_extraction: null,
      correction_source: correction.source,
      source_url: correction.source.url,
      last_attempted_at: correctedAt
    };
    stats.prepared += 1;
  }

  return stats;
}

async function run() {
  const state = fs.existsSync(STATE_PATH)
    ? JSON.parse(fs.readFileSync(STATE_PATH, "utf8"))
    : { schema_version: "1.0.0", issuers: {} };
  const stats = prepareLegacyOfferDateCorrections(state);
  if (stats.prepared > 0) {
    fs.mkdirSync(path.dirname(STATE_PATH), { recursive: true });
    fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2) + "\n");
  }
  console.log(JSON.stringify({ historical_offer_date_legacy_corrections: stats }, null, 2));
}

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;

if (isMain) run().catch((error) => {
  console.error(error);
  process.exit(1);
});
