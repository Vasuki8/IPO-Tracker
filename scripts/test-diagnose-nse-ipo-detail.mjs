import assert from "node:assert/strict";
import { collectBidLotFields } from "./diagnose-nse-ipo-detail.mjs";

const payload = {
  symbol: "TEST",
  issueInfo: {
    bidLot: 34,
    minimumOrderQuantity: 34,
    faceValue: 1
  },
  categories: [
    { name: "Retail", minimumBidQuantity: 34 },
    { name: "NII", minimumBidAmount: 200001 }
  ]
};

const fields = collectBidLotFields(payload);
const byPath = new Map(fields.map((item) => [item.path, item.value]));

assert.equal(byPath.get("issueInfo.bidLot"), 34);
assert.equal(byPath.get("issueInfo.minimumOrderQuantity"), 34);
assert.equal(byPath.get("categories.0.minimumBidQuantity"), 34);
assert.equal(byPath.get("categories.1.minimumBidAmount"), 200001);
assert.equal(byPath.has("issueInfo.faceValue"), false);

console.log("NSE ipo-detail diagnostic field discovery tests passed.");
