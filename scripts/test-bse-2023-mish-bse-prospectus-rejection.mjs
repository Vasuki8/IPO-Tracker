import assert from 'node:assert/strict';
import fs from 'node:fs';

const rejection=JSON.parse(fs.readFileSync('data/evidence/bse-2023-mish-bse-prospectus-rejection-2026-10-05.json','utf8'));
const prior=JSON.parse(fs.readFileSync('data/evidence/bse-2023-mish-source-receipt-2026-10-05.json','utf8'));
const progress=JSON.parse(fs.readFileSync('data/discovery/bse-2023-review-progress-2026-09-28.json','utf8'));

assert.equal(rejection.status,'rejected_wrong_issuer_document');
assert.equal(rejection.issuer_name,'Mish Designs Limited');
assert.equal(rejection.discovery_bse_scrip_code,'544015');
assert.equal(rejection.source_authority,'BSE Limited');
assert.equal(rejection.collection.run_id,37363801195);
assert.equal(rejection.collection.artifact_id,11368075318);
assert.equal(rejection.collection.artifact_bytes,2578896);
assert.equal(rejection.collection.artifact_sha256,'6b1718c6931c0dfcaabbbcd864561dca74c40a7cf7f8770f27bb670660262695');
assert.equal(rejection.collection.response_bytes,2572076);
assert.equal(rejection.collection.response_sha256,'663aeffedb6d21f2eb71a48fcb634dcdfd3e35807fa0dde113047e813d39cd1d');
assert.equal(rejection.collection.pdf_pages,234);
assert.equal(rejection.collection.extracted_text_sha256,'38298cc5c3bc8a03a894e89a6f2072633957f4112b3fd9ba5a0b9513e8e1aa29');

assert.equal(rejection.semantic_review.cover_page,1);
assert.equal(rejection.semantic_review.cover_issuer,'ARROWHEAD SEPERATION ENGINEERING LIMITED');
assert.equal(rejection.semantic_review.cover_cin,'U74210MH1991PLC062643');
assert.equal(rejection.semantic_review.cover_issue_price_inr,233);
assert.equal(rejection.semantic_review.cover_issue_open_date,'2023-11-16');
assert.equal(rejection.semantic_review.cover_issue_close_date,'2023-11-20');
assert.deepEqual(rejection.semantic_review.mish_mentions_pages,[179]);
assert.equal(rejection.semantic_review.mish_scrip_code_present,false);
assert.equal(rejection.semantic_review.decision,'reject_as_mish_source');
assert.match(rejection.semantic_review.reason,/Arrowhead Seperation Engineering Limited/);

assert.equal(rejection.publication_import_allowed,false);
assert.equal(rejection.semantic_field_approval_allowed,false);
assert.equal(rejection.prior_mish_source_receipt,'data/evidence/bse-2023-mish-source-receipt-2026-10-05.json');
assert.equal(rejection.prior_issuer_prospectus.response_sha256,
  prior.documents.find(d=>d.key==='final_prospectus').response_sha256);
assert.equal(rejection.prior_issuer_prospectus.response_bytes,
  prior.documents.find(d=>d.key==='final_prospectus').response_bytes);
assert.equal(rejection.prior_issuer_prospectus.pdf_pages,
  prior.documents.find(d=>d.key==='final_prospectus').pdf_pages);

const mish=progress.rows.find(r=>r.bse_scrip_code==='544015');
assert.equal(mish.disposition,'awaiting_review');
assert.equal(mish.stable_id,null);
assert.equal(mish.manifest,null);
assert.equal(mish.release_pr,null);
assert.equal(mish.live_receipt,null);

console.log(JSON.stringify({mish_bse_prospectus_rejection_tests:{
  rejected_wrong_issuer:true,
  false_positive_search_context_retained:true,
  no_field_approval:true,
  mish_queue_unchanged:true,
}}));
