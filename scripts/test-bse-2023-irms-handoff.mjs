import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
const read=p=>fs.readFileSync(new URL('../'+p,import.meta.url));
const sha=b=>createHash('sha256').update(b).digest('hex');
const workflow=read('.github/workflows/collect-bse-2023-irms-evidence.yml').toString('utf8');
const bundle=JSON.parse(read('data/evidence/bse-2023-irms-source-receipt-2026-09-28.json'));
const planBytes=read('data/discovery/bse-2023-irms-source-plan-2026-09-28.json');
const plan=JSON.parse(planBytes);

test('PR checks are offline and source requests require a manual dispatch',()=>{
 const sections=workflow.split('\n  sources:\n');assert.equal(sections.length,2);
 assert.match(sections[1],/^    if: github\.event_name == 'workflow_dispatch'$/m);
 assert.doesNotMatch(sections[0],/run: node scripts\/collect-bse-2023-irms-evidence\.mjs/);
 assert.match(workflow,/^  workflow_dispatch:$/m);assert.doesNotMatch(workflow,/^  (?:schedule|push):/m);
});
test('collection remains read-only and retains failure evidence without suppressing errors',()=>{
 assert.match(workflow,/permissions:\n  contents: read\n/);
 assert.doesNotMatch(workflow,/contents: write|continue-on-error|git push|git commit|apply-reviewed|build-published-data\.mjs(?! --check)/);
 assert.equal((workflow.match(/persist-credentials: false/g)||[]).length,2);
 assert.match(workflow,/name: Retain complete or partial collection\n        if: always\(\)/);
 assert.match(workflow,/github\.run_id.*github\.run_attempt/);
});
test('retained source set is complete without relabeling either partial collection',()=>{
 assert.equal(bundle.schema_version,'1.0.0');assert.equal(bundle.status,'retained_source_set_complete_across_partial_collections');
 assert.equal(bundle.source_set_complete,true);assert.equal(bundle.single_collection_complete,false);
 for(const k of ['publication_import_allowed','semantic_review_complete','complete_indian_ipo_universe','discovery_source_refetched'])assert.equal(bundle[k],false);
 assert.equal(bundle.plan_sha256,sha(planBytes));assert.equal(bundle.source_queue_sha256,plan.source_queue_sha256);
 assert.equal(bundle.collections.length,2);
 for(const c of bundle.collections){
  assert.equal(c.receipt_sha256,sha(JSON.stringify(c.receipt,null,2)+'\n'));
  assert.equal(c.receipt.status,'partial');assert.equal(c.receipt.plan_sha256,bundle.plan_sha256);
  assert.equal(c.receipt.publication_import_allowed,false);assert.equal(c.receipt.semantic_review_complete,false);
  assert.equal(c.receipt.discovery_source_collected_at,plan.discovery_source_collected_at);
  assert.equal(c.receipt.source_documents_accepted,7);
  assert.equal(c.workflow_run_id,36431201278);assert.equal(c.artifact.retention_days,14);
  assert.match(c.artifact.digest,/^sha256:[a-f0-9]{64}$/);
  assert.equal(c.identity_preflight.ok,true);assert.deepEqual(c.identity_preflight.warnings,[]);
  assert.equal(c.identity_preflight.published,8);assert.equal(c.identity_preflight.awaiting,22);
 }
 assert.equal(bundle.collections[0].receipt.documents.find(d=>d.code==='544053'&&d.kind==='prospectus').accepted,false);
 assert.equal(bundle.collections[1].receipt.documents.find(d=>d.code==='544060'&&d.kind==='prospectus').accepted,false);
});
test('each selected source resolves to accepted original bytes with exact identity and totals',()=>{
 const expected=new Map(plan.issuers.flatMap(i=>['landing','prospectus'].map(kind=>[i.discovery_bse_scrip_code+':'+kind,i[kind+'_url']])));
 assert.equal(bundle.selected_documents.length,8);let total=0;
 for(const s of bundle.selected_documents){
  const key=s.code+':'+s.kind;assert.ok(expected.has(key),'duplicate or unexpected source');
  const c=bundle.collections.find(c=>c.workflow_attempt===s.workflow_attempt);
  const d=c?.receipt.documents.find(d=>d.code===s.code&&d.kind===s.kind);
  assert.ok(d?.accepted);assert.equal(d.url,expected.get(key));expected.delete(key);
  assert.equal(d.evidence_file,s.evidence_file);assert.equal(d.response_sha256,s.response_sha256);
  assert.match(d.response_sha256,/^[a-f0-9]{64}$/);assert.ok(d.response_bytes>0);total+=d.response_bytes;
 }
 assert.equal(expected.size,0);assert.equal(total,bundle.unique_response_bytes);assert.equal(total,39977695);
 assert.equal(bundle.total_retained_response_bytes,bundle.collections.reduce((n,c)=>n+c.receipt.total_response_bytes,0));
 for(const i of plan.issuers)assert.equal(i.document_date,null,'do not rewrite the original collection plan as a field approval');
 for(const c of bundle.collections)for(const d of c.receipt.documents.filter(d=>d.accepted)){
  const selected=bundle.selected_documents.find(s=>s.code===d.code&&s.kind===d.kind);
  assert.equal(d.response_sha256,selected.response_sha256,'changed source versions require explicit conflict review');
 }
});
