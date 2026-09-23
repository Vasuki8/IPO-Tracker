(function attachLotSize(root) {
  function fieldValue(field) {
    return field && field.value !== null && field.value !== undefined ? field.value : null;
  }

  function lotSizeField(ipo) {
    const marketLot = ipo?.market_lot;
    if (fieldValue(marketLot) !== null) return marketLot;

    const minimumBid = ipo?.minimum_bid_quantity;
    if (fieldValue(minimumBid) !== null) return minimumBid;

    return null;
  }

  function lotSizeValue(ipo) {
    return fieldValue(lotSizeField(ipo));
  }

  root.IPOLotSize = { lotSizeField, lotSizeValue };
})(typeof window !== "undefined" ? window : globalThis);
