import assert from "node:assert/strict";
import fs from "node:fs";import os from "node:os";import path from "node:path";
import {collect,sha256,trustedSourceUrl,validateReceipt,validateReview} from "./materialize-bse-audit-conflict-evidence.mjs";
const proj={issuer:"Example Limited"};const source=(key,url)=>({key,authority:"Official",document_type:"Official",url,projection:proj,projection_sha256:sha256(Buffer.from(JSON.stringify(proj)))});
const review={schema_version:"1.0.0",status:"reviewed_bse_issue_summary_high_priority_reconciliation",actions:Array.from({length:5},()=>({})),auto_import_allowed:false,
 sources:[
  source("j","https://www.bseindia.com/j.pdf"),source("a","https://www.sebi.gov.in/a.pdf"),source("b","https://nsearchives.nseindia.com/b.pdf"),source("c","https://www.bseindia.com/c.pdf"),
  source("d","https://www.sebi.gov.in/d.pdf"),source("e","https://nsearchives.nseindia.com/e.pdf"),source("f","https://www.bseindia.com/f.pdf"),
  source("g","https://www.sebi.gov.in/g.html"),source("h","https://www.bseindia.com/h.pdf"),source("i","https://www.sebi.gov.in/i.html")
 ]};
const rb=Buffer.from(JSON.stringify(review));assert.equal(validateReview(review).keys.size,10);
for(const bad of ["http://www.sebi.gov.in/a","https://evil.test/a","https://www.bseindia.com.evil.test/a"])assert.equal(trustedSourceUrl(bad),null);
const dir=fs.mkdtempSync(path.join(os.tmpdir(),"recon-evidence-"));
try{
 const pdf=Buffer.from("%PDF-1.7\ntest"),html=Buffer.from("<!doctype html><html>test</html>");
 const fetchImpl=async url=>{const b=url.endsWith(".html")?html:pdf;const r=new Response(b,{status:200,headers:{"content-type":url.endsWith(".html")?"text/html":"application/pdf"}});Object.defineProperty(r,"url",{value:url});return r;};
 let t=0;const receipt=await collect({review,reviewBytes:rb,outDir:dir,fetchImpl,clock:()=>`2026-09-26T17:00:${String(t++).padStart(2,"0")}.000Z`});
 assert.equal(receipt.documents.length,10);assert.equal(fs.readdirSync(dir).length,10);assert.deepEqual(validateReceipt(receipt,review,rb),{documents:10,bytes:receipt.total_response_bytes});
 const bad=structuredClone(receipt);bad.documents[0].response_sha256="bad";assert.throws(()=>validateReceipt(bad,review,rb));
}finally{fs.rmSync(dir,{recursive:true,force:true});}
console.log(JSON.stringify({bse_reconciliation_evidence_tests:{trusted_hosts:true,projection_hashes:true,documents:10,receipt:true}}));
