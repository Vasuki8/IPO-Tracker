from pathlib import Path
p=Path('scripts/extract-nse-ipo-detail-fields.mjs')
s=p.read_text()
old='''  const match = text.match(pattern);
  if (!match) return null;

  const min = Number(match[1].replace(/,/g, ""));'''
new=r'''  // Some official ranges repeat the share unit before the separator, e.g.
  // "Rs. 50/- per equity share to Rs. 53/- equity share". Keep this alternative
  // fully anchored and require an INR marker and share unit on both bounds.
  const repeatedUnitPattern = new RegExp(
    "^\\s*" + currency + "\\s*" + amount + "\\s*(?:\\/\\-)?\\s*" +
    "per\\s+(?:Equity\\s+)?Shares?\\s+to\\s+" + currency + "\\s*" + amount +
    "\\s*(?:\\/\\-)?\\s*(?:per\\s+)?(?:Equity\\s+)?Shares?\\s*$",
    "i"
  );
  const match = text.match(pattern) || text.match(repeatedUnitPattern);
  if (!match) return null;

  const min = Number(match[1].replace(/,/g, ""));'''
assert s.count(old)==1
s=s.replace(old,new)
old='''    const quantity = parseEquityShareQuantity(rawValue);
    if (quantity !== null) {
      values.push({ title, quantity, rawValue });
    }'''
new=r'''    // Only the minimum-bid parser accepts this explicit qualifier. Do not
    // reinterpret a prefixed minimum as a market lot or accept other qualifiers.
    const minimumQualified = /^Minimum\s+[0-9][0-9,]*\s+Equity\s+Shares(?:\s+and\s+in\s+multiples\s+thereof)?$/i.test(rawValue);
    const quantity = parseEquityShareQuantity(minimumQualified
      ? rawValue.replace(/^Minimum\s+/i, "")
      : rawValue);
    if (quantity !== null) {
      values.push({ title, quantity, rawValue });
    }'''
assert s.count(old)==1
p.write_text(s.replace(old,new))

p=Path('scripts/test-reviewed-nse-ipos.mjs')
s=p.read_text()
line="await import('./test-reviewed-nse-batch6.mjs');"
assert line not in s
p.write_text(s.rstrip()+"\n\n"+line+"\n")
