import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {context,expected,MANIFEST} from './apply-reviewed-bse-2023-irms.mjs';
import {expectedPublic} from './verify-bse-2023-rvpe.mjs';
import {LIVE_DATA_URL,fetchPublishedSnapshot} from './verify-bse-publication.mjs';
import {sha256} from './verify-bse-listing-candidates.mjs';
import {canonicalIssuer} from './sync-sebi-documents.mjs';
const stamp=v=>typeof v==='string'&&Number.isFinite(Date.parse(v));
export async function verifyIrmsPublication({ctx=context(),fetchImpl=fetch,outputDir=null,clock=()=>new Date().toISOString()}={}){
 if(outputDir)fs.mkdirSync(outputDir); // Never mix a previous fetch with this one.
 const report={ok:false,release_pr:342,url:LIVE_DATA_URL,manifest:MANIFEST,started_at:clock(),snapshot_fetched_at:null,checked_at:null,response_sha256:null,response_bytes:null,generated_at:null,published_records:null,records:[],error:null};
 try{
  const targets=expected(ctx).map(expectedPublic),bytes=await fetchPublishedSnapshot(fetchImpl);
  report.snapshot_fetched_at=clock();report.response_sha256=sha256(bytes);report.response_bytes=bytes.length;
  if(outputDir)fs.writeFileSync(path.join(outputDir,'live-data.json'),bytes,{flag:'wx'});
  const data=JSON.parse(bytes);report.generated_at=data.generated_at;report.published_records=data.records?.length??null;
  report.checked_at=clock();
  assert.ok([report.started_at,report.snapshot_fetched_at,report.checked_at,data.generated_at].every(stamp),'invalid_snapshot_clock');
  assert.ok(Date.parse(report.started_at)<=Date.parse(report.snapshot_fetched_at)&&Date.parse(report.snapshot_fetched_at)<=Date.parse(report.checked_at),'non_monotonic_fetch_clock');
  assert.ok(Date.parse(data.generated_at)<=Date.parse(report.checked_at)&&targets.every(t=>Date.parse(t.last_collected_at)<=Date.parse(data.generated_at)),'invalid_generation_clock');
  assert.equal(data.schema_version,'1.2.0','invalid_public_schema');assert.ok(Array.isArray(data.records),'missing_public_records');
  const byId=new Map();
  for(const r of data.records){assert.ok(typeof r?.id==='string'&&r.id&&!byId.has(r.id),'duplicate_or_invalid_live_id');byId.set(r.id,r);}
  for(const target of targets){
   assert.equal(data.records.filter(r=>canonicalIssuer(r.issuer_name)===canonicalIssuer(target.issuer_name)).length,1,'duplicate_or_missing_canonical_issuer');
   assert.deepEqual(byId.get(target.id),target,'public_projection_mismatch:'+target.id);
  }
  report.records=targets.map(t=>t.id);report.ok=true;
  return report;
 }catch(e){report.error=e.message;report.checked_at=clock();throw e;}
 finally{if(outputDir)fs.writeFileSync(path.join(outputDir,'verification.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});}
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
 const arg=process.argv[2];
 if(process.argv.length!==3||!arg.startsWith('--output-dir=')){console.error('use --output-dir=NEW_ABSOLUTE_DIRECTORY');process.exitCode=1;}
 else{const dir=arg.slice('--output-dir='.length);if(!path.isAbsolute(dir)){console.error('absolute_directory_required');process.exitCode=1;}else verifyIrmsPublication({outputDir:dir}).then(r=>console.log(JSON.stringify(r,null,2))).catch(e=>{console.error(e.message);process.exitCode=1;});}
}
