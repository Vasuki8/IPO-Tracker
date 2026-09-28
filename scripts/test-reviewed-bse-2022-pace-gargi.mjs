import assert from "node:assert/strict";
import fs from "node:fs";
import {spawnSync} from "node:child_process";
import {apply,context,expected,loadRecovery,FIELDS,REVIEW,RECEIPT} from "./apply-reviewed-bse-2022-pace-gargi.mjs";
import {sha256} from "./verify-bse-listing-candidates.mjs";

const ctx=context(),rows=expected(ctx),current=loadRecovery(),before=structuredClone(current);
for(const m of Object.values(before))m.records=m.records.filter(r=>!rows.some(x=>x.id===r.id));
const now=new Date().toISOString(),first=apply(before,ctx,now);
assert.deepEqual(first.stats,{records:2,added:2,skipped:0,changed:true});
assert.deepEqual(apply(first.recovery,ctx,now).stats,{records:2,added:0,skipped:2,changed:false});

const p=rows.find(r=>r.id==="pace-e-commerce-ventures-limited");
const g=rows.find(r=>r.id==="pngs-gargi-fashion-jewellery-limited");
assert.deepEqual(
 [p.board,p.bse_scrip_code,p.price_band.value,p.issue_price.value,p.issue_size_inr.value,p.market_lot.value,p.minimum_bid_quantity.value,p.open_date.value,p.close_date.value,p.listing_date.value],
 ["SME",null,null,103,665339000,1200,1200,"2022-09-29","2022-10-04","2022-10-20"]
);
assert.deepEqual(
 [g.board,g.bse_scrip_code,g.price_band.value,g.issue_price.value,g.issue_size_inr.value,g.market_lot.value,g.minimum_bid_quantity.value,g.open_date.value,g.close_date.value,g.listing_date.value],
 ["SME",null,null,30,78000000,4000,4000,"2022-12-08","2022-12-13","2022-12-20"]
);
assert.deepEqual([p.board_evidence[0].page,p.issue_price.page,p.issue_size_inr.page,p.market_lot.page,p.minimum_bid_quantity.page,p.listing_date.page],[1,2,2,165,181,158]);
assert.deepEqual([g.board_evidence[0].page,g.issue_price.page,g.issue_size_inr.page,g.market_lot.page,g.minimum_bid_quantity.page,g.listing_date.page],[1,8,1,220,233,65]);
assert.equal(p.issue_price.source.document_sha256,"879e6677c687005aad74a50de944a4ea8a9df9affc20dd11cbdf05876b23c9bc");
assert.equal(p.listing_date.source.document_sha256,"045b0b8b2c10c5662d41a68dcd740593d9fba44879e866d556d5f528dbacd826");
assert.equal(g.issue_price.source.document_sha256,"b1565f0f1e7e50a8737c0b6b685be515bba464f553d7ac2a084885a9a0367c9c");
assert.equal(g.listing_date.source.document_sha256,"4125c44ef599db2df7407c16887f2fd64ff3cc7a279224670272b855ba6099e9");

for(const row of rows){
 assert.equal(row.price_band.status,"missing");
 assert.equal(row.isin,null);assert.equal(row.nse_symbol,null);assert.equal(row.bse_scrip_code,null);
 assert.notStrictEqual(row.market_lot,row.minimum_bid_quantity);
 assert.equal(row.market_lot.value,row.minimum_bid_quantity.value);
}
for(const model of rows){
 const collision=structuredClone(before);
 collision["2023"].records.push({id:"other",issuer_name:"Other",bse_scrip_code:model.bse_2022_pace_gargi_import.discovery_bse_scrip_code});
 assert.throws(()=>apply(collision,ctx,now),/identity_collision/);
}
const altered=structuredClone(first.recovery);
altered["2022"].records.find(r=>r.id===p.id).minimum_bid_quantity.value++;
assert.throws(()=>apply(altered,ctx,now),/changed_import_fact/);

const badCtx=structuredClone(ctx);
badCtx.sources.get("pace_prospectus").projection.issue_price=104;
assert.throws(()=>expected(badCtx),/projection_mismatch/);

assert.equal(rows.reduce((n,r)=>n+FIELDS.filter(k=>r[k].value!==null).length,0),14);
assert.equal(ctx.manifest.review_sha256,sha256(fs.readFileSync(REVIEW)));
assert.equal(ctx.manifest.receipt_sha256,sha256(fs.readFileSync(RECEIPT)));

const bytes=fs.readFileSync("data/recovery/2022/nse-issue-information.json");
const cli=spawnSync(process.execPath,["scripts/apply-reviewed-bse-2022-pace-gargi.mjs","--check"],{encoding:"utf8"});
assert.equal(cli.status,0,cli.stderr);
assert.deepEqual(fs.readFileSync("data/recovery/2022/nse-issue-information.json"),bytes);

console.log(JSON.stringify({bse_2022_pace_gargi_tests:{
 records:2,verified_fields:14,field_page_evidence:true,source_hashes:true,fixed_price_band_missing:true,
 lot_and_min_bid_distinct_fields:true,null_preserving:true,rerun_safe:true,cross_year_collision:true,
 changed_fact_rejected:true,manifest_content_binding:true,read_only_check:true
}}));
