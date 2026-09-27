import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { parseNseDate } from "./sync-nse-live.mjs";
import { parsePastIssuePrice } from "./diagnose-nse-past-issues.mjs";

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const RECOVERY_ROOT=path.join(ROOT,"data","recovery");
const NSE_HOME="https://www.nseindia.com/market-data/all-upcoming-issues-ipo";
const PAST_URL="https://www.nseindia.com/api/public-past-issues";
const USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";

function norm(v){return String(v??"").replace(/\s+/g," ").trim();}
function slug(v){return norm(v).toLowerCase().replace(/&/g," and ").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");}
function series(row){return norm(row.securityType??row.series).toUpperCase();}
function company(row){return norm(row.company??row.companyName);}
function listing(row){return parseNseDate(row.listingDate);}
function symbol(v){return norm(v).toUpperCase();}
export function isHistoricalEquityRow(row,year){
  const date=listing(row); const s=series(row);
  return Boolean(date&&Number(date.slice(0,4))===Number(year)&&["EQ","SME"].includes(s)&&norm(row.symbol)&&company(row));
}
function evidence(row,now){
  return {url:PAST_URL,document_type:"NSE Public Past Issues",document_identity:"NSE Public Past Issues — "+symbol(row.symbol),publication_date:null,page:null,collected_at:now};
}
export function buildHistoricalRecord(row,now){
  const e=evidence(row,now); const date=listing(row); const price=parsePastIssuePrice(row.issuePrice);
  const record={
    id:slug(company(row)),issuer_name:company(row),board:series(row)==="SME"?"SME":"Mainboard",sector:null,status:"listed",
    nse_symbol:symbol(row.symbol),nse_series:series(row),
    nse_source:{url:e.url,document_type:e.document_type,document_identity:e.document_identity,publication_date:null,collected_at:now},
    terms:{price_band:null,market_lot:null,minimum_bid_quantity:null,open_date:null,close_date:null},
    documents:[{type:e.document_type,identity:e.document_identity,url:e.url,publication_date:null,collected_at:now}],
    first_observed_at:now,last_collected_at:now,
    board_evidence:[e],status_evidence:[e],
    listing_date:{value:date,source_value:norm(row.listingDate),status:"verified",page:null,source:{...e}}
  };
  if(price!==null) record.issue_price={value:price,source_value:norm(row.issuePrice),status:"verified",page:null,source:{...e}};
  return record;
}
function mergeRecord(existing,row,now){
  let changed=false; const e=evidence(row,now); const date=listing(row); const price=parsePastIssuePrice(row.issuePrice);
  if(!existing.nse_symbol){existing.nse_symbol=symbol(row.symbol);changed=true;}
  if(!existing.nse_series){existing.nse_series=series(row);changed=true;}
  if((existing.listing_date?.value==null)&&date){existing.listing_date={value:date,source_value:norm(row.listingDate),status:"verified",page:null,source:{...e}};changed=true;}
  if((existing.issue_price?.value==null)&&price!==null){existing.issue_price={value:price,source_value:norm(row.issuePrice),status:"verified",page:null,source:{...e}};changed=true;}
  existing.documents??=[]; if(!existing.documents.some(d=>d.url===e.url&&d.identity===e.document_identity)){existing.documents.push({type:e.document_type,identity:e.document_identity,url:e.url,publication_date:null,collected_at:now});changed=true;}
  if(changed)existing.last_collected_at=now; return changed;
}
function indexAdd(map,key,entry){
  if(!key)return;
  const list=map.get(key)||[];
  const token=String(entry.year)+":"+String(entry.record?.id||"");
  if(!list.some(x=>String(x.year)+":"+String(x.record?.id||"")===token))list.push(entry);
  map.set(key,list);
}
function registerIdentity(index,year,record){
  indexAdd(index.bySymbol,symbol(record?.nse_symbol),{year:String(year),record});
  indexAdd(index.byName,slug(record?.issuer_name),{year:String(year),record});
}
export function buildRecoveryIdentityIndex(manifestsByYear){
  const index={bySymbol:new Map(),byName:new Map()};
  for(const [year,manifest] of Object.entries(manifestsByYear||{})){
    for(const record of manifest?.records||[])registerIdentity(index,year,record);
  }
  return index;
}
function identityHits(index,row){
  const candidates=[...(index?.bySymbol?.get(symbol(row.symbol))||[]),...(index?.byName?.get(slug(company(row)))||[])];
  const seen=new Set();
  return candidates.filter(entry=>{
    const token=String(entry.year)+":"+String(entry.record?.id||"");
    if(seen.has(token))return false;seen.add(token);return true;
  });
}
async function fetchRows(){
 const landing=await fetch(NSE_HOME,{headers:{"user-agent":USER_AGENT,"accept":"text/html"}});
 if(!landing.ok)throw new Error("NSE landing HTTP "+landing.status);
 const cookies=(typeof landing.headers.getSetCookie==="function"?landing.headers.getSetCookie():[landing.headers.get("set-cookie")].filter(Boolean)).map(x=>x.split(";")[0]).join("; ");
 const r=await fetch(PAST_URL,{headers:{"user-agent":USER_AGENT,"accept":"application/json,text/plain,*/*","referer":NSE_HOME,"cookie":cookies},signal:AbortSignal.timeout(20000)});
 if(!r.ok)throw new Error("NSE past issues HTTP "+r.status); const p=await r.json(); if(!Array.isArray(p))throw new Error("NSE past issues is not an array"); return p;
}
export function materializeYear(rows,year,manifest,now,identityIndex=null){
 const selected=(rows||[]).filter(r=>isHistoricalEquityRow(r,year));
 const bySymbol=new Map((manifest.records||[]).map(r=>[symbol(r.nse_symbol),r]).filter(([s])=>s));
 const byName=new Map((manifest.records||[]).map(r=>[slug(r.issuer_name),r]));
 const index=identityIndex||buildRecoveryIdentityIndex({[year]:manifest});
 let added=0,enriched=0; const holds=[];
 for(const row of selected){
   const sym=symbol(row.symbol),name=slug(company(row));
   let existing=bySymbol.get(sym)||byName.get(name);
   if(existing){if(mergeRecord(existing,row,now))enriched++;continue;}
   const hits=identityHits(index,row);
   const crossYear=hits.filter(hit=>String(hit.year)!==String(year));
   if(crossYear.length){
     holds.push({issuer_name:company(row),symbol:sym,source_listing_date:listing(row),target_year:Number(year),
       existing_years:[...new Set(crossYear.map(hit=>Number(hit.year)))].sort(),
       existing_ids:[...new Set(crossYear.map(hit=>hit.record?.id).filter(Boolean))].sort(),
       reason:"existing_recovery_identity_in_different_year"});
     continue;
   }
   if(hits.length>1)throw new Error("ambiguous same-year historical identity: "+company(row));
   if(hits.length===1){existing=hits[0].record;if(mergeRecord(existing,row,now))enriched++;continue;}
   const rec=buildHistoricalRecord(row,now); manifest.records.push(rec);bySymbol.set(sym,rec);byName.set(slug(rec.issuer_name),rec);registerIdentity(index,year,rec);added++;
 }
 manifest.records.sort((a,b)=>a.issuer_name.localeCompare(b.issuer_name)); if(added||enriched)manifest.generated_at=now;
 return {official_rows:selected.length,added,enriched,cross_year_holds:holds.length,holds,total_records:manifest.records.length};
}
function loadRecoveryManifests(){
 const manifests={};
 if(!fs.existsSync(RECOVERY_ROOT))return manifests;
 for(const dir of fs.readdirSync(RECOVERY_ROOT,{withFileTypes:true}).filter(x=>x.isDirectory()&&/^20\d{2}$/.test(x.name))){
   const file=path.join(RECOVERY_ROOT,dir.name,"nse-issue-information.json");
   if(fs.existsSync(file))manifests[dir.name]=JSON.parse(fs.readFileSync(file,"utf8"));
 }
 return manifests;
}
async function run(){
 const yearArg=process.argv.find(a=>a.startsWith("--year="))?.split("=")[1]??"2025";
 const years=yearArg.includes("-")
   ? (()=>{const [start,end]=yearArg.split("-").map(Number);if(!Number.isInteger(start)||!Number.isInteger(end)||start>end)return [];return Array.from({length:end-start+1},(_,i)=>start+i);})()
   : yearArg.split(",").map(Number);
 if(!years.length||years.some(year=>!Number.isInteger(year)||year<2000))throw new Error("invalid year/year range");
 const rows=await fetchRows(),now=new Date().toISOString(),summaries=[],manifests=loadRecoveryManifests(),identityIndex=buildRecoveryIdentityIndex(manifests);
 for(const year of years){
   const key=String(year),file=path.join(RECOVERY_ROOT,key,"nse-issue-information.json"),existed=fs.existsSync(file);
   const manifest=manifests[key]??{source_family:"Official NSE / SEBI / BSE offer-document and exchange evidence",collection_started_at:now,generated_at:now,records:[]};
   manifests[key]=manifest;
   const result=materializeYear(rows,year,manifest,now,identityIndex);
   if(result.official_rows>0||existed){
     fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,JSON.stringify(manifest,null,2)+"\n");
   }
   summaries.push({year,...result});
 }
 console.log(JSON.stringify({years,summaries,past_rows:rows.length,cross_year_holds:summaries.reduce((n,x)=>n+x.cross_year_holds,0)},null,2));
}
const isMain=process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url;if(isMain)run().catch(e=>{console.error(e);process.exit(1);});
