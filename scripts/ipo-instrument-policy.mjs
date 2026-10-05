// This adapter uses the same EQ/SME families as the historical NSE collector.
// An unknown series is unapproved, not evidence that an issuer is a debt issuer.
export const normalizeSeries = value => String(value ?? '').trim().toUpperCase();
export const isEquitySeries = value => ['EQ', 'SME'].includes(normalizeSeries(value));
const nonEquityFlags = ['isDebtSec', 'isETFSec', 'isMunicipalBond', 'isHybridSymbol'];
function flaggedInstrument(value) {
  return value !== undefined && value !== null &&
    ![false, 0, '', 'false', '0', 'no', 'n'].includes(typeof value === 'string' ? value.trim().toLowerCase() : value);
}
export function liveIssueIneligibility(issue) {
  if (!issue || typeof issue !== 'object' || !String(issue.companyName ?? '').trim() || !String(issue.symbol ?? '').trim()) return 'missing_live_identity';
  if (!isEquitySeries(issue.series)) return 'unsupported_live_series';
  if (nonEquityFlags.some(key => flaggedInstrument(issue[key]) || flaggedInstrument(issue.metaInfo?.[key]))) return 'non_equity_or_unresolved_instrument_flag';
  return null;
}
export function retainedRecordIneligibility(record) {
  // Do not filter by board: reviewed equity IPOs may legitimately lack a board
  // or NSE-series mapping. Preserve their independent official evidence.
  const series = normalizeSeries(record.nse_series);
  let sourceSeries = '';
  try {
    const url = new URL(record.nse_source?.url);
    if (['www.nseindia.com','nseindia.com'].includes(url.hostname)) sourceSeries = normalizeSeries(url.searchParams.get('series'));
  } catch { /* An absent series is not an invented classification. */ }
  if ([series,sourceSeries].some(value => value && !isEquitySeries(value))) return 'unsupported_retained_series';
  if (record.nse_source?.document_type === 'NSE IPO Live Feed' && !series) return 'missing_retained_live_series';
  if (nonEquityFlags.some(key => flaggedInstrument(record[key]) || flaggedInstrument(record.metaInfo?.[key]))) return 'non_equity_or_unresolved_instrument_flag';
  return null;
}
