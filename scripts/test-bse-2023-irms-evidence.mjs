import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {validatePlan, collectEvidence, validateReceipt} from './collect-bse-2023-irms-evidence.mjs';
const planBytes=fs.readFileSync(new URL('../data/discovery/bse-2023-irms-source-plan-2026-09-28.json',import.meta.url));
const plan=JSON.parse(planBytes);
const hash=b=>createHash('sha256').update(b).digest('hex');
const bytes=p=>Buffer.from(JSON.stringify(p));
function workspace(t){const p=fs.mkdtempSync(path.join(os.tmpdir(),'irms-test-'));t.after(()=>fs.rmSync(p,{recursive:true,force:true}));return path.join(p,'evidence');}
function fetcher(overrides={}){return async (url,options)=>{
 assert.equal(options.redirect,'error');
 assert.ok(options.signal instanceof AbortSignal);
 if(overrides[url])return overrides[url](url,options);
 const issuer=plan.issuers.find(i=>i.landing_url===url||i.prospectus_url===url);
 assert.ok(issuer,'only reviewed source-plan URLs are requested');
 return new Response(url===issuer.landing_url?`<!doctype html><html>${issuer.issuer_name}<iframe src="/web/?file=${encodeURIComponent(issuer.prospectus_url)}"></iframe></html>`:'%PDF-1.7\noriginal bytes\n%%EOF', {status:200,headers:{'content-type':url===issuer.landing_url?'text/html':'application/pdf'}});
};}
const clock=()=>{let n=0;return()=>new Date(Date.UTC(2026,8,28,14,0,n++)).toISOString();};
test('accepts the four-candidate read-only source plan',()=>assert.equal(validatePlan(planBytes).issuers.length,4));
for(const [name,mutate] of [
 ['publication flag',p=>p.publication_import_allowed=true],
 ['semantic review flag',p=>p.semantic_review_complete=true],
 ['universe completeness flag',p=>p.complete_indian_ipo_universe=true],
 ['duplicate issuer',p=>p.issuers[1]=p.issuers[0]],
 ['unexpected candidate',p=>p.issuers[0].discovery_bse_scrip_code='999999'],
 ['inferred document date',p=>p.issuers[1].document_date='2024-05-15'],
 ['credential URL',p=>p.issuers[0].prospectus_url=p.issuers[0].prospectus_url.replace('https://','https://user:pass@')],
 ['external host',p=>p.issuers[0].prospectus_url='https://example.com/doc.pdf'],
 ['non-HTTPS source',p=>p.issuers[0].prospectus_url=p.issuers[0].prospectus_url.replace('https:','http:')],
 ['traversal URL',p=>p.issuers[0].prospectus_url='https://www.sebi.gov.in/sebi_data/attachdocs/../private.pdf'],
 ['unknown field injection',p=>p.issuers[0].issue_price=32]
])test(`rejects ${name}`,()=>{const p=structuredClone(plan);mutate(p);assert.throws(()=>validatePlan(bytes(p)));});
test('rejects queue bytes that do not match the retained snapshot',()=>assert.throws(()=>validatePlan(planBytes,{queueBytes:Buffer.from('{}')}),/queue/));
test('retains all eight original responses and separate clocks without import approval',async t=>{
 const dir=workspace(t),r=await collectEvidence({planBytes,evidenceDir:dir,fetchImpl:fetcher(),clock:clock()});
 assert.equal(r.status,'complete');assert.equal(r.documents.length,8);assert.equal(r.source_documents_accepted,8);
 assert.equal(r.publication_import_allowed,false);assert.equal(r.semantic_review_complete,false);
 assert.equal(r.discovery_source_collected_at,plan.discovery_source_collected_at);assert.equal(r.plan_sha256,hash(planBytes));
 assert.equal(r.landing_pdf_bindings.length,4);assert.ok(r.landing_pdf_bindings.every(b=>b.link_found));
 assert.equal(validateReceipt(r,planBytes,dir).accepted,8);
 assert.deepEqual(fs.readFileSync(path.join(dir,'source-plan.json')),planBytes);
 for(const d of r.documents){assert.equal(hash(fs.readFileSync(path.join(dir,d.evidence_file))),d.response_sha256);assert.ok(d.requested_at<=d.collected_at);}
});
test('records network failures while retaining other original responses',async t=>{
 const dir=workspace(t),r=await collectEvidence({planBytes,evidenceDir:dir,clock:clock(),fetchImpl:fetcher({[plan.issuers[0].prospectus_url]:()=>{throw new Error('network down');}})});
 assert.equal(r.status,'partial');assert.equal(r.source_documents_accepted,7);assert.equal(r.documents[1].error,'network_error');assert.equal(r.documents[1].response_sha256,null);assert.equal(validateReceipt(r,planBytes,dir).accepted,7);
});
test('rejects a HTML challenge masquerading as a PDF and retains the rejected bytes',async t=>{
 const dir=workspace(t),r=await collectEvidence({planBytes,evidenceDir:dir,clock:clock(),fetchImpl:fetcher({[plan.issuers[0].prospectus_url]:()=>new Response('<html>blocked</html>',{headers:{'content-type':'application/pdf'}})})});
 assert.equal(r.status,'partial');assert.equal(r.documents[1].error,'unexpected_body_type');assert.match(r.documents[1].evidence_file,/\.response$/);assert.equal(validateReceipt(r,planBytes,dir).accepted,7);
});
test('does not call a redirect target and records non-success HTTP responses',async t=>{
 const dir=workspace(t),r=await collectEvidence({planBytes,evidenceDir:dir,clock:clock(),fetchImpl:fetcher({[plan.issuers[0].prospectus_url]:()=>new Response('redirect',{status:302,headers:{location:'https://example.com'}})})});
 assert.equal(r.status,'partial');assert.equal(r.documents[1].error,'http_status');assert.equal(r.documents[1].http_status,302);
});
test('refuses oversized source bodies without retaining truncated bytes',async t=>{
 const dir=workspace(t),r=await collectEvidence({planBytes,evidenceDir:dir,clock:clock(),maxSourceBytes:1024,fetchImpl:fetcher({[plan.issuers[0].prospectus_url]:()=>new Response('%PDF-'+ 'x'.repeat(2048))})});
 assert.equal(r.status,'partial');assert.equal(r.documents[1].error,'source_size_limit');assert.equal(r.documents[1].evidence_file,null);
});
test('an unlinked PDF keeps the batch incomplete even when every response fetches',async t=>{
 const dir=workspace(t),r=await collectEvidence({planBytes,evidenceDir:dir,clock:clock(),fetchImpl:fetcher({[plan.issuers[0].landing_url]:()=>new Response('<html>Unrelated document</html>',{headers:{'content-type':'text/html'}})})});
 assert.equal(r.status,'partial');assert.equal(r.source_documents_accepted,8);assert.equal(r.landing_pdf_bindings[0].link_found,false);assert.equal(validateReceipt(r,planBytes,dir).accepted,8);
});
test('refuses an existing evidence directory to prevent mixing collections',async t=>{
 const dir=workspace(t);fs.mkdirSync(dir);await assert.rejects(()=>collectEvidence({planBytes,evidenceDir:dir,fetchImpl:fetcher(),clock:clock()}),/exist/i);
});
test('detects forged receipt hashes, clocks, flags, totals and file traversal',async t=>{
 const dir=workspace(t),r=await collectEvidence({planBytes,evidenceDir:dir,fetchImpl:fetcher(),clock:clock()});
 for(const mutate of [x=>x.plan_sha256='0'.repeat(64),x=>x.publication_import_allowed=true,x=>x.semantic_review_complete=true,x=>x.total_response_bytes++,x=>x.documents[0].response_sha256='0'.repeat(64),x=>x.documents[0].evidence_file='../outside.html',x=>x.documents[0].requested_at='2099-01-01T00:00:00Z',x=>x.landing_pdf_bindings[0].link_found=false,x=>x.documents.pop()]){const bad=structuredClone(r);mutate(bad);assert.throws(()=>validateReceipt(bad,planBytes,dir));}
 fs.appendFileSync(path.join(dir,r.documents[0].evidence_file),'tamper');assert.throws(()=>validateReceipt(r,planBytes,dir));
});
