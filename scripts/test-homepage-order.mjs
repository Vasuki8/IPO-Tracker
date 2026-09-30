import assert from "node:assert/strict";
import fs from "node:fs";

await import("../assets/ipo-order.js");

const { compareNewestFirst } = globalThis.IPOOrder;

const mixedDateRows = [
  { issuer_name: "January opening", open_date: { value: "2026-01-15" }, listing_date: { value: "2026-09-01" } },
  { issuer_name: "August listing", listing_date: { value: "2026-08-21" } },
  { issuer_name: "July closing", open_date: { value: "invalid" }, close_date: { value: "2026-07-20" } },
  { issuer_name: "Undated" },
];
for (const input of [mixedDateRows, [...mixedDateRows].reverse()]) {
  assert.deepEqual(
    [...input].sort(compareNewestFirst).map((row) => row.issuer_name),
    ["August listing", "July closing", "January opening", "Undated"],
    "newest first must compare each record's first valid opening, closing, or listing date across date kinds",
  );
}

assert.ok(
  compareNewestFirst(
    { issuer_name: "Impossible opening", open_date: { value: "2026-02-30" }, close_date: { value: "2026-01-20" } },
    { issuer_name: "February opening", open_date: { value: "2026-02-15" } },
  ) > 0,
  "impossible calendar dates must fall back to the first valid available date",
);

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

const fallbackRows = [
  { issuer_name: "Undated Z" },
  { issuer_name: "Listing older", listing_date: { value: "2024-12-20" } },
  { issuer_name: "Undated A", open_date: { value: null } },
  { issuer_name: "Listing newer", listing_date: { value: "2025-12-20" } },
  { issuer_name: "Closing older", close_date: { value: "2025-06-01" }, listing_date: { value: "2026-12-20" } },
  { issuer_name: "Closing newer", close_date: { value: "2026-06-01" } },
  { issuer_name: "Undated B", open_date: { value: "invalid" }, close_date: { value: "invalid" }, listing_date: { value: "invalid" } },
];
const fallbackOrder = ["Closing newer", "Listing newer", "Closing older", "Listing older", "Undated A", "Undated B", "Undated Z"];
for (const input of [fallbackRows, [...fallbackRows].reverse()]) {
  assert.deepEqual(
    [...input].sort(compareNewestFirst).map((row) => row.issuer_name),
    fallbackOrder,
    "missing or invalid opening dates must fall back to closing, listing, then name",
  );
}
assert.ok(
  compareNewestFirst(
    { issuer_name: "Earlier listing", open_date: { value: "2026-01-01" }, listing_date: { value: "2026-01-10" } },
    { issuer_name: "Later listing", open_date: { value: "2026-01-01" }, listing_date: { value: "2026-01-20" } },
  ) > 0,
  "equal opening dates and missing closing dates must fall back to listing dates",
);
for (const a of [...rows, ...fallbackRows, ...mixedDateRows]) {
  for (const b of [...rows, ...fallbackRows, ...mixedDateRows]) {
    const forward = compareNewestFirst(a, b);
    const reverse = compareNewestFirst(b, a);
    assert.ok(Number.isFinite(forward), "comparator must return a finite result for missing dates");
    assert.equal(Math.sign(forward) + Math.sign(reverse), 0, "comparison must be antisymmetric");
  }
}

const payload = JSON.parse(fs.readFileSync(new URL("../data/ipos.json", import.meta.url), "utf8"));
const published = payload.records;
const independentlySorted = [...payload.records].sort(compareNewestFirst);
assert.deepEqual(
  published.map((row) => row.id),
  independentlySorted.map((row) => row.id),
  "published dataset must already be newest-first"
);

function firstAvailableDate(row) {
  for (const field of ["open_date", "close_date", "listing_date"]) {
    const value = row[field]?.value;
    if (value && !Number.isNaN(Date.parse(`${value}T00:00:00Z`))) return value;
  }
  return "";
}

for (let index = 1; index < published.length; index += 1) {
  const previous = firstAvailableDate(published[index - 1]);
  const current = firstAvailableDate(published[index]);
  assert.ok(previous >= current, `best-available date order failed at index ${index}: ${previous} < ${current}`);
}

const publishedDates = published
  .map(firstAvailableDate)
  .filter(Boolean)
  .sort();

assert.ok(publishedDates.length > 0, "published dataset must contain at least one valid date");
assert.equal(
  firstAvailableDate(published[0]),
  publishedDates.at(-1),
  "first published row must have the newest best-available date"
);

const lastDatedRow = [...published].reverse().find((row) => firstAvailableDate(row));
assert.equal(
  firstAvailableDate(lastDatedRow),
  publishedDates[0],
  "last dated published row must have the oldest best-available date"
);

const ensIndex = published.findIndex((row) => row.id === "ens-enterprises-limited");
const january2026Index = published.findIndex((row) => row.open_date?.value?.startsWith("2026-01"));
assert.ok(ensIndex >= 0 && january2026Index >= 0, "published regression issuers must exist");
assert.ok(ensIndex < january2026Index, "ENS's August 2026 listing must appear before January 2026 openings");

console.log("Homepage newest-first ordering tests passed.");
