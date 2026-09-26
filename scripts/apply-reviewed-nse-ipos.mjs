import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { issuerKey as baseIssuerKey } from './verify-bse-listing-candidates.mjs';
import { parsePastIssuePrice } from './diagnose-nse-past-issues.mjs';
import { buildHistoricalRecord } from './sync-nse-historical.mjs';
import { parseMarketLotFromIpoDetail, parseMinimumBidFromIpoDetail, parsePriceBandFromIpoDetail } from './extract-nse-ipo-detail-fields.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const REVIEW_VERSION = '1.0.0';
export const PAST_URL = 'https://www.nseindia.com/api/public-past-issues';
export const FIELD_NAMES = ['listing_date', 'open_date', 'close_date', 'issue_price', 'price_band', 'market_lot', 'minimum_bid_quantity'];
export const hash = b => createHash('sha256').update(b).digest('hex');
export const norm = v => String(v ?? '').replace(/\s+/g, ' ').trim();
const title = v => norm(v).toLowerCase();
// Ignore only an apostrophe inside a word, not other spelling differences.
// Symbols, ISIN, board and all source identity checks still have to agree.
const issuerKey = v => baseIssuerKey(String(v ?? '').replace(/([A-Za-z])['’](?=[A-Za-z])/g, '$1'));
const unquote = v => norm(v).replace(/^"|"$/g, '');
const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const requireThat = (condition, reason) => { if (!condition) throw new Error(reason); };
const validHash = v => typeof v === 'string' && /^[a-f0-9]{64}$/.test(v);
const validStamp = v => typeof v === 'string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{3})?Z$/.test(v) && Number.isFinite(Date.parse(v)) && new Date(v).toISOString() === (v.includes('.') ? v : v.replace('Z', '.000Z'));
const validDate = v => typeof v === 'string' && /^\d{4}-\d\d-\d\d$/.test(v) && Number.isFinite(Date.parse(v)) && new Date(v).toISOString().slice(0, 10) === v;
function nseDate(raw) {
  const m = norm(raw).match(/^(\d{1,2})-([A-Za-z]+)-(\d{4})$/);
  if (!m) return null;
  const months = new Map([
    ['jan','01'],['january','01'],['feb','02'],['february','02'],['mar','03'],['march','03'],
    ['apr','04'],['april','04'],['may','05'],['jun','06'],['june','06'],['jul','07'],['july','07'],
    ['aug','08'],['august','08'],['sep','09'],['sept','09'],['september','09'],['oct','10'],['october','10'],
    ['nov','11'],['november','11'],['dec','12'],['december','12']
  ]);
  const month = months.get(m[2].toLowerCase());
  if (!month) return null;
  const iso = m[3] + '-' + month + '-' + String(Number(m[1])).padStart(2, '0');
  return validDate(iso) && Number(m[1]) === Number(iso.slice(8)) ? iso : null;
}
export const detailUrl = c => 'https://www.nseindia.com/api/ipo-detail?symbol=' + encodeURIComponent(c.nse_symbol) + '&series=' + (c.board === 'SME' ? 'SME' : 'EQ');
const TITLES = new Set(['symbol', 'issue size', 'issue period', 'issue type', 'price range', 'price band', 'market lot', 'lot size', 'bid lot', 'minimum order quantity', 'revised/extended issue period', 'revised price range']);

// Literal selected JSON fields, not a reconstructed full response. Original
// response bytes/hash remain in the recorded source artifact. Selection keeps
// every occurrence of each used title, so conflicting duplicates are not hidden.
export function projectDetail(payload) {
  const m = payload?.metaInfo || {};
  return { companyName: payload?.companyName ?? null, metaInfo: Object.fromEntries(
    ['companyName', 'symbol', 'isin', 'listingDate', 'segment', 'isDebtSec', 'isETFSec', 'isMunicipalBond', 'isHybridSymbol'].map(k => [k, m[k] ?? null])),
  issueInfo: { symbol: payload?.issueInfo?.symbol ?? null,
    dataList: (payload?.issueInfo?.dataList || []).filter(i => TITLES.has(title(i?.title))).map(i => ({ title: i.title, value: i.value })) } };
}
function sourceCheck(s, expectedUrl, projection) {
  requireThat(s?.url === expectedUrl && s.final_url === expectedUrl && s.http_status === 200 &&
    validStamp(s.collected_at) && validHash(s.response_sha256) && validHash(s.projection_sha256) &&
    hash(JSON.stringify(projection)) === s.projection_sha256 && s.publication_date === null, 'invalid_source_or_projection');
}
function identityEvidence(source, pointer) {
  return { url: source.url, document_type: source.document_type, document_identity: source.document_identity,
    document_sha256: source.response_sha256, publication_date: source.publication_date ?? null,
    collected_at: source.collected_at, page: source.page ?? null, evidence_locator: pointer };
}
function identitySourceCheck(source) {
  requireThat(source && source.http_status === 200 && source.final_url === source.url &&
    /^https:\/\/(?:www\.)?(?:sebi\.gov\.in|nseindia\.com|nsearchives\.nseindia\.com)\//i.test(source.url) &&
    validStamp(source.collected_at) && validHash(source.response_sha256) && validHash(source.projection_sha256) &&
    source.projection && typeof source.projection === 'object' && hash(JSON.stringify(source.projection)) === source.projection_sha256 &&
    typeof source.document_type === 'string' && source.document_type.length > 3 &&
    typeof source.document_identity === 'string' && source.document_identity.length > 3 &&
    typeof source.artifact_file === 'string' && source.artifact_file.length > 3 &&
    (source.publication_date === null || validDate(source.publication_date)) &&
    (source.page == null || (Number.isInteger(source.page) && source.page >= 1)), 'invalid_identity_source');
}
function validateIdentity(entry, candidate, projection, pastRow) {
  const meta = projection.metaInfo || {}, fallback = entry.identity_fallback;
  if (!fallback) {
    requireThat(meta.symbol === candidate.nse_symbol &&
      [projection.companyName, meta.companyName, pastRow.company, pastRow.companyName].filter(v => v != null)
        .every(n => issuerKey(n) === issuerKey(candidate.issuer_name)) &&
      typeof projection.companyName === 'string' && projection.companyName.length > 3, 'issuer_identity_mismatch');
    requireThat(/^INE[A-Z0-9]{8}\d$/.test(meta.isin) && meta.segment === (candidate.board === 'SME' ? 'SME' : 'EQUITY') &&
      norm(pastRow.securityType) === (candidate.board === 'SME' ? 'SME' : 'EQ') &&
      ['isDebtSec','isETFSec','isMunicipalBond','isHybridSymbol'].every(k => meta[k] === false), 'non_equity_or_board_mismatch');
    requireThat(validDate(meta.listingDate) && meta.listingDate === candidate.listing_date &&
      meta.listingDate === nseDate(pastRow.listingDate), 'listing_date_mismatch');
    return { issuer_name: projection.companyName, nse_symbol: meta.symbol, isin: meta.isin, listing_date: meta.listingDate,
      listing_source: evidence(entry.detail_source, candidate.nse_symbol, true, '/metaInfo/listingDate'),
      board_source: evidence(entry.detail_source, candidate.nse_symbol, true, '/metaInfo/segment'), identity_sources: [] };
  }

  requireThat(fallback.schema_version === '1.0.0' && fallback.lookup_symbol === candidate.nse_symbol &&
    norm(projection.companyName).toUpperCase() === candidate.nse_symbol &&
    ['companyName','symbol','isin','listingDate','segment','isDebtSec','isETFSec','isMunicipalBond','isHybridSymbol'].every(k => meta[k] == null),
    'identity_fallback_requires_missing_endpoint_metadata');
  requireThat(issuerKey(fallback.company_name) === issuerKey(candidate.issuer_name) &&
    /^[A-Z0-9-]+$/.test(fallback.nse_symbol) && /^INE[A-Z0-9]{8}\d$/.test(fallback.isin) &&
    fallback.board === candidate.board && fallback.listing_date === candidate.listing_date &&
    fallback.security_class === 'Equity' && fallback.completed_initial_public_offer === true &&
    norm(pastRow.securityType) === (candidate.board === 'SME' ? 'SME' : 'EQ') &&
    nseDate(pastRow.listingDate) === fallback.listing_date, 'invalid_identity_fallback');
  requireThat(Array.isArray(fallback.sources) && fallback.sources.length >= 2 && fallback.sources.length <= 4, 'identity_fallback_source_count');
  fallback.sources.forEach(identitySourceCheck);
  const identitySource = fallback.sources.find(source => {
    const p = source.projection || {};
    return issuerKey(p.company_name) === issuerKey(fallback.company_name) && p.nse_symbol === fallback.nse_symbol &&
      p.isin === fallback.isin && p.board === fallback.board;
  });
  const listingSource = fallback.sources.find(source => {
    const p = source.projection || {};
    return issuerKey(p.company_name) === issuerKey(fallback.company_name) && p.listing_date === fallback.listing_date &&
      p.completed_initial_public_offer === true;
  });
  requireThat(identitySource && listingSource, 'identity_fallback_missing_positive_fields');
  return { issuer_name: fallback.company_name, nse_symbol: fallback.nse_symbol, isin: fallback.isin,
    listing_date: fallback.listing_date,
    listing_source: identityEvidence(listingSource, listingSource.evidence_locator || '/projection/listing_date'),
    board_source: identityEvidence(identitySource, identitySource.evidence_locator || '/projection/board'),
    identity_sources: fallback.sources };
}
function oneItem(payload, name, required = true) {
  const items = payload.issueInfo.dataList.filter(i => title(i.title) === name);
  requireThat(items.length <= 1 && (!required || items.length === 1), 'missing_or_duplicate_' + name);
  return items[0] || null;
}
function reviewedPeriod(p) {
  const ordinary = oneItem(p, 'issue period', false), revised = oneItem(p, 'revised/extended issue period', false);
  requireThat(Boolean(ordinary) !== Boolean(revised), 'missing_or_competing_offer_period');
  const item = revised || ordinary;
  const pattern = revised
    ? /^(\d{1,2}-[A-Za-z]+-\d{4})\s+to\s+(\d{1,2}-[A-Za-z]+-\d{4}) \(The Issue is further extended from start date (\d{2})\/(\d{2})\/(\d{4}) to end date (\d{2})\/(\d{2})\/(\d{4})\)$/i
    : /^(\d{1,2}-[A-Za-z]+-\d{4})\s+to\s+(\d{1,2}-[A-Za-z]+-\d{4})(?: \(The Issue is further extended to (\d{1,2}-[A-Za-z]+-\d{4})\))?$/i;
  const match = unquote(item.value).match(pattern);
  requireThat(match, 'unrecognized_offer_period');
  const open = nseDate(match[1]), close = nseDate(match[2]);
  // An explicit extended endpoint must repeat the stated closing date exactly.
  if (!revised && match[3]) requireThat(close === nseDate(match[3]) && close !== null, 'inconsistent_extended_offer_period');
  if (revised) requireThat(open === match[5] + '-' + match[4] + '-' + match[3] &&
    close === match[8] + '-' + match[7] + '-' + match[6], 'inconsistent_revised_offer_period');
  return { open, close, rawOpen: match[1], rawClose: match[2], title: norm(item.title) };
}
function reviewedBand(p) {
  const revised = oneItem(p, 'revised price range', false);
  if (!revised) return parsePriceBandFromIpoDetail(p);
  requireThat(!p.issueInfo.dataList.some(i => ['price range', 'price band'].includes(title(i.title))), 'competing_price_bands');
  // Normalize the title only for the existing parser; retain the literal title
  // and value in the manifest and the published field's evidence locator.
  const input = { ...p, issueInfo: { ...p.issueInfo, dataList: p.issueInfo.dataList.map(i =>
    i === revised ? { ...i, title: 'Price Range' } : i) } };
  const result = parsePriceBandFromIpoDetail(input);
  return { ...result, source_title: norm(revised.title) };
}
function evidence(source, symbol, detail, pointer) {
  return { url: source.url, document_type: detail ? 'NSE Issue Information API' : 'NSE Public Past Issues',
    document_identity: (detail ? 'NSE Issue Information — ' : 'NSE Public Past Issues — ') + symbol,
    document_sha256: source.response_sha256, publication_date: null, collected_at: source.collected_at,
    page: null, evidence_locator: pointer };
}

export function validateEntry(entry, queue) {
  const c = queue.candidates.find(c => c.nse_symbol === entry?.candidate?.nse_symbol);
  requireThat(c && equal(c, entry.candidate) && entry.decision === 'verified_initial_equity_ipo', 'unapproved_candidate');
  requireThat(/^[A-Z0-9-]+$/.test(c.nse_symbol) && ['SME', 'Mainboard'].includes(c.board), 'invalid_candidate');
  const p = entry.detail, m = p?.metaInfo, r = entry.past_row;
  requireThat(p && equal(projectDetail(p), p), 'invalid_detail_projection');
  for (const t of TITLES) oneItem(p, t, false);
  sourceCheck(entry.detail_source, detailUrl(c), p); sourceCheck(entry.past_source, PAST_URL, r);
  requireThat(p.issueInfo.symbol === c.nse_symbol &&
    norm(oneItem(p, 'symbol').value) === c.nse_symbol && norm(r?.symbol) === c.nse_symbol, 'symbol_mismatch');
  requireThat([r.company, r.companyName].filter(v => v != null).every(n => issuerKey(n) === issuerKey(c.issuer_name)), 'past_issuer_identity_mismatch');
  const identity = validateIdentity(entry, c, p, r);
  const offer = unquote(oneItem(p, 'issue size').value);
  const initialPublicEquity = /^(?:Initial Public (?:Offer(?:ing)?|Issue)|Intial Public Offer(?:ing)?)\b/i.test(offer);
  requireThat(initialPublicEquity && /\bequity shares\b/i.test(offer) &&
    !/\b(?:follow[ -]?on|further public|rights issue|partly[ -]paid|debenture|non[ -]convertible|FPO)\b/i.test(offer), 'initial_equity_ipo_not_established');
  requireThat(identity.listing_date <= entry.detail_source.collected_at.slice(0, 10) &&
    identity.listing_date <= entry.past_source.collected_at.slice(0, 10), 'listing_date_future');
  const period = reviewedPeriod(p), { open, close } = period;
  requireThat(validDate(open) && validDate(close) && open <= close && close <= identity.listing_date &&
    open === nseDate(r.ipoStartDate) && close === nseDate(r.ipoEndDate), 'offer_period_mismatch');
  const price = parsePastIssuePrice(r.issuePrice);
  requireThat(price !== null && price > 0, 'missing_explicit_final_price');
  const facts = {};
  function fact(key, value, raw, source, pointer, isDetail = true) {
    facts[key] = { value, source_value: raw, status: 'verified', page: null,
      source: evidence(source, c.nse_symbol, isDetail, pointer), corrections: [] };
  }
  if (entry.identity_fallback) facts.listing_date = { value: identity.listing_date, source_value: identity.listing_date,
    status: 'verified', page: identity.listing_source.page, source: identity.listing_source, corrections: [] };
  else fact('listing_date', identity.listing_date, identity.listing_date, entry.detail_source, '/metaInfo/listingDate');
  fact('open_date', open, period.rawOpen, entry.detail_source, '/issueInfo/dataList[' + period.title + ']');
  fact('close_date', close, period.rawClose, entry.detail_source, '/issueInfo/dataList[' + period.title + ']');
  fact('issue_price', price, norm(r.issuePrice), entry.past_source, '/' + c.row_index + '/issuePrice', false);
  const band = reviewedBand(p), lot = parseMarketLotFromIpoDetail(p), min = parseMinimumBidFromIpoDetail(p);
  for (const [key, result, present] of [
    ['price_band', band, p.issueInfo.dataList.some(i => ['price range', 'price band', 'revised price range'].includes(title(i.title)))],
    ['market_lot', lot, p.issueInfo.dataList.some(i => ['market lot', 'lot size'].includes(title(i.title)))],
    ['minimum_bid_quantity', min, p.issueInfo.dataList.some(i => title(i.title) === 'minimum order quantity')]
  ]) {
    if (!present) continue; // Bid Lot alone is never reclassified as market lot or minimum bid.
    if (key === 'price_band' && result.value == null) {
      // A stated fixed price is not a two-ended price band. Corroborate the
      // past feed's final price, but leave price_band absent rather than infer.
      const fixed = unquote(oneItem(p, 'price range').value).match(/^Rs\.?\s*([0-9]+(?:\.[0-9]{1,2})?)\s+per equity share$/i);
      requireThat(/^Fixed Price$/i.test(unquote(oneItem(p, 'issue type').value)) && fixed && Number(fixed[1]) === price, 'unresolved_price_band');
      continue;
    }
    requireThat(result.value != null && !result.reason, 'unresolved_' + key);
    fact(key, result.value, result.source_value, entry.detail_source, '/issueInfo/dataList[' + result.source_title + ']');
  }
  if (facts.price_band) requireThat(price >= facts.price_band.value.min && price <= facts.price_band.value.max, 'price_outside_band');
  return { candidate: c, issuer_name: identity.issuer_name, nse_symbol: identity.nse_symbol, isin: identity.isin,
    facts, offer, board_source: identity.board_source, identity_sources: identity.identity_sources };
}
export function validateReviewedBatch(manifest, queue) {
  requireThat(manifest?.schema_version === '1.0.0' && manifest.verifier_version === REVIEW_VERSION &&
    manifest.projection_method === 'literal_selected_json_fields_all_used_titles_retained' &&
    manifest.source_run_id && /^\d+$/.test(manifest.source_run_id) && Number.isSafeInteger(manifest.source_artifact_id) &&
    validHash(manifest.source_artifact_sha256) && validHash(manifest.queue_sha256) &&
    hash(JSON.stringify(queue)) === manifest.queue_sha256 && Array.isArray(manifest.entries) &&
    manifest.entries.length > 0 && manifest.entries.length <= 15 && queue.auto_import_allowed === false &&
    queue.candidates.length <= 15 && queue.candidates.length > 0, 'invalid_reviewed_batch');
  requireThat(new Set(queue.candidates.map(c => c.nse_symbol)).size === queue.candidates.length, 'duplicate_queue_symbol');
  const checked = manifest.entries.map(e => validateEntry(e, queue));
  for (const key of ['isin', 'issuer_name']) requireThat(new Set(checked.map(c => key === 'issuer_name' ? issuerKey(c[key]) : c[key])).size === checked.length, 'duplicate_reviewed_identity');
  requireThat(new Set(checked.map(c => c.candidate.nse_symbol)).size === checked.length, 'duplicate_reviewed_symbol');
  return checked;
}
export function reviewedRecord(entry, checked, manifest, manifestPath) {
  const now = [entry.detail_source.collected_at, entry.past_source.collected_at].sort().at(-1);
  const r = buildHistoricalRecord({ ...entry.past_row, company: checked.issuer_name, symbol: checked.nse_symbol }, now);
  r.isin = checked.isin;
  r.nse_symbol = checked.nse_symbol;
  r.nse_source = { ...checked.facts.listing_date.source };
  r.board_evidence = [{ ...checked.board_source }]; r.status_evidence = [{ ...r.nse_source }];
  const identityDocs = checked.identity_sources.map(source => ({ type: source.document_type, identity: source.document_identity,
    url: source.url, publication_date: source.publication_date ?? null, collected_at: source.collected_at,
    document_sha256: source.response_sha256, page: source.page ?? null }));
  r.documents = [...identityDocs, r.nse_source, checked.facts.issue_price.source].map(e => ({ type: e.type || e.document_type,
    identity: e.identity || e.document_identity, url: e.url, publication_date: e.publication_date ?? null,
    collected_at: e.collected_at, document_sha256: e.document_sha256, ...(e.page == null ? {} : { page:e.page }) }))
    .filter((doc, i, all) => all.findIndex(other => other.url === doc.url && other.type === doc.type) === i);
  for (const [f, field] of Object.entries(checked.facts)) r[f] = structuredClone(field);
  r.nse_verified_ipo_batch = { manifest: manifestPath, verifier_version: REVIEW_VERSION,
    source_run_id: manifest.source_run_id, source_artifact_id: manifest.source_artifact_id,
    source_artifact_sha256: manifest.source_artifact_sha256,
    detail_response_sha256: entry.detail_source.response_sha256, decision: entry.decision,
    ...(entry.identity_fallback ? { identity_fallback_source_hashes: entry.identity_fallback.sources.map(source => source.response_sha256) } : {}) };
  return r;
}
function strings(v) { return typeof v === 'string' ? [v] : v && typeof v === 'object' ? Object.values(v).flatMap(strings) : []; }
function matches(r, record, aliases, cache, lookupSymbols = new Set()) {
  let identity = cache.get(r);
  if (!identity) {
    const values = strings(r), symbols = new Set([norm(r.nse_symbol).toUpperCase()]);
    for (const raw of values.filter(v => v.startsWith('https://'))) {
      try { const u = new URL(raw);
        if (['nseindia.com', 'www.nseindia.com'].includes(u.hostname) &&
            ['/api/ipo-detail', '/get-quotes/ipo'].includes(u.pathname)) symbols.add(norm(u.searchParams.get('symbol')).toUpperCase());
      } catch { /* Invalid legacy URLs are not identity evidence. */ }
    }
    identity = { symbols, isin: new Set(values.filter(v => /^IN[A-Z0-9]{10}$/i.test(v)).map(v => v.toUpperCase())) };
    cache.set(r, identity);
  }
  return r.id === record.id || aliases.has(issuerKey(r.issuer_name)) || identity.symbols.has(record.nse_symbol) ||
    [...lookupSymbols].some(symbol => identity.symbols.has(symbol)) || identity.isin.has(record.isin);
}
// Pure, whole-batch plan: callers write nothing until all manifests have passed.
export function applyReviewedBatch(recoveryByYear, published, manifest, queue, manifestPath) {
  const checked = validateReviewedBatch(manifest, queue), recovery = structuredClone(recoveryByYear);
  const stats = { added: 0, already_present: 0 }, changed = new Set(), cache = new WeakMap();
  for (let i = 0; i < checked.length; i++) {
    const c = checked[i], record = reviewedRecord(manifest.entries[i], c, manifest, manifestPath), year = record.listing_date.value.slice(0, 4);
    requireThat(Number(year) >= 2020 && Number(year) <= 2026, 'out_of_scope_year');
    const aliases = new Set([issuerKey(record.issuer_name), issuerKey(c.candidate.issuer_name)]);
    const lookupSymbols = new Set([record.nse_symbol, c.candidate.nse_symbol]);
    const rawHits = Object.entries(recovery).flatMap(([y, m]) => m.records.filter(r => matches(r, record, aliases, cache, lookupSymbols)).map(r => ({ y, r })));
    const publicHits = (published.records || []).filter(r => matches(r, record, aliases, cache, lookupSymbols));
    if (rawHits.length) {
      requireThat(rawHits.length === 1 && rawHits[0].y === year && rawHits[0].r.id === record.id &&
        rawHits[0].r.isin === record.isin && rawHits[0].r.nse_symbol === record.nse_symbol &&
        issuerKey(rawHits[0].r.issuer_name) === issuerKey(record.issuer_name) && rawHits[0].r.board === record.board && rawHits[0].r.status === 'listed' &&
        equal(rawHits[0].r.nse_verified_ipo_batch, record.nse_verified_ipo_batch) &&
        Object.entries(c.facts).every(([f, v]) => equal(rawHits[0].r[f]?.value, v.value) &&
          rawHits[0].r[f]?.status === 'verified' && rawHits[0].r[f]?.source_value === v.source_value && equal(rawHits[0].r[f]?.source, v.source)) &&
        publicHits.length <= 1 && publicHits.every(r => r.id === record.id), 'existing_identity_or_evidence_conflict:' + record.nse_symbol);
      stats.already_present++; continue;
    }
    requireThat(publicHits.length === 0, 'published_identity_without_approved_recovery:' + record.nse_symbol);
    requireThat(recovery[year] && Array.isArray(recovery[year].records), 'missing_recovery_year');
    recovery[year].records.push(record);
    recovery[year].generated_at = [recovery[year].generated_at, record.last_collected_at].sort().at(-1);
    changed.add(year); stats.added++;
  }
  for (const y of changed) recovery[y].records.sort((a, b) => a.issuer_name.localeCompare(b.issuer_name));
  return { recovery, stats, changed_years: [...changed] };
}
export function loadReviewed(root = ROOT) {
  const dir = path.join(root, 'data/verified-nse-ipos');
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter(f => /^\d{4}-\d\d-\d\d-batch\d+\.json$/.test(f)).sort().map(f => {
    const manifest_path = 'data/verified-nse-ipos/' + f, manifest = JSON.parse(fs.readFileSync(path.join(root, manifest_path)));
    requireThat(/^data\/discovery\/ipo-universe-review-\d{4}-\d\d-\d\d-batch\d+\.json$/.test(manifest.queue_path), 'unapproved_queue_path');
    return { manifest_path, manifest, queue: JSON.parse(fs.readFileSync(path.join(root, manifest.queue_path))) };
  });
}
export function loadRecovery(root = ROOT) {
  return Object.fromEntries(Array.from({ length: 7 }, (_, i) => String(2020 + i)).map(y => [y,
    JSON.parse(fs.readFileSync(path.join(root, 'data/recovery', y, 'nse-issue-information.json')))]));
}
function run() {
  requireThat(process.argv.slice(2).every(a => a === '--check'), 'only_--check_supported');
  const batches = loadReviewed(); requireThat(batches.length > 0, 'no_reviewed_nse_batches');
  for (const b of batches) validateReviewedBatch(b.manifest, b.queue);
  if (process.argv.includes('--check')) { console.log(JSON.stringify({ reviewed_nse_ipos: batches.reduce((n, b) => n + b.manifest.entries.length, 0) })); return; }
  let recovery = loadRecovery(); const published = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/ipos.json'))), changed = new Set();
  const stats = { added: 0, already_present: 0 };
  for (const b of batches) { const a = applyReviewedBatch(recovery, published, b.manifest, b.queue, b.manifest_path);
    recovery = a.recovery; for (const k of Object.keys(stats)) stats[k] += a.stats[k]; for (const y of a.changed_years) changed.add(y); }
  for (const y of changed) fs.writeFileSync(path.join(ROOT, 'data/recovery', y, 'nse-issue-information.json'), JSON.stringify(recovery[y], null, 2) + '\n');
  console.log(JSON.stringify({ reviewed_nse_import: stats }));
}
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) run();
