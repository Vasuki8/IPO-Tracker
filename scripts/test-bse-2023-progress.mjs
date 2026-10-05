import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {createHash} from 'node:crypto';
import {validateProgress,checkProgress,PROGRESS,QUEUE} from './check-bse-2023-progress.mjs';
const digest=b=>createHash('sha256').update(b).digest('hex');
const gitBlob=b=>{const bytes=Buffer.from(b);return createHash('sha1').update(Buffer.from('blob '+bytes.length+'\0')).update(bytes).digest('hex');};
const fixture=()=>{
 const rows=[{issuer_name:'First Limited',bse_scrip_code:'543743',source_year:2023,source_row_index:1},{issuer_name:'Next Limited',bse_scrip_code:'543998',source_year:2023,source_row_index:2}];
 const queue={schema_version:'1.0.0',status:'discovery_only_review_queue',source_year:2023,auto_import_allowed:false,complete_indian_ipo_universe:false,source_refetched:false,source_collected_at:'2026-09-26T16:40:34.440Z',rows};
 const qb=Buffer.from(JSON.stringify(queue));
 const manifest='data/verified-bse-listings/2026-09-28-fixture.json',reviewPath='data/discovery/fixture-review.json',receipt='docs/verification/fixture-live.json';
 const review={actions:[{stable_id:'first-limited',discovery_bse_scrip_code:'543743',issuer_name:'First Limited'}]},rb=Buffer.from(JSON.stringify(review));
 const done={bse_scrip_code:'543743',source_row_index:1,disposition:'published_reviewed_ipo',stable_id:'first-limited',manifest,release_pr:329,live_receipt:receipt};
 const waiting={bse_scrip_code:'543998',source_row_index:2,disposition:'awaiting_review',stable_id:null,manifest:null,release_pr:null,live_receipt:null};
 const record={id:'first-limited',issuer_name:'First Limited',listing_date:{value:'2023-01-12'}};
 return{queueBytes:qb,progress:{schema_version:'1.0.0',status:'reviewed_queue_progress',source_year:2023,source_queue:QUEUE,source_queue_sha256:digest(qb),source_collected_at:queue.source_collected_at,reviewed_at:'2026-09-28T04:50:00.000Z',auto_import_allowed:false,source_refetched:false,complete_indian_ipo_universe:false,original_candidates:2,reviewed_and_published:1,awaiting_review:1,next_bounded_review_codes:['543998'],rows:[done,waiting]},recoveryByYear:{2023:{records:[record]}},published:{schema_version:'1.2.0',records:[record]},manifests:{[manifest]:{status:'approved_bse_2023_fixture_import',target_year:2023,review_path:reviewPath,review_sha256:digest(rb),actions:[{key:'first',stable_id:'first-limited'}]}},reviewBytes:{[reviewPath]:rb},liveReceipts:{[receipt]:{release_pr:329,ok:true,url:'https://vasuki8.github.io/IPO-Tracker/data/ipos.json',checked_at:'2026-09-28T04:20:53.915Z',generated_at:'2026-09-28T04:19:55.164Z',response_bytes:1000,response_sha256:'a'.repeat(64),published_records:1,records:['first-limited']}},projectStatus:'## Exact next bounded task\nNext Limited (543998)\n## History\nFirst Limited (543743)',readme:'## Handoff for the next prompt\nNext Limited (543998)\n### Exact next backend task\nNext Limited (543998)\n## History\nFirst Limited (543743)'};
};
const base=fixture();
assert.deepEqual(validateProgress(base),{ok:true,original_candidates:2,published:1,awaiting:1,next:['543998'],source_refetched:false,warnings:[]});
const gitPinned=fixture();const gitManifest=Object.values(gitPinned.manifests)[0],gitReview=Object.values(gitPinned.reviewBytes)[0];delete gitManifest.review_sha256;gitManifest.review_git_blob_sha=gitBlob(gitReview);assert.equal(validateProgress(gitPinned).ok,true,'git-blob-pinned reviewed releases must remain valid');
const publicationStyle=fixture();
{
 const manifest=Object.values(publicationStyle.manifests)[0];
 const oldPath=manifest.review_path;
 const modernPath='data/discovery/fixture-publication-review.json';
 const modernReview={candidate:{stable_id:'first-limited',discovery_bse_scrip_code:'543743',issuer_name:'First Limited'}};
 const modernBytes=Buffer.from(JSON.stringify(modernReview));
 delete publicationStyle.reviewBytes[oldPath];
 delete manifest.review_path;
 delete manifest.review_sha256;
 manifest.publication_review_path=modernPath;
 manifest.publication_review_git_blob_sha=gitBlob(modernBytes);
 publicationStyle.reviewBytes[modernPath]=modernBytes;
 assert.equal(validateProgress(publicationStyle).ok,true,'single-candidate publication reviews must close progress when Git-blob pinned');
}
let rejected=0;
for(const mutate of [
 x=>x.progress.auto_import_allowed=true,x=>x.progress.source_refetched=true,x=>x.progress.complete_indian_ipo_universe=true,
 x=>x.progress.source_queue='../other.json',x=>x.progress.source_queue_sha256='0'.repeat(64),x=>x.progress.source_collected_at=x.progress.reviewed_at,x=>x.progress.reviewed_at='2020-01-01T00:00:00Z',x=>x.progress.reviewed_at='bad',
 x=>x.progress.original_candidates++,x=>x.progress.reviewed_and_published++,x=>x.progress.awaiting_review++,x=>x.progress.rows.pop(),x=>x.progress.rows.push(x.progress.rows[0]),x=>x.progress.rows[1].source_row_index=1,
 x=>x.progress.rows[1].bse_scrip_code='999999',x=>x.progress.rows[1].disposition='invented',x=>x.progress.rows[1].stable_id='unapproved',x=>x.progress.rows[1].release_pr=999,
 x=>x.progress.rows[0].manifest='../secret.json',x=>x.progress.rows[0].live_receipt='../secret.json',x=>x.progress.rows[0].release_pr=0,x=>x.progress.rows[0].stable_id='next-limited',
 x=>x.progress.next_bounded_review_codes=['543743'],x=>x.progress.next_bounded_review_codes=['543998','543998'],x=>x.progress.next_bounded_review_codes=[],x=>x.progress.next_bounded_review_codes=['999999'],
 x=>x.recoveryByYear[2022]=x.recoveryByYear[2023],x=>{x.recoveryByYear[2022]=x.recoveryByYear[2023];delete x.recoveryByYear[2023];},x=>x.recoveryByYear[2023].records=[],x=>x.published.records=[],x=>x.published.records.push(x.published.records[0]),x=>x.published.records[0]={...x.published.records[0],issuer_name:'Other'},
 x=>Object.values(x.manifests)[0].actions=[],x=>Object.values(x.manifests)[0].target_year=2024,x=>Object.values(x.manifests)[0].status='discovery',x=>Object.values(x.manifests)[0].review_path='../escape.json',x=>Object.values(x.manifests)[0].review_sha256='0'.repeat(64),
 x=>{const m=Object.values(x.manifests)[0];m.publication_review_path='data/discovery/other-review.json';},
 x=>x.progress.rows[0].release_pr=330,x=>Object.values(x.liveReceipts)[0].release_pr=330,
 x=>Object.values(x.liveReceipts)[0].ok=false,x=>Object.values(x.liveReceipts)[0].records=[],x=>Object.values(x.liveReceipts)[0].response_sha256='bad',x=>Object.values(x.liveReceipts)[0].checked_at='2099-01-01T00:00:00Z',x=>Object.values(x.liveReceipts)[0].url='https://evil.example',x=>Object.values(x.liveReceipts)[0].generated_at='2099-01-01T00:00:00Z',
 x=>x.projectStatus=x.projectStatus.replace('Next Limited','Wrong Issuer'),x=>x.projectStatus=x.projectStatus.replace('543998','543743'),x=>x.readme=x.readme.replace('Next Limited','First Limited'),x=>x.readme=x.readme.replaceAll('543998','543743'),x=>x.readme='missing sections'
]){const x=structuredClone(base);mutate(x);assert.throws(()=>validateProgress(x));rejected++;}
const pending=fixture();pending.recoveryByYear[2023].records.push({id:'next-limited',issuer_name:'Next Limited'});assert.equal(validateProgress(pending).warnings[0].code,'543998');assert.equal(pending.progress.rows[1].disposition,'awaiting_review');
const changedDiscovery=fixture();const q=JSON.parse(changedDiscovery.queueBytes);q.rows[0].discovery_issue_price=999;q.rows[0].discovery_listing_date='2025-01-01';changedDiscovery.queueBytes=Buffer.from(JSON.stringify(q));changedDiscovery.progress.source_queue_sha256=digest(changedDiscovery.queueBytes);assert.equal(validateProgress(changedDiscovery).ok,true,'discovery facts cannot correct published facts');
const noPending=fixture();noPending.progress.rows.pop();noPending.progress.original_candidates=1;noPending.progress.awaiting_review=0;noPending.progress.next_bounded_review_codes=[];const sq=JSON.parse(noPending.queueBytes);sq.rows.pop();noPending.queueBytes=Buffer.from(JSON.stringify(sq));noPending.progress.source_queue_sha256=digest(noPending.queueBytes);noPending.projectStatus='## Exact next bounded task\nQueue complete.';noPending.readme='## Handoff for the next prompt\nQueue complete.\n### Exact next backend task\nQueue complete.';assert.equal(validateProgress(noPending).awaiting,0);
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'ipo-progress-'));try{
 const put=(p,v)=>{fs.mkdirSync(path.dirname(path.join(tmp,p)),{recursive:true});fs.writeFileSync(path.join(tmp,p),typeof v==='string'||Buffer.isBuffer(v)?v:JSON.stringify(v));};
 put(PROGRESS,base.progress);put(QUEUE,base.queueBytes);put('data/ipos.json',base.published);put('data/recovery/2023/nse-issue-information.json',base.recoveryByYear[2023]);put('docs/PROJECT_STATUS.md',base.projectStatus);put('README.md',base.readme);
 for(const [p,m] of Object.entries(base.manifests))put(p,m);for(const [p,b] of Object.entries(base.reviewBytes))put(p,b);for(const [p,r] of Object.entries(base.liveReceipts))put(p,r);
 const files=fs.readdirSync(tmp,{recursive:true}).map(p=>path.join(tmp,p)).filter(p=>fs.statSync(p).isFile());const original=files.map(p=>fs.readFileSync(p));assert.equal(checkProgress(tmp).ok,true);files.forEach((p,i)=>assert.deepEqual(fs.readFileSync(p),original[i]));
 const bad=structuredClone(base.progress);bad.rows[0].manifest='../missing-secret.json';put(PROGRESS,bad);assert.throws(()=>checkProgress(tmp),/unsafe_manifest_path/);
}finally{fs.rmSync(tmp,{recursive:true,force:true});}
console.log(JSON.stringify({bse_2023_progress_tests:{rejected_mutations:rejected,immutable_source_clock:true,source_fact_non_authority:true,pending_closeout_warning:true,complete_queue:true,read_only:true}}));
