import assert from "node:assert/strict";
import fs from "node:fs";
import {spawnSync} from "node:child_process";
import {apply,context,expected,loadRecovery,FIELDS,REVIEW,RECEIPT} from "./apply-reviewed-bse-2022-eighty-virtuoso.mjs";
import {sha256} from "./verify-bse-listing-candidates.mjs";

const ctx=context(),rows=expected(ctx),current=loadRecovery(),before=structuredClone(current);
for(const m of Object.values(before))m.records=m.records.filter(r=>!rows.some(x=>x.id===r.id));
const now=new Date().toISOString(),first=apply(before,ctx,now);
assert.deepEqual(first.stats,{records:2,added:2,skipped:0,changed:true});
assert.deepEqual(apply(first.recovery,ctx,now).stats,{records:2,added:0,skipped:2,changed:false});

const e=rows.find(r=>r.id==="eighty-jewellers-limited");
const v=rows.find(r=>r.id==="virtuoso-optoelectronics-limited");
assert.deepEqual(
 [e.board,e.bse_scrip_code,e.price_band.value,e.issue_price.value,e.issue_size_inr.value,e.market_lot.value,e.minimum_bid_quantity.value,e.open_date.value,e.close_date.value,e.listing_date.value],
 ["SME",null,null,41,110700000,3000,3000,"2022-03-31","2022-04-05","2022-04-13"]
);
assert.deepEqual(
 [v.board,v.bse_scrip_code,v.price_band.value,v.issue_price.value,v.issue_size_inr.value,v.market_lot.value,v.minimum_bid_quantity.value,v.open_date.value,v.close_date.value,v.listing_date.value],
 ["SME",null,null,56,302400000,2000,2000,"2022-09-02","2022-09-07","2022-09-15"]
);
assert.deepEqual([e.board_evidence[0].page,e.issue_price.page,e.market_lot.page,e.minimum_bid_quantity.page,e.listing_date.page],[1,2,184,184,6]);
assert.deepEqual([v.board_evidence[0].page,v.issue_price.page,v.market_lot.page,v.minimum_bid_quantity.page,v.listing_date.page],[1,7,269,269,70]);
assert.equal(e.issue_price.source.document_sha256,"27a2b38213630a159bcc821ac42bb275f07f24b99f7ec060de46f71a423ddb55");
assert.equal(e.listing_date.source.document_sha256,"71a2a51585a420a15238f11e0ddca0617dae6196b71705778ea7f64661cff70d");
assert.equal(v.issue_price.source.document_sha256,"dbb404c0e2100e6d197aabcf7a9b305d3bc353c9a6566e77acc3e9f7cdab3ace");
assert.equal(v.listing_date.source.document_sha256,"9f39077a6cf2d035ee79f4a1cb3288266a0ec2b7bf3f6474d199425e221935c6");

for(const row of rows){
 assert.equal(row.price_band.status,"missing");
 assert.equal(row.isin,null);assert.equal(row.nse_symbol,null);assert.equal(row.bse_scrip_code,null);
 assert.notStrictEqual(row.market_lot,row.minimum_bid_quantity);
 assert.equal(row.market_lot.value,row.minimum_bid_quantity.value);
}
for(const model of rows){
 const collision=structuredClone(before);
 collision["2023"].records.push({id:"other",issuer_name:"Other",bse_scrip_code:model.bse_2022_eighty_virtuoso_import.discovery_bse_scrip_code});
 assert.throws(()=>apply(collision,ctx,now),/identity_collision/);
}
const altered=structuredClone(first.recovery);
altered["2022"].records.find(r=>r.id===e.id).minimum_bid_quantity.value++;
assert.throws(()=>apply(altered,ctx,now),/changed_import_fact/);

const badCtx=structuredClone(ctx);
badCtx.sources.get("eighty_prospectus").projection.issue_price=42;
assert.throws(()=>expected(badCtx),/projection_mismatch/);

assert.equal(rows.reduce((n,r)=>n+FIELDS.filter(k=>r[k].value!==null).length,0),14);
assert.equal(ctx.manifest.review_sha256,sha256(fs.readFileSync(REVIEW)));
assert.equal(ctx.manifest.receipt_sha256,sha256(fs.readFileSync(RECEIPT)));

const bytes=fs.readFileSync("data/recovery/2022/nse-issue-information.json");
const cli=spawnSync(process.execPath,["scripts/apply-reviewed-bse-2022-eighty-virtuoso.mjs","--check"],{encoding:"utf8"});
assert.equal(cli.status,0,cli.stderr);
assert.deepEqual(fs.readFileSync("data/recovery/2022/nse-issue-information.json"),bytes);

console.log(JSON.stringify({bse_2022_eighty_virtuoso_tests:{
 records:2,verified_fields:14,field_page_evidence:true,source_hashes:true,fixed_price_band_missing:true,
 lot_and_min_bid_distinct_fields:true,null_preserving:true,rerun_safe:true,cross_year_collision:true,
 changed_fact_rejected:true,manifest_content_binding:true,read_only_check:true
}}));
