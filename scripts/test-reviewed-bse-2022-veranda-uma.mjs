import assert from "node:assert/strict";
import fs from "node:fs";
import {spawnSync} from "node:child_process";
import {apply,context,expected,loadRecovery,FIELDS} from "./apply-reviewed-bse-2022-veranda-uma.mjs";

const ctx=context(),rows=expected(ctx),current=loadRecovery(),before=structuredClone(current);
for(const m of Object.values(before))m.records=m.records.filter(r=>!rows.some(x=>x.id===r.id));
const now=new Date().toISOString(),first=apply(before,ctx,now);
assert.deepEqual(first.stats,{records:2,added:2,skipped:0,changed:true});
assert.deepEqual(apply(first.recovery,ctx,now).stats,{records:2,added:0,skipped:2,changed:false});
const v=rows.find(r=>r.id==="veranda-learning-solutions-limited"),u=rows.find(r=>r.id==="uma-exports-limited");
assert.deepEqual([v.board,v.bse_scrip_code,v.listing_date.value,v.issue_price.value,v.issue_size_inr.value,v.market_lot.value,v.minimum_bid_quantity.value,v.open_date.value,v.close_date.value],[null,null,"2022-04-11",137,2000000000,1,100,"2022-03-29","2022-03-31"]);
assert.deepEqual([u.board,u.bse_scrip_code,u.listing_date.value,u.issue_price.value,u.issue_size_inr.value,u.market_lot.value,u.minimum_bid_quantity.value,u.open_date.value,u.close_date.value],[null,null,"2022-04-07",68,600000000,null,null,"2022-03-28","2022-03-30"]);
assert.equal(v.issue_price.source.document_sha256,"6863886bde37782575fe455fc5e736693731e8604227498954ed9660fca3a79c");
assert.equal(v.listing_date.source.document_sha256,"dba8585edc5958b5505400c370001eb2db2aebf3923974dfd0ad8fbd53a5cb3f");
assert.equal(u.issue_price.source.document_sha256,"8ce36c20cbe531fa558f767c2a73871b56e7232c01c9b02015b164e1029bc35a");
assert.equal(u.open_date.source.document_sha256,"8ce36c20cbe531fa558f767c2a73871b56e7232c01c9b02015b164e1029bc35a");
assert.equal(v.market_lot.value,1);assert.equal(v.minimum_bid_quantity.value,100);assert.notDeepEqual(v.market_lot,v.minimum_bid_quantity);
assert.equal(u.market_lot.value,null);assert.equal(u.minimum_bid_quantity.value,null);
for(const row of rows){assert.equal(row.price_band.value,null);assert.equal(row.isin,null);assert.equal(row.nse_symbol,null)}
for(const model of rows){const collision=structuredClone(before);collision["2023"].records.push({id:"other",issuer_name:"Other",bse_scrip_code:model.bse_2022_veranda_uma_import.discovery_bse_scrip_code});assert.throws(()=>apply(collision,ctx,now),/identity_collision/)}
const altered=structuredClone(first.recovery);altered["2022"].records.find(r=>r.id===v.id).minimum_bid_quantity.value++;assert.throws(()=>apply(altered,ctx,now),/changed_import_fact/);
const badCtx=structuredClone(ctx);badCtx.sources.get("veranda_prospectus").projection.issue_price=138;assert.throws(()=>expected(badCtx),/projection_mismatch/);
assert.equal(rows.reduce((n,r)=>n+FIELDS.filter(k=>r[k].value!==null).length,0),12);
const bytes=fs.readFileSync("data/recovery/2022/nse-issue-information.json");
const cli=spawnSync(process.execPath,["scripts/apply-reviewed-bse-2022-veranda-uma.mjs","--check"],{encoding:"utf8"});
assert.equal(cli.status,0,cli.stderr);assert.deepEqual(fs.readFileSync("data/recovery/2022/nse-issue-information.json"),bytes);
console.log(JSON.stringify({bse_2022_veranda_uma_tests:{records:2,verified_fields:12,veranda_lot_vs_min_bid:true,uma_missing_lot_preserved:true,null_preserving:true,rerun_safe:true,cross_year_collision:true,changed_fact_rejected:true,read_only_check:true}}));
