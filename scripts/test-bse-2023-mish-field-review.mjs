import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {validateReview,checkRepository} from './check-bse-2023-mish-field-review.mjs';

const gitBlob=bytes=>{const b=Buffer.from(bytes);return createHash('sha1').update(Buffer.from('blob '+b.length+'\0')).update(b).digest('hex');};
const review=JSON.parse(fs.readFileSync('data/discovery/bse-2023-mish-field-review-2026-10-05.json','utf8'));
const queue=JSON.parse(fs.readFileSync('data/discovery/bse-2023-review-queue-2026-09-28.json','utf8'));
const progress=JSON.parse(fs.readFileSync('data/discovery/bse-2023-review-progress-2026-09-28.json','utf8'));
const published=JSON.parse(fs.readFileSync('data/ipos.json','utf8'));
const planBytes=fs.readFileSync(review.source_bindings.source_plan);
const receiptBytes=fs.readFileSync(review.source_bindings.source_receipt);
const rejectionBytes=fs.readFileSync(review.source_bindings.rejected_bse_candidate);
const recoveryByYear={};
for(const year of fs.readdirSync('data/recovery')){
  const p=`data/recovery/${year}/nse-issue-information.json`;
  if(/^20\d{2}$/.test(year)&&fs.existsSync(p))recoveryByYear[year]=JSON.parse(fs.readFileSync(p,'utf8'));
}
const fixture=()=>({
  review:structuredClone(review),
  queue:structuredClone(queue),
  progress:structuredClone(progress),
  sourcePlanBytes:Buffer.from(planBytes),
  sourceReceiptBytes:Buffer.from(receiptBytes),
  rejectionBytes:Buffer.from(rejectionBytes),
  recoveryByYear:structuredClone(recoveryByYear),
  published:structuredClone(published),
});
assert.deepEqual(checkRepository(),{
  ok:true,
  issuer:'mish-designs-limited',
  verified_core_fields:7,
  held_research_fields:2,
  publication_import_allowed:false,
  recovery_identity_hits:0,
});
assert.equal(gitBlob(planBytes),review.source_bindings.source_plan_git_blob_sha);
assert.equal(gitBlob(receiptBytes),review.source_bindings.source_receipt_git_blob_sha);
assert.equal(gitBlob(rejectionBytes),review.source_bindings.rejected_bse_candidate_git_blob_sha);

let rejected=0;
for(const [name,mutate] of [
 ['publication flag',x=>x.review.publication_import_allowed=true],
 ['stable id',x=>x.review.issuer.stable_id='other'],
 ['source plan pin',x=>x.review.source_bindings.source_plan_git_blob_sha='0'.repeat(40)],
 ['wrong-source acceptance',x=>x.rejectionBytes=Buffer.from(JSON.stringify({...JSON.parse(x.rejectionBytes),status:'accepted'}))],
 ['queue disposition',x=>x.progress.rows.find(r=>r.bse_scrip_code==='544015').disposition='published_reviewed_ipo'],
 ['pre-existing public Mish',x=>x.published.records.push({id:'mish-designs-limited',issuer_name:'Mish Designs Limited'})],
 ['pre-existing recovery Mish',x=>x.recoveryByYear['2022'].records.push({id:'mish-designs-limited',issuer_name:'Mish Designs Limited'})],
 ['issue price',x=>x.review.fields.issue_price.value=123],
 ['issue size status',x=>x.review.fields.issue_size_inr.status='provisional'],
 ['issue size normalization',x=>x.review.fields.issue_size_inr.normalization_multiplier=10000000],
 ['board promotion',x=>x.review.fields.board.value='sme'],
 ['price band invented',x=>x.review.fields.price_band={value:{min:120,max:122},status:'verified'}],
 ['market lot promoted',x=>{x.review.fields.market_lot.value=1000;x.review.fields.market_lot.status='verified';}],
 ['minimum bid promoted',x=>{x.review.fields.minimum_bid_quantity.value=1000;x.review.fields.minimum_bid_quantity.status='verified';}],
 ['minimum amount inferred',x=>{x.review.fields.minimum_application_amount_inr.value=122000;x.review.fields.minimum_application_amount_inr.status='verified';}],
 ['open date drift',x=>x.review.fields.open_date.value='2023-11-02'],
 ['close date drift',x=>x.review.fields.close_date.value='2023-10-31'],
 ['drop date conflict',x=>x.review.fields.open_date.corrections=[]],
 ['listing date drift',x=>x.review.fields.listing_date.value='2023-11-08'],
 ['NSE invention',x=>x.review.fields.nse_symbol={value:'MISH',status:'verified'}],
 ['ISIN invention',x=>x.review.fields.isin={value:'INE000000000',status:'verified'}]
]){
 const x=fixture();mutate(x);assert.throws(()=>validateReview(x),undefined,name);rejected++;
}
console.log(JSON.stringify({mish_semantic_review_tests:{
  rejected_mutations:rejected,
  core_bse_fields_verified:true,
  prospectus_date_conflict_retained:true,
  lot_and_bid_held_research_only:true,
  minimum_application_amount_not_inferred:true,
  all_year_identity_clear:true,
  publication_import_allowed:false,
}}));
