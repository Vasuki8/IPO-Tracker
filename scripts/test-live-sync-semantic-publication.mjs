import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { buildRecoveryProposal, buildJsonProposal, gitJson } from "./prepare-live-sync-proposal.mjs";
import { applyRecoveryProposal, applyRecoveryProposals, mergeThreeWay } from "./apply-live-sync-proposal.mjs";

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

const largeRepo = fs.mkdtempSync(path.join(os.tmpdir(), "live-sync-large-git-json-"));
try {
  execFileSync("git", ["init", "-q"], { cwd: largeRepo });
  execFileSync("git", ["config", "user.name", "IPO Tracker Test"], { cwd: largeRepo });
  execFileSync("git", ["config", "user.email", "test@example.invalid"], { cwd: largeRepo });
  const largeValue = "x".repeat(2 * 1024 * 1024);
  fs.writeFileSync(path.join(largeRepo, "large.json"), JSON.stringify({
    records: [{ id: "large", issuer_name: "Large Fixture Limited", large_value: largeValue }]
  }));
  execFileSync("git", ["add", "large.json"], { cwd: largeRepo });
  execFileSync("git", ["commit", "-q", "-m", "large fixture"], { cwd: largeRepo });

  const loaded = gitJson("HEAD", "large.json", largeRepo);
  assert.equal(loaded.records[0].large_value.length, largeValue.length,
    "git baseline JSON larger than Node's default child-process buffer must remain readable");
} finally {
  fs.rmSync(largeRepo, { recursive: true, force: true });
}

console.log("Semantic live-sync proposal/apply tests passed.");

const newYearProposal=buildRecoveryProposal(undefined,{collection_started_at:"2027-01-01T00:00:00Z",generated_at:"2027-01-02T00:00:00Z",records:[{id:"alpha",issuer_name:"Alpha Limited"},{id:"shared",issuer_name:"Shared Limited",terms:{market_lot:100}}]});
const concurrentNewYear={collection_started_at:"2027-01-01T01:00:00Z",generated_at:"2027-01-03T00:00:00Z",records:[{id:"beta",issuer_name:"Beta Limited"},{id:"shared",issuer_name:"Shared Limited",terms:{market_lot:200}}]};
const newYearMerged=applyRecoveryProposal(concurrentNewYear,newYearProposal);
assert.deepEqual(newYearMerged.manifest.records.map(r=>r.id),["alpha","beta","shared"],"Concurrent new manifest must preserve both sets of stable identities");
assert.equal(newYearMerged.manifest.records.find(r=>r.id==="shared").terms.market_lot,200);
assert.equal(newYearMerged.stats.conflicts,1,"Divergent same identity must remain a visible conflict");
assert.equal(newYearMerged.manifest.generated_at,concurrentNewYear.generated_at);
assert.equal(newYearMerged.manifest.collection_started_at,concurrentNewYear.collection_started_at);
assert.equal(applyRecoveryProposal(newYearMerged.manifest,newYearProposal).changed,false);
assert.equal(applyRecoveryProposal(undefined,newYearProposal).manifest.records.length,2);
console.log("Concurrent new-year manifest merge tests passed.");

// BUG-007: cross-year moves must be identity-atomic across recovery manifests.
// A concurrent source edit may block the removal; in that case the target
// addition must also be held so one stable ID never exists in two years.
const sourcePath = "data/recovery/2026/nse-issue-information.json";
const targetPath = "data/recovery/2027/nse-issue-information.json";
const movingBefore = {
  id: "moving-limited",
  issuer_name: "Moving Limited",
  status: "upcoming",
  terms: { open_date: "2026-12-31" },
  documents: [{ type: "NSE", url: "https://nse/moving" }],
  last_collected_at: "2026-12-20T00:00:00Z"
};
const movingAfter = {
  ...movingBefore,
  status: "open",
  terms: { open_date: "2027-01-02" },
  last_collected_at: "2027-01-02T01:00:00Z"
};
const sourceBefore = {
  generated_at: "2026-12-20T00:00:00Z",
  records: [movingBefore, { id: "source-safe", issuer_name: "Source Safe Limited" }]
};
const sourceAfter = {
  generated_at: "2027-01-02T01:00:00Z",
  records: [{ id: "source-safe", issuer_name: "Source Safe Limited" }]
};
const targetBefore = {
  generated_at: "2026-12-20T00:00:00Z",
  records: [{ id: "target-existing", issuer_name: "Target Existing Limited" }]
};
const targetAfter = {
  generated_at: "2027-01-02T01:00:00Z",
  records: [
    { id: "target-existing", issuer_name: "Target Existing Limited" },
    movingAfter,
    { id: "target-safe", issuer_name: "Target Safe Limited" }
  ]
};
const migrationProposals = {
  [sourcePath]: buildRecoveryProposal(sourceBefore, sourceAfter),
  [targetPath]: buildRecoveryProposal(targetBefore, targetAfter)
};

const cleanMigration = applyRecoveryProposals(
  { [sourcePath]: sourceBefore, [targetPath]: targetBefore },
  migrationProposals
);
assert.equal(cleanMigration.rolled_back_identities.length, 0);
assert.equal(cleanMigration.manifests[sourcePath].records.some((record) => record.id === movingBefore.id), false);
assert.deepEqual(
  cleanMigration.manifests[targetPath].records.filter((record) => record.id === movingBefore.id),
  [movingAfter],
  "clean migration must move the stable identity exactly once"
);
assert.ok(cleanMigration.manifests[targetPath].records.some((record) => record.id === "target-safe"));

const replayMigration = applyRecoveryProposals(cleanMigration.manifests, migrationProposals);
assert.deepEqual(replayMigration.changed_paths, [], "cross-year migration replay must be idempotent");
assert.equal(
  Object.values(replayMigration.manifests).flatMap((manifest) => manifest.records)
    .filter((record) => record.id === movingBefore.id).length,
  1
);

const concurrentSource = structuredClone(sourceBefore);
concurrentSource.records[0] = {
  ...movingBefore,
  sector: "concurrent review",
  last_collected_at: "2026-12-21T00:00:00Z"
};
const heldMigration = applyRecoveryProposals(
  { [sourcePath]: concurrentSource, [targetPath]: targetBefore },
  migrationProposals
);
assert.deepEqual(heldMigration.rolled_back_identities, [movingBefore.id]);
assert.deepEqual(
  heldMigration.manifests[sourcePath].records.find((record) => record.id === movingBefore.id),
  concurrentSource.records[0],
  "concurrently edited source identity must be preserved"
);
assert.equal(
  heldMigration.manifests[targetPath].records.some((record) => record.id === movingBefore.id),
  false,
  "blocked source removal must also block the target-year duplicate"
);
assert.ok(
  heldMigration.manifests[targetPath].records.some((record) => record.id === "target-safe"),
  "unrelated safe additions in the same manifest must still apply"
);
assert.equal(
  Object.values(heldMigration.manifests).flatMap((manifest) => manifest.records)
    .filter((record) => record.id === movingBefore.id).length,
  1
);
assert.equal(heldMigration.stats.cross_year_identity_rollbacks, 1);

const preexistingDuplicate = {
  [sourcePath]: sourceBefore,
  [targetPath]: {
    ...targetBefore,
    records: [...targetBefore.records, structuredClone(movingBefore)]
  }
};
assert.throws(
  () => applyRecoveryProposals(preexistingDuplicate, migrationProposals),
  /preexisting_recovery_identity_collision:moving-limited/
);
console.log("Cross-year identity-atomic recovery merge tests passed.");

// BUG-003: a publication collision must never splice a field's value and source.
// Removing the atomic-field guard must make these real merge tests fail.
const observedField = (value, source, status = "verified") => ({
  value, status, source: { url: `https://www.nseindia.com/${source}`, document_identity: source },
  corrections: [{ reason: source }]
});
const collisions = [
  ["competing values", observedField(100, "a"), observedField(120, "a"), observedField(110, "b")],
  ["source-only concurrent edit", observedField(100, "a"), observedField(100, "c"), observedField(110, "a")],
  ["band endpoints", observedField({min:100,max:200}, "a"), observedField({min:150,max:200}, "a"), observedField({min:100,max:125}, "b")],
  ["cleared conflict", observedField(100, "a"), observedField(null, "c", "conflict"), observedField(110, "b")],
];
for (const [label, original, current, incoming] of collisions) {
  const originals = structuredClone([original, current, incoming]);
  const result = mergeThreeWay(current, original, incoming);
  assert.deepEqual(result.value, current, `${label}: hold the complete current field, including source and history`);
  assert.equal(result.changed, false, label);
  assert.equal(result.stats.conflicts, 1, `${label}: report one atomic collision`);
  assert.deepEqual([original, current, incoming], originals, `${label}: do not mutate inputs`);
  const accepted = mergeThreeWay(original, original, incoming);
  assert.deepEqual(accepted.value, incoming, `${label}: accept a non-concurrent update as a complete field`);
  assert.equal(accepted.stats.conflicts, 0);
  assert.equal(mergeThreeWay(accepted.value, original, incoming).changed, false, `${label}: replay is idempotent`);
}
const nestedBefore = {id:"atomic",issuer_name:"Atomic Limited",issue_price:observedField(100,"a"),application_requirements:{retail:{minimum_bid_quantity:observedField(10,"a")}}};
const nestedCurrent = structuredClone(nestedBefore);
nestedCurrent.issue_price = observedField(120,"a");
nestedCurrent.application_requirements.retail.minimum_bid_quantity = observedField(20,"a");
const nestedAfter = structuredClone(nestedBefore);
nestedAfter.issue_price = observedField(110,"b");
nestedAfter.application_requirements.retail.minimum_bid_quantity = observedField(15,"b");
nestedAfter.sector = "independent update";
const nestedProposal = buildRecoveryProposal({records:[nestedBefore]}, {records:[nestedAfter]});
const nestedResult = applyRecoveryProposal({records:[nestedCurrent]}, nestedProposal);
assert.deepEqual(nestedResult.manifest.records[0].issue_price, nestedCurrent.issue_price);
assert.deepEqual(nestedResult.manifest.records[0].application_requirements, nestedCurrent.application_requirements);
assert.equal(nestedResult.manifest.records[0].sector, "independent update");
assert.equal(nestedResult.stats.conflicts, 2);
assert.equal(applyRecoveryProposal(nestedResult.manifest,nestedProposal).changed, false);
console.log("Atomic evidence merge regressions passed: values, bands, sources, cleared fields, nested application requirements and idempotent replay.");
