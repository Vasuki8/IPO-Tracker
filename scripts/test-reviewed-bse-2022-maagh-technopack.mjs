import assert from "node:assert/strict";
import fs from "node:fs";
import {spawnSync} from "node:child_process";
import {apply,context,expected,loadRecovery,FIELDS,REVIEW,RECEIPT} from "./apply-reviewed-bse-2022-maagh-technopack.mjs";
import {sha256} from "./verify-bse-listing-candidates.mjs";

const ctx=context(),rows=expected(ctx),current=loadRecovery(),before=structuredClone(current);
for(const m of Object.values(before))m.records=m.records.filter(r=>!rows.some(x=>x.id===r.id));
const now=new Date().toISOString(),first=apply(before,ctx,now);
assert.deepEqual(first.stats,{records:2,added:2,skipped:0,changed:true});
assert.deepEqual(apply(first.recovery,ctx,now).stats,{records:2,added:0,skipped:2,changed:false});
const m=rows.find(r=>r.id==="maagh-advertising-and-marketing-services-limited");
const t=rows.find(r=>r.id==="technopack-polymers-limited");
assert.deepEqual([m.board,m.bse_scrip_code,m.price_band.value,m.issue_price.value,m.issue_size_inr.value,m.market_lot.value,m.minimum_bid_quantity.value,m.open_date.value,m.close_date.value,m.listing_date.value],["SME",null,null,60,91200000,2000,2000,"2022-09-26","2022-09-29","2022-10-13"]);
assert.deepEqual([t.board,t.bse_scrip_code,t.price_band.value,t.issue_price.value,t.issue_size_inr.value,t.market_lot.value,t.minimum_bid_quantity.value,t.open_date.value,t.close_date.value,t.listing_date.value],["SME",null,null,55,78650000,2000,2000,"2022-11-02","2022-11-07","2022-11-16"]);
assert.deepEqual([m.issue_price.page,m.market_lot.page,m.minimum_bid_quantity.page,m.listing_date.page],[1,144,156,145]);
assert.deepEqual([t.issue_price.page,t.market_lot.page,t.minimum_bid_quantity.page,t.listing_date.page],[7,7,7,29]);
assert.equal(m.issue_price.source.document_sha256,"f2155b92eabfaab17473d57f382402be38b8b2e4b95c6a14a548be0a86877bcb");
assert.equal(m.listing_date.source.document_sha256,"8dc73673eb409a0604e22c5a250c9b9f5b72372378a74faffdd272205822d39d");
assert.equal(t.issue_price.source.document_sha256,"69097ff3ab7c76813426ac307d2e3efb06757f30aa1bfccc57c1691dda4f9b98");
assert.equal(t.listing_date.source.document_sha256,"8dfb5c4bf9ef6a61dd48ff407f4ebc912173cc0e25a2b8aa3b0a6b2977a26924");
for(const row of rows){assert.equal(row.price_band.status,"missing");assert.equal(row.isin,null);assert.equal(row.nse_symbol,null);assert.equal(row.bse_scrip_code,null);assert.notStrictEqual(row.market_lot,row.minimum_bid_quantity);assert.equal(row.market_lot.value,row.minimum_bid_quantity.value)}
for(const model of rows){const collision=structuredClone(before);collision["2023"].records.push({id:"other",issuer_name:"Other",bse_scrip_code:model.bse_2022_maagh_technopack_import.discovery_bse_scrip_code});assert.throws(()=>apply(collision,ctx,now),/identity_collision/)}
const altered=structuredClone(first.recovery);altered["2022"].records.find(r=>r.id===m.id).minimum_bid_quantity.value++;assert.throws(()=>apply(altered,ctx,now),/changed_import_fact/);
const badCtx=structuredClone(ctx);badCtx.sources.get("maagh_prospectus").projection.issue_price=61;assert.throws(()=>expected(badCtx),/projection_mismatch/);
assert.equal(rows.reduce((n,r)=>n+FIELDS.filter(k=>r[k].value!==null).length,0),14);
assert.equal(ctx.manifest.review_sha256,sha256(fs.readFileSync(REVIEW)));assert.equal(ctx.manifest.receipt_sha256,sha256(fs.readFileSync(RECEIPT)));
const bytes=fs.readFileSync("data/recovery/2022/nse-issue-information.json");
const cli=spawnSync(process.execPath,["scripts/apply-reviewed-bse-2022-maagh-technopack.mjs","--check"],{encoding:"utf8"});
assert.equal(cli.status,0,cli.stderr);assert.deepEqual(fs.readFileSync("data/recovery/2022/nse-issue-information.json"),bytes);
console.log(JSON.stringify({bse_2022_maagh_technopack_tests:{records:2,verified_fields:14,field_page_evidence:true,source_hashes:true,fixed_price_band_missing:true,lot_and_min_bid_distinct_fields:true,null_preserving:true,rerun_safe:true,cross_year_collision:true,changed_fact_rejected:true,manifest_content_binding:true,read_only_check:true}}));
