import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {canonicalIssuer} from './sync-sebi-documents.mjs';

const ROOT=fileURLToPath(new URL('../',import.meta.url));
export const TARGETS=[
  {code:'544059',issuer_name:'SHANTI SPINTEX LIMITED'},
  {code:'543970',issuer_name:'Shoora Designs Limited'},
  {code:'543895',issuer_name:'Exhicon Events Media Solutions Limited'},
  {code:'543953',issuer_name:'Khazanchi Jewellers Limited'}
];
const req=(ok,message)=>{if(!ok)throw new Error(message);};
const read=p=>JSON.parse(fs.readFileSync(path.join(ROOT,p),'utf8'));

export function auditNextBatch(root=ROOT){
  const progress=JSON.parse(fs.readFileSync(path.join(root,'data/discovery/bse-2023-review-progress-2026-09-28.json'),'utf8'));
  req(JSON.stringify(progress.next_bounded_review_codes)===JSON.stringify(TARGETS.map(t=>t.code)),'next_batch_changed');
  const recoveryRoot=path.join(root,'data/recovery');
  const recovery=[];
  for(const year of fs.readdirSync(recoveryRoot).filter(y=>/^20\d{2}$/.test(y)).sort()){
    const file=path.join(recoveryRoot,year,'nse-issue-information.json');
    if(!fs.existsSync(file))continue;
    const data=JSON.parse(fs.readFileSync(file,'utf8'));
    for(const record of data.records||[])recovery.push({...record,recovery_year:Number(year)});
  }
  const published=read('data/ipos.json').records||[];
  const results=TARGETS.map(target=>{
    const key=canonicalIssuer(target.issuer_name);
    const recovery_matches=recovery.filter(r=>String(r.bse_scrip_code??'')===target.code||canonicalIssuer(r.issuer_name)===key)
      .map(r=>({recovery_year:r.recovery_year,id:r.id,issuer_name:r.issuer_name,bse_scrip_code:r.bse_scrip_code??null,nse_symbol:r.nse_symbol??null}));
    const public_matches=published.filter(r=>String(r.bse_scrip_code??'')===target.code||canonicalIssuer(r.issuer_name)===key)
      .map(r=>({id:r.id,issuer_name:r.issuer_name,bse_scrip_code:r.bse_scrip_code??null,nse_symbol:r.nse_symbol??null}));
    const exact_code_different_name=recovery_matches.filter(r=>String(r.bse_scrip_code??'')===target.code&&canonicalIssuer(r.issuer_name)!==key);
    return {
      ...target,
      canonical_issuer:key,
      recovery_matches,
      public_matches,
      exact_code_different_name,
      identity_hold:recovery_matches.length>0||public_matches.length>0,
      publication_import_allowed:false
    };
  });
  return {
    schema_version:'1.0.0',
    status:'read_only_all_year_identity_preflight',
    target_year:2023,
    recovery_records_checked:recovery.length,
    public_records_checked:published.length,
    next_bounded_review_codes:TARGETS.map(t=>t.code),
    results,
    identity_holds:results.filter(r=>r.identity_hold).length,
    publication_import_allowed:false,
    note:'Exact canonical-name/BSE-code reconciliation only. A clear result permits source review, not publication; fuzzy matching is intentionally excluded.'
  };
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
  try{console.log(JSON.stringify({bse_2023_ssek_identity:auditNextBatch()},null,2));}
  catch(error){console.error(error.message);process.exitCode=1;}
}
