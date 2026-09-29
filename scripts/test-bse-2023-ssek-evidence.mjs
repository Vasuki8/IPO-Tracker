import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {validatePlan,collectEvidence} from './collect-bse-2023-ssek-evidence.mjs';

const planBytes=fs.readFileSync(new URL('../data/discovery/bse-2023-ssek-source-plan-2026-09-29.json',import.meta.url));
const plan=JSON.parse(planBytes);
const queueBytes=fs.readFileSync(new URL('../data/discovery/bse-2023-review-queue-2026-09-28.json',import.meta.url));
const clock=()=>{let n=0;return()=>new Date(Date.UTC(2026,8,29,17,0,n++)).toISOString();};
function workspace(t){const p=fs.mkdtempSync(path.join(os.tmpdir(),'ssek-test-'));t.after(()=>fs.rmSync(p,{recursive:true,force:true}));return path.join(p,'evidence');}
function fetcher(overrides={}){return async url=>{
  if(overrides[url])return overrides[url]();
  const issuer=plan.issuers.find(i=>i.landing_url===url||i.prospectus_url===url);assert.ok(issuer);
  const body=url===issuer.landing_url?`<!doctype html><html><a href="/web/?file=${encodeURIComponent(issuer.prospectus_url)}">PDF</a></html>`:'%PDF-1.7\nsource\n%%EOF';
  return new Response(body,{status:200,headers:{'content-type':url===issuer.landing_url?'text/html':'application/pdf'}});
};}
test('plan binds current four immutable queue rows',()=>{const p=validatePlan(planBytes,{queueBytes});assert.deepEqual(p.issuers.map(i=>i.discovery_bse_scrip_code),['544059','543970','543895','543953']);assert.equal(p.issuers[1].landing_displayed_date,'2024-04-04');assert.equal(p.issuers[1].document_date,null);});
for(const [name,mutate] of [
 ['publication flag',p=>p.publication_import_allowed=true],
 ['document date laundering',p=>p.issuers[1].document_date='2023-08-09'],
 ['wrong candidate',p=>p.issuers[0].discovery_bse_scrip_code='999999'],
 ['external source',p=>p.issuers[0].prospectus_url='https://example.com/a.pdf'],
 ['credential URL',p=>p.issuers[0].prospectus_url=p.issuers[0].prospectus_url.replace('https://','https://u:p@')]
])test('rejects '+name,()=>{const p=structuredClone(plan);mutate(p);assert.throws(()=>validatePlan(Buffer.from(JSON.stringify(p))));});
test('retains eight linked official responses without approving import',async t=>{const r=await collectEvidence({planBytes,evidenceDir:workspace(t),fetchImpl:fetcher(),clock:clock()});assert.equal(r.status,'complete');assert.equal(r.source_documents_accepted,8);assert.ok(r.landing_pdf_bindings.every(x=>x.link_found));assert.equal(r.publication_import_allowed,false);});
test('partial source failure stays partial',async t=>{const target=plan.issuers[0].prospectus_url;const r=await collectEvidence({planBytes,evidenceDir:workspace(t),fetchImpl:fetcher({[target]:()=>{throw new Error('down');}}),clock:clock()});assert.equal(r.status,'partial');assert.equal(r.source_documents_accepted,7);assert.equal(r.documents.find(d=>d.url===target).error,'network_error');});
