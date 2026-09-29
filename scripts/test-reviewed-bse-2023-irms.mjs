import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {sha256} from './verify-bse-listing-candidates.mjs';
import {expectedPublic} from './verify-bse-2023-rvpe.mjs';
const moduleUrl=new URL('./apply-reviewed-bse-2023-irms.mjs',import.meta.url);
assert.ok(fs.existsSync(moduleUrl),'the reviewed IRMS importer must exist');
const {context,validate,expected,apply,loadRecovery,verifyOriginals}=await import(moduleUrl.href);
const ctx=context(),now='2026-09-29T15:00:00.000Z';
const clone=()=>structuredClone(ctx),raw=()=>expected(ctx);
const fixture=()=>Object.fromEntries([2020,2021,2022,2023,2024,2025,2026].map(y=>[y,{schema_version:'1.0.0',generated_at:'2026-09-28T01:00:00.000Z',records:[{id:`unrelated-${y}`,issuer_name:`Other ${y} Limited`,evidence:{held:null,history:['retain']}}]}]));
test('validates the separately approved four-issuer listing review and original prospectus review',()=>{
 assert.deepEqual(validate(ctx),{ok:true,records:4,verified:28,provisional:2,conflict:1,missing:1});
 assert.equal(ctx.fieldContext.review.publication_import_allowed,false);
 assert.ok(ctx.fieldContext.review.actions.every(a=>a.terms.listing_date.value===null));
 assert.equal(ctx.receipt.collections[0].receipt.status,'partial');
 assert.ok(ctx.receipt.collections[0].receipt.documents.every(d=>d.status===404&&!d.accepted));
});
test('constructs exact listing dates, historical lots and supported exchange identifiers',()=>{
 const records=raw();
 assert.deepEqual(records.map(r=>r.listing_date.value),['2023-11-29','2023-12-26','2023-12-27','2023-08-23']);
 assert.deepEqual(records.map(r=>r.market_lot.value),[1,1,1,3000]);
 assert.deepEqual(records.map(r=>r.minimum_bid_quantity.value),[460,250,150,3000]);
 assert.deepEqual(records.map(r=>r.bse_scrip_code),['544026','544053','544060','543963']);
 assert.deepEqual(records.map(r=>r.nse_symbol),['IREDA','MOTISONS','RBZJEWEL',null]);
 for(const r of records){assert.equal(r.board,null);assert.equal(r.isin,null);assert.equal(r.status,'listed');assert.equal(r.status_evidence[0].document_type,'Exchange-hosted Annual Report PDF');assert.equal(r.minimum_application_amount_inr,undefined);}
 assert.equal(records[3].price_band.value,null);
 assert.equal(records[3].price_band.status,'missing');
});
test('retains both IREDA amount observations and does not promote provisional proceeds',()=>{
 const [i,m,r,s]=raw();
 assert.equal(i.issue_size_inr.value,21502120000);assert.equal(i.issue_size_inr.status,'conflict');
 assert.equal(i.issue_size_inr.additional_sources[0].page,38);
 assert.equal(i.issue_size_inr.corrections[0].competing_observations[0].value,21502200000);
 assert.equal(i.issue_size_inr.corrections[0].preferred_candidate.original_status,'provisional');
 assert.equal(m.issue_size_inr.status,'provisional');assert.equal(r.issue_size_inr.status,'provisional');
 assert.equal(s.issue_size_inr.value,160272000);assert.equal(s.issue_size_inr.status,'verified');
 assert.match(i.issue_size_inr.qualification,/Basis of Allotment/);
});
test('adds exactly four, keeps every unrelated year and record unchanged, then reruns without changes',()=>{
 const before=fixture(),copy=structuredClone(before),first=apply(before,ctx,now);
 assert.equal(first.stats.added,4);assert.equal(first.stats.skipped,0);assert.deepEqual(before,copy);
 for(const y of Object.keys(before)){assert.deepEqual(first.recovery[y].records.filter(r=>r.id.startsWith('unrelated-')),before[y].records);if(y!=='2023')assert.deepEqual(first.recovery[y],before[y]);}
 const second=apply(first.recovery,ctx,'2026-09-29T16:00:00.000Z');
 assert.deepEqual(second.stats,{records:4,added:0,skipped:4,changed:false});assert.deepEqual(second.recovery,first.recovery);
});
for(const y of ['2020','2022','2024','2026'])for(const key of ['id','issuer_name','bse_scrip_code','nse_symbol'])test(`rejects ${y} ${key} collision without mutating input`,()=>{
 const all=fixture(),target=raw()[0],collision={id:'alias-record',issuer_name:'Some prior alias Limited',[key]:key==='issuer_name'?target.issuer_name.toUpperCase():target[key]};
 all[y].records.push(collision);const before=structuredClone(all);assert.throws(()=>apply(all,ctx,now),/identity_collision/);assert.deepEqual(all,before);
});
for(const key of ['issue_price','listing_date','documents','last_collected_at','bse_2023_irms_import'])test(`rejects replay over enriched ${key}`,()=>{
 const first=apply(fixture(),ctx,now).recovery,record=first['2023'].records.find(r=>r.id===raw()[0].id);
 if(key==='documents')record.documents.push({url:'https://www.sebi.gov.in/new.pdf'});
 else if(key==='last_collected_at')record[key]='2026-10-01T00:00:00.000Z';
 else if(key==='bse_2023_irms_import')delete record[key];
 else record[key].value=key==='issue_price'?33:'2023-11-30';
 assert.throws(()=>apply(first,ctx,now),/changed_import_record/);
});
for(const [name,mutate] of [
 ['listing date',c=>c.review.actions[0].listing_date.value='2023-11-28'],
 ['approval date substituted',c=>c.review.actions[1].listing_date.value='2023-08-02'],
 ['listing page',c=>c.review.actions[2].listing_date.page=1],
 ['listing year',c=>c.review.source_year=2024],
 ['wrong issuer',c=>c.review.actions[0].issuer_name='Other Limited'],
 ['extra candidate',c=>c.review.actions.push(c.review.actions[0])],
 ['wrong BSE code',c=>c.review.actions[3].identifiers.bse_scrip_code.value='999999'],
 ['invented board',c=>c.review.actions[0].identifiers.board='Mainboard'],
 ['invented ISIN',c=>c.review.actions[0].identifiers.isin='INE202E01016'],
 ['source host substitution',c=>c.review.actions[0].document.url='https://example.com/report.pdf'],
 ['unretained archives mirror',c=>c.review.actions[0].document.url=c.review.actions[0].document.url.replace('nsearchives.','archives.')],
 ['receipt date laundering',c=>c.receipt.collections[1].receipt.documents[0].collected_at=now],
 ['relabel 404 success',c=>c.receipt.collections[0].receipt.documents[0].accepted=true],
 ['lost amount conflict',c=>c.review.actions[0].amount_conflict=null],
 ['annual amount unit',c=>c.review.actions[0].amount_conflict.competing_observation.source_unit='INR lakh'],
 ['annual amount changed',c=>c.review.actions[0].amount_conflict.competing_observation.value=21502120000],
 ['lost approval inconsistency',c=>c.review.actions[1].document_inconsistencies=[]],
 ['fabricated publication date',c=>c.review.actions[3].document.publication_date='2024-09-07'],
 ['collection becomes review clock',c=>c.review.actions[3].document.collected_at=c.review.reviewed_at],
 ['review before source',c=>c.review.reviewed_at='2024-09-07T01:00:00.000Z'],
 ['self-approved manifest',c=>c.manifest.actions[0].stable_id='different-id'],
 ['old prospectus changed',c=>c.fieldContext.review.actions[0].terms.issue_size_inr.status='verified_stated_term']
])test(`rejects ${name}`,()=>{const c=clone();mutate(c);assert.throws(()=>validate(c));});
test('rejects altered raw field-review/source bytes and invalid generation clocks',()=>{
 for(const k of ['reviewBytes','receiptBytes','fieldReviewBytes']){const c=clone();c[k]=Buffer.from('{}');assert.throws(()=>validate(c));}
 for(const n of ['not a clock','2023-01-01T00:00:00.000Z'])assert.throws(()=>apply(fixture(),ctx,n));
 const d=fixture();d['2024'].records[0].id=d['2020'].records[0].id;assert.throws(()=>apply(d,ctx,now),/duplicate_existing_id/);
});
test('original-byte revalidation fails closed on missing and forged source files',t=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'irms-original-test-'));t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
 assert.throws(()=>verifyOriginals(ctx,dir));
 for(const a of ctx.review.actions)fs.writeFileSync(path.join(dir,a.document.evidence_file),'%PDF-1.7\nforged');
 assert.throws(()=>verifyOriginals(ctx,dir),/original_bytes_mismatch/);
});
test('isolated pre-import copy tolerates later production enrichment without replay; amount nulls stay missing',()=>{
 const production=loadRecovery(),before=structuredClone(production),all=structuredClone(production),ids=new Set(raw().map(r=>r.id));
 for(const m of Object.values(all))m.records=m.records.filter(r=>!ids.has(r.id));
 const r=apply(all,ctx,now);assert.deepEqual(production,before);assert.equal(r.stats.added,4);
 for(const record of raw().map(expectedPublic)){
  assert.equal(record.minimum_application_amount_inr.value,null);
  assert.ok(Object.values(record.application_requirements).every(x=>x.minimum_application_amount_inr.value===null));
  assert.ok(record.listing_date.evidence[0].url.startsWith('https://'));
 }
});
const verifierUrl=new URL('./verify-bse-2023-irms.mjs',import.meta.url);
test('publication verification implementation is required',()=>assert.ok(fs.existsSync(verifierUrl)));
const published=()=>({schema_version:'1.2.0',generated_at:'2026-09-29T14:30:00.000Z',records:raw().map(expectedPublic)});
async function verifyData(data,t){
 const {verifyIrmsPublication}=await import(verifierUrl.href);
 const base=fs.mkdtempSync(path.join(os.tmpdir(),'irms-live-test-'));t.after(()=>fs.rmSync(base,{recursive:true,force:true}));
 const dir=path.join(base,'snapshot'),body=Buffer.from(JSON.stringify(data));
 const result=await verifyIrmsPublication({ctx,outputDir:dir,clock:()=>now,fetchImpl:async(url,options)=>{
  assert.equal(url,'https://vasuki8.github.io/IPO-Tracker/data/ipos.json');assert.equal(options.redirect,'error');return new Response(body);
 }});
 assert.equal(result.response_sha256,sha256(body));assert.deepEqual(fs.readFileSync(path.join(dir,'live-data.json')),body);return result;
}
test('checks every exact public field and retains actual fetched bytes and separate clocks',async t=>{
 const r=await verifyData(published(),t);assert.equal(r.ok,true);assert.equal(r.records.length,4);assert.equal(r.release_pr,342);assert.equal(r.generated_at,'2026-09-29T14:30:00.000Z');assert.equal(r.checked_at,now);
});
for(const [name,change] of [
 ['missing issuer',d=>d.records.pop()],['duplicate id',d=>d.records.push(d.records[0])],
 ['duplicate canonical name',d=>d.records.push({...d.records[0],id:'duplicate-issuer'})],
 ['missing amount conflict',d=>d.records[0].issue_size_inr.status='verified'],
 ['minimum amount inference',d=>d.records[0].minimum_application_amount_inr.value=14720],
 ['listing date drift',d=>d.records[1].listing_date.value='2023-12-25'],
 ['lot-bid mixup',d=>d.records[2].market_lot.value=150],
 ['wrong evidence clock',d=>d.records[3].listing_date.evidence[0].collected_at=now],
 ['future generation',d=>d.generated_at='2099-01-01T00:00:00.000Z'],
 ['generation before collected sources',d=>d.generated_at='2023-12-31T00:00:00.000Z']
])test(`live verification rejects ${name}`,async t=>{const d=published();change(d);await assert.rejects(()=>verifyData(d,t));});

test('one-shot publisher uses only the existing active workflow and is retired after closeout',()=>{
 const root=new URL('../',import.meta.url),workflow=fs.readFileSync(new URL('.github/workflows/update-ipos.yml',root),'utf8');
 const file=new URL('docs/verification/bse-2023-irms-release-2026-09-29.json',root);
 assert.ok(fs.existsSync(file),'explicit release lifecycle record required');const state=JSON.parse(fs.readFileSync(file));
 if(['prepared_import_pending','published_verification_pending'].includes(state.status)){
  assert.match(workflow,/reviewed_irms:/,'bounded publisher required while pending');
  assert.match(workflow,/github.event_name == 'push' && startsWith\(github.event.head_commit.message, 'release\(irms\):'\)/);
  const job=workflow.split('  reviewed_irms:')[1].split('  sync:')[0];
  assert.match(job,/git fetch origin main/);assert.match(job,/git reset --hard origin\/main/);
  assert.match(job,/apply-reviewed-bse-2023-irms\.mjs --apply/);
  assert.match(job,/git add data\/recovery\/2023\/nse-issue-information\.json data\/ipos\.json/);
  assert.doesNotMatch(job,/curl |wget |sync-nse|collect-|continue-on-error/);
 }else{
  assert.equal(state.status,'verified_and_publisher_retired');assert.equal(state.new_public_records,4);
  assert.doesNotMatch(workflow,/reviewed_irms:|apply-reviewed-bse-2023-irms\.mjs --apply/);
  const live=JSON.parse(fs.readFileSync(new URL(state.live_receipt,root)));assert.equal(live.ok,true);assert.equal(live.release_pr,342);assert.equal(live.records.length,4);
 }
 assert.equal(fs.existsSync(new URL('.github/workflows/research-irms-listing-originals.yml',root)),false,'temporary research workflow must not remain');
});
