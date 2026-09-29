import assert from "node:assert/strict";
import fs from "node:fs";
import {
  DEFAULT_SEBI_PDF_DOWNLOAD_ATTEMPTS,
  downloadOfficialSebiPdf,
  isOfficialSebiAttachmentPdf
} from "./download-official-sebi-pdf.mjs";

const url="https://www.sebi.gov.in/sebi_data/attachdocs/sep-2025/example.pdf";
assert.equal(DEFAULT_SEBI_PDF_DOWNLOAD_ATTEMPTS,4);
assert.equal(isOfficialSebiAttachmentPdf(url),true);
for(const unsafe of [
  "http://www.sebi.gov.in/sebi_data/attachdocs/x.pdf",
  "https://evil.example/sebi_data/attachdocs/x.pdf",
  "https://www.sebi.gov.in.evil.test/sebi_data/attachdocs/x.pdf",
  "https://www.sebi.gov.in/filings/public-issues/x.pdf",
  "javascript:alert(1)"
]) assert.equal(isOfficialSebiAttachmentPdf(unsafe),false);

let calls=0;
const resumed=downloadOfficialSebiPdf(url,{maxSeconds:45,attempts:3,execImpl:(cmd,args)=>{
  assert.equal(cmd,"curl");
  const out=args[args.indexOf("--output")+1];
  calls++;
  if(calls===1){
    assert.equal(args.includes("--continue-at"),false);
    fs.writeFileSync(out,Buffer.from("%PDF-1.7\npartial-"));
    const error=new Error("Operation timed out");
    error.stderr=Buffer.from("curl: (28) Operation timed out");
    throw error;
  }
  assert.equal(args.includes("--continue-at"),true);
  fs.appendFileSync(out,Buffer.from("rest"));
}});
assert.equal(calls,2);
assert.equal(resumed.attempts_used,2);
assert.equal(resumed.resumed,true);
assert.equal(resumed.failures.length,1);
assert.equal(resumed.bytes.toString(),"%PDF-1.7\npartial-rest");

let restartCalls=0;
const restarted=downloadOfficialSebiPdf(url,{maxSeconds:45,attempts:3,execImpl:(cmd,args)=>{
  const out=args[args.indexOf("--output")+1];
  restartCalls++;
  if(restartCalls===1){
    fs.writeFileSync(out,Buffer.from("%PDF-partial"));
    throw new Error("timeout");
  }
  if(restartCalls===2){
    assert.equal(args.includes("--continue-at"),true);
    const error=new Error("HTTP server does not seem to support byte ranges. Cannot resume.");
    error.stderr=Buffer.from(error.message);
    throw error;
  }
  assert.equal(args.includes("--continue-at"),false);
  fs.writeFileSync(out,Buffer.from("%PDF-fresh-complete"));
}});
assert.equal(restartCalls,3);
assert.equal(restarted.attempts_used,3);
assert.equal(restarted.resumed,true);
assert.equal(restarted.bytes.toString(),"%PDF-fresh-complete");

assert.throws(()=>downloadOfficialSebiPdf("https://evil.example/x.pdf"),/unsafe/);
assert.throws(()=>downloadOfficialSebiPdf(url,{maxSeconds:5}),/max_seconds/);
assert.throws(()=>downloadOfficialSebiPdf(url,{attempts:9}),/attempts/);

console.log(JSON.stringify({sebi_pdf_download_tests:{
  resumable_timeout_recovery:true,
  safe_fresh_fallback:true,
  official_url_guard:true,
  bounded_attempts:true
}}));
