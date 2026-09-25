// Temporary, pinned source-to-manifest materializer. Removed before merge.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {hash, projectDetail, validateReviewedBatch, loadRecovery, applyReviewedBatch} from './apply-reviewed-nse-ipos.mjs';
const sourceDir=process.env.SOURCE_DIR;
assert.ok(sourceDir,'SOURCE_DIR required');
const src=JSON.parse(fs.readFileSync(path.join(sourceDir,'sources.json')));
assert.equal(src.run_id,'36187113307');
assert.equal(src.source_commit_sha,'a678c760130f082327ee591f5e38c154c68150d5');
assert.equal(src.rows.length,19);
for(const s of src.rows){
  assert.equal(s.status,200,s.file);
  const bytes=fs.readFileSync(path.join(sourceDir,s.file));
  assert.equal(bytes.length,s.bytes,s.file);assert.equal(hash(bytes),s.sha256,s.file);
}
const queuePath='data/discovery/ipo-universe-review-2026-09-25-batch8.json';
const queueBytes=fs.readFileSync(queuePath),queue=JSON.parse(queueBytes);
assert.equal(hash(queueBytes),src.input.sha256);
assert.equal(queue.auto_import_allowed,false);assert.equal(queue.candidates.length,14);
const ps=src.rows.find(s=>s.kind==='past'),past=JSON.parse(fs.readFileSync(path.join(sourceDir,ps.file)));
assert.equal(ps.sha256,queue.source_response_sha256,'canonical past-source drift');
const bs=src.rows.find(s=>s.kind==='deployed_baseline'),baselineBytes=fs.readFileSync(path.join(sourceDir,bs.file)),baseline=JSON.parse(baselineBytes);
assert.equal(baseline.records.length,1309);
assert.equal(hash(baselineBytes),'f1b0d662e1dc8a61cd4a821451143e85ea5a6e53425f158431a26953ca8b3df0');
assert.deepEqual(fs.readFileSync('data/ipos.json'),baselineBytes,'checkout differs from reviewed baseline');
const evidence=(s,p)=>({url:s.url,final_url:s.final_url,http_status:s.status,publication_date:null,collected_at:s.collected_at,response_sha256:s.sha256,projection_sha256:hash(JSON.stringify(p)),artifact_file:s.file});
const provenance={source_run_id:src.run_id,source_snapshot_commit:src.source_commit_sha,source_branch_head:'8fcd9b2557fedaf237f5fc0a1b2a0237b9015330',source_artifact_id:10886636012,source_artifact_sha256:'7169cbd2c166521850ac2fac44c4f4be808440df1ffc0acd45951cd84b2df1bb',queue_path:queuePath};
const all=queue.candidates.map(candidate=>{
  const ds=src.rows.find(s=>s.kind==='ipo_detail'&&s.symbol===candidate.nse_symbol);
  const detail=projectDetail(JSON.parse(fs.readFileSync(path.join(sourceDir,ds.file)))),past_row=past[candidate.row_index];
  assert.equal(past_row.symbol,candidate.nse_symbol);
  return{candidate,decision:'verified_initial_equity_ipo',detail_source:evidence(ds,detail),detail,past_source:evidence(ps,past_row),past_row};
});
const approved=['SUMAX','LUMINO','ASHUTOSH','PERNIASPOP','SHANTIINOR','DEEPA','GLASSWALL','PRASOLCHEM','STEAMHOUSE','VINOD','KHERIAAUTO','SPECTRAA'];
const manifestPath='data/verified-nse-ipos/2026-09-25-batch8.json';
const manifest={schema_version:'1.0.0',verifier_version:'1.0.0',...provenance,queue_sha256:hash(JSON.stringify(queue)),projection_method:'literal_selected_json_fields_all_used_titles_retained',scope_note:'Twelve independently reviewed initial equity IPOs; DOLLEX migration and 13DCCL28 debt event excluded. VINOD is explicitly fixed price; no price band, issue size or application amount inferred. No production parser change is required.',entries:all.filter(e=>approved.includes(e.candidate.nse_symbol))};
const checked=validateReviewedBatch(manifest,queue);
const facts=Object.fromEntries(['listing_date','open_date','close_date','issue_price','price_band','market_lot','minimum_bid_quantity'].map(k=>[k,checked.filter(c=>c.facts[k]).length]));
assert.deepEqual(facts,{listing_date:12,open_date:12,close_date:12,issue_price:12,price_band:11,market_lot:6,minimum_bid_quantity:6});
const raw=loadRecovery(),saved=JSON.stringify(raw),plan=applyReviewedBatch(raw,baseline,manifest,queue,manifestPath);
assert.deepEqual(plan.stats,{added:12,already_present:0});assert.equal(JSON.stringify(raw),saved);
assert.deepEqual(applyReviewedBatch(plan.recovery,baseline,manifest,queue,manifestPath).stats,{added:0,already_present:12});
const doc=(s,extra)=>({url:s.url,final_url:s.final_url,http_status:s.status,collected_at:s.collected_at,document_sha256:s.sha256,artifact_file:s.file,...extra});
const dollex=all.find(e=>e.candidate.nse_symbol==='DOLLEX'),debt=all.find(e=>e.candidate.nse_symbol==='13DCCL28');
assert.equal(dollex.detail.metaInfo.isin,'INE0JHH01011');assert.equal(dollex.detail.metaInfo.segment,'EQUITY');
assert.equal(dollex.past_row.ipoStartDate,'15-DEC-2022');
assert.equal(debt.detail.metaInfo.isDebtSec,true);assert.equal(debt.detail.metaInfo.isin,'INE04Q907231');
const eqs=src.rows.find(s=>s.kind==='equity_ipo_identity'),eq=projectDetail(JSON.parse(fs.readFileSync(path.join(sourceDir,eqs.file))));
assert.equal(eq.metaInfo.symbol,'DCCL');assert.equal(eq.metaInfo.isin,'INE04Q901010');assert.equal(eq.metaInfo.isDebtSec,true);
const excluded=[
  {...dollex,decision:'excluded_migration_not_new_ipo',auto_import_allowed:false,
   reason:'Official issuer disclosure encloses NSE/LIST/314 dated September 9, 2026, approving migration from SME Emerge to NSE Main Board effective September 11, 2026. The issuer endpoint carries the original December 2022 IPO terms; its September 2026 date is not a new equity IPO.',
   independent_official_evidence:doc(src.rows.find(s=>s.kind==='migration_approval'),{document_identity:'Dollex Agrotech disclosure enclosing NSE/LIST/314',publication_date:'2026-09-09',effective_date:'2026-09-11',reviewed_pages:[1,2],review_method:'PDF text extraction and visual inspection of retained original pages',isin:'INE0JHH01011',symbol:'DOLLEX',evidence:'Migration from SME Emerge platform to Capital Market Segment (Main Board).',trading_lot_not_ipo_application_lot:1}),
   original_offer_period:{open:'2022-12-15',close:'2022-12-20'},scope_note:'Excludes this 2026 migration event, not the existence of an earlier equity IPO.'},
  {...debt,decision:'excluded_debt_security_not_initial_equity_ipo',auto_import_allowed:false,
   reason:'NSE issuer response marks 13DCCL28 as debt; ISIN INE04Q907231 matches NSE/CML/76341, a privately placed coupon-bearing security, not the earlier equity IPO. Do not mix May 2025 equity-offer terms with the September 2026 debt listing.',
   independent_official_evidence:doc(src.rows.find(s=>s.kind==='debt_listing_circular'),{document_identity:'NSE/CML/76341',publication_date:'2026-09-15',effective_date:'2026-09-16',reviewed_pages:[1,3],review_method:'PDF text extraction and visual inspection of retained original pages',isin:'INE04Q907231',symbol:'13DCCL28',series:'N0',description:'DCCL 13% 2028',coupon_percent:13,maturity_date:'2028-09-10',trading_lot_not_ipo_application_lot:1}),
   additional_endpoint:{source:evidence(eqs,eq),projection:eq,disposition:'retained_mixed_metadata_not_equity_approval',note:'The separate DCCL endpoint reports INE04Q901010 and May 2025 IPO terms but isDebtSec=true. This inconsistent flag is preserved, not silently cleared or used to approve an equity record. The debt exclusion relies on matching 13DCCL28/INE04Q907231 in the authoritative circular.'}}
];
for(const e of excluded)assert.throws(()=>validateReviewedBatch({...manifest,entries:[{...e,decision:'verified_initial_equity_ipo'}]},queue));
const review={schema_version:'1.0.0',status:'reviewed_12_approved_1_migration_1_debt_excluded',reviewed_at:'2026-09-25T20:44:19.397Z',...provenance,
 baseline:{public_records:1309,public_sha256:hash(baselineBytes),dataset_generated_at:baseline.generated_at,snapshot_fetched_at:bs.collected_at,source_snapshot_matches_served_bytes:true},
 stats:{reviewed_candidates:14,verified_initial_equity_ipos:12,held:0,excluded_migrations:1,excluded_debt_securities:1,approved_exact_missing:12,approved_identity_conflicts:0,verified_facts:71,...facts},
 sources:{original_response_hashes_checked:19,successful_responses:19,unsuccessful_responses:0,successful_detail_responses:14,past_response_sha256:ps.sha256},
 parser_changes:[],notes:['Existing reviewed importer handles all twelve official forms without relaxing gates.','VINOD fixed price Rs. 94 is not a two-ended band.','DOLLEX migration and 13DCCL28 debt require positive official classification; rejection alone is not classification.','DCCL additional endpoint mixed metadata is retained without approval.'],
 entries:checked.map(c=>({symbol:c.candidate.nse_symbol,issuer_name:c.issuer_name,observed_alias:c.candidate.issuer_name,isin:c.isin,board:c.candidate.board,decision:'approved_verified_initial_equity_ipo',offer_evidence:c.offer,offer_period:{open:c.facts.open_date.value,close:c.facts.close_date.value},listing_date:c.facts.listing_date.value,recovery_matches:[],published_matches:[]})),excluded,held:[]};
fs.writeFileSync(manifestPath,JSON.stringify(manifest)+'\n');
fs.writeFileSync('data/discovery/nse-universe-batch8-review-2026-09-25.json',JSON.stringify(review,null,2)+'\n');
const runner='scripts/test-reviewed-nse-ipos.mjs',tests=fs.readFileSync(runner,'utf8');
if(!tests.includes('test-reviewed-nse-batch8.mjs'))fs.writeFileSync(runner,tests.trimEnd()+'\n\nawait import("./test-reviewed-nse-batch8.mjs");\n');
console.log(JSON.stringify({source_hashes_checked:19,approved:12,facts:71,excluded_migration:1,excluded_debt:1,held:0,parser_changes:0,preservation:true,idempotent:true}));
