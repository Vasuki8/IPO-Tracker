(function attachIpoOrder(root) {
  function fieldValue(field) {
    return field && field.value !== null && field.value !== undefined ? field.value : null;
  }

  function dateKey(field) {
    const value = fieldValue(field);
    if (!value) return Number.NEGATIVE_INFINITY;
    const parsed = Date.parse(String(value) + "T00:00:00Z");
    return Number.isNaN(parsed) || new Date(parsed).toISOString().slice(0, 10) !== String(value)
      ? Number.NEGATIVE_INFINITY
      : parsed;
  }

  function compareNewestFirst(a, b) {
    const fields = ["open_date", "close_date", "listing_date"];
    const aDates = fields.map((field) => dateKey(a?.[field]));
    const bDates = fields.map((field) => dateKey(b?.[field]));
    const aPrimary = aDates.find((date) => Number.isFinite(date)) ?? Number.NEGATIVE_INFINITY;
    const bPrimary = bDates.find((date) => Number.isFinite(date)) ?? Number.NEGATIVE_INFINITY;
    if (aPrimary !== bPrimary) return aPrimary > bPrimary ? -1 : 1;

    for (let index = 0; index < fields.length; index += 1) {
      const aDate = aDates[index];
      const bDate = bDates[index];
      if (aDate !== bDate) return aDate > bDate ? -1 : 1;
    }

    return String(a?.issuer_name || "").localeCompare(
      String(b?.issuer_name || ""),
      "en",
      { sensitivity: "base" }
    );
  }

  root.IPOOrder = Object.freeze({ compareNewestFirst });
})(typeof window !== "undefined" ? window : globalThis);
