import assert from "node:assert/strict";
import { retainedFieldStatus } from "./publish-field-status.mjs";

assert.equal(retainedFieldStatus({ value: 1 }), "verified");
assert.equal(retainedFieldStatus({ value: 1, status: "verified" }), "verified");
assert.equal(retainedFieldStatus({ value: 1, status: "provisional" }), "provisional");
assert.equal(retainedFieldStatus({ value: 1, status: "conflict" }), "conflict");
assert.equal(retainedFieldStatus({ value: 1, status: "missing" }), "verified");
assert.equal(retainedFieldStatus({ value: 1, status: "unexpected" }), "verified");

console.log("Published retained-field status tests passed.");
