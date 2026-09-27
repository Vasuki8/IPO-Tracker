import assert from "node:assert/strict";
import fs from "node:fs";
import {spawnSync} from "node:child_process";
import {apply,context,expected,loadRecovery,FIELDS,REVIEW,RECEIPT} from "./apply-reviewed-bse-2022-tmb-dcx.mjs";
import {sha256} from "./verify-bse-listing-candidates.mjs";
import {verifyTmbDcxPublication} from "./verify-bse-2022-tmb-dcx.mjs";

const ctx=context(),rows=expected(ctx),current=loadRecovery(),before=structuredClone(current);
for(const m of Object.values(before))m.records=m.records.filter(r=>!rows.some(x=>x.id===r.id));
const now=new Date().toISOString(),first=apply(before,ctx,now);
assert.deepEqual(first.stats,{records:2,added:2,skipped:0,changed:true});
assert.deepEqual(apply(first.recovery,ctx,now).stats,{records:2,added:0,skipped:2,changed:false});
const t=rows.find(r=>r.id==="tamilnad-mercantile-bank-limited"),d=rows.find(r=>r.id==="dcx-systems-limited");
assert.deepEqual([t.board,t.bse_scrip_code,t.price_band.value,t.issue_price.value,t.issue_size_inr.value,t.market_lot.value,t.minimum_bid_quantity.value,t.open_date.value,t.close_date.value,t.listing_date.value],[null,null,{min:500,max:525},510,8078400000,1,28,"2022-09-05","2022-09-07","2022-09-15"]);
assert.deepEqual([d.board,d.bse_scrip_code,d.price_band.value,d.issue_price.value,d.issue_size_inr.value,d.market_lot.value,d.minimum_bid_quantity.value,d.open_date.value,d.close_date.value,d.listing_date.value],[null,null,{min:197,max:207},207,5000000000,1,72,"2022-10-31","2022-11-02","2022-11-11"]);
assert.equal(t.issue_price.source.document_sha256,"e66c2d0fa884a262b6755ad8d9a986ffe8df82fe36cc05f704616d5fb6c76dc9");
assert.equal(t.listing_date.source.document_sha256,"5509123f25a4403576f24c05b35b439b42435b0d4c6530e7e7018462b78aed22");
assert.equal(d.issue_price.source.document_sha256,"b7e1ecf1d751f396deb31d8b7cfcc2590115316ca3fe4958530ff95caece685e");
assert.equal(d.listing_date.source.document_sha256,"1739111ca1b8c3eccf3047bba833c643e2e2fc0c26045a6a3bd4151694de0a9f");
assert.deepEqual([t.price_band.page,t.market_lot.page,t.minimum_bid_quantity.page,t.listing_date.page],[9,321,327,381]);
assert.deepEqual([d.price_band.page,d.market_lot.page,d.minimum_bid_quantity.page,d.listing_date.page],[355,356,362,418]);
for(const r of rows){assert.equal(r.market_lot.value,1);assert.notEqual(r.minimum_bid_quantity.value,r.market_lot.value);assert.equal(r.isin,null);assert.equal(r.nse_symbol,null);assert.equal(r.bse_scrip_code,null)}
for(const model of rows){const collision=structuredClone(before);collision["2023"].records.push({id:"other",issuer_name:"Other",bse_scrip_code:model.bse_2022_tmb_dcx_import.discovery_bse_scrip_code});assert.throws(()=>apply(collision,ctx,now),/identity_collision/)}
const altered=structuredClone(first.recovery);altered["2022"].records.find(r=>r.id===t.id).minimum_bid_quantity.value++;assert.throws(()=>apply(altered,ctx,now),/changed_import_fact/);
const badProjection=structuredClone(ctx);badProjection.sources.get("tmb_prospectus").projection.issue_price=511;assert.throws(()=>expected(badProjection),/projection_mismatch/);
assert.equal(rows.reduce((n,r)=>n+FIELDS.filter(k=>r[k].value!==null).length,0),16);
assert.equal(ctx.manifest.review_sha256,sha256(fs.readFileSync(REVIEW)));assert.equal(ctx.manifest.receipt_sha256,sha256(fs.readFileSync(RECEIPT)));
const bytes=fs.readFileSync("data/recovery/2022/nse-issue-information.json");
const cli=spawnSync(process.execPath,["scripts/apply-reviewed-bse-2022-tmb-dcx.mjs","--check"],{encoding:"utf8"});
assert.equal(cli.status,0,cli.stderr);assert.deepEqual(fs.readFileSync("data/recovery/2022/nse-issue-information.json"),bytes);
const published=JSON.parse(fs.readFileSync("data/ipos.json","utf8"));
let fetchCalls=0;
const fakeFetch=async()=>{fetchCalls++;return new Response(JSON.stringify(published),{status:200,headers:{"content-type":"application/json"}})};
const live=await verifyTmbDcxPublication({fetchImpl:fakeFetch});
assert.equal(fetchCalls,1);assert.equal(live.ok,true);assert.deepEqual(live.records,["tamilnad-mercantile-bank-limited","dcx-systems-limited"]);
console.log(JSON.stringify({bse_2022_tmb_dcx_tests:{records:2,verified_fields:16,field_page_evidence:true,source_hashes:true,lot_vs_min_bid:true,null_preserving:true,rerun_safe:true,cross_year_collision:true,changed_fact_rejected:true,manifest_content_binding:true,read_only_check:true,live_fetch_contract:true}}));
