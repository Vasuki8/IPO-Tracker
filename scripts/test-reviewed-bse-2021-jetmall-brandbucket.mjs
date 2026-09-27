import assert from "node:assert/strict";
import fs from "node:fs";
import {spawnSync} from "node:child_process";
import {apply,context,expected,loadRecovery,FIELDS} from "./apply-reviewed-bse-2021-jetmall-brandbucket.mjs";

const ctx=context(),rows=expected(ctx),current=loadRecovery(),before=structuredClone(current);
for(const m of Object.values(before))m.records=m.records.filter(r=>!rows.some(x=>x.id===r.id));
const now=new Date().toISOString(),first=apply(before,ctx,now);
assert.deepEqual(first.stats,{records:2,added:2,skipped:0,changed:true});
assert.deepEqual(apply(first.recovery,ctx,now).stats,{records:2,added:0,skipped:2,changed:false});
const j=rows.find(r=>r.id==="jetmall-spices-and-masala-limited"),b=rows.find(r=>r.id==="brandbucket-media-and-technology-limited");
assert.deepEqual([j.board,j.bse_scrip_code,j.listing_date.value,j.issue_price.value,j.issue_size_inr.value,j.market_lot.value,j.minimum_bid_quantity.value,j.open_date.value,j.close_date.value],["SME",null,"2021-04-19",20,49800000,6000,6000,"2021-03-31","2021-04-07"]);
assert.deepEqual([b.board,b.bse_scrip_code,b.listing_date.value,b.issue_price.value,b.issue_size_inr.value,b.market_lot.value,b.minimum_bid_quantity.value,b.open_date.value,b.close_date.value],["SME",null,"2021-12-31",55,82500000,2000,2000,"2021-12-20","2021-12-23"]);
assert.equal(j.issue_price.source.document_sha256,"659c1d64fc45d8309ed25d0662440e69d2bf3c4db1de8173b73e149034367dca");
assert.equal(j.listing_date.source.document_sha256,"9bd3b574f12daaf6550932efd84bf005ded2fb664af4d495831b878eab5f2bdf");
assert.equal(b.issue_price.source.document_sha256,"1267b7e0e6f7df853cc58b411c0eeb53ee8f13ec334061c0532059b21b929925");
assert.equal(b.listing_date.source.document_sha256,"2b25b9178aa19776d8b812e53e67a715a417ca179d50a1a4f0f83a1f472dc9ea");
for(const row of rows){assert.equal(row.price_band.value,null);assert.equal(row.isin,null);assert.equal(row.nse_symbol,null);assert.equal(row.market_lot.value,row.minimum_bid_quantity.value);assert.notEqual(row.market_lot.source,null);assert.notEqual(row.minimum_bid_quantity.source,null)}
for(const model of rows){const collision=structuredClone(before);collision["2022"].records.push({id:"other",issuer_name:"Other",bse_scrip_code:model.bse_2021_jetmall_brandbucket_import.discovery_bse_scrip_code});assert.throws(()=>apply(collision,ctx,now),/identity_collision/)}
const altered=structuredClone(first.recovery);altered["2021"].records.find(r=>r.id===j.id).minimum_bid_quantity.value++;assert.throws(()=>apply(altered,ctx,now),/changed_import_fact/);
const badCtx=structuredClone(ctx);badCtx.sources.get("jetmall_final").projection.issue_price=21;assert.throws(()=>expected(badCtx),/projection_mismatch/);
assert.equal(rows.reduce((n,r)=>n+FIELDS.filter(k=>r[k].value!==null).length,0),14);
const bytes=fs.readFileSync("data/recovery/2021/nse-issue-information.json");
const cli=spawnSync(process.execPath,["scripts/apply-reviewed-bse-2021-jetmall-brandbucket.mjs","--check"],{encoding:"utf8"});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(fs.readFileSync("data/recovery/2021/nse-issue-information.json"),bytes);
console.log(JSON.stringify({jetmall_brandbucket_tests:{records:2,verified_fields:16,null_preserving:true,lot_and_bid_separate_sources:true,rerun_safe:true,cross_year_collision:true,changed_fact_rejected:true,read_only_check:true}}));
