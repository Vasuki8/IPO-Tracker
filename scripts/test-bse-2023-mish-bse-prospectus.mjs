import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {validatePlan,collectEvidence,validateReceipt} from './collect-bse-2023-mish-bse-prospectus.mjs';
const planBytes=fs.readFileSync(new URL('../data/discovery/bse-2023-mish-bse-prospectus-plan-2026-10-05.json',import.meta.url));
const priorBytes=fs.readFileSync(new URL('../data/evidence/bse-2023-mish-source-receipt-2026-10-05.json',import.meta.url));
const plan=JSON.parse(planBytes);
const sha=b=>createHash('sha256').update(b).digest('hex');
function workspace(t){const root=fs.mkdtempSync(path.join(os.tmpdir(),'mish-bse-prospectus-'));t.after(()=>fs.rmSync(root,{recursive:true,force:true}));return path.join(root,'evidence');}
function clock(){let n=0;return()=>new Date(Date.UTC(2026,9,5,19,0,n++)).toISOString();}
function goodFetch(){return async(url,options)=>{assert.equal(url,plan.source.url);assert.equal(options.redirect,'error');assert.ok(options.signal instanceof AbortSignal);return new Response('%PDF-1.7\nBSE Mish prospectus bytes\n%%EOF',{status:200,headers:{'content-type':'application/pdf'}});};}

test('accepts only the pinned BSE Mish prospectus plan',()=>{
 const p=validatePlan(planBytes,{priorReceiptBytes:priorBytes});
 assert.equal(p.discovery_bse_scrip_code,'544015');assert.equal(p.publication_import_allowed,false);
});
for(const [name,mutate] of [
 ['publication flag',p=>p.publication_import_allowed=true],
 ['semantic flag',p=>p.semantic_review_complete=true],
 ['issuer',p=>p.issuer_name='Other Limited'],
 ['code',p=>p.discovery_bse_scrip_code='999999'],
 ['prior receipt',p=>p.prior_source_receipt='data/evidence/other.json'],
 ['URL',p=>p.source.url='https://example.com/x.pdf'],
 ['authority',p=>p.source.authority='Other'],
 ['role',p=>p.source.role='listing_notice']
])test('rejects '+name,()=>{const p=structuredClone(plan);mutate(p);assert.throws(()=>validatePlan(Buffer.from(JSON.stringify(p)),{priorReceiptBytes:priorBytes}));});

test('rejects an unrelated prior receipt',()=>{
 const prior=JSON.parse(priorBytes);prior.candidate.issuer_name='Other Limited';
 assert.throws(()=>validatePlan(planBytes,{priorReceiptBytes:Buffer.from(JSON.stringify(prior))}),/prior/);
});

test('retains a valid BSE PDF without authorizing publication',async t=>{
 const dir=workspace(t),r=await collectEvidence({planBytes,priorReceiptBytes:priorBytes,evidenceDir:dir,fetchImpl:goodFetch(),clock:clock()});
 assert.equal(r.status,'complete');assert.equal(r.document.accepted,true);assert.equal(r.publication_import_allowed,false);
 assert.equal(r.issuer_prospectus_reference.response_sha256,'1779a684e9f5dac3441fa13dfd129a7d5ba6bb89670695ea8d04f01d3de9a804');
 assert.equal(validateReceipt(r,planBytes,priorBytes,dir).accepted,true);
 const b=fs.readFileSync(path.join(dir,'bse_final_prospectus.pdf'));assert.equal(sha(b),r.document.response_sha256);
});

test('retains rejected HTML challenge bytes as a partial collection',async t=>{
 const dir=workspace(t),r=await collectEvidence({planBytes,priorReceiptBytes:priorBytes,evidenceDir:dir,clock:clock(),fetchImpl:async()=>new Response('<html>blocked</html>',{status:200,headers:{'content-type':'application/pdf'}})});
 assert.equal(r.status,'partial');assert.equal(r.document.error,'unexpected_body_type');assert.match(r.document.evidence_file,/\.response$/);
});

test('records network failure without fabricating evidence',async t=>{
 const dir=workspace(t),r=await collectEvidence({planBytes,priorReceiptBytes:priorBytes,evidenceDir:dir,clock:clock(),fetchImpl:async()=>{throw new Error('blocked');}});
 assert.equal(r.status,'partial');assert.equal(r.document.error,'network_error');assert.equal(r.document.response_sha256,null);assert.equal(r.document.response_bytes,0);
});

test('detects receipt tampering',async t=>{
 const dir=workspace(t),r=await collectEvidence({planBytes,priorReceiptBytes:priorBytes,evidenceDir:dir,fetchImpl:goodFetch(),clock:clock()});
 for(const mutate of [
  x=>x.plan_sha256='0'.repeat(64),
  x=>x.publication_import_allowed=true,
  x=>x.issuer_prospectus_reference.response_sha256='0'.repeat(64),
  x=>x.document.response_sha256='0'.repeat(64),
  x=>x.document.evidence_file='../outside.pdf',
  x=>x.document.requested_at='2099-01-01T00:00:00.000Z'
 ]){const bad=structuredClone(r);mutate(bad);assert.throws(()=>validateReceipt(bad,planBytes,priorBytes,dir));}
});
