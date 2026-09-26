import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {collectFabinoEvidence,sha256,trustedFabinoSourceUrl,validateFabinoReceipt,validateFabinoReview} from "./materialize-fabino-listing-evidence.mjs";

const projection=(issuer,extra={})=>({issuer,...extra});
const src=(key,url,type,projectionValue)=>({key,authority:"BSE Limited",document_type:type,document_identity:key,publication_date:"2022-01-12",url,page:null,evidence_locator:"test",source_bytes_sha256:null,projection:projectionValue,projection_sha256:sha256(Buffer.from(JSON.stringify(projectionValue)))});
const review={
 schema_version:"1.0.0",status:"resolved_bse_listing_year_conflict_import_pending",
 issuer:{issuer_name:"Fabino Life Sciences Limited",bse_scrip_code:"543444",isin:"INE0DRT01018"},
 decision:{correct_listing_date:"2022-01-13"},
 sources:[
  src("notice","https://www.bseindia.com/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=20220112-10","BSE Listing Notice",projection("Fabino Life Sciences Limited",{notice_no:"20220112-10"})),
  src("press","https://www.bseindia.com/downloads/example.pdf","Press Release",projection("Fabino Life Sciences Limited",{listing_date:"2022-01-13"})),
  src("prospectus","https://www.bseindia.com/corporates/download/example.pdf","Prospectus",projection("Fabino Life Sciences Limited",{offer_open:"2021-12-31"})),
  src("sebi","https://www.sebi.gov.in/filings/public-issues/example.html","SEBI Filing",projection("Fabino Life Sciences Limited",{filing_date:"2021-12-30"}))
 ]
};
const reviewBytes=Buffer.from(JSON.stringify(review));
assert.equal(validateFabinoReview(review).source_keys.size,4);
assert.ok(trustedFabinoSourceUrl(review.sources[0].url));
for(const bad of ["http://www.bseindia.com/x","https://bseindia.com.evil.test/x","https://evil.test/x","javascript:alert(1)"])assert.equal(trustedFabinoSourceUrl(bad),null);

const dir=fs.mkdtempSync(path.join(os.tmpdir(),"fabino-evidence-"));
try{
 const pdf=Buffer.from("%PDF-1.7\nsynthetic\n"),html=Buffer.from("<!doctype html><html>synthetic</html>");
 const fetchImpl=async url=>{
  const isHtml=url.includes("DispNewNoticesCirculars")||url.includes("sebi.gov.in");
  const response=new Response(isHtml?html:pdf,{status:200,headers:{"content-type":isHtml?"text/html":"application/pdf"}});
  Object.defineProperty(response,"url",{value:url});return response;
 };
 let tick=0;
 const receipt=await collectFabinoEvidence({review,reviewBytes,evidenceDir:dir,fetchImpl,clock:()=>`2026-09-26T15:00:${String(tick++).padStart(2,"0")}.000Z`});
 assert.equal(receipt.documents.length,4);
 assert.equal(receipt.documents.filter(d=>d.detected_type==="pdf").length,2);
 assert.equal(receipt.documents.filter(d=>d.detected_type==="html").length,2);
 assert.deepEqual(validateFabinoReceipt(receipt,review,reviewBytes),{documents:4,bytes:2*pdf.length+2*html.length});
 assert.equal(fs.readdirSync(dir).length,4);
 const bad=structuredClone(receipt);bad.documents[0].response_sha256="bad";
 assert.throws(()=>validateFabinoReceipt(bad,review,reviewBytes));
}finally{fs.rmSync(dir,{recursive:true,force:true});}
console.log(JSON.stringify({fabino_evidence_tests:{trusted_hosts:true,review_projection_hashes:true,documents:4,byte_hash_receipt:true}}));
