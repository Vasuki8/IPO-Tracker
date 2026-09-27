import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {isDeepStrictEqual as same} from 'node:util';
import {ROOT, ID, ALIAS_ID, FIELDS, context, loadRecovery, apply, expected} from './apply-reviewed-bse-2022-hariom-rainbow.mjs';
import {sha256} from './verify-bse-listing-candidates.mjs';
import {fetchPublishedSnapshot, LIVE_DATA_URL} from './verify-bse-publication.mjs';
const req = (ok,m) => {if (!ok) throw new Error(m);};
export const publicSource = s => ({url:s.url, document_type:s.document_type,
  document_identity:s.document_identity, publication_date:s.publication_date,
  page:s.page, collected_at:s.collected_at});
export function audit({ctx, recovery, data, checkedAt, baseline = null}) {
  req(data?.schema_version === '1.2.0' && Array.isArray(data.records) &&
    Number.isFinite(Date.parse(data.generated_at)) && Number.isFinite(Date.parse(checkedAt)) &&
    Date.parse(data.generated_at) <= Date.parse(checkedAt), 'invalid_live_dataset');
  req(new Set(data.records.map(r => r.id)).size === data.records.length, 'duplicate_live_id');
  req(apply(recovery,ctx,checkedAt).stats.added === 0, 'unpublished_recovery');
  const row = expected(ctx), hits = data.records.filter(r => r.id === ID || r.issuer_name === row.issuer_name);
  req(hits.length === 1, 'live_hariom_missing_or_duplicate');
  const live = hits[0];
  req(live.board === null && live.status === 'listed' && live.issuer_name === row.issuer_name &&
    live.first_observed_at === row.first_observed_at && live.last_collected_at === row.last_collected_at,
    'live_identity_or_clock_mismatch');
  req(same(live.status_evidence, row.status_evidence.map(publicSource)) &&
    same(live.board_evidence, []), 'live_status_evidence_mismatch');
  const publicDocument = d => ({type:d.type, identity:d.identity, url:d.url,
    publication_date:d.publication_date, collected_at:d.collected_at});
  req(same(live.documents,row.documents.map(publicDocument)), 'live_documents_mismatch');
  for (const k of FIELDS) {
    const f = row[k], g = live[k];
    const sources = [f.source,...(f.additional_sources || [])].map(publicSource);
    req(same(g?.value,f.value) && g.status === f.status && same(g.evidence,sources) &&
      same(g.corrections,f.corrections), 'live_field_mismatch:' + k);
  }
  req(live.minimum_application_amount_inr.value === null && live.minimum_application_amount_inr.status === 'missing', 'application_amount_out_of_scope');
  const alias = data.records.filter(r => r.id === ALIAS_ID);
  req(alias.length === 1 && alias[0].issuer_name === ctx.review.existing_alias.recovery_issuer_name &&
    alias[0].issue_price.value === 542 && alias[0].minimum_bid_quantity.value === 27, 'alias_public_mismatch');
  let comparison = null;
  if (baseline) {
    const original = new Map(baseline.records.map(r => [r.id,r]));
    req(original.size === baseline.records.length && !original.has(ID), 'invalid_baseline');
    const additions = data.records.filter(r => !original.has(r.id)).map(r => r.id);
    const current = new Map(data.records.map(r => [r.id,r]));
    const removed = [...original.keys()].filter(id => !current.has(id));
    const changed = [...original].filter(([id,r]) => current.has(id) && !same(current.get(id),r)).map(([id]) => id);
    req(same(additions,[ID]) && removed.length === 0 && changed.length === 0, 'unexpected_publication_scope');
    comparison = {baseline_records:original.size, added:additions, removed, changed, alias_unchanged:true};
  }
  return {schema_version:'1.0.0',status:'verified',checked_at:checkedAt,read_only:true,
    published_records:data.records.length,dataset_generated_at:data.generated_at,
    added_issuer:ID,reconciled_alias:ALIAS_ID,verified_fields:7,conflicting_fields:['issue_size_inr'],
    source_evidence_count:live.issue_size_inr.evidence.length,baseline_comparison:comparison,
    document_hash_scope:'Original hashes verified in retained recovery. Public evidence does not serialize document hashes.'};
}
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  const args = process.argv.slice(2);
  req(args.length === 1 && args[0].startsWith('--output-dir='), 'output_directory_required');
  const output = args[0].slice('--output-dir='.length);
  fs.mkdirSync(output,{recursive:true});
  let report = {status:'failed',read_only:true,source_url:LIVE_DATA_URL,workflow_run_id:process.env.GITHUB_RUN_ID || null};
  try {
    const ctx = context(), recovery = loadRecovery(), bytes = await fetchPublishedSnapshot();
    report.snapshot_fetched_at = new Date().toISOString();
    report.snapshot_sha256 = sha256(bytes);
    report.snapshot_bytes = bytes.length;
    fs.writeFileSync(path.join(output,'deployed-data.json'),bytes);
    report = {...report,...audit({ctx,recovery,data:JSON.parse(bytes),checkedAt:new Date().toISOString()})};
    const committed = fs.readFileSync(path.join(ROOT,'data/ipos.json'));
    report.committed_dataset_sha256 = sha256(committed);
    report.matches_checked_out_dataset = sha256(bytes) === sha256(committed);
  } catch (e) {report.error = e.message; report.status = 'failed';}
  fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2) + '\n');
  console.log(JSON.stringify(report));
  if (report.status !== 'verified') process.exitCode = 1;
}
