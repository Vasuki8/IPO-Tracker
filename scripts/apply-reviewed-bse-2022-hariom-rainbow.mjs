// Bounded one-issuer release with an explicitly reviewed existing-name alias.
// Review, receipt and manifest are approvals; network collection alone is not.
import fs from 'node:fs';
import path from 'node:path';
import {isDeepStrictEqual as same} from 'node:util';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {sha256, strictDate} from './verify-bse-listing-candidates.mjs';
import {issuerKey} from './apply-reviewed-bse-2022-veranda-uma.mjs';

export const ROOT = fileURLToPath(new URL('../', import.meta.url));
export const REVIEW = 'data/discovery/bse-2022-hariom-rainbow-review-2026-09-27.json';
export const RECEIPT = 'data/evidence/bse-2022-hariom-rainbow-source-receipt-2026-09-27.json';
export const MANIFEST = 'data/verified-bse-listings/2026-09-27-hariom-rainbow.json';
export const ID = 'hariom-pipe-industries-limited';
export const ALIAS_ID = 'rainbow-childrens-medicare-limited';
export const FIELDS = ['price_band', 'issue_price', 'issue_size_inr', 'market_lot',
  'minimum_bid_quantity', 'open_date', 'close_date', 'listing_date'];
const SOURCE_KEYS = ['hariom_prospectus', 'hariom_track', 'rainbow_prospectus'];
const TARGET = 'data/recovery/2022/nse-issue-information.json';
const req = (ok, message) => {if (!ok) throw new Error(message);};
const timestamp = v => typeof v === 'string' && /^\d{4}-\d{2}-\d{2}T[\d:.]+Z$/.test(v) && Number.isFinite(Date.parse(v));
const integer = v => Number.isSafeInteger(v) && v > 0;
const hash = v => typeof v === 'string' && /^[a-f0-9]{64}$/.test(v);
const equalKeys = (a, b) => same([...a].sort(), [...b].sort());
const punctuationKey = v => issuerKey(v).replace(/[\s’']/g, '');
function officialUrl(value) {
  const u = new URL(value);
  req(u.protocol === 'https:' && !u.username && !u.password && !u.port &&
    ['www.sebi.gov.in', 'www.bseindia.com'].includes(u.hostname), 'unsafe_source_url');
  return value;
}

export function context(root = ROOT) {
  const read = name => fs.readFileSync(path.join(root, name));
  const reviewBytes = read(REVIEW), receiptBytes = read(RECEIPT);
  const ctx = {reviewBytes, receiptBytes, review: JSON.parse(reviewBytes),
    receipt: JSON.parse(receiptBytes), manifest: JSON.parse(read(MANIFEST))};
  validateContext(ctx);
  return ctx;
}
export function validateContext(ctx) {
  const {review: r, receipt: c, manifest: m, reviewBytes, receiptBytes} = ctx;
  // Prevent stale parsed objects/maps or a mutated caller from bypassing byte binding.
  req(same(JSON.parse(Buffer.from(reviewBytes)), r) && same(JSON.parse(Buffer.from(receiptBytes)), c), 'parsed_evidence_changed');
  req(m.schema_version === '1.0.0' && m.status === 'approved_hariom_import_and_rainbow_alias' &&
    m.target_year === 2022 && m.review_path === REVIEW && m.receipt_path === RECEIPT &&
    m.review_sha256 === sha256(reviewBytes) && m.receipt_sha256 === sha256(receiptBytes) &&
    c.review_sha256 === m.review_sha256 && c.review_path === REVIEW, 'unbound_review_or_receipt');
  req(same(m.import_ids, [ID]) && same(m.existing_alias_ids, [ALIAS_ID]) &&
    m.minimum_application_amount === 'out_of_scope', 'invalid_manifest_scope');
  req(r.schema_version === '1.0.0' && r.status === 'reviewed_hariom_and_rainbow_alias' &&
    r.source_year === 2022 && r.auto_import_allowed === false, 'invalid_review_scope');
  req(c.schema_version === '1.0.0' && c.status === 'reviewed_original_documents' &&
    integer(c.artifact_id) && hash(c.artifact_sha256) && c.artifact_id === m.source_artifact_id &&
    c.artifact_sha256 === m.source_artifact_sha256 && /^\d+$/.test(c.workflow_run_id), 'invalid_artifact_binding');
  req(Array.isArray(r.sources) && Array.isArray(c.documents) &&
    equalKeys(r.sources.map(s => s.key), SOURCE_KEYS) &&
    equalKeys(c.documents.map(s => s.key), SOURCE_KEYS), 'invalid_source_membership');
  req(timestamp(c.collection_completed_at), 'invalid_collection_clock');
  for (const s of r.sources) {
    const d = c.documents.find(x => x.key === s.key);
    req(d.source_url === s.url && d.final_url === s.url && d.http_status === 200 &&
      integer(d.response_bytes) && hash(d.response_sha256), 'source_receipt_mismatch');
    officialUrl(s.url);
    req(s.document_identity && s.document_type && strictDate(s.document_date) === s.document_date &&
      s.publication_date === null && timestamp(d.collected_at) &&
      s.document_date <= d.collected_at.slice(0, 10) && d.collected_at <= c.collection_completed_at, 'invalid_source_dates');
  }
  req(integer(c.total_response_bytes) && c.documents.reduce((n,d) => n + d.response_bytes, 0) === c.total_response_bytes,
    'receipt_byte_mismatch');
  const a = r.import;
  req(a.stable_id === ID && a.issuer_name === 'Hariom Pipe Industries Limited' && a.discovery_bse_scrip_code === '543517' &&
    a.issue_type === 'IPO' && a.identity_source === 'hariom_prospectus' && a.identity_pdf_page === 2 &&
    a.board === null && equalKeys(Object.keys(a.fields), FIELDS), 'invalid_import_identity');
  for (const [name, f] of Object.entries(a.fields)) {
    req(['hariom_prospectus', 'hariom_track'].includes(f.source_key) && integer(f.pdf_page) &&
      typeof f.source_value === 'string' && f.source_value.length > 0 && f.evidence_locator &&
      f.status === (name === 'issue_size_inr' ? 'conflict' : 'verified'), 'invalid_field_evidence:' + name);
    if (name.endsWith('_date')) req(strictDate(f.value) === f.value && f.unit === 'date', 'invalid_field_date');
    else if (name === 'price_band') req(integer(f.value?.min) && integer(f.value?.max) &&
      f.value.min <= f.value.max && f.unit === 'INR/share', 'invalid_price_band');
    else req(integer(f.value) && f.unit === (name === 'issue_price' ? 'INR/share' :
      name === 'issue_size_inr' ? 'INR lakh' : 'shares'), 'invalid_field_unit_or_value');
  }
  const f = a.fields;
  req(f.open_date.value <= f.close_date.value && f.close_date.value <= f.listing_date.value &&
    f.listing_date.value.startsWith('2022-') && f.issue_price.value >= f.price_band.value.min &&
    f.issue_price.value <= f.price_band.value.max, 'inconsistent_issue_dates_or_price');
  req(a.conflicts?.length === 1 && a.conflicts[0].field === 'issue_size_inr' &&
    a.conflicts[0].status === 'unresolved' && a.conflicts[0].preferred_candidate_source === 'hariom_prospectus', 'conflict_must_be_retained');
  const conflict = a.conflicts[0], b = conflict.competing;
  // Unit normalization only. No price-times-share-count or guessed unit repair.
  req(f.issue_size_inr.source_key === 'hariom_prospectus' && b.source_key === 'hariom_track' &&
    b.unit === 'INR million' && b.value === Math.round(Number(b.source_value) * 1e6) &&
    f.issue_size_inr.value === Math.round(Number(f.issue_size_inr.source_value) * 1e5) &&
    integer(b.value) && b.value !== f.issue_size_inr.value && integer(b.pdf_page) && b.evidence_locator &&
    typeof conflict.reason === 'string' && conflict.reason.length > 30, 'invalid_or_erased_size_conflict');
  const alias = r.existing_alias;
  req(alias.stable_id === ALIAS_ID && alias.discovery_bse_scrip_code === '543524' &&
    alias.discovery_issuer_name === "Rainbow Children's Medicare Limited" &&
    alias.recovery_issuer_name === 'Rainbow Childrens Medicare Limited' && alias.nse_symbol === 'RAINBOW' &&
    alias.source_key === 'rainbow_prospectus' && alias.decision === 'existing_recovery_alias_no_import' &&
    same(alias.corroboration, {issue_price: 542, minimum_bid_quantity: 27}), 'invalid_alias_approval');
}
function source(ctx, fact) {
  const s = ctx.review.sources.find(x => x.key === fact.source_key);
  const d = ctx.receipt.documents.find(x => x.key === fact.source_key);
  return {url:s.url, document_type:s.document_type, document_identity:s.document_identity,
    document_date:s.document_date, publication_date:s.publication_date, page:fact.pdf_page,
    evidence_locator:fact.evidence_locator, collected_at:d.collected_at, document_sha256:d.response_sha256};
}
export function expected(ctx) {
  validateContext(ctx);
  const a = ctx.review.import;
  const out = {id:ID, issuer_name:a.issuer_name, board:null, sector:null, status:'listed',
    nse_symbol:null, nse_series:null, nse_source:null, bse_symbol:null, bse_scrip_code:null, isin:null, bse_source:null,
    terms:{price_band:null, market_lot:null, minimum_bid_quantity:null, open_date:null, close_date:null},
    board_evidence:[], status_evidence:[source(ctx,a.fields.listing_date)]};
  for (const [name, f] of Object.entries(a.fields)) out[name] = {
    value:f.value, source_value:f.source_value, unit:f.unit, status:f.status, page:f.pdf_page,
    source:source(ctx,f), corrections:[]};
  const conflict = a.conflicts[0], b = conflict.competing;
  out.issue_size_inr.additional_sources = [source(ctx,b)];
  out.issue_size_inr.corrections = [{kind:'unresolved_source_conflict', status:'unresolved',
    note:conflict.reason, candidate:{value:out.issue_size_inr.value, source_value:out.issue_size_inr.source_value,
      unit:out.issue_size_inr.unit, source_key:a.fields.issue_size_inr.source_key, pdf_page:out.issue_size_inr.page},
    competing:{value:b.value, source_value:b.source_value, unit:b.unit, source_key:b.source_key, pdf_page:b.pdf_page}}];
  out.documents = ctx.review.sources.filter(s => s.key !== 'rainbow_prospectus').map(s => {
    const d = ctx.receipt.documents.find(x => x.key === s.key);
    return {type:s.document_type, identity:s.document_identity, url:s.url,
      publication_date:s.publication_date, document_date:s.document_date,
      collected_at:d.collected_at, document_sha256:d.response_sha256};
  });
  out.first_observed_at = out.last_collected_at = out.documents.map(d => d.collected_at).sort().at(-1);
  out.bse_2022_hariom_import = {manifest:MANIFEST, review:REVIEW, receipt:RECEIPT,
    review_sha256:ctx.manifest.review_sha256, receipt_sha256:ctx.manifest.receipt_sha256,
    artifact_id:ctx.receipt.artifact_id, artifact_sha256:ctx.receipt.artifact_sha256,
    discovery_bse_scrip_code:a.discovery_bse_scrip_code};
  return out;
}
export function loadRecovery(root = ROOT) {
  const dir = path.join(root,'data/recovery');
  return Object.fromEntries(fs.readdirSync(dir).filter(y => /^20\d{2}$/.test(y))
    .map(y => [y,path.join(dir,y,'nse-issue-information.json')]).filter(([,p]) => fs.existsSync(p))
    .map(([y,p]) => [y,JSON.parse(fs.readFileSync(p))]));
}
export function verifyAlias(all, ctx) {
  const a = ctx.review.existing_alias;
  const hits = all.filter(({record:r}) => r.id === ALIAS_ID || punctuationKey(r.issuer_name) === punctuationKey(a.recovery_issuer_name) ||
    r.nse_symbol === a.nse_symbol || String(r.bse_scrip_code || '') === a.discovery_bse_scrip_code);
  req(hits.length === 1 && hits[0].year === '2022', 'alias_collision_or_missing');
  const r = hits[0].record;
  req(r.id === ALIAS_ID && r.issuer_name === a.recovery_issuer_name && r.nse_symbol === a.nse_symbol && r.status === 'listed', 'alias_identity_changed');
  for (const [k,v] of Object.entries(a.corroboration)) req(r[k]?.value === v && r[k]?.status === 'verified' &&
    r[k]?.source?.url?.startsWith('https://www.nseindia.com/'), 'alias_evidence_changed');
  return r;
}
export function apply(recovery, ctx, now) {
  const next = expected(ctx);
  req(timestamp(now) && now >= ctx.receipt.collection_completed_at &&
    timestamp(recovery['2022']?.generated_at) && now >= recovery['2022'].generated_at, 'invalid_generation_clock');
  const all = Object.entries(recovery).flatMap(([year,m]) => m.records.map(record => ({year,record})));
  req(new Set(all.map(x => x.record.id)).size === all.length, 'duplicate_existing_id');
  verifyAlias(all, ctx);
  const hits = all.filter(({record:r}) => r.id === ID || issuerKey(r.issuer_name) === issuerKey(next.issuer_name) ||
    String(r.bse_scrip_code || '') === '543517' || r.nse_symbol === 'HARIOMPIPE' ||
    r.documents?.some(d => d.url === next.documents[0].url));
  if (hits.length) {
    req(hits.length === 1 && hits[0].year === '2022' && hits[0].record.id === ID, 'identity_collision');
    const old = hits[0].record;
    // Every initially published field is still reviewed; never erase newer enrichment.
    for (const k of Object.keys(next)) req(same(old[k],next[k]), 'changed_reviewed_record:' + k);
    return {recovery:structuredClone(recovery), stats:{added:0, already_present:1, existing_aliases:1, conflicts:1}};
  }
  const out = structuredClone(recovery);
  out['2022'].records.push(next);
  out['2022'].generated_at = now;
  return {recovery:out, stats:{added:1, already_present:0, existing_aliases:1, conflicts:1}};
}
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  try {
    const args = process.argv.slice(2);
    req(args.length === 1 && ['--check','--apply'].includes(args[0]), 'use_--check_or_--apply');
    const result = apply(loadRecovery(), context(), new Date().toISOString());
    if (args[0] === '--apply' && result.stats.added) {
      const target = path.join(ROOT,TARGET);
      fs.writeFileSync(target + '.tmp', JSON.stringify(result.recovery['2022'],null,2) + '\n');
      fs.renameSync(target + '.tmp',target);
    }
    console.log(JSON.stringify({hariom_rainbow_release:result.stats}));
  } catch (e) {console.error(e.message); process.exitCode = 1;}
}
