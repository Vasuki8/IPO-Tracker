import assert from "node:assert/strict";
import fs from "node:fs";
import {spawnSync} from "node:child_process";
import {apply,context,expected,loadRecovery,FIELDS} from "./apply-reviewed-bse-2021-hp-nuvoco.mjs";

const ctx=context(),rows=expected(ctx),current=loadRecovery(),before=structuredClone(current);
for(const m of Object.values(before))m.records=m.records.filter(r=>!rows.some(x=>x.id===r.id));
const now=new Date().toISOString(),first=apply(before,ctx,now);
assert.deepEqual(first.stats,{records:2,added:2,skipped:0,changed:true});
assert.deepEqual(apply(first.recovery,ctx,now).stats,{records:2,added:0,skipped:2,changed:false});
const hp=rows.find(r=>r.id==="hp-adhesives-limited"),nv=rows.find(r=>r.id==="nuvoco-vistas-corporation-limited");
assert.deepEqual([hp.board,hp.bse_scrip_code,hp.listing_date.value,hp.issue_price.value,hp.issue_size_inr.value,hp.open_date.value,hp.close_date.value],[null,null,"2021-12-27",274,1259633000,"2021-12-15","2021-12-17"]);
assert.deepEqual([nv.board,nv.bse_scrip_code,nv.listing_date.value,nv.issue_price.value,nv.issue_size_inr.value,nv.open_date.value,nv.close_date.value],[null,null,"2021-08-23",570,50000000000,null,null]);
for(const row of rows){assert.equal(row.price_band.value,null);assert.equal(row.market_lot.value,null);assert.equal(row.minimum_bid_quantity.value,null);assert.equal(row.isin,null);assert.equal(row.nse_symbol,null);assert.ok(row.documents.every(d=>d.url.startsWith("https://www.sebi.gov.in/")))}
assert.equal(hp.issue_price.source.document_sha256,"376b1942c91cb0d2eca5c1b926bd1c57f5dffde70683abae6ebf1febcaa18996");
assert.equal(hp.listing_date.source.document_sha256,"2af4759ade441271a93eaf54fdd737cdc733027ef8bc814b79993abd8c879884");
assert.equal(nv.listing_date.source.document_sha256,"d232068ec2d77cc53ff79ad1ef9f8cc6121adf1c2d43ff04380a2394f611d88b");
for(const model of rows){
  const collision=structuredClone(before);
  collision["2022"].records.push({id:"other",issuer_name:"Other",bse_scrip_code:model.bse_2021_hp_nuvoco_import.discovery_bse_scrip_code});
  assert.throws(()=>apply(collision,ctx,now),/identity_collision/);
}
const altered=structuredClone(first.recovery);altered["2021"].records.find(r=>r.id===hp.id).issue_price.value++;
assert.throws(()=>apply(altered,ctx,now),/changed_import_fact/);
const badCtx=structuredClone(ctx);badCtx.sources.get("hp_prospectus").projection.issue_price=275;assert.throws(()=>expected(badCtx),/projection_mismatch/);
assert.equal(rows.reduce((n,r)=>n+FIELDS.filter(k=>r[k].value!==null).length,0),8);
const bytes=fs.readFileSync("data/recovery/2021/nse-issue-information.json");
const cli=spawnSync(process.execPath,["scripts/apply-reviewed-bse-2021-hp-nuvoco.mjs","--check"],{encoding:"utf8"});
assert.equal(cli.status,0,cli.stderr);assert.deepEqual(fs.readFileSync("data/recovery/2021/nse-issue-information.json"),bytes);
console.log(JSON.stringify({hp_nuvoco_tests:{records:2,verified_fields:8,null_preserving:true,rerun_safe:true,cross_year_collision:true,changed_fact_rejected:true,read_only_check:true}}));
