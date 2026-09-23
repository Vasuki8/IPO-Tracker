export function listingYearOf(item) {
  const record = item?.record ?? item;
  const value = String(record?.listing_date?.value || "");
  const year = Number(value.slice(0, 4));
  return Number.isInteger(year) && year >= 2000 && year <= 2100 ? year : null;
}

export function selectBalancedByListingYear(items, max) {
  if (!Array.isArray(items) || !Number.isInteger(max) || max <= 0) return [];

  const groups = new Map();
  for (const item of items) {
    const year = listingYearOf(item);
    if (year === null) continue;
    if (!groups.has(year)) groups.set(year, []);
    groups.get(year).push(item);
  }

  for (const group of groups.values()) {
    group.sort((a, b) => {
      const ar = a?.record ?? a;
      const br = b?.record ?? b;
      const dateOrder = String(br?.listing_date?.value || "").localeCompare(String(ar?.listing_date?.value || ""));
      return dateOrder || String(ar?.issuer_name || "").localeCompare(String(br?.issuer_name || ""));
    });
  }

  const years = [...groups.keys()].sort((a, b) => b - a);
  const selected = [];
  let index = 0;

  while (selected.length < max) {
    let added = false;
    for (const year of years) {
      const group = groups.get(year);
      if (index >= group.length) continue;
      selected.push(group[index]);
      added = true;
      if (selected.length >= max) break;
    }
    if (!added) break;
    index += 1;
  }

  return selected;
}
