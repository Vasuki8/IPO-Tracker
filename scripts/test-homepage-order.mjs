import assert from "node:assert/strict";
import fs from "node:fs";

await import("../assets/ipo-order.js");

const { compareNewestFirst } = globalThis.IPOOrder;

const rows = [
  { issuer_name: "Older", open_date: { value: "2026-09-18" }, close_date: { value: "2026-09-22" } },
  { issuer_name: "Newest B", open_date: { value: "2026-09-23" }, close_date: { value: "2026-09-25" } },
  { issuer_name: "Newest A", open_date: { value: "2026-09-23" }, close_date: { value: "2026-09-25" } },
  { issuer_name: "Missing date", open_date: { value: null }, close_date: { value: null } }
];

const sorted = [...rows].sort(compareNewestFirst);
assert.deepEqual(
  sorted.map((row) => row.issuer_name),
  ["Newest A", "Newest B", "Older", "Missing date"]
);

const payload = JSON.parse(fs.readFileSync(new URL("../data/ipos.json", import.meta.url), "utf8"));
const published = [...payload.records].sort(compareNewestFirst);

for (let index = 1; index < published.length; index += 1) {
  const previous = published[index - 1].open_date?.value ?? "";
  const current = published[index].open_date?.value ?? "";
  assert.ok(previous >= current, `open-date order failed at index ${index}: ${previous} < ${current}`);
}

assert.equal(published[0].open_date?.value, "2026-09-23");
assert.equal(published.at(-1).open_date?.value, "2026-08-28");

console.log("Homepage newest-first ordering tests passed.");
