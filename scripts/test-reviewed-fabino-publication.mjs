import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {MANIFEST_PATH,RECEIPT_PATH,REVIEW_PATH,applyReviewedFabino,loadRecovery} from "./apply-reviewed-fabino.mjs";
import {auditFabinoPublication} from "./verify-reviewed-fabino-publication.mjs";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const reviewBytes=fs.readFileSync(path.join(root,REVIEW_PATH));
const review=JSON.parse(reviewBytes),receipt=JSON.parse(fs.readFileSync(path.join(root,RECEIPT_PATH),"utf8"));
const manifest=JSON.parse(fs.readFileSync(path.join(root,MANIFEST_PATH),"utf8"));
const raw=loadRecovery(root),published=JSON.parse(fs.readFileSync(path.join(root,"data","ipos.json"),"utf8"));
for(const data of Object.values(raw))data.records=data.records.filter(r=>r.id!=="fabino-life-sciences-limited"&&String(r.bse_scrip_code||"")!=="543444");
const prior={...published,records:published.records.filter(r=>r.id!=="fabino-life-sciences-limited")};
const plan=applyReviewedFabino(raw,prior,manifest,review,receipt,reviewBytes);
const r=plan.recovery["2022"].records.find(x=>x.id==="fabino-life-sciences-limited");
const ev=src=>({url:src.url,document_type:src.document_type,document_identity:src.document_identity,publication_date:src.publication_date??null,page:src.page??null,collected_at:src.collected_at});
const fld=name=>({value:r[name].value,status:"verified",evidence:[ev(r[name].source)],corrections:r[name].corrections||[]});
const synthetic={schema_version:"1.2.0",generated_at:receipt.collection_completed_at,records:[{
  id:r.id,issuer_name:r.issuer_name,board:r.board,status:r.status,
  open_date:fld("open_date"),close_date:fld("close_date"),issue_price:fld("issue_price"),market_lot:fld("market_lot"),listing_date:fld("listing_date"),
  minimum_application_amount_inr:{value:null,status:"missing",evidence:[],corrections:[]}
}]};
const audit=auditFabinoPublication({manifest,review,receipt,reviewBytes,recovery:plan.recovery,data:synthetic,checkedAt:receipt.collection_completed_at});
assert.equal(audit.status,"verified");
assert.equal(audit.listing_date,"2022-01-13");
const broken=structuredClone(synthetic);broken.records[0].listing_date.value="2021-01-13";
const failed=auditFabinoPublication({manifest,review,receipt,reviewBytes,recovery:plan.recovery,data:broken,checkedAt:receipt.collection_completed_at});
assert.equal(failed.status,"failed");
assert.ok(failed.errors.includes("listing_date"));
console.log(JSON.stringify({reviewed_fabino_publication_tests:{positive:true,wrong_year_detected:true,correction_history_checked:true}}));
