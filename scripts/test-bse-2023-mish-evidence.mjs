import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {validatePlan,collectEvidence,validateReceipt} from './collect-bse-2023-mish-evidence.mjs';

const planBytes=fs.readFileSync(new URL('../data/discovery/bse-2023-mish-source-plan-2026-10-05.json',import.meta.url));
const plan=JSON.parse(planBytes);
const hash=b=>createHash('sha256').update(b).digest('hex');
const json=p=>Buffer.from(JSON.stringify(p));
function workspace(t){const p=fs.mkdtempSync(path.join(os.tmpdir(),'mish-evidence-test-'));t.after(()=>fs.rmSync(p,{recursive:true,force:true}));return path.join(p,'evidence');}
function clock(){let n=0;return()=>new Date(Date.UTC(2026,9,5,18,0,n++)).toISOString();}
const sourceByUrl=new Map(plan.issuer.sources.map(s=>[s.url,s]));
function landingHtml(){
 return '<!doctype html><html><body><a href="/Investor_Assets/Initial%20Public%20Offer/Prospectus_of_Mish_Designs_Limited.pdf">Mish Designs Limited Prospectus</a></body></html>';
}
function fetcher(overrides={}){return async (url,options)=>{
 assert.equal(options.redirect,'error');assert.ok(options.signal instanceof AbortSignal);
 const source=sourceByUrl.get(url);assert.ok(source,'collector requested only pinned URLs');
 if(overrides[url])return overrides[url](url,options);
 const body=source.kind==='html'?landingHtml():'%PDF-1.7\noriginal Mish evidence bytes\n%%EOF';
 return new Response(body,{status:200,headers:{'content-type':source.kind==='html'?'text/html':'application/pdf'}});
};}

test('accepts the single-candidate read-only Mish source plan',()=>{
 const p=validatePlan(planBytes);
 assert.equal(p.issuer.discovery_bse_scrip_code,'544015');
 assert.equal(p.issuer.source_row_index,27);
 assert.equal(p.issuer.sources.length,3);
 assert.equal(p.publication_import_allowed,false);
});
for(const [name,mutate] of [
 ['publication flag',p=>p.publication_import_allowed=true],
 ['semantic review flag',p=>p.semantic_review_complete=true],
 ['universe completeness flag',p=>p.complete_indian_ipo_universe=true],
 ['wrong code',p=>p.issuer.discovery_bse_scrip_code='999999'],
 ['wrong row',p=>p.issuer.source_row_index=28],
 ['wrong issuer',p=>p.issuer.issuer_name='Other Limited'],
 ['extra source',p=>p.issuer.sources.push({...p.issuer.sources[0],key:'extra'})],
 ['external prospectus',p=>p.issuer.sources[1].url='https://example.com/prospectus.pdf'],
 ['query injection',p=>p.issuer.sources[2].url+='?download=1'],
 ['role mutation',p=>p.issuer.sources[2].role='prospectus']
])test('rejects '+name,()=>{const p=structuredClone(plan);mutate(p);assert.throws(()=>validatePlan(json(p)));});

test('rejects queue bytes that do not match the retained queue snapshot',()=>{
 assert.throws(()=>validatePlan(planBytes,{queueBytes:Buffer.from('{}')}),/queue/);
});

test('retains three source responses, hashes and separate clocks without import approval',async t=>{
 const dir=workspace(t),r=await collectEvidence({planBytes,evidenceDir:dir,fetchImpl:fetcher(),clock:clock()});
 assert.equal(r.status,'complete');assert.equal(r.source_documents_accepted,3);assert.equal(r.issuer_landing_links_prospectus,true);
 assert.equal(r.publication_import_allowed,false);assert.equal(r.semantic_review_complete,false);
 assert.equal(r.plan_sha256,hash(planBytes));assert.equal(validateReceipt(r,planBytes,dir).accepted,3);
 assert.deepEqual(fs.readFileSync(path.join(dir,'source-plan.json')),planBytes);
 for(const d of r.documents){
  assert.equal(hash(fs.readFileSync(path.join(dir,d.evidence_file))),d.response_sha256);
  assert.ok(d.requested_at<=d.collected_at);
 }
});

test('records a BSE network failure while retaining issuer sources',async t=>{
 const bse=plan.issuer.sources.find(s=>s.key==='bse_annual_report_2023_24').url;
 const dir=workspace(t),r=await collectEvidence({planBytes,evidenceDir:dir,fetchImpl:fetcher({[bse]:()=>{throw new Error('blocked');}}),clock:clock()});
 assert.equal(r.status,'partial');assert.equal(r.source_documents_accepted,2);
 const failed=r.documents.find(d=>d.url===bse);assert.equal(failed.error,'network_error');assert.equal(failed.response_sha256,null);
 assert.equal(validateReceipt(r,planBytes,dir).accepted,2);
});

test('rejects a HTML challenge masquerading as a prospectus PDF',async t=>{
 const pdf=plan.issuer.sources.find(s=>s.key==='final_prospectus').url;
 const dir=workspace(t),r=await collectEvidence({planBytes,evidenceDir:dir,fetchImpl:fetcher({[pdf]:()=>new Response('<html>blocked</html>',{status:200,headers:{'content-type':'application/pdf'}})}),clock:clock()});
 assert.equal(r.status,'partial');const d=r.documents.find(x=>x.url===pdf);
 assert.equal(d.error,'unexpected_body_type');assert.match(d.evidence_file,/\.response$/);
});

test('requires the official investor-relations page to link the pinned prospectus',async t=>{
 const landing=plan.issuer.sources.find(s=>s.key==='issuer_investor_relations').url;
 const dir=workspace(t),r=await collectEvidence({planBytes,evidenceDir:dir,fetchImpl:fetcher({[landing]:()=>new Response('<!doctype html><html>No prospectus link</html>',{headers:{'content-type':'text/html'}})}),clock:clock()});
 assert.equal(r.source_documents_accepted,3);assert.equal(r.issuer_landing_links_prospectus,false);assert.equal(r.status,'partial');
});

test('refuses oversized bodies rather than retaining truncated evidence',async t=>{
 const pdf=plan.issuer.sources.find(s=>s.key==='final_prospectus').url;
 const dir=workspace(t),r=await collectEvidence({planBytes,evidenceDir:dir,maxSourceBytes:1024,fetchImpl:fetcher({[pdf]:()=>new Response('%PDF-'+ 'x'.repeat(2048))}),clock:clock()});
 const d=r.documents.find(x=>x.url===pdf);assert.equal(d.error,'source_size_limit');assert.equal(d.evidence_file,null);assert.equal(r.status,'partial');
});

test('refuses reuse of an evidence directory',async t=>{
 const dir=workspace(t);fs.mkdirSync(dir);
 await assert.rejects(()=>collectEvidence({planBytes,evidenceDir:dir,fetchImpl:fetcher(),clock:clock()}),/exist/i);
});

test('detects forged receipt flags, hashes, clocks and path traversal',async t=>{
 const dir=workspace(t),r=await collectEvidence({planBytes,evidenceDir:dir,fetchImpl:fetcher(),clock:clock()});
 for(const mutate of [
  x=>x.plan_sha256='0'.repeat(64),
  x=>x.publication_import_allowed=true,
  x=>x.semantic_review_complete=true,
  x=>x.total_response_bytes++,
  x=>x.documents[0].response_sha256='0'.repeat(64),
  x=>x.documents[0].evidence_file='../outside.html',
  x=>x.documents[0].requested_at='2099-01-01T00:00:00.000Z',
  x=>x.issuer_landing_links_prospectus=false,
  x=>x.documents.pop()
 ]){const bad=structuredClone(r);mutate(bad);assert.throws(()=>validateReceipt(bad,planBytes,dir));}
 fs.appendFileSync(path.join(dir,r.documents[0].evidence_file),'tamper');
 assert.throws(()=>validateReceipt(r,planBytes,dir));
});
