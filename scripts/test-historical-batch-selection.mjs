import assert from "node:assert/strict";
import { listingYearOf, selectBalancedByListingYear } from "./historical-batch-selection.mjs";

const item = (name, date) => ({ record: { issuer_name: name, listing_date: { value: date } } });
const items = [
  item("A25", "2025-12-20"),
  item("B25", "2025-11-20"),
  item("A24", "2024-12-20"),
  item("B24", "2024-11-20"),
  item("A23", "2023-12-20"),
  item("B23", "2023-11-20")
];

assert.equal(listingYearOf(items[0]), 2025);
assert.equal(listingYearOf({ record: { listing_date: { value: null } } }), null);

assert.deepEqual(
  selectBalancedByListingYear(items, 6).map(({ record }) => record.issuer_name),
  ["A25", "A24", "A23", "B25", "B24", "B23"]
);

assert.deepEqual(
  selectBalancedByListingYear(items, 4).map(({ record }) => record.issuer_name),
  ["A25", "A24", "A23", "B25"]
);

assert.deepEqual(selectBalancedByListingYear(items, 0), []);
console.log("Historical batch year-balancing tests passed.");
