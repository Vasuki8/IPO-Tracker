import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {isDeepStrictEqual as same} from 'node:util';
import {sha256} from './verify-bse-listing-candidates.mjs';
export const SUMMARY='data/discovery/bse-retained-reconciliation-2026-09-28.json';
export const QUEUE='data/discovery/bse-2023-review-queue-2026-09-28.json';
const ROOT=fileURLToPath(new URL('../',import.meta.url));
const req=(x,m)=>{if(!x)throw Error(m);};
const hash=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const number=x=>Number.isSafeInteger(x)&&x>=0;
export function validateSnapshot(s,q,fullBytes=null){
 req(s?.schema_version==='1.0.0'&&s.status==='retained_source_reconciliation'&&s.read_only===true&&s.source_refetched===false&&s.auto_import_allowed===false&&s.full_indian_ipo_universe_complete===false,'unsafe_snapshot_scope');
 req(Number.isFinite(Date.parse(s.source_collected_at))&&Number.isFinite(Date.parse(s.reconciled_at))&&Date.parse(s.source_collected_at)<=Date.parse(s.reconciled_at),'invalid_snapshot_clock');
 req(same(s.years.map(y=>y.year),[2020,2021,2022,2023,2024,2025,2026]),'snapshot_year_scope');
 const t={source_rows:0,exact_matches:0,reviewed_aliases:0,awaiting_review:0};
 for(const y of s.years){req([y.source_rows,y.exact,y.reviewed_alias,y.awaiting_review].every(number)&&y.exact+y.reviewed_alias+y.awaiting_review===y.source_rows,'snapshot_year_counts');t.source_rows+=y.source_rows;t.exact_matches+=y.exact;t.reviewed_aliases+=y.reviewed_alias;t.awaiting_review+=y.awaiting_review;}
 for(const k of Object.keys(t))req(t[k]===s.totals[k],'snapshot_total_counts');
 req(number(s.totals.recovery_records)&&s.totals.recovery_records>=s.totals.exact_matches,'invalid_recovery_count');
 const p=s.source_pin;
 req(p.path==='data/discovery/bse-issue-summary-coverage-audit-2026-09-26.json'&&p.artifact_id===10910707544&&hash(p.zip_sha256)&&p.checked_responses===16&&p.receipts.length===16&&new Set(p.receipts.map(x=>x.file)).size===16,'invalid_source_pin');
 req(p.receipts.every(x=>/^raw\/[a-z0-9-]+\.json$/.test(x.file)&&hash(x.sha256)&&number(x.bytes)&&Number.isFinite(Date.parse(x.collected_at)))&&p.total_response_bytes===p.receipts.reduce((n,x)=>n+x.bytes,0),'invalid_source_receipts');
 req(s.source_collected_at===p.receipts.map(x=>x.collected_at).sort().at(-1),'source_clock_not_preserved');
 req(p.source_commit_labels_disagree===(p.source_commit!==p.compact_pin_source_commit)&&s.exceptions.source_commit_labels_disagree===p.source_commit_labels_disagree,'source_label_conflict_hidden');
 req(/^[a-f0-9]{40}$/.test(s.recovery_snapshot.commit)&&s.recovery_snapshot.files.every(x=>/^data\/recovery\/20\d{2}\/nse-issue-information.json$/.test(x.path)&&hash(x.sha256)),'invalid_recovery_pin');
 req(s.alias_approvals.length===2&&s.alias_approvals.every(x=>/^data\/discovery\/bse-202[12]-unmatched-disposition-2026-09-27.json$/.test(x.path)&&hash(x.sha256)),'invalid_alias_pin');
 req(hash(s.full_report.sha256)&&number(s.full_report.bytes)&&s.full_report.bytes>0,'invalid_full_report_pin');
 req(q?.schema_version==='1.0.0'&&q.status==='discovery_only_review_queue'&&q.source_year===2023&&q.auto_import_allowed===false&&q.complete_indian_ipo_universe===false&&q.source_refetched===false,'unsafe_queue_scope');
 req(q.source_collected_at===s.source_collected_at&&q.reconciled_at===s.reconciled_at&&q.reconciliation_path===SUMMARY&&q.reconciliation_full_sha256===s.full_report.sha256,'unbound_queue');
 const y=s.years.find(y=>y.year===2023);
 req(q.source_rows===y.source_rows&&q.matched_rows===y.exact+y.reviewed_alias&&q.awaiting_review===y.awaiting_review&&q.rows.length===q.awaiting_review,'queue_count_mismatch');
 req(same(q.source_response,p.receipts.find(x=>x.file==='raw/ipo-year-2023.json')),'queue_source_mismatch');
 const codes=new Set(),indices=new Set();
 for(const row of q.rows){req(row.source_year===2023&&row.disposition==='awaiting_review'&&row.auto_import_allowed===false&&row.matched_id===null&&typeof row.issuer_name==='string'&&row.issuer_name.length>2&&/^\d{6}$/.test(row.bse_scrip_code)&&!codes.has(row.bse_scrip_code)&&number(row.source_row_index)&&row.source_row_index<q.source_rows&&!indices.has(row.source_row_index),'invalid_candidate_row');codes.add(row.bse_scrip_code);indices.add(row.source_row_index);}
 req(q.next_bounded_review_codes.length>0&&q.next_bounded_review_codes.length<=6&&new Set(q.next_bounded_review_codes).size===q.next_bounded_review_codes.length&&q.next_bounded_review_codes.every(c=>codes.has(c)),'invalid_next_candidate_batch');
 if(fullBytes){
  req(fullBytes.length===s.full_report.bytes&&sha256(fullBytes)===s.full_report.sha256,'full_report_byte_mismatch');
  const report=JSON.parse(fullBytes);
  for(const k of ['schema_version','status','reconciled_at','source_collected_at','source_refetched','read_only','auto_import_allowed','full_indian_ipo_universe_complete','totals','source_pin','recovery_snapshot','alias_approvals'])req(same(report[k],s[k]),'full_report_summary_mismatch:'+k);
  req(same(report.years.map(({rows,...y})=>y),s.years),'full_report_year_mismatch');
  req(same(report.years.find(y=>y.year===2023).rows.filter(r=>r.disposition==='awaiting_review'),q.rows),'full_report_queue_mismatch');
  req(same(report.years.flatMap(y=>y.rows.filter(r=>r.source_identity_issue)),s.exceptions.missing_source_code_rows),'full_report_exception_mismatch');
 }
 return{ok:true,source_rows:t.source_rows,awaiting_review:t.awaiting_review,next_year:2023,next_batch:q.next_bounded_review_codes,source_refetched:false,full_report_bytes_checked:Boolean(fullBytes)};
}
export function checkSnapshot(root=ROOT,fullPath=null){return validateSnapshot(JSON.parse(fs.readFileSync(path.join(root,SUMMARY))),JSON.parse(fs.readFileSync(path.join(root,QUEUE))),fullPath?fs.readFileSync(fullPath):null);}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){try{console.log(JSON.stringify({retained_snapshot:checkSnapshot(ROOT,process.argv[2]??null)}));}catch(e){console.error(e.message);process.exitCode=1;}}
