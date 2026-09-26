import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {collect,sha256,trustedSourceUrl,validateReceipt,validateReview} from "./materialize-bse-2020-unmatched-evidence.mjs";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const reviewBytes=fs.readFileSync(path.join(root,"data/discovery/bse-2020-unmatched-review-2026-09-26.json"));
const review=JSON.parse(reviewBytes);
assert.deepEqual(validateReview(review),{actions:4,sources:11});
assert.equal(review.import_allowed,false);assert.equal(review.publication_change,false);
assert.deepEqual(review.actions.map(a=>[a.issuer_name,a.bse_scrip_code]),[
  ["Likhitha Infrastructure Limited","543240"],["SecMark Consultancy Limited","543234"],
  ["SM Auto Stamping Limited","543065"],["Shine Fashions (India) Limited","543244"]
]);
const recovery=JSON.parse(fs.readFileSync(path.join(root,"data/recovery/2020/nse-issue-information.json"),"utf8")).records||[];
const norm=v=>String(v??"").toLowerCase().replace(/&/g," and ").replace(/\bltd\.?\b/g," limited ").replace(/[^a-z0-9]+/g," ").replace(/\blimited\s*$/g,"").replace(/\s+/g," ").trim();
for(const action of review.actions){
  assert.equal(recovery.some(r=>norm(r.issuer_name)===norm(action.issuer_name)),false,"issuer already present: "+action.issuer_name);
  assert.equal(recovery.some(r=>String(r.bse_scrip_code||"")===action.bse_scrip_code),false,"scrip already present: "+action.bse_scrip_code);
}
for(const bad of ["http://www.sebi.gov.in/a","https://evil.test/a","https://www.bseindia.com.evil.test/a"])assert.equal(trustedSourceUrl(bad),null);
const dir=fs.mkdtempSync(path.join(os.tmpdir(),"bse-2020-unmatched-"));
try{
  const pdf=Buffer.from("%PDF-1.7\ntest"),html=Buffer.from("<!doctype html><html>test</html>");
  const fetchImpl=async url=>{const b=/likhitha\.co\.in/.test(url)?html:pdf;const r=new Response(b,{status:200,headers:{"content-type":b===html?"text/html":"application/pdf"}});Object.defineProperty(r,"url",{value:url});return r;};
  let t=0;const receipt=await collect({review,reviewBytes,outDir:dir,fetchImpl,clock:()=>`2026-09-26T20:10:${String(t++).padStart(2,"0")}.000Z`});
  assert.equal(receipt.documents.length,11);assert.equal(fs.readdirSync(dir).length,11);
  assert.deepEqual(validateReceipt(receipt,review,reviewBytes),{documents:11,bytes:receipt.total_response_bytes});
  const bad=structuredClone(receipt);bad.documents[0].response_sha256=sha256(Buffer.from("tampered"));bad.documents[0].final_url="https://evil.test/file.pdf";
  assert.throws(()=>validateReceipt(bad,review,reviewBytes));
}finally{fs.rmSync(dir,{recursive:true,force:true});}
console.log(JSON.stringify({bse_2020_unmatched_review_tests:{issuers:4,sources:11,recovery_collisions:0,materializer:true,publication_change:false}}));
