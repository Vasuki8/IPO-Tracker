import assert from "node:assert/strict";
import fs from "node:fs";

await import("../assets/ipo-order.js");

const { compareNewestFirst } = globalThis.IPOOrder;

const rows = [
  { issuer_name: "Older", open_date: { value: "2026-09-18" }, close_date: { value: "2026-09-22" }, listing_date: { value: "2026-09-28" } },
  { issuer_name: "Newest B", open_date: { value: "2026-09-23" }, close_date: { value: "2026-09-25" }, listing_date: { value: "2026-10-01" } },
  { issuer_name: "Newest A", open_date: { value: "2026-09-23" }, close_date: { value: "2026-09-25" }, listing_date: { value: "2026-10-01" } },
  { issuer_name: "Historical Newer", open_date: { value: null }, close_date: { value: null }, listing_date: { value: "2025-12-20" } },
  { issuer_name: "Historical Older", open_date: { value: null }, close_date: { value: null }, listing_date: { value: "2025-11-20" } },
  { issuer_name: "Missing date", open_date: { value: null }, close_date: { value: null }, listing_date: { value: null } }
];

const sorted = [...rows].sort(compareNewestFirst);
assert.deepEqual(
  sorted.map((row) => row.issuer_name),
  ["Newest A", "Newest B", "Older", "Historical Newer", "Historical Older", "Missing date"]
);

const payload = JSON.parse(fs.readFileSync(new URL("../data/ipos.json", import.meta.url), "utf8"));
const published = payload.records;
const independentlySorted = [...payload.records].sort(compareNewestFirst);
assert.deepEqual(
  published.map((row) => row.id),
  independentlySorted.map((row) => row.id),
  "published dataset must already be newest-first"
);

for (let index = 1; index < published.length; index += 1) {
  const previous = published[index - 1].open_date?.value ?? "";
  const current = published[index].open_date?.value ?? "";
  assert.ok(previous >= current, `open-date order failed at index ${index}: ${previous} < ${current}`);
}

const publishedDates = published
  .map((row) => row.open_date?.value)
  .filter(Boolean)
  .sort();

assert.ok(publishedDates.length > 0, "published dataset must contain at least one open date");
assert.equal(
  published[0].open_date?.value,
  publishedDates.at(-1),
  "first published row must have the newest available open date"
);

const lastDatedRow = [...published].reverse().find((row) => row.open_date?.value);
assert.equal(
  lastDatedRow?.open_date?.value,
  publishedDates[0],
  "last dated published row must have the oldest available open date"
);

console.log("Homepage newest-first ordering tests passed.");
