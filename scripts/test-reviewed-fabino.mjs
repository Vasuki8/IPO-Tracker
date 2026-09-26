import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {MANIFEST_PATH,RECEIPT_PATH,REVIEW_PATH,applyReviewedFabino,fabinoRecoveryRecord,loadRecovery,validateFabinoImportManifest} from "./apply-reviewed-fabino.mjs";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const reviewBytes=fs.readFileSync(path.join(root,REVIEW_PATH));
const review=JSON.parse(reviewBytes),receipt=JSON.parse(fs.readFileSync(path.join(root,RECEIPT_PATH),"utf8"));
const manifest=JSON.parse(fs.readFileSync(path.join(root,MANIFEST_PATH),"utf8"));
validateFabinoImportManifest(manifest,review,receipt,reviewBytes);
const candidate=fabinoRecoveryRecord(manifest,review,receipt,reviewBytes);
assert.equal(candidate.issuer_name,"Fabino Life Sciences Limited");
assert.equal(candidate.bse_scrip_code,"543444");
assert.equal(candidate.isin,"INE0DRT01018");
assert.equal(candidate.listing_date.value,"2022-01-13");
assert.equal(candidate.listing_date.corrections.length,1);
assert.equal(candidate.listing_date.corrections[0].previous_value,"2021-01-13");
assert.match(candidate.listing_date.corrections[0].previous_source_value,/January 13, 2021/);
assert.equal(candidate.issue_price.value,36);
assert.equal(candidate.market_lot.value,3000);
assert.equal(candidate.open_date.value,"2021-12-31");
assert.equal(candidate.close_date.value,"2022-01-05");
assert.equal(candidate.fabino_listing_year_correction.conflict_preserved,true);

const raw=loadRecovery(root),published=JSON.parse(fs.readFileSync(path.join(root,"data","ipos.json"),"utf8"));
for(const data of Object.values(raw))data.records=data.records.filter(r=>r.id!==candidate.id&&String(r.bse_scrip_code||"")!=="543444"&&String(r.isin||"")!=="INE0DRT01018");
const prior={...published,records:published.records.filter(r=>r.id!==candidate.id&&String(r.issuer_name||"").toLowerCase()!=="fabino life sciences limited")};
const snapshot=JSON.stringify(raw);
const plan=applyReviewedFabino(raw,prior,manifest,review,receipt,reviewBytes);
assert.deepEqual(plan.stats,{added:1,already_present:0});
assert.deepEqual(plan.changed_years,["2022"]);
assert.equal(JSON.stringify(raw),snapshot);
assert.ok(plan.recovery["2022"].records.some(r=>r.id===candidate.id));
assert.equal(Object.values(plan.recovery).flatMap(x=>x.records).filter(r=>r.id===candidate.id).length,1);
const second=applyReviewedFabino(plan.recovery,prior,manifest,review,receipt,reviewBytes);
assert.deepEqual(second.stats,{added:0,already_present:1});
assert.deepEqual(second.recovery,plan.recovery);

const conflict=structuredClone(raw);
conflict["2021"].records.push({...candidate,listing_date:{...candidate.listing_date,value:"2021-01-13"}});
assert.throws(()=>applyReviewedFabino(conflict,prior,manifest,review,receipt,reviewBytes),/collision|conflict/);

const badManifest=structuredClone(manifest);
badManifest.fields.listing_date.source="bse_listing_notice";
assert.throws(()=>validateFabinoImportManifest(badManifest,review,receipt,reviewBytes),/correction_policy|projection/);

console.log(JSON.stringify({reviewed_fabino_tests:{added_in_rehearsal:1,target_year:2022,idempotent:true,wrong_year_collision_blocked:true,source_conflict_preserved:true,generic_bse_parser_unchanged:true}}));
