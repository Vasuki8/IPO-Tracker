(function attachIpoOrder(root) {
  function fieldValue(field) {
    return field && field.value !== null && field.value !== undefined ? field.value : null;
  }

  function dateKey(field) {
    const value = fieldValue(field);
    if (!value) return Number.NEGATIVE_INFINITY;
    const parsed = Date.parse(String(value) + "T00:00:00Z");
    return Number.isNaN(parsed) ? Number.NEGATIVE_INFINITY : parsed;
  }

  function compareNewestFirst(a, b) {
    const openDifference = dateKey(b?.open_date) - dateKey(a?.open_date);
    if (openDifference !== 0) return openDifference;

    const closeDifference = dateKey(b?.close_date) - dateKey(a?.close_date);
    if (closeDifference !== 0) return closeDifference;

    const listingDifference = dateKey(b?.listing_date) - dateKey(a?.listing_date);
    if (listingDifference !== 0) return listingDifference;

    return String(a?.issuer_name || "").localeCompare(
      String(b?.issuer_name || ""),
      "en",
      { sensitivity: "base" }
    );
  }

  root.IPOOrder = Object.freeze({ compareNewestFirst });
})(typeof window !== "undefined" ? window : globalThis);
