import fs from "node:fs";
import path from "node:path";
import {createHash} from "node:crypto";
import {validateDrhpData} from "./drhp-integrity.mjs";
import {validateNseDrhpData} from "./nse-drhp-integrity.mjs";
import {buildPreIpoView,mergeOfficialDraftSources} from "../assets/drhp-lifecycle.js";
const args=process.argv.slice(2);if(args.length!==1||!args[0].startsWith("--output-dir="))throw new Error("use --output-dir=PATH");
const out=path.resolve(args[0].slice(13));fs.mkdirSync(out,{recursive:true});
const hash=b=>createHash("sha256").update(b).digest("hex"),report={schema_version:"1.0.0",status:"failed",checked_at:null,files:[],errors:[]};
let servedSebi=null,servedNse=null,servedIpos=null;
for(const file of ["data/drhp-filings.json","data/nse-drhp-filings.json","drhp.html","assets/drhp.js","assets/drhp-lifecycle.js","assets/styles.css","index.html","ops/drhp-collection.json"]){
  const url="https://vasuki8.github.io/IPO-Tracker/"+file+"?verify="+Date.now();
  try{const r=await fetch(url,{cache:"no-store",signal:AbortSignal.timeout(20000)}),bytes=Buffer.from(await r.arrayBuffer()),fetched_at=new Date().toISOString();
    fs.writeFileSync(path.join(out,file.replaceAll("/","-")),bytes);const expected=fs.readFileSync(file),match=r.ok&&hash(bytes)===hash(expected);
    report.files.push({path:file,url,status:r.status,fetched_at,sha256:hash(bytes),expected_sha256:hash(expected),bytes:bytes.length,match});if(!match)report.errors.push("served_bytes_mismatch:"+file);
    if(file==="data/drhp-filings.json"&&r.ok){servedSebi=JSON.parse(bytes);report.sebi=validateDrhpData(servedSebi);}
    if(file==="data/nse-drhp-filings.json"&&r.ok){servedNse=JSON.parse(bytes);report.nse=validateNseDrhpData(servedNse);}
  }catch(e){report.errors.push(file+":"+String(e));}
}
try{const url="https://vasuki8.github.io/IPO-Tracker/data/ipos.json?verify="+Date.now(),r=await fetch(url,{cache:"no-store",signal:AbortSignal.timeout(20000)}),bytes=Buffer.from(await r.arrayBuffer());
  if(!r.ok)throw new Error("HTTP "+r.status);servedIpos=JSON.parse(bytes);report.ipo_snapshot={url,fetched_at:new Date().toISOString(),sha256:hash(bytes),bytes:bytes.length,records:servedIpos.records?.length};
}catch(e){report.errors.push("data/ipos.json:"+String(e));}
if(servedSebi&&servedNse&&servedIpos){
  try{const merged=mergeOfficialDraftSources(servedSebi,servedNse),view=buildPreIpoView(merged,servedIpos),abakkusSource=servedNse.companies.find(c=>/\babakkus\b/i.test(c.issuer_name)),abakkus=view.companies.find(c=>/\babakkus\b/i.test(c.issuer_name));
    report.pre_ipo={source_companies:view.counts.source_companies,companies:view.counts.pre_ipo_companies,filings:view.counts.pre_ipo_filings,transitioned_to_normal_lifecycle:view.counts.transitioned_companies,lifecycle_gaps:view.counts.lifecycle_gaps,
      lifecycle_statuses:view.lifecycle_statuses,abakkus_source_present:Boolean(abakkusSource),abakkus_visible:Boolean(abakkus),abakkus_filing_date:abakkusSource?.latest_filing_date||null};
    if(view.counts.pre_ipo_companies+view.counts.transitioned_companies!==view.counts.source_companies)report.errors.push("pre_ipo_reconciliation_count_mismatch");
    if(!view.counts.pre_ipo_companies)report.errors.push("empty_pre_ipo_view");if(!abakkusSource||!abakkus)report.errors.push("abakkus_missing_from_pre_ipo");
  }catch(e){report.errors.push("pre_ipo_reconciliation:"+String(e));}
}
report.checked_at=new Date().toISOString();report.status=report.errors.length?"failed":"verified";fs.writeFileSync(path.join(out,"report.json"),JSON.stringify(report,null,2)+"\n");console.log(JSON.stringify(report));if(report.errors.length)process.exitCode=1;
