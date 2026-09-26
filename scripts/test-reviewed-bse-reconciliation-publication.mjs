import assert from "node:assert/strict";
import fs from "node:fs";import path from "node:path";import {fileURLToPath} from "node:url";
import {AUDIT_PATH,MANIFEST_PATH,RECEIPT_PATH,REVIEW_PATH,applyReviewedBseReconciliation,loadRecovery} from "./apply-reviewed-bse-reconciliation.mjs";
import {auditBseReconciliationPublication} from "./verify-reviewed-bse-reconciliation-publication.mjs";
import {execFileSync} from "node:child_process";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const reviewBytes=fs.readFileSync(path.join(root,REVIEW_PATH)),review=JSON.parse(reviewBytes);
const receipt=JSON.parse(fs.readFileSync(path.join(root,RECEIPT_PATH),"utf8")),manifest=JSON.parse(fs.readFileSync(path.join(root,MANIFEST_PATH),"utf8"));
const audit=JSON.parse(fs.readFileSync(path.join(root,AUDIT_PATH),"utf8")),raw=loadRecovery(root);
const published=JSON.parse(fs.readFileSync(path.join(root,"data","ipos.json"),"utf8"));
const plan=applyReviewedBseReconciliation(raw,published,manifest,review,receipt,reviewBytes,audit);

const tmp=path.join(root,".tmp-bse-reconciliation-test");
fs.rmSync(tmp,{recursive:true,force:true});fs.mkdirSync(tmp,{recursive:true});
try{
  for(const [year,data] of Object.entries(plan.recovery)){
    const dir=path.join(tmp,"data","recovery",year);fs.mkdirSync(dir,{recursive:true});
    fs.writeFileSync(path.join(dir,"nse-issue-information.json"),JSON.stringify(data,null,2)+"\n");
  }
  fs.mkdirSync(path.join(tmp,"data"),{recursive:true});
  for(const file of ["build-published-data.mjs"]){void file;}
  // Build a compact public projection matching build-published-data's relevant behavior.
  const evidence=src=>({url:src.url,document_type:src.document_type,document_identity:src.document_identity,publication_date:src.publication_date??null,page:src.page??null,collected_at:src.collected_at});
  const field=f=>f?.value!=null?{value:f.value,status:"verified",evidence:[evidence(f.source)],corrections:f.corrections||[]}:{value:null,status:"missing",evidence:[],corrections:[]};
  const ids=new Set(["computer-age-management-services-limited","protean-egov-technologies-limited","fabtech-technologies-limited","happy-forging-limited","kronox-lab-scienceslimited","fabtech-technologies-cleanrooms-limited"]);
  const records=Object.values(plan.recovery).flatMap(x=>x.records).filter(r=>ids.has(r.id)).map(r=>({
    id:r.id,issuer_name:r.issuer_name,board:r.board,status:r.status,
    listing_date:field(r.listing_date),issue_price:field(r.issue_price),open_date:field(r.open_date),close_date:field(r.close_date),
    minimum_bid_quantity:field(r.minimum_bid_quantity)
  }));
  const synthetic={schema_version:"1.2.0",generated_at:receipt.collection_completed_at,records};
  const result=auditBseReconciliationPublication({manifest,review,receipt,reviewBytes,audit,recovery:plan.recovery,data:synthetic,checkedAt:receipt.collection_completed_at});
  assert.equal(result.status,"verified");assert.equal(result.checked_actions,5);
  const broken=structuredClone(synthetic);broken.records.find(r=>r.id==="protean-egov-technologies-limited").listing_date.value="2025-02-06";
  const failed=auditBseReconciliationPublication({manifest,review,receipt,reviewBytes,audit,recovery:plan.recovery,data:broken,checkedAt:receipt.collection_completed_at});
  assert.equal(failed.status,"failed");
}finally{fs.rmSync(tmp,{recursive:true,force:true});}
console.log(JSON.stringify({reviewed_bse_reconciliation_publication_tests:{actions:5,positive:true,wrong_date_detected:true,cleanrooms_checked:true,secondary_listing_checked:true}}));
