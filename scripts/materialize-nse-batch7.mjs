import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const digest=b=>createHash('sha256').update(b).digest('hex');
const parserPath='scripts/apply-reviewed-nse-ipos.mjs';
let parser=fs.readFileSync(parserPath,'utf8');
const beforeHash='4cfb95cb7824195f9645e1459a5a5c4acf34525f59a8a206368354586f544f28';
const afterHash='47579122000d9ba00d1561367c61c2061b2d97f72511ac0eabc42e1b2b52a6c7';
if(digest(parser)!==afterHash){
  assert.equal(digest(parser),beforeHash,'unreviewed parser revision');
  const old=String.raw`: /^(\d{1,2}-[A-Za-z]+-\d{4})\s+to\s+(\d{1,2}-[A-Za-z]+-\d{4})$/;`;
  const replacement=String.raw`: /^(\d{1,2}-[A-Za-z]+-\d{4})\s+to\s+(\d{1,2}-[A-Za-z]+-\d{4})(?: \(The Issue is further extended to (\d{1,2}-[A-Za-z]+-\d{4})\))?$/i;`;
  assert.equal(parser.split(old).length,2);parser=parser.replace(old,replacement);
  const line='  const open = nseDate(match[1]), close = nseDate(match[2]);';
  assert.equal(parser.split(line).length,2);
  parser=parser.replace(line,line+"\n  // An explicit extended endpoint must repeat the stated closing date exactly.\n  if (!revised && match[3]) requireThat(close === nseDate(match[3]) && close !== null, 'inconsistent_extended_offer_period');");
  assert.equal(digest(parser),afterHash);fs.writeFileSync(parserPath,parser);
}
const {hash,projectDetail,validateReviewedBatch,loadRecovery,applyReviewedBatch}=await import('./apply-reviewed-nse-ipos.mjs');
const sourceDir=process.env.SOURCE_DIR;
assert.ok(sourceDir,'SOURCE_DIR required');
const src=JSON.parse(fs.readFileSync(path.join(sourceDir,'sources.json')));
assert.equal(src.run_id,'36180291566');
assert.equal(src.source_commit_sha,'d451a6166aea8437d976228014c563fc70885981');
assert.equal(src.rows.length,21);
for(const s of src.rows){assert.equal(s.status,200,s.file);const b=fs.readFileSync(path.join(sourceDir,s.file));assert.equal(b.length,s.bytes,s.file);assert.equal(hash(b),s.sha256,s.file);}
const queuePath='data/discovery/ipo-universe-review-2026-09-25-batch7.json';
const queueBytes=fs.readFileSync(queuePath),queue=JSON.parse(queueBytes);
assert.equal(hash(queueBytes),src.input.sha256);assert.equal(queue.auto_import_allowed,false);assert.equal(queue.candidates.length,15);
const pastSource=src.rows.find(s=>s.kind==='past'),past=JSON.parse(fs.readFileSync(path.join(sourceDir,pastSource.file)));
assert.equal(pastSource.sha256,queue.source_response_sha256,'canonical past source drift');
const baselineSource=src.rows.find(s=>s.kind==='deployed_baseline'),baselineBytes=fs.readFileSync(path.join(sourceDir,baselineSource.file)),baseline=JSON.parse(baselineBytes);
assert.equal(baseline.records.length,1296);assert.equal(hash(baselineBytes),'0fe577e052a06eef0e477eff7a0530a289b5715d25da42e372fc5071f4e9b1e0');
assert.deepEqual(fs.readFileSync('data/ipos.json'),baselineBytes,'checkout is not reviewed baseline');
const evidence=(s,p)=>({url:s.url,final_url:s.final_url,http_status:s.status,publication_date:null,collected_at:s.collected_at,response_sha256:s.sha256,projection_sha256:hash(JSON.stringify(p)),artifact_file:s.file});
const provenance={source_run_id:src.run_id,source_snapshot_commit:src.source_commit_sha,source_branch_head:'b81403fee76d64771720eed8b86e7127e0e707f7',source_artifact_id:10884545129,source_artifact_sha256:'4196efe544c31deee32ebd6d642e11d5f904266aee97a10b43c96f392dd27da6',queue_path:queuePath};
const all=queue.candidates.map(candidate=>{const s=src.rows.find(s=>s.kind==='ipo_detail'&&s.symbol===candidate.nse_symbol);const detail=projectDetail(JSON.parse(fs.readFileSync(path.join(sourceDir,s.file))));const past_row=past[candidate.row_index];assert.equal(past_row.symbol,candidate.nse_symbol);return{candidate,decision:'verified_initial_equity_ipo',detail_source:evidence(s,detail),detail,past_source:evidence(pastSource,past_row),past_row};});
const approved=['SKYTECH','FASCINATE','HORIZONIND','LALITHAA','SHANKESH','SUNSHINE','GAJA','TEMPSENS','AUGMONT','ABH','MADHURKNIT','SKYWAYS','SYMBIOTEC'];
const manifestPath='data/verified-nse-ipos/2026-09-25-batch7.json';
const manifest={schema_version:'1.0.0',verifier_version:'1.0.0',...provenance,queue_sha256:hash(JSON.stringify(queue)),projection_method:'literal_selected_json_fields_all_used_titles_retained',scope_note:'Thirteen independently reviewed initial public equity IPOs. Two debt securities excluded using issuer-specific flags, matched ISINs and official exchange circulars. FASCINATE explicit extended close is cross-checked, not inferred. No issue size or application amount inferred.',entries:all.filter(e=>approved.includes(e.candidate.nse_symbol))};
const checked=validateReviewedBatch(manifest,queue),facts=Object.fromEntries(['listing_date','open_date','close_date','issue_price','price_band','market_lot','minimum_bid_quantity'].map(k=>[k,checked.filter(c=>c.facts[k]).length]));
assert.equal(checked.length,13);assert.deepEqual(facts,{listing_date:13,open_date:13,close_date:13,issue_price:13,price_band:13,market_lot:4,minimum_bid_quantity:9});
const raw=loadRecovery(),saved=JSON.stringify(raw),plan=applyReviewedBatch(raw,baseline,manifest,queue,manifestPath);
assert.deepEqual(plan.stats,{added:13,already_present:0});assert.equal(JSON.stringify(raw),saved);
assert.deepEqual(applyReviewedBatch(plan.recovery,baseline,manifest,queue,manifestPath).stats,{added:0,already_present:13});
const decisions=[
  {symbol:'1150VIES30',isin:'INE0TR007022',circular:'NSE/CML/76063',publication_date:'2026-08-31',reviewed_pages:[1,5],security:'VIESL30',description:'VIESL 11.50% 2030 Sr I',coupon_percent:11.5,maturity_date:'2030-08-27',equity_symbol:'VIESL',equity_isin:'INE0TR001017',reason:'NSE marks 1150VIES30 as debt. ISIN INE0TR007022 matches the Other Debt Securities circular entry VIESL30, not the separately filed equity ISIN. The 2024 equity-offer terms mixed into the aggregate row are not a new 2026 equity IPO.',date_note:'The debt-market circular is effective August 31; ipo-detail reports September 1 for the security in the capital-market segment. Neither is an equity IPO listing date.'},
  {symbol:'12AIL28',isin:'INE0R9407016',circular:'NSE/CML/76110',publication_date:'2026-09-01',reviewed_pages:[1,2],security:'12AIL28',description:'AIL 12% 2028',coupon_percent:12,maturity_date:'2028-08-28',equity_symbol:'AVPINFRA',equity_isin:'INE0R9401019',reason:'NSE marks 12AIL28 as debt. ISIN INE0R9407016 matches the privately placed coupon-bearing security in NSE/CML/76110 and differs from AVPINFRA equity. The aggregate row mixes its 2024 equity offer period with a 2026 debt listing.',date_note:'The circular admits this security effective September 2, 2026. Its secondary-market lot of 1 is not an IPO application lot.'}
];
const excluded=decisions.map(d=>{
  const e=all.find(e=>e.candidate.nse_symbol===d.symbol),s=src.rows.find(s=>s.kind==='debt_listing_circular'&&s.symbol===d.symbol),eq=src.rows.find(s=>s.kind==='distinct_equity_identity'&&s.symbol===d.symbol);
  assert.equal(e.detail.metaInfo.isDebtSec,true);assert.equal(e.detail.metaInfo.isin,d.isin);assert.equal(e.detail.issueInfo.symbol,null);assert.notEqual(d.isin,d.equity_isin);
  const html=fs.readFileSync(path.join(sourceDir,eq.file),'utf8');assert.ok(html.includes(d.equity_isin)&&html.includes(d.equity_symbol));
  const result={...e,decision:'excluded_debt_security_not_initial_equity_ipo',auto_import_allowed:false,reason:d.reason,date_note:d.date_note,
    independent_official_evidence:{url:s.url,final_url:s.final_url,http_status:s.status,publication_date:d.publication_date,collected_at:s.collected_at,document_sha256:s.sha256,artifact_file:s.file,document_identity:d.circular,reviewed_pages:d.reviewed_pages,review_method:'PDF text extraction and independent visual inspection of rendered retained original pages',security:d.security,description:d.description,isin:d.isin,coupon_percent:d.coupon_percent,maturity_date:d.maturity_date},
    distinct_equity_identity:{url:eq.url,final_url:eq.final_url,http_status:eq.status,publication_date:null,collected_at:eq.collected_at,document_sha256:eq.sha256,artifact_file:eq.file,evidence_locator:'General information about company: NSE Symbol, ISIN, Class of security',nse_symbol:d.equity_symbol,isin:d.equity_isin,security_class:'Equity'}};
  assert.throws(()=>validateReviewedBatch({...manifest,entries:[{...result,decision:'verified_initial_equity_ipo'}]},queue));return result;
});
const review={schema_version:'1.0.0',status:'reviewed_13_approved_2_debt_excluded',reviewed_at:'2026-09-25T19:36:00.288Z',...provenance,
  baseline:{public_records:1296,public_sha256:hash(baselineBytes),dataset_generated_at:baseline.generated_at,snapshot_fetched_at:baselineSource.collected_at,source_snapshot_matches_served_bytes:true},
  stats:{reviewed_candidates:15,verified_initial_equity_ipos:13,held:0,excluded_debt_securities:2,approved_exact_missing:13,approved_identity_conflicts:0,verified_facts:78,...facts},
  sources:{original_response_hashes_checked:21,successful_responses:21,unsuccessful_responses:0,successful_detail_responses:15,past_response_sha256:pastSource.sha256},
  parser_notes:['Recognize only the fully anchored Issue Period suffix (The Issue is further extended to DATE); the suffix must repeat the stated closing date and agree with the independent past-source close.','Retain the literal full date expression and current official price band; do not use older aggregator dates or estimate a revised window.'],
  entries:checked.map(c=>({symbol:c.candidate.nse_symbol,issuer_name:c.issuer_name,observed_alias:c.candidate.issuer_name,isin:c.isin,board:c.candidate.board,decision:'approved_verified_initial_equity_ipo',offer_evidence:c.offer,offer_period:{open:c.facts.open_date.value,close:c.facts.close_date.value},listing_date:c.facts.listing_date.value,recovery_matches:[],published_matches:[]})),excluded,held:[]};
fs.writeFileSync(manifestPath,JSON.stringify(manifest)+'\n');
fs.writeFileSync('data/discovery/nse-universe-batch7-review-2026-09-25.json',JSON.stringify(review,null,2)+'\n');
const testRunner='scripts/test-reviewed-nse-ipos.mjs';let tests=fs.readFileSync(testRunner,'utf8');if(!tests.includes('test-reviewed-nse-batch7.mjs'))fs.writeFileSync(testRunner,tests.trimEnd()+'\n\nawait import("./test-reviewed-nse-batch7.mjs");\n');
console.log(JSON.stringify({source_hashes_checked:21,approved:13,facts:78,excluded_debt:2,held:0,preservation:true,idempotent:true,parser_sha256:afterHash}));
