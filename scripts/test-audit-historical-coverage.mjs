import assert from "node:assert/strict";import {buildHistoricalCoverageAudit} from "./audit-historical-coverage.mjs";
const rows=buildHistoricalCoverageAudit([2026,2025,2024],new Set([2026]),[{year:2025},{year:2025}]);
assert.deepEqual(rows,[{year:2026,recovery_present:true,bse_verified_sources:0,status:"materialized"},{year:2025,recovery_present:false,bse_verified_sources:2,status:"universe_not_materialized"},{year:2024,recovery_present:false,bse_verified_sources:0,status:"universe_not_materialized"}]);
console.log("Historical coverage audit tests passed.");