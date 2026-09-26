import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {validateDrhpData} from './drhp-integrity.mjs';
const args=process.argv.slice(2);
if(args.length!==1||!args[0].startsWith('--output-dir='))throw new Error('use --output-dir=PATH');
const out=path.resolve(args[0].slice(13));fs.mkdirSync(out,{recursive:true});
const hash=b=>createHash('sha256').update(b).digest('hex');
const report={schema_version:'1.0.0',status:'failed',checked_at:null,files:[],errors:[]};
for(const file of ['data/drhp-filings.json','drhp.html','assets/pre-ipo-filter.js','assets/drhp.js','assets/styles.css','index.html']){
  const url='https://vasuki8.github.io/IPO-Tracker/'+file+'?verify='+Date.now();
  try{
    const r=await fetch(url,{cache:'no-store',signal:AbortSignal.timeout(20000)}),bytes=Buffer.from(await r.arrayBuffer());
    const fetched_at=new Date().toISOString();fs.writeFileSync(path.join(out,file.replaceAll('/','-')),bytes);
    const expected=fs.readFileSync(file),match=r.ok&&hash(bytes)===hash(expected);
    report.files.push({path:file,url,status:r.status,fetched_at,sha256:hash(bytes),expected_sha256:hash(expected),bytes:bytes.length,match});
    if(!match)report.errors.push('served_bytes_mismatch:'+file);
    if(file==='data/drhp-filings.json'&&r.ok){const d=JSON.parse(bytes);report.counts=validateDrhpData(d);report.source_collection_completed_at=d.collection_completed_at;report.dataset_generated_at=d.generated_at;report.retained_not_seen_latest=d.coverage.retained_not_seen_latest;report.pagination_consistent=d.coverage.pagination_consistent;}
  }catch(e){report.errors.push(file+':'+String(e));}
}
report.checked_at=new Date().toISOString();report.status=report.errors.length?'failed':'verified';
fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));if(report.errors.length)process.exitCode=1;
