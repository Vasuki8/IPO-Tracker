import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { hash, projectDetail, validateReviewedBatch, applyReviewedBatch, loadRecovery } from './apply-reviewed-nse-ipos.mjs';

const dir=process.env.SOURCE_DIR || '/mnt/data/nse_batch6_sources';
const src=JSON.parse(fs.readFileSync(path.join(dir,'sources.json')));
assert.equal(src.run_id,'36174755920');
assert.equal(src.source_commit_sha,'c82637ae5bc82ce59831dcfa1d10ff2438b1ad4b');
const queuePath='data/discovery/ipo-universe-review-2026-09-25-batch6.json';
const queueBytes=fs.readFileSync(queuePath),queue=JSON.parse(queueBytes);
assert.equal(hash(queueBytes),src.input.sha256);
assert.equal(queue.candidates.length,15);
assert.equal(queue.auto_import_allowed,false);
assert.equal(src.rows.length,24);
for(const s of src.rows){
  const b=fs.readFileSync(path.join(dir,s.file));
  assert.equal(b.length,s.bytes,s.file+':bytes');assert.equal(hash(b),s.sha256,s.file+':hash');
  assert.equal(s.status,s.kind==='migration_circular'?404:200,s.file+':http');
}
const ps=src.rows.find(s=>s.kind==='past'),past=JSON.parse(fs.readFileSync(path.join(dir,ps.file)));
const bs=src.rows.find(s=>s.kind==='deployed_baseline'),baselineBytes=fs.readFileSync(path.join(dir,bs.file)),baseline=JSON.parse(baselineBytes);
assert.equal(baseline.records.length,1284);
assert.equal(hash(baselineBytes),'a542ba9d96d621dff867f7310c99d5c74f2864898501c46b214d94db112f1e91');
assert.equal(hash(fs.readFileSync('data/ipos.json')),hash(baselineBytes),'source baseline must match served bytes');
const evidence=(s,p)=>({url:s.url,final_url:s.final_url,http_status:s.status,publication_date:null,collected_at:s.collected_at,response_sha256:s.sha256,projection_sha256:hash(JSON.stringify(p)),artifact_file:s.file});
const all=queue.candidates.map(candidate=>{
  const s=src.rows.find(s=>s.kind==='ipo_detail'&&s.symbol===candidate.nse_symbol);
  const detail=projectDetail(JSON.parse(fs.readFileSync(path.join(dir,s.file)))),past_row=past[candidate.row_index];
  assert.equal(past_row.symbol,candidate.nse_symbol);
  return {candidate,decision:'verified_initial_equity_ipo',detail_source:evidence(s,detail),detail,past_source:evidence(ps,past_row),past_row};
});
const approved=['MVELECTRO','ANAWIL','ARDEE','OPTIMYSTIX','TECHNOCRAF','DHOOTTRANS','MOLBIO','MILKYMIST','BLEL','PRAMODINI','SHIPROCKET','CREDENT'];
const provenance={source_run_id:src.run_id,source_snapshot_commit:src.source_commit_sha,source_branch_head:'f9206e03a758dda98716d9092bede1dfcc66d026',source_artifact_id:10881946171,source_artifact_sha256:'432491018daa0a376559937a81dde8726623ccb4e110761d7340091a9b240e63',queue_path:queuePath};
const manifest={schema_version:'1.0.0',verifier_version:'1.0.0',...provenance,queue_sha256:hash(JSON.stringify(queue)),projection_method:'literal_selected_json_fields_all_used_titles_retained',scope_note:'Twelve reviewed initial-equity IPOs only. ANNAPURNA and SWARAJ are main-board migrations; LEAP is held for missing issuer identity. No aggregate-only import or inferred size/application amount.',entries:all.filter(e=>approved.includes(e.candidate.nse_symbol))};
const checked=validateReviewedBatch(manifest,queue);
assert.equal(checked.length,12);
const fields={};for(const c of checked)for(const k of Object.keys(c.facts))fields[k]=(fields[k]||0)+1;
assert.deepEqual(fields,{listing_date:12,open_date:12,close_date:12,issue_price:12,price_band:12,minimum_bid_quantity:8,market_lot:4});
const manifestPath='data/verified-nse-ipos/2026-09-25-batch6.json';
const raw=loadRecovery(),rawBefore=JSON.stringify(raw),plan=applyReviewedBatch(raw,baseline,manifest,queue,manifestPath);
assert.deepEqual(plan.stats,{added:12,already_present:0});assert.equal(JSON.stringify(raw),rawBefore);
const rerun=applyReviewedBatch(plan.recovery,baseline,manifest,queue,manifestPath);
assert.deepEqual(rerun.stats,{added:0,already_present:12});assert.deepEqual(rerun.recovery,plan.recovery);
function migration(symbol,identity,reference,date,effective,pages,excerpt){
  const e=all.find(e=>e.candidate.nse_symbol===symbol),s=src.rows.find(s=>s.file===symbol+'-migration-disclosure-1.pdf');
  assert.equal(e.detail.metaInfo.isin,identity);assert.equal(e.detail.metaInfo.segment,'EQUITY');assert.equal(e.past_row.securityType,'SME');
  return {...e,decision:'excluded_migration_not_new_ipo',auto_import_allowed:false,reason:'The official exchange approval establishes an SME-to-Main-Board migration in August 2026, not a new equity IPO. Preserve the original 2022 offer observations and the conflicting price observations; do not combine migration dates with old IPO terms.',independent_official_evidence:{url:s.url,final_url:s.final_url,http_status:s.status,collected_at:s.collected_at,publication_date:date,document_identity:reference,document_sha256:s.sha256,artifact_file:s.file,reviewed_pages:pages,migration_effective_date:effective,isin:identity,evidence_excerpt:excerpt,visually_reviewed:true}};
}
const excluded=[
  migration('ANNAPURNA','INE0MGM01017','NSE/CML/75660 enclosed in issuer disclosure','2026-08-10','2026-08-12',[1,2,3],'pursuant to migration from SME Emerge platform'),
  migration('SWARAJ','INE0GMR01016','NSE/LIST/307 enclosed in issuer disclosure','2026-08-11','2026-08-13',[1,2],'pursuant to Migration from SME Emerge platform')
];
const leap=all.find(e=>e.candidate.nse_symbol==='LEAP');
assert.equal(leap.detail.companyName,'LEAP');assert.equal(leap.detail.metaInfo.isin,null);assert.equal(leap.detail.metaInfo.symbol,null);assert.equal(leap.detail.metaInfo.listingDate,null);
const held=[{...leap,decision:'held_missing_issuer_identity',auto_import_allowed:false,reason:'NSE response contains issueInfo offer terms but companyName is only the symbol LEAP and all selected metaInfo identity/security fields are null. Aggregate past-issues data alone cannot establish the missing legal name, ISIN, board or listing identity.'}];
for(const e of [...excluded,...held])assert.throws(()=>validateReviewedBatch({...manifest,entries:[{...e,decision:'verified_initial_equity_ipo'}]},queue));
const review={schema_version:'1.0.0',status:'reviewed_12_approved_2_migrations_1_identity_hold',reviewed_at:src.generated_at,...provenance,baseline:{public_records:baseline.records.length,public_sha256:hash(baselineBytes),dataset_generated_at:baseline.generated_at,snapshot_fetched_at:bs.collected_at,source_snapshot_matches_served_bytes:true},stats:{reviewed_candidates:15,verified_initial_equity_ipos:12,held_missing_identity:1,excluded_migrations:2,approved_exact_missing:12,approved_identity_conflicts:0,verified_facts:72,...fields},sources:{original_response_hashes_checked:src.rows.length,successful_responses:23,unsuccessful_responses:1,successful_detail_responses:15,past_response_sha256:ps.sha256,failures:src.rows.filter(s=>s.status!==200),note:'The guessed standalone circular path returned 404; the exact NSE circular enclosed in the official issuer disclosure was retrieved and visually reviewed. A failed fetch is not source absence.'},parser_notes:['ARDEE explicitly repeats per-equity-share units between price bounds; accept this fully anchored form with INR markers on both bounds.','Minimum-prefixed quantities are accepted only in Bid Lot/Minimum Order Quantity, with a bounded suffix. Literal source_value is retained; market lot semantics are unchanged.'],entries:checked.map(c=>({symbol:c.candidate.nse_symbol,issuer_name:c.issuer_name,observed_alias:c.candidate.issuer_name,isin:c.isin,board:c.candidate.board,decision:'approved_verified_initial_equity_ipo',offer_evidence:c.offer,offer_period:{open:c.facts.open_date.value,close:c.facts.close_date.value},listing_date:c.facts.listing_date.value,recovery_matches:[],published_matches:[]})),excluded,held};
fs.writeFileSync(manifestPath,JSON.stringify(manifest)+'\n');
fs.writeFileSync('data/discovery/nse-universe-batch6-review-2026-09-25.json',JSON.stringify(review,null,2)+'\n');
console.log(JSON.stringify({reviewed_batch6:review.stats,manifest_sha256:hash(fs.readFileSync(manifestPath)),review_sha256:hash(fs.readFileSync('data/discovery/nse-universe-batch6-review-2026-09-25.json'))}));
