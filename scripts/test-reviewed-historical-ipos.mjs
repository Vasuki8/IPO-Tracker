import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  MANIFEST_PATH, REVIEW_PATH, RECEIPT_PATH,
  applyReviewedHistoricalIpos,
  historicalRecoveryRecord,
  loadRecovery,
  validateHistoricalImportManifest
} from "./apply-reviewed-historical-ipos.mjs";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const reviewBytes=fs.readFileSync(path.join(root,REVIEW_PATH));
const review=JSON.parse(reviewBytes);
const receipt=JSON.parse(fs.readFileSync(path.join(root,RECEIPT_PATH),"utf8"));
const manifest=JSON.parse(fs.readFileSync(path.join(root,MANIFEST_PATH),"utf8"));
const checked=validateHistoricalImportManifest(manifest,review,receipt,reviewBytes);
assert.equal(checked.length,9);
assert.deepEqual(checked.map(x=>x.hist.nse_symbol),["MWL","QMSMEDI","VIVIANA","ANNAPURNA","SWARAJ","VIESL","AVPINFRA","DOLLEX","DCCL"]);

const raw=loadRecovery(root);
const published=JSON.parse(fs.readFileSync(path.join(root,"data","ipos.json"),"utf8"));
const identities=checked.map(item=>historicalRecoveryRecord(item,manifest,receipt));
const ids=new Set(identities.map(r=>r.id));
const names=new Set(identities.map(r=>r.issuer_name.toLowerCase()));
for(const data of Object.values(raw)){
  data.records=data.records.filter(r=>!ids.has(r.id)&&!names.has(String(r.issuer_name||"").toLowerCase()));
}
const prior={...published,records:published.records.filter(r=>!ids.has(r.id)&&!names.has(String(r.issuer_name||"").toLowerCase()))};
const snapshot=JSON.stringify(raw), publishedSnapshot=JSON.stringify(published);
const plan=applyReviewedHistoricalIpos(raw,prior,manifest,review,receipt,reviewBytes);
assert.deepEqual(plan.stats,{added:9,already_present:0,already_present_external:0});
assert.deepEqual(plan.changed_years,["2022","2024","2025"]);
assert.equal(JSON.stringify(raw),snapshot,"planning must not mutate recovery input");
assert.equal(JSON.stringify(published),publishedSnapshot,"planning must not mutate published input");

const bySymbol=new Map(Object.values(plan.recovery).flatMap(x=>x.records).filter(r=>r.historical_verified_ipo_review?.manifest===MANIFEST_PATH).map(r=>[r.nse_symbol,r]));
assert.equal(bySymbol.size,9);
assert.equal(bySymbol.get("MWL").listing_date.value,"2022-07-11");
assert.equal(bySymbol.get("QMSMEDI").issue_price.value,121);
assert.equal(bySymbol.get("AVPINFRA").minimum_bid_quantity.value,1600);
assert.equal(bySymbol.get("DOLLEX").market_lot.value,4000);
assert.equal(bySymbol.get("VIESL").open_date,undefined,"issuer-site offer dates are deliberately not imported");
assert.equal(bySymbol.get("SWARAJ").issue_price,undefined,"archives.nseindia.com is not added to the publication allowlist");

const second=applyReviewedHistoricalIpos(plan.recovery,prior,manifest,review,receipt,reviewBytes);
assert.deepEqual(second.stats,{added:0,already_present:9,already_present_external:0});
assert.deepEqual(second.recovery,plan.recovery);

const collision=structuredClone(raw);
collision["2020"].records.push({id:"collision",issuer_name:"Different Limited",nse_symbol:"OTHER",isin:bySymbol.get("MWL").isin});
assert.throws(()=>applyReviewedHistoricalIpos(collision,prior,manifest,review,receipt,reviewBytes),/collision|conflict/);

const badManifest=structuredClone(manifest);
badManifest.entries[0].field_sources.issue_price="mwl_prospectus";
assert.throws(()=>validateHistoricalImportManifest(badManifest,review,receipt,reviewBytes),/projection_mismatch/);

console.log(JSON.stringify({reviewed_historical_ipo_tests:{
  issuers:9,
  added_in_rehearsal:9,
  years:["2022","2024","2025"],
  idempotent:true,
  cross_year_collision_blocked:true,
  excluded_2026_events_not_imported:true,
  publication_host_boundary_preserved:true
}}));
