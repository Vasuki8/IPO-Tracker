// Reconcile archived source bytes against current recovery. Never collect or publish IPOs.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {isDeepStrictEqual as same} from 'node:util';
import {sha256,parseBseYearRows,parseBseYearSummary} from './audit-bse-issue-summary-coverage.mjs';
import {matchIndexCompany} from './audit-bse-sme-ipo-index.mjs';
const ROOT=fileURLToPath(new URL('../',import.meta.url));
export const PIN='data/discovery/bse-issue-summary-coverage-audit-2026-09-26.json';
const req=(ok,m)=>{if(!ok)throw Error(m);};
const compact=s=>String(s??'').toLowerCase().replace(/\blimited\b|\bltd\b/g,'').replace(/[^a-z0-9]/g,'');
// Only a specific retained, reviewed disposition may authorize an alias link.
export function reconcileRows({yearBlocks,recovery,aliases=[],reconciledAt,sourceCollectedAt}){
 req(Number.isFinite(Date.parse(reconciledAt))&&Number.isFinite(Date.parse(sourceCollectedAt))&&Date.parse(sourceCollectedAt)<=Date.parse(reconciledAt),'invalid_reconciliation_clock');
 req(new Set(recovery.map(x=>x.record.id)).size===recovery.length,'duplicate_recovery_id');
 const approved=new Map();
 for(const a of aliases){const key=a.year+'|'+a.code;req(!approved.has(key)&&a.disposition==='existing_recovery_alias'&&typeof a.approval_path==='string'&&a.approval_path.startsWith('data/discovery/'),'invalid_alias_membership');approved.set(key,a);}
 const usedAliases=new Set(),seen=new Set(),years=[];let total=0,exact=0,aliasCount=0,pending=0;
 for(const block of yearBlocks){
  const counts={exact:0,reviewed_alias:0,awaiting_review:0},rows=[];
  req(Number.isInteger(block.year)&&!years.some(y=>y.year===block.year)&&block.rows.length===block.total,'invalid_year_scope');
  const codeCounts=new Map();for(const r of block.rows)if(r.bse_scrip_code)codeCounts.set(r.bse_scrip_code,(codeCounts.get(r.bse_scrip_code)??0)+1);
  for(const row of block.rows){
   const key=block.year+'|'+row.bse_scrip_code,rowKey=block.year+'|'+row.source_row_index;
   req(Number.isSafeInteger(row.source_row_index)&&row.source_row_index>=0&&!seen.has(rowKey),'duplicate_source_row');seen.add(rowKey);
   const identityIssue=!row.bse_scrip_code?'missing_bse_scrip_code':codeCounts.get(row.bse_scrip_code)>1?'duplicate_bse_scrip_code':null;
   const selection=matchIndexCompany(row.issuer_name,recovery),a=approved.get(key);
   let chosen=selection.match_type==='exact'?selection.match:null,kind=chosen?'exact':'awaiting_review';
   if(a){const hits=recovery.filter(x=>x.record.id===a.id);req(row.issuer_name===a.source_name&&hits.length===1&&Number(hits[0].year)===block.year&&hits[0].record.issuer_name===a.retained_name,'alias_binding_mismatch');req(!chosen||chosen.record.id===a.id,'alias_exact_identity_conflict');chosen=hits[0];kind='reviewed_alias';usedAliases.add(key);}
   const conflictingDate=Boolean(chosen?.record.listing_date?.value&&chosen.record.listing_date.value!==row.listing_date);
   const wrongYear=Boolean(chosen&&Number(chosen.year)!==block.year);
   if(conflictingDate||wrongYear||identityIssue)kind='awaiting_review';
   const hints=kind==='awaiting_review'?recovery.filter(x=>compact(x.record.issuer_name)===compact(row.issuer_name)||String(x.record.bse_scrip_code??'')===row.bse_scrip_code).map(x=>({id:x.record.id,year:Number(x.year)})):[];
   counts[kind]++;
   rows.push({issuer_name:row.issuer_name,bse_scrip_code:row.bse_scrip_code,source_year:block.year,source_row_index:row.source_row_index,discovery_listing_date:row.listing_date,discovery_issue_price:row.issue_price,disposition:kind,matched_id:chosen?.record.id??null,matched_year:chosen?Number(chosen.year):null,reviewed_alias_approval:a?.approval_path??null,listing_date_conflict:conflictingDate,cross_year_conflict:wrongYear,source_identity_issue:identityIssue,candidate_hints:hints,auto_import_allowed:false});
  }
  years.push({year:block.year,source_rows:rows.length,...counts,rows});total+=rows.length;exact+=counts.exact;aliasCount+=counts.reviewed_alias;pending+=counts.awaiting_review;
 }
 req(usedAliases.size===approved.size,'unused_alias_approval');
 return{schema_version:'1.0.0',status:'retained_source_reconciliation',reconciled_at:reconciledAt,source_collected_at:sourceCollectedAt,source_refetched:false,read_only:true,auto_import_allowed:false,full_indian_ipo_universe_complete:false,totals:{source_rows:total,recovery_records:recovery.length,exact_matches:exact,reviewed_aliases:aliasCount,awaiting_review:pending},years,scope_note:'Archived BSE historical rows reconciled to a newer recovery snapshot. This is not a fresh exchange collection, field-completeness audit, or authority to import suggested candidates.'};
}
export function verifiedYearBlocks({inputDir,pin}){
 const collection=JSON.parse(fs.readFileSync(path.join(inputDir,'collection.json'))),receipts=pin.source_receipts;
 req(Array.isArray(receipts)&&collection.schema_version==='2.0.0','invalid_retained_collection');
 const lastSource=receipts.map(r=>r.collected_at).sort().at(-1);
 req(Number.isFinite(Date.parse(lastSource))&&Date.parse(collection.completed_at)>=Date.parse(lastSource)&&Date.parse(collection.completed_at)<=Date.parse(pin.generated_at)&&String(collection.run_id)===String(pin.workflow_run_id),'changed_collection_clock_or_origin');
 const checked=[];
 for(const r of receipts){req(/^raw\/[a-z0-9-]+\.json$/.test(r.file),'unsafe_receipt_path');const b=fs.readFileSync(path.join(inputDir,r.file));req(b.length===r.bytes&&sha256(b)===r.sha256,'source_hash_mismatch:'+r.file);checked.push(r);}
 const blocks=[];
 for(const year of [2020,2021,2022,2023,2024,2025,2026]){
  const rp=checked.find(r=>r.file===`raw/ipo-year-${year}.json`),sp=checked.find(r=>r.file===`raw/ipo-tracker-${year}.json`);
  req(rp&&sp,'missing_year_receipt');
  const rows=parseBseYearRows(JSON.parse(fs.readFileSync(path.join(inputDir,rp.file))),year),summary=parseBseYearSummary(JSON.parse(fs.readFileSync(path.join(inputDir,sp.file))),year);
  const saved=collection.yearly.find(b=>b.year===year);
  req(saved&&same(saved.rows,rows)&&same(saved.summary,summary),'retained_projection_mismatch');
  req(rows.length===summary.TotalIPO,'year_total_mismatch');
  blocks.push({year,total:summary.TotalIPO,rows,source_receipt:rp});
 }
 return{blocks,checked,collection};
}
export function run({inputDir,output,root=ROOT,reconciledAt=new Date().toISOString(),recoveryCommit=null}){
 const read=p=>JSON.parse(fs.readFileSync(path.join(root,p)));
 const pin=read(PIN),{blocks,checked,collection}=verifiedYearBlocks({inputDir,pin});
 const recovery=[],recoveryReceipts=[],aliases=[],aliasReceipts=[];
 for(const y of fs.readdirSync(path.join(root,'data/recovery')).filter(y=>/^20\d{2}$/.test(y))){const p=`data/recovery/${y}/nse-issue-information.json`;if(!fs.existsSync(path.join(root,p)))continue;const b=fs.readFileSync(path.join(root,p));recoveryReceipts.push({path:p,sha256:sha256(b)});for(const record of JSON.parse(b).records)recovery.push({year:Number(y),record});}
 for(const y of [2021,2022]){const p=`data/discovery/bse-${y}-unmatched-disposition-2026-09-27.json`,b=fs.readFileSync(path.join(root,p));aliasReceipts.push({path:p,sha256:sha256(b)});for(const r of JSON.parse(b).rows.filter(r=>r.disposition==='existing_recovery_alias'))aliases.push({year:y,code:r.bse_scrip_code,source_name:r.issuer_name,retained_name:r.reviewed_issuer_name,id:r.stable_id,disposition:r.disposition,approval_path:p});}
 const report=reconcileRows({yearBlocks:blocks,recovery,aliases,reconciledAt,sourceCollectedAt:checked.map(r=>r.collected_at).sort().at(-1)});
 report.source_pin={path:PIN,artifact_id:10910707544,zip_sha256:'5105397fdae479e05e46528ecb2cf7665f3f329c6cbae74169ac9dc64b35cac5',collection_run_id:collection.run_id,source_commit:collection.source_commit_sha,compact_pin_source_commit:pin.source_commit_sha,source_commit_labels_disagree:collection.source_commit_sha!==pin.source_commit_sha,checked_responses:checked.length,total_response_bytes:checked.reduce((n,r)=>n+r.bytes,0),receipts:checked};
 report.recovery_snapshot={commit:recoveryCommit,files:recoveryReceipts};report.alias_approvals=aliasReceipts;
 const target=path.resolve(output),protectedPaths=[...recoveryReceipts,...aliasReceipts,{path:PIN},{path:'data/ipos.json'}].map(r=>path.resolve(root,r.path));
 protectedPaths.push(path.resolve(inputDir,'collection.json'),...checked.map(r=>path.resolve(inputDir,r.file)));
 req(!protectedPaths.includes(target),'output_overwrites_source');
 fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,JSON.stringify(report,null,2)+'\n');return report;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){try{const a=Object.fromEntries(process.argv.slice(2).map(a=>{const i=a.indexOf('=');req(a.startsWith('--')&&i>2,'invalid_argument');return[a.slice(2,i),a.slice(i+1)];}));req(a.input&&a.output,'input_and_output_required');const r=run({inputDir:a.input,output:a.output,root:a.root??ROOT,reconciledAt:a['as-of']??new Date().toISOString(),recoveryCommit:a['recovery-commit']??null});console.log(JSON.stringify({retained_bse_reconciliation:r.totals,source_collected_at:r.source_collected_at,reconciled_at:r.reconciled_at,source_refetched:false}));}catch(e){console.error(e.message);process.exitCode=1;}}
