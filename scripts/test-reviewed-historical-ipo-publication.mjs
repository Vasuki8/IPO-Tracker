import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  MANIFEST_PATH,REVIEW_PATH,RECEIPT_PATH,
  applyReviewedHistoricalIpos,loadRecovery
} from "./apply-reviewed-historical-ipos.mjs";
import { auditHistoricalPublication } from "./verify-reviewed-historical-ipo-publication.mjs";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const reviewBytes=fs.readFileSync(path.join(root,REVIEW_PATH));
const review=JSON.parse(reviewBytes);
const receipt=JSON.parse(fs.readFileSync(path.join(root,RECEIPT_PATH),"utf8"));
const manifest=JSON.parse(fs.readFileSync(path.join(root,MANIFEST_PATH),"utf8"));
const raw=loadRecovery(root);
const published=JSON.parse(fs.readFileSync(path.join(root,"data","ipos.json"),"utf8"));

const names=new Set(review.decisions.map(d=>d.issuer_name.toLowerCase()));
for(const data of Object.values(raw))data.records=data.records.filter(r=>!names.has(String(r.issuer_name||"").toLowerCase()));
const prior={...published,records:published.records.filter(r=>!names.has(String(r.issuer_name||"").toLowerCase()))};
const plan=applyReviewedHistoricalIpos(raw,prior,manifest,review,receipt,reviewBytes);

function publicFromRecovery(recovery){
  const records=[];
  for(const data of Object.values(recovery)){
    for(const r of data.records){
      if(!r.historical_verified_ipo_review)continue;
      const evidence=source=>({url:source.url,document_type:source.document_type,document_identity:source.document_identity,
        publication_date:source.publication_date??null,page:source.page??null,collected_at:source.collected_at});
      const field=f=>r[f]?{value:r[f].value,status:"verified",evidence:[evidence(r[f].source)],corrections:[]}:{value:null,status:"missing",evidence:[],corrections:[]};
      records.push({id:r.id,issuer_name:r.issuer_name,board:r.board,status:r.status,
        listing_date:field("listing_date"),open_date:field("open_date"),close_date:field("close_date"),issue_price:field("issue_price"),
        market_lot:field("market_lot"),minimum_bid_quantity:field("minimum_bid_quantity"),
        minimum_application_amount_inr:{value:null,status:"missing",evidence:[],corrections:[]}});
    }
  }
  return {schema_version:"1.2.0",generated_at:receipt.collection_completed_at,records};
}
const synthetic=publicFromRecovery(plan.recovery);
const audit=auditHistoricalPublication({manifest,review,receipt,reviewBytes,recovery:plan.recovery,data:synthetic,checkedAt:receipt.collection_completed_at});
assert.equal(audit.status,"verified");
assert.equal(audit.checked_issuers,9);
const broken=structuredClone(synthetic);
broken.records.find(r=>r.issuer_name==="Mangalam Worldwide Limited").listing_date.value="2022-07-12";
const failed=auditHistoricalPublication({manifest,review,receipt,reviewBytes,recovery:plan.recovery,data:broken,checkedAt:receipt.collection_completed_at});
assert.equal(failed.status,"failed");
assert.ok(failed.results.find(r=>r.symbol==="MWL").errors.includes("listing_date"));
console.log(JSON.stringify({reviewed_historical_publication_tests:{issuers:9,positive:true,mutation_detected:true}}));
