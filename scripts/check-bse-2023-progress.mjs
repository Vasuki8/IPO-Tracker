import fs from 'node:fs';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {sha256} from './verify-bse-listing-candidates.mjs';
import {canonicalIssuer} from './sync-sebi-documents.mjs';
export const QUEUE='data/discovery/bse-2023-review-queue-2026-09-28.json';
export const PROGRESS='data/discovery/bse-2023-review-progress-2026-09-28.json';
const ROOT=fileURLToPath(new URL('../',import.meta.url));
const LIVE='https://vasuki8.github.io/IPO-Tracker/data/ipos.json';
const PUBLISHED='published_reviewed_ipo',AWAITING='awaiting_review';
const req=(ok,message)=>{if(!ok)throw new Error(message);};
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const gitHash=v=>typeof v==='string'&&/^[a-f0-9]{40}$/.test(v);
const gitBlob=bytes=>{const b=Buffer.from(bytes);return createHash('sha1').update(Buffer.from('blob '+b.length+'\0')).update(b).digest('hex');};
const clock=v=>typeof v==='string'&&/^\d{4}-\d{2}-\d{2}T.*Z$/.test(v)&&Number.isFinite(Date.parse(v));
const nonnegative=v=>Number.isSafeInteger(v)&&v>=0;
const safeManifest=p=>typeof p==='string'&&/^data\/verified-bse-listings\/[a-z0-9-]+\.json$/.test(p);
const safeReview=p=>typeof p==='string'&&/^data\/discovery\/[a-z0-9-]+\.json$/.test(p);
const safeReceipt=p=>typeof p==='string'&&/^docs\/verification\/[a-z0-9-]+\.json$/.test(p);
const parse=b=>JSON.parse(Buffer.from(b).toString('utf8'));
function unique(records,label){
 req(Array.isArray(records),'invalid_'+label+'_records');const map=new Map();
 for(const r of records){req(typeof r?.id==='string'&&r.id.length>0&&!map.has(r.id),'duplicate_or_missing_'+label+'_id');map.set(r.id,r);}
 return map;
}
function section(text,heading){
 req(typeof text==='string','missing_handoff');const parts=text.split(heading);req(parts.length===2,'missing_or_duplicate_section:'+heading);
 return parts[1].split(/\n#{1,6} /)[0];
}
// The source queue is immutable discovery evidence. Only explicit reviewed
// release references close candidates; name/code matches merely raise warnings.
export function validateProgress({queueBytes,progress:p,recoveryByYear,published,manifests,reviewBytes,liveReceipts,projectStatus,readme}){
 const q=parse(queueBytes);
 req(q?.schema_version==='1.0.0'&&q.status==='discovery_only_review_queue'&&q.source_year===2023&&q.auto_import_allowed===false&&q.complete_indian_ipo_universe===false&&q.source_refetched===false&&Array.isArray(q.rows),'invalid_source_queue');
 req(p?.schema_version==='1.0.0'&&p.status==='reviewed_queue_progress'&&p.source_year===2023&&p.auto_import_allowed===false&&p.source_refetched===false&&p.complete_indian_ipo_universe===false,'unsafe_progress_scope');
 req(p.source_queue===QUEUE&&hash(p.source_queue_sha256)&&p.source_queue_sha256===sha256(queueBytes),'source_queue_binding_mismatch');
 req(clock(p.source_collected_at)&&p.source_collected_at===q.source_collected_at&&clock(p.reviewed_at)&&Date.parse(p.reviewed_at)>=Date.parse(p.source_collected_at),'invalid_progress_clock');
 req([p.original_candidates,p.reviewed_and_published,p.awaiting_review].every(nonnegative)&&p.original_candidates===q.rows.length&&p.reviewed_and_published+p.awaiting_review===p.original_candidates&&Array.isArray(p.rows)&&p.rows.length===q.rows.length,'progress_count_mismatch');
 const source=new Map(),indices=new Set();
 for(const r of q.rows){req(/^\d{6}$/.test(r.bse_scrip_code)&&r.source_year===2023&&nonnegative(r.source_row_index)&&!indices.has(r.source_row_index)&&!source.has(r.bse_scrip_code)&&typeof r.issuer_name==='string','invalid_source_identity');source.set(r.bse_scrip_code,r);indices.add(r.source_row_index);}
 req(recoveryByYear&&typeof recoveryByYear==='object','invalid_recovery');
 const recoveryRows=Object.entries(recoveryByYear).flatMap(([year,m])=>{req(/^20\d{2}$/.test(year)&&Array.isArray(m.records),'invalid_recovery_year');return m.records.map(r=>({...r,recovery_year:Number(year)}));});
 const recovery=unique(recoveryRows,'recovery');req(published?.schema_version==='1.2.0','invalid_public_schema');const publicIndex=unique(published.records,'public');
 const codes=new Set(),warnings=[];let completed=0,awaiting=0;
 for(const row of p.rows){
  const original=source.get(row.bse_scrip_code);req(original&&!codes.has(row.bse_scrip_code)&&row.source_row_index===original.source_row_index,'progress_row_identity_mismatch');codes.add(row.bse_scrip_code);
  req([PUBLISHED,AWAITING].includes(row.disposition),'unknown_disposition');
  if(row.disposition===AWAITING){
   req(['stable_id','manifest','release_pr','live_receipt'].every(k=>row[k]===null),'awaiting_has_release_fields');awaiting++;
   const hits=recoveryRows.filter(r=>canonicalIssuer(r.issuer_name)===canonicalIssuer(original.issuer_name)||String(r.bse_scrip_code??'')===row.bse_scrip_code);
   if(hits.length)warnings.push({code:row.bse_scrip_code,reason:'possible_pending_closeout_or_alias',matches:hits.map(r=>({id:r.id,year:r.recovery_year}))});
   continue;
  }
  completed++;req(typeof row.stable_id==='string'&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(row.stable_id)&&Number.isSafeInteger(row.release_pr)&&row.release_pr>0,'invalid_release_identity');
  req(safeManifest(row.manifest),'unsafe_manifest_path');req(safeReceipt(row.live_receipt),'unsafe_live_receipt_path');
  const m=manifests[row.manifest];req(m&&/^approved_bse_2023_[a-z0-9_]+_import$/.test(m.status)&&m.target_year===2023&&Array.isArray(m.actions)&&m.actions.filter(a=>a.stable_id===row.stable_id).length===1,'unapproved_release_manifest');
  req(safeReview(m.review_path),'unsafe_review_path');const rb=reviewBytes[m.review_path];const sha256Bound=rb&&hash(m.review_sha256)&&sha256(rb)===m.review_sha256,gitBound=rb&&gitHash(m.review_git_blob_sha)&&gitBlob(rb)===m.review_git_blob_sha;req(sha256Bound||gitBound,'release_review_binding_mismatch');
  const review=parse(rb);const action=review.actions?.filter(a=>a.stable_id===row.stable_id&&a.discovery_bse_scrip_code===row.bse_scrip_code);req(action?.length===1&&canonicalIssuer(action[0].issuer_name)===canonicalIssuer(original.issuer_name),'release_discovery_identity_mismatch');
  const r=recovery.get(row.stable_id),pub=publicIndex.get(row.stable_id);
  req(r&&pub&&r.recovery_year===2023&&canonicalIssuer(r.issuer_name)===canonicalIssuer(original.issuer_name)&&canonicalIssuer(pub.issuer_name)===canonicalIssuer(original.issuer_name),'released_identity_not_present');
  const live=liveReceipts[row.live_receipt];
  req(live?.release_pr===row.release_pr,'live_release_pr_mismatch');
  req(live?.ok===true&&live.url===LIVE&&clock(live.checked_at)&&clock(live.generated_at)&&Date.parse(live.generated_at)<=Date.parse(live.checked_at)&&Date.parse(live.checked_at)<=Date.parse(p.reviewed_at),'invalid_live_receipt_clock');
  req(hash(live.response_sha256)&&Number.isSafeInteger(live.response_bytes)&&live.response_bytes>0&&Number.isSafeInteger(live.published_records)&&live.published_records>0&&Array.isArray(live.records)&&new Set(live.records).size===live.records.length&&live.records.includes(row.stable_id),'unverified_live_identity');
 }
 req(completed===p.reviewed_and_published&&awaiting===p.awaiting_review,'declared_counts_disagree');
 const next=p.next_bounded_review_codes;req(Array.isArray(next)&&next.length<=6&&new Set(next).size===next.length&&(awaiting?next.length>0:next.length===0)&&next.every(c=>p.rows.some(r=>r.bse_scrip_code===c&&r.disposition===AWAITING)),'invalid_next_batch');
 for(const text of [section(projectStatus,'## Exact next bounded task'),section(readme,'## Handoff for the next prompt'),section(readme,'### Exact next backend task')]){
  const listed=[...text.matchAll(/\((\d{6})\)/g)].map(m=>m[1]);req(listed.length===next.length&&listed.every(c=>next.includes(c))&&new Set(listed).size===listed.length,'stale_handoff_codes');
  for(const c of next)req(canonicalIssuer(text).includes(canonicalIssuer(source.get(c).issuer_name)),'stale_handoff_name:'+c);
 }
 return{ok:true,original_candidates:p.original_candidates,published:completed,awaiting,next,source_refetched:false,warnings};
}
export function checkProgress(root=ROOT){
 const read=p=>fs.readFileSync(path.join(root,p));const p=parse(read(PROGRESS)),manifests={},reviewBytes={},liveReceipts={};
 req(Array.isArray(p.rows),'invalid_progress_rows');
 for(const row of p.rows.filter(r=>r.disposition===PUBLISHED)){
  req(safeManifest(row.manifest),'unsafe_manifest_path');req(safeReceipt(row.live_receipt),'unsafe_live_receipt_path');
  const m=parse(read(row.manifest));req(safeReview(m.review_path),'unsafe_review_path');manifests[row.manifest]=m;reviewBytes[m.review_path]=read(m.review_path);liveReceipts[row.live_receipt]=parse(read(row.live_receipt));
 }
 const dir=path.join(root,'data/recovery');const recoveryByYear=Object.fromEntries(fs.readdirSync(dir).filter(y=>/^20\d{2}$/.test(y)&&fs.existsSync(path.join(dir,y,'nse-issue-information.json'))).map(y=>[y,parse(read(`data/recovery/${y}/nse-issue-information.json`))]));
 return validateProgress({progress:p,queueBytes:read(QUEUE),recoveryByYear,published:parse(read('data/ipos.json')),manifests,reviewBytes,liveReceipts,projectStatus:read('docs/PROJECT_STATUS.md').toString('utf8'),readme:read('README.md').toString('utf8')});
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){try{console.log(JSON.stringify({bse_2023_progress:checkProgress()},null,2));}catch(e){console.error(e.message);process.exitCode=1;}}
