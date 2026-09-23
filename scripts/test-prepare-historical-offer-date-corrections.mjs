import assert from "node:assert/strict";
import {
  LEGACY_OFFER_DATE_CORRECTIONS,
  prepareLegacyOfferDateCorrections
} from "./prepare-historical-offer-date-corrections.mjs";

const state = {
  schema_version: "1.0.0",
  issuers: {
    "2024|unimech-aerospace-and-manufacturing-limited": {
      issuer_name: "Unimech Aerospace and Manufacturing Limited",
      parser_version: "1.0.0",
      status: "extracted",
      open_date: null,
      close_date: "2024-12-05",
      open_extraction: null,
      close_extraction: { value: "2024-12-05", source_value: "Offer Closing Date. F&S letter dated December 5, 2024", page: 29 }
    },
    "2025|corona-remedies-limited": {
      issuer_name: "Corona Remedies Limited",
      parser_version: "1.0.0",
      status: "extracted",
      open_date: "2025-12-05",
      close_date: null,
      open_extraction: { value: "2025-12-05", source_value: "Anchor Investor Offer Opening Date December 5, 2025", page: 8 }
    },
    "2025|nephrocare-health-services-limited": {
      issuer_name: "Nephrocare Health Services Limited",
      parser_version: "1.0.0",
      status: "extracted",
      open_date: "2025-12-09",
      close_date: null,
      open_extraction: { value: "2025-12-09", source_value: "Offer Opening Date December 9, 2025 on which Bids by Anchor Investors were submitted", page: 9 }
    }
  }
};

const stats = prepareLegacyOfferDateCorrections(state, "2026-09-23T21:35:00Z");
assert.equal(stats.prepared, 3);
assert.equal(stats.skipped_value_mismatch, 0);

const unimech = state.issuers["2024|unimech-aerospace-and-manufacturing-limited"];
assert.equal(unimech.parser_version, "2.0.0");
assert.equal(unimech.status, "corrected_official_nse");
assert.equal(unimech.open_date, "2024-12-23");
assert.equal(unimech.close_date, "2024-12-26");
assert.equal(unimech.legacy_close_extraction.value, "2024-12-05");
assert.equal(unimech.correction.source.page, 4);

const second = prepareLegacyOfferDateCorrections(state, "2026-09-23T21:36:00Z");
assert.equal(second.prepared, 0);
assert.equal(second.already_corrected, 3);

const mismatch = {
  schema_version: "1.0.0",
  issuers: {
    "2025|corona-remedies-limited": {
      parser_version: "2.0.0",
      status: "extracted",
      open_date: "2025-12-08",
      close_date: "2025-12-10"
    }
  }
};
const mismatchStats = prepareLegacyOfferDateCorrections(mismatch, "2026-09-23T21:35:00Z");
assert.equal(mismatchStats.prepared, 0);
assert.ok(mismatchStats.skipped_value_mismatch >= 1);

assert.equal(Object.keys(LEGACY_OFFER_DATE_CORRECTIONS).length, 3);
console.log("Historical offer-date legacy correction tests passed.");
