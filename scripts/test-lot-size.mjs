import assert from "node:assert/strict";
import "../assets/lot-size.js";

const { lotSizeField, lotSizeValue } = globalThis.IPOLotSize;

const direct = {
  market_lot: { value: 120, status: "verified" },
  minimum_bid_quantity: { value: 60, status: "verified" }
};
assert.equal(lotSizeValue(direct), 120);
assert.equal(lotSizeField(direct), direct.market_lot);

const fallback = {
  market_lot: { value: null, status: "missing" },
  minimum_bid_quantity: { value: 41, status: "verified" }
};
assert.equal(lotSizeValue(fallback), 41);
assert.equal(lotSizeField(fallback), fallback.minimum_bid_quantity);

const provisionalMarketLot = {
  market_lot: { value: 999, status: "provisional" },
  minimum_bid_quantity: { value: 40, status: "verified" }
};
assert.equal(lotSizeValue(provisionalMarketLot), 40);
assert.equal(lotSizeField(provisionalMarketLot), provisionalMarketLot.minimum_bid_quantity);

const conflictWithoutFallback = {
  market_lot: { value: 120, status: "conflict" },
  minimum_bid_quantity: { value: null, status: "missing" }
};
assert.equal(lotSizeValue(conflictWithoutFallback), null);
assert.equal(lotSizeField(conflictWithoutFallback), null);

const provisionalFallback = {
  market_lot: { value: null, status: "missing" },
  minimum_bid_quantity: { value: 41, status: "provisional" }
};
assert.equal(lotSizeValue(provisionalFallback), null);
assert.equal(lotSizeField(provisionalFallback), null);

const missing = {
  market_lot: { value: null, status: "missing" },
  minimum_bid_quantity: { value: null, status: "missing" }
};
assert.equal(lotSizeValue(missing), null);
assert.equal(lotSizeField(missing), null);

console.log("Verified lot-size display fallback tests passed.");
