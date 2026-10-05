import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { productDataset, directoryDataset, draftDataset, failedDraftHealth } from "./fixtures/browser-data.mjs";
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),"ipo-browser-fixtures-"));
try {
  fs.mkdirSync(path.join(tmp,"scripts")); fs.mkdirSync(path.join(tmp,"data"));
  fs.copyFileSync("scripts/validate-data.mjs",path.join(tmp,"scripts/validate-data.mjs"));
  fs.copyFileSync("data/ipo-schema.json",path.join(tmp,"data/ipo-schema.json"));
  for(const make of [productDataset,directoryDataset]) {
    const a=make(),b=make(); assert.deepEqual(a,b,"fixture generation is deterministic");
    a.records[0].open_date.value=null;
    assert.notDeepEqual(a,b,"individual scenarios do not share mutable objects");
    fs.writeFileSync(path.join(tmp,"data/ipos.json"),JSON.stringify(b));
    const result=spawnSync(process.execPath,[path.join(tmp,"scripts/validate-data.mjs")],{encoding:"utf8"});
    assert.equal(result.status,0,result.stdout+result.stderr);
  }
  assert.equal(directoryDataset().records.length,101);
  const health=failedDraftHealth(),source=draftDataset();
  assert.equal(health.status,"failed");
  assert.equal(health.last_successful_collection_at,source.collection_completed_at);
  assert.ok(health.attempted_at>source.collection_completed_at);
  console.log("Fixed browser fixtures: deterministic, isolated, valid published shapes and independent freshness clocks.");
} finally { fs.rmSync(tmp,{recursive:true,force:true}); }
