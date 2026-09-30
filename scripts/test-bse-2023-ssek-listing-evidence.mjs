import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {validatePlan,collectListingEvidence} from './collect-bse-2023-ssek-listing-evidence.mjs';
import {buildExtractionIndex} from './inspect-bse-2023-ssek-listing-evidence.mjs';

const root=new URL('../',import.meta.url);
const planBytes=fs.readFileSync(new URL('data/discovery/bse-2023-ssek-listing-source-plan-2026-09-29.json',root));
const fieldReviewBytes=fs.readFileSync(new URL('data/discovery/bse-2023-ssek-field-review-2026-09-29.json',root));
const plan=JSON.parse(planBytes);
const clock=()=>{let n=0;return()=>new Date(Date.UTC(2026,8,29,18,0,n++)).toISOString();};
function workspace(t){const p=fs.mkdtempSync(path.join(os.tmpdir(),'ssek-listing-test-'));t.after(()=>fs.rmSync(p,{recursive:true,force:true}));return path.join(p,'evidence');}
function fetcher(overrides={}){return async url=>{
 if(overrides[url])return overrides[url]();
 const issuer=plan.issuers.find(i=>i.source_url===url);assert.ok(issuer);
 return new Response('%PDF-1.7\noriginal '+issuer.discovery_bse_scrip_code+'\n%%EOF',{status:200,headers:{'content-type':'application/pdf'}});
};}
test('listing plan is bound to the reviewed four and contains no approved semantic values',()=>{
 const p=validatePlan(planBytes,{fieldReviewBytes});
 assert.deepEqual(p.issuers.map(i=>i.discovery_bse_scrip_code),['544059','543970','543895','543953']);
 assert.ok(p.issuers.every(i=>i.listing_date===null&&i.verified_bse_scrip_code===null&&i.board===null));
});
for(const [name,mutate] of [
 ['publication flag',p=>p.publication_import_allowed=true],
 ['semantic flag',p=>p.semantic_review_complete=true],
 ['listing date laundering',p=>p.issuers[0].listing_date='2023-12-27'],
 ['wrong source',p=>p.issuers[1].source_url='https://example.com/report.pdf'],
 ['credential URL',p=>p.issuers[2].source_url=p.issuers[2].source_url.replace('https://','https://u:p@')],
 ['field review substitution',p=>p.field_review.git_blob_sha='0'.repeat(40)]
])test('rejects '+name,()=>{const p=structuredClone(plan);mutate(p);assert.throws(()=>validatePlan(Buffer.from(JSON.stringify(p)),{fieldReviewBytes}));});
test('collects exactly four original PDFs without approving import',async t=>{
 const dir=workspace(t),r=await collectListingEvidence({planBytes,fieldReviewBytes,evidenceDir:dir,fetchImpl:fetcher(),clock:clock()});
 assert.equal(r.status,'complete');assert.equal(r.source_documents_accepted,4);assert.equal(r.publication_import_allowed,false);
 assert.ok(r.documents.every(d=>d.accepted&&d.response_sha256&&d.evidence_file.endsWith('.pdf')));
});
test('source failure remains partial and cannot be mislabeled complete',async t=>{
 const target=plan.issuers[0].source_url,dir=workspace(t);
 const r=await collectListingEvidence({planBytes,fieldReviewBytes,evidenceDir:dir,fetchImpl:fetcher({[target]:()=>{throw new Error('down');}}),clock:clock()});
 assert.equal(r.status,'partial');assert.equal(r.source_documents_accepted,3);assert.equal(r.documents[0].error,'network_error');
});
test('extraction index revalidates retained bytes and reports pages without semantic approval',async t=>{
 const dir=workspace(t),r=await collectListingEvidence({planBytes,fieldReviewBytes,evidenceDir:dir,fetchImpl:fetcher(),clock:clock()});
 assert.equal(r.status,'complete');
 for(const d of r.documents){
  const base=path.join(dir,d.evidence_file.slice(0,-4));
  fs.writeFileSync(base+'.pdfinfo','Pages:          2\n');
  fs.writeFileSync(base+'.txt','Corporate information BSE code '+d.code+'\fThe equity shares were listed on the BSE SME platform on 29 August 2023.\f');
 }
 const x=buildExtractionIndex(dir);assert.equal(x.status,'extraction_research_only');assert.equal(x.publication_import_allowed,false);
 assert.ok(x.documents.every(d=>d.pdf_pages===2&&d.code_hits.length===1&&d.listing_hits.length===1));
});
