import assert from "node:assert/strict";
import { buildRecoveryProposal, buildJsonProposal } from "./prepare-live-sync-proposal.mjs";
import { applyRecoveryProposal, mergeThreeWay } from "./apply-live-sync-proposal.mjs";

const baseRecord = {
  id: "alpha",
  issuer_name: "Alpha Limited",
  status: "upcoming",
  terms: { market_lot: null, open_date: "2026-09-24" },
  issue_size_inr: { value: null },
  documents: [{ type: "NSE", url: "https://nse/a" }],
  last_collected_at: "2026-09-23T10:00:00Z"
};
const producedRecord = {
  ...baseRecord,
  status: "open",
  terms: { market_lot: 100, open_date: "2026-09-24" },
  issue_size_inr: { value: 500000000 },
  documents: [
    { type: "NSE", url: "https://nse/a" },
    { type: "SEBI", url: "https://sebi/b" }
  ],
  last_collected_at: "2026-09-23T11:00:00Z"
};

const before = { generated_at: "2026-09-23T10:00:00Z", records: [baseRecord] };
const after = {
  generated_at: "2026-09-23T11:00:00Z",
  records: [
    producedRecord,
    { id: "beta", issuer_name: "Beta Limited", status: "upcoming", terms: {}, documents: [] }
  ]
};
const proposal = buildRecoveryProposal(before, after);
assert.equal(proposal.changed_records.length, 1);
assert.equal(proposal.added_records.length, 1);

const concurrent = {
  generated_at: "2026-09-23T10:30:00Z",
  records: [{
    ...baseRecord,
    issue_size_inr: { value: 600000000 },
    documents: [
      { type: "NSE", url: "https://nse/a" },
      { type: "SEBI PDF", url: "https://sebi/concurrent" }
    ],
    last_collected_at: "2026-09-23T10:30:00Z"
  }]
};

const applied = applyRecoveryProposal(concurrent, proposal);
const alpha = applied.manifest.records.find((record) => record.id === "alpha");
const beta = applied.manifest.records.find((record) => record.id === "beta");
assert.equal(alpha.status, "open");
assert.equal(alpha.terms.market_lot, 100);
assert.equal(alpha.issue_size_inr.value, 600000000, "concurrent non-null field must win");
assert.ok(alpha.documents.some((doc) => doc.url === "https://sebi/concurrent"));
assert.ok(alpha.documents.some((doc) => doc.url === "https://sebi/b"));
assert.equal(beta.issuer_name, "Beta Limited");
assert.ok(applied.stats.conflicts >= 1);

const mergeStats = { applied: 0, conflicts: 0, already: 0 };
const arrayMerged = mergeThreeWay(
  [{ id: 1 }, { id: 3 }],
  [{ id: 1 }],
  [{ id: 1 }, { id: 2 }],
  mergeStats
);
assert.deepEqual(arrayMerged.value, [{ id: 1 }, { id: 3 }, { id: 2 }]);

assert.equal(buildJsonProposal({ issuers: {} }, { issuers: {} }), null);
assert.ok(buildJsonProposal({ issuers: {} }, { issuers: { a: { status: "x" } } }));

console.log("Semantic live-sync proposal/apply tests passed.");
