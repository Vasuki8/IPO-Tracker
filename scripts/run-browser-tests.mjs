// Run every browser gate, retain per-script logs, and fail the batch on ANY failure.
import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
const tests=["test-ui.mjs","test-product-logic-ui.mjs","test-drhp-freshness.mjs","browser-route-focus.mjs"];
const repeats=Number(process.env.BROWSER_TEST_REPEAT || 1);
if (!Number.isInteger(repeats)||repeats<1||repeats>5) throw new Error("BROWSER_TEST_REPEAT must be 1..5");
const results=[];
const out=process.env.UI_SCREENSHOT_DIR;
if (out) mkdirSync(out,{recursive:true});
for(let iteration=1;iteration<=repeats;iteration++) for(const test of tests) {
  const result=spawnSync(process.execPath,[path.join("scripts",test)],{encoding:"utf8",timeout:120000,env:process.env});
  const log=(result.stdout||"")+(result.stderr||"")+(result.error?"\n"+result.error.message:"");
  const passed=result.status===0&&!result.error;
  console.log(`${passed?"PASS":"FAIL"} iteration=${iteration} ${test}\n${log}`);
  if(out) writeFileSync(path.join(out,`${iteration}-${test}.log`),log);
  results.push({iteration,test,passed,exit_code:result.status,signal:result.signal,error:result.error?.message||null});
}
if(out) writeFileSync(path.join(out,"browser-results.json"),JSON.stringify(results,null,2)+"\n");
if(results.some(result=>!result.passed)) process.exitCode=1;
