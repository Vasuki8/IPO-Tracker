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
const REVIEWED_RECONCILIATION_PATH=path.join(ROOT,"data","verified-bse-reconciliations","2026-09-26-high-priority.json");

function norm(v){return String(v??"").replace(/\s+/g," ").trim();}
function slug(v){return norm(v).toLowerCase().replace(/&/g," and ").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");}
function series(row){return norm(row.securityType??row.series).toUpperCase();}
function company(row){return norm(row.company??row.companyName);}
function listing(row){return parseNseDate(row.listingDate);}
export function isHistoricalEquityRow(row,year){
  const date=listing(row); const s=series(row);
  return Boolean(date&&Number(date.slice(0,4))===Number(year)&&["EQ","SME"].includes(s)&&norm(row.symbol)&&company(row));
}
function evidence(row,now){
  return {url:PAST_URL,document_type:"NSE Public Past Issues",document_identity:"NSE Public Past Issues — "+norm(row.symbol).toUpperCase(),publication_date:null,page:null,collected_at:now};
}
export function buildHistoricalRecord(row,now){
  const e=evidence(row,now); const date=listing(row); const price=parsePastIssuePrice(row.issuePrice);
  const record={
    id:slug(company(row)),issuer_name:company(row),board:series(row)==="SME"?"SME":"Mainboard",sector:null,status:"listed",
    nse_symbol:norm(row.symbol).toUpperCase(),nse_series:series(row),
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
  if(!existing.nse_symbol){existing.nse_symbol=norm(row.symbol).toUpperCase();changed=true;}
  if(!existing.nse_series){existing.nse_series=series(row);changed=true;}
  if((existing.listing_date?.value==null)&&date){existing.listing_date={value:date,source_value:norm(row.listingDate),status:"verified",page:null,source:{...e}};changed=true;}
  if((existing.issue_price?.value==null)&&price!==null){existing.issue_price={value:price,source_value:norm(row.issuePrice),status:"verified",page:null,source:{...e}};changed=true;}
  existing.documents??=[]; if(!existing.documents.some(d=>d.url===e.url&&d.identity===e.document_identity)){existing.documents.push({type:e.document_type,identity:e.document_identity,url:e.url,publication_date:null,collected_at:now});changed=true;}
  if(changed)existing.last_collected_at=now; return changed;
}
async function fetchRows(){
 const landing=await fetch(NSE_HOME,{headers:{"user-agent":USER_AGENT,"accept":"text/html"}});
 if(!landing.ok)throw new Error("NSE landing HTTP "+landing.status);
 const cookies=(typeof landing.headers.getSetCookie==="function"?landing.headers.getSetCookie():[landing.headers.get("set-cookie")].filter(Boolean)).map(x=>x.split(";")[0]).join("; ");
 const r=await fetch(PAST_URL,{headers:{"user-agent":USER_AGENT,"accept":"application/json,text/plain,*/*","referer":NSE_HOME,"cookie":cookies},signal:AbortSignal.timeout(20000)});
 if(!r.ok)throw new Error("NSE past issues HTTP "+r.status); const p=await r.json(); if(!Array.isArray(p))throw new Error("NSE past issues is not an array"); return p;
}
export function isSupersededHistoricalObservation(row,superseded=[]){
  const symbol=norm(row?.symbol).toUpperCase(),date=listing(row);
  return (superseded||[]).some(item=>norm(item?.symbol).toUpperCase()===symbol&&item?.listing_date===date);
}
export function materializeYear(rows,year,manifest,now,superseded=[]){
 const selected=(rows||[]).filter(r=>isHistoricalEquityRow(r,year)&&!isSupersededHistoricalObservation(r,superseded));
 const bySymbol=new Map((manifest.records||[]).map(r=>[norm(r.nse_symbol).toUpperCase(),r]).filter(([s])=>s));
 const byName=new Map((manifest.records||[]).map(r=>[slug(r.issuer_name),r]));
 let added=0,enriched=0;
 for(const row of selected){
   const sym=norm(row.symbol).toUpperCase(); const existing=bySymbol.get(sym)||byName.get(slug(company(row)));
   if(existing){if(mergeRecord(existing,row,now))enriched++;continue;}
   const rec=buildHistoricalRecord(row,now); manifest.records.push(rec);bySymbol.set(sym,rec);byName.set(slug(rec.issuer_name),rec);added++;
 }
 manifest.records.sort((a,b)=>a.issuer_name.localeCompare(b.issuer_name)); if(added||enriched)manifest.generated_at=now;
 return {official_rows:selected.length,added,enriched,total_records:manifest.records.length};
}
async function run(){
 const yearArg=process.argv.find(a=>a.startsWith("--year="))?.split("=")[1]??"2025";
 const years=yearArg.includes("-")
   ? (()=>{const [start,end]=yearArg.split("-").map(Number);if(!Number.isInteger(start)||!Number.isInteger(end)||start>end)return [];return Array.from({length:end-start+1},(_,i)=>start+i);})()
   : yearArg.split(",").map(Number);
 if(!years.length||years.some(year=>!Number.isInteger(year)||year<2000))throw new Error("invalid year/year range");
 const rows=await fetchRows(); const now=new Date().toISOString(); const summaries=[];
 const reviewed=fs.existsSync(REVIEWED_RECONCILIATION_PATH)?JSON.parse(fs.readFileSync(REVIEWED_RECONCILIATION_PATH,"utf8")):null;
 const superseded=(reviewed?.actions||[]).map(action=>action.superseded_nse_observation).filter(Boolean);
 for(const year of years){
   const file=path.join(RECOVERY_ROOT,String(year),"nse-issue-information.json");
   const manifest=fs.existsSync(file)?JSON.parse(fs.readFileSync(file,"utf8")):{source_family:"Official NSE / SEBI / BSE offer-document and exchange evidence",collection_started_at:now,generated_at:now,records:[]};
   const result=materializeYear(rows,year,manifest,now,superseded);
   if(result.official_rows>0||fs.existsSync(file)){
     fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,JSON.stringify(manifest,null,2)+"\n");
   }
   summaries.push({year,...result});
 }
 console.log(JSON.stringify({years,summaries,past_rows:rows.length},null,2));
}
const isMain=process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url;if(isMain)run().catch(e=>{console.error(e);process.exit(1);});
