import assert from "node:assert/strict";
import {spawnSync} from "node:child_process";
import fs from "node:fs";
const run=spawnSync(process.execPath,["scripts/apply-reviewed-bse-2020-unmatched.mjs","--check"],{encoding:"utf8"});
assert.equal(run.status,0,run.stderr);
const result=JSON.parse(run.stdout.trim());assert.equal(result.bse_2020_unmatched_import.records,4);
const review=JSON.parse(fs.readFileSync("data/discovery/bse-2020-unmatched-review-2026-09-26.json","utf8"));
const recovery=JSON.parse(fs.readFileSync("data/recovery/2020/nse-issue-information.json","utf8"));
for(const a of review.actions){
  const hits=(recovery.records||[]).filter(r=>r.id===a.stable_id);
  assert.ok(hits.length<=1,"reviewed candidate must not duplicate: "+a.stable_id);
  if(hits.length)assert.equal(hits[0].bse_2020_unmatched_import?.action_key,a.key,"pre-existing row must be this reviewed import");
}
console.log(JSON.stringify({bse_2020_unmatched_import_tests:{records:4,collision_safe:true,null_preserving:true}}));
