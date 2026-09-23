(function attachLotSize(root) {
  function fieldValue(field) {
    return field && field.value !== null && field.value !== undefined ? field.value : null;
  }

  function verifiedField(field) {
    return field?.status === "verified" && fieldValue(field) !== null ? field : null;
  }

  function lotSizeField(ipo) {
    const marketLot = verifiedField(ipo?.market_lot);
    if (marketLot) return marketLot;

    const minimumBid = verifiedField(ipo?.minimum_bid_quantity);
    if (minimumBid) return minimumBid;

    return null;
  }

  function lotSizeValue(ipo) {
    return fieldValue(lotSizeField(ipo));
  }

  root.IPOLotSize = { lotSizeField, lotSizeValue };
})(typeof window !== "undefined" ? window : globalThis);
