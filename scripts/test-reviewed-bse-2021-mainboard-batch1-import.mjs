import assert from "node:assert/strict";
import fs from "node:fs";
import {spawnSync} from "node:child_process";
import {context,expected,apply,loadRecovery} from "./apply-reviewed-bse-2021-mainboard-batch1.mjs";
const ctx=context(),rows=expected(ctx),current=loadRecovery(),before=structuredClone(current);
for(const y of Object.values(before))y.records=y.records.filter(r=>!rows.some(e=>e.id===r.id));
const now=new Date().toISOString(),first=apply(before,ctx,now);assert.deepEqual(first.stats,{records:3,added:3,skipped:0,changed:true});assert.deepEqual(apply(first.recovery,ctx,now).stats,{records:3,added:0,skipped:3,changed:false});
assert.equal(rows.length,3);for(const r of rows){assert.equal(r.board,null);assert.equal(r.bse_scrip_code,null);assert.equal(r.market_lot.value,null);assert.equal(r.minimum_bid_quantity.value,null);assert.ok(r.documents.length>=2);assert.ok(r.documents.every(d=>d.url.startsWith("https://www.sebi.gov.in/")))}
const irfc=rows.find(r=>r.id==="indian-railway-finance-corporation-limited");assert.equal(irfc.issue_price.value,26);assert.equal(irfc.issue_size_inr.value,46334000000);assert.equal(irfc.open_date.value,"2021-01-18");assert.equal(irfc.close_date.value,"2021-01-20");assert.equal(irfc.listing_date.value,"2021-01-29");
const anupam=rows.find(r=>r.id==="anupam-rasayan-india-limited");assert.equal(anupam.issue_price.value,555);assert.equal(anupam.issue_size_inr.value,7600000000);assert.equal(anupam.open_date.value,null);assert.equal(anupam.listing_date.value,"2021-03-24");
const exxaro=rows.find(r=>r.id==="exxaro-tiles-limited");assert.equal(exxaro.issue_price.value,120);assert.equal(exxaro.issue_size_inr.value,1611000000);assert.equal(exxaro.listing_date.value,"2021-08-16");
const collision=structuredClone(before);collision["2022"].records.push({id:"other",issuer_name:"Other",bse_scrip_code:"543257"});assert.throws(()=>apply(collision,ctx,now),/identity_collision/);
const bytes=fs.readFileSync("data/recovery/2021/nse-issue-information.json"),cli=spawnSync(process.execPath,["scripts/apply-reviewed-bse-2021-mainboard-batch1.mjs","--check"],{encoding:"utf8"});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(fs.readFileSync("data/recovery/2021/nse-issue-information.json"),bytes);
console.log(JSON.stringify({bse_2021_batch1_import_tests:{records:3,verified_fields:11,null_preserving:true,rerun_safe:true,cross_year_collision:true}}));
