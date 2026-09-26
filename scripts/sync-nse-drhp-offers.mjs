import fs from "node:fs";
import path from "node:path";
import {createHash} from "node:crypto";
import {pathToFileURL} from "node:url";

export const NSE_OFFER_PAGE="https://www.nseindia.com/companies-listing/corporate-filings-offer-documents?tabIndex=equity";
export const NSE_OFFER_API_BASE="https://www.nseindia.com/api/corporates/offerdocs";
export const DEFAULT_YEAR=2026;
const UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";
const sha256=b=>createHash("sha256").update(b).digest("hex");
const norm=v=>String(v??"").replace(/\s+/g," ").trim();

function cookieHeader(headers){
  const values=typeof headers.getSetCookie==="function"?headers.getSetCookie():[headers.get("set-cookie")].filter(Boolean);
  return values.map(v=>v.split(";")[0]).filter(Boolean).join("; ");
}
async function fetchWithRetry(url,options,attempts=3){
  let last;
  for(let i=1;i<=attempts;i++){
    try{const r=await fetch(url,options);if(r.ok)return r;last=new Error("HTTP "+r.status+" "+url);}
    catch(e){last=e;}
    if(i<attempts)await new Promise(resolve=>setTimeout(resolve,i*900));
  }
  throw last;
}
export function parseNseOfferDate(value){
  const m=norm(value).match(/^(\d{1,2})-([A-Za-z]{3})-(\d{4})$/);
  if(!m)return null;
  const months={jan:"01",feb:"02",mar:"03",apr:"04",may:"05",jun:"06",jul:"07",aug:"08",sep:"09",oct:"10",nov:"11",dec:"12"};
  const month=months[m[2].toLowerCase()];if(!month)return null;
  const iso=m[3]+"-"+month+"-"+String(Number(m[1])).padStart(2,"0"),d=new Date(iso+"T00:00:00Z");
  return Number.isFinite(d.getTime())&&d.toISOString().slice(0,10)===iso?iso:null;
}
export function canonicalNseDraftIssuer(value){
  return norm(value).toLowerCase().replace(/&/g," and ").replace(/\bltd\.?\b/g," limited ")
    .replace(/[^a-z0-9]+/g," ").replace(/\blimited\s*$/g,"").replace(/\s+/g," ").trim();
}
export function officialNseArchiveUrl(value){
  try{const u=new URL(value);return u.protocol==="https:"&&u.hostname==="nsearchives.nseindia.com"&&!u.username&&!u.password&&u.pathname.startsWith("/corporate/")?u.href:null;}catch{return null;}
}
function cleanMissing(value){const x=norm(value);return !x||x==="-"?null:x;}
export function projectNseDraftRows(rows,{year=DEFAULT_YEAR,index="equities",response_sha256=null,collected_at=null,source_url=null}={}){
  if(!Array.isArray(rows))throw new Error("nse_offerdocs_not_array");
  const board=index==="sme"?"SME":"Mainboard",out=[];
  for(const row of rows){
    const issuer_name=norm(row?.company),filing_date=parseNseOfferDate(row?.drhpDate),filing_url=officialNseArchiveUrl(row?.drhpAttach);
    if(!issuer_name||!filing_date||Number(filing_date.slice(0,4))!==year||!filing_url)continue;
    if(!/draft (?:prospectus|red herring prospectus)/i.test(norm(row?.drhp)))continue;
    const issue_open_date=parseNseOfferDate(cleanMissing(row?.issue_open_date));
    const issue_close_date=parseNseOfferDate(cleanMissing(row?.issue_close_date));
    const isin=cleanMissing(row?.isin),symbol=cleanMissing(row?.symbol);
    out.push({
      issuer_name,board,filing_type:"DRHP",filing_date,filing_url,
      processing_status:cleanMissing(row?.drhpStatus),
      issue_open_date,issue_close_date,
      isin:isin&&/^IN[A-Z0-9]{10}$/i.test(isin)?isin.toUpperCase():null,
      symbol:symbol&&symbol!=="-"?symbol.toUpperCase():null,
      pan:cleanMissing(row?.pan_no),
      source_evidence:{
        authority:"National Stock Exchange of India",
        url:source_url||NSE_OFFER_API_BASE+"?index="+index,
        document_type:"NSE Issuer Offer Documents API",
        document_identity:"NSE Issuer Offer Documents — "+index,
        response_sha256,collected_at,
        evidence_locator:"company="+issuer_name
      }
    });
  }
  return out;
}
export function buildNseDraftCompanies(entries){
  const groups=new Map();
  for(const entry of [...entries].sort((a,b)=>b.filing_date.localeCompare(a.filing_date)||a.issuer_name.localeCompare(b.issuer_name))){
    const key=canonicalNseDraftIssuer(entry.issuer_name);if(!key)continue;
    const group=groups.get(key)||{issuer_name:entry.issuer_name,board_hints:new Set(),isins:new Set(),symbols:new Set(),filings:[]};
    group.board_hints.add(entry.board);if(entry.isin)group.isins.add(entry.isin);if(entry.symbol)group.symbols.add(entry.symbol);
    const old=group.filings.find(f=>f.filing_url===entry.filing_url);
    if(old){
      if(canonicalNseDraftIssuer(old.issuer_name)!==key||old.filing_date!==entry.filing_date)throw new Error("conflicting_nse_drhp_identity");
      Object.assign(old,entry);
    }else group.filings.push(entry);
    groups.set(key,group);
  }
  return [...groups.values()].map(g=>{
    g.filings.sort((a,b)=>b.filing_date.localeCompare(a.filing_date)||a.filing_url.localeCompare(b.filing_url));
    const latest=g.filings[0];
    return {issuer_name:g.issuer_name,latest_filing_date:latest.filing_date,latest_filing_type:latest.filing_type,latest_filing_url:latest.filing_url,
      latest_processing_status:latest.processing_status||null,board_hints:[...g.board_hints].sort(),isins:[...g.isins].sort(),symbols:[...g.symbols].sort(),
      filing_count:g.filings.length,filings:g.filings};
  }).sort((a,b)=>b.latest_filing_date.localeCompare(a.latest_filing_date)||a.issuer_name.localeCompare(b.issuer_name));
}
export async function collectNseDraftOffers({year=DEFAULT_YEAR,fetchImpl=fetch,clock=()=>new Date().toISOString()}={}){
  const landing=await fetchWithRetry(NSE_OFFER_PAGE,{headers:{"user-agent":UA,accept:"text/html,application/xhtml+xml","accept-language":"en-US,en;q=0.9"},signal:AbortSignal.timeout(30000)});
  const cookie=cookieHeader(landing.headers),source_responses=[],selected=[];
  for(const index of ["equities","sme"]){
    const url=NSE_OFFER_API_BASE+"?index="+index,requested_at=clock();
    const r=await fetchImpl(url,{headers:{"user-agent":UA,accept:"application/json,text/plain,*/*","accept-language":"en-US,en;q=0.9",referer:NSE_OFFER_PAGE,cookie,"cache-control":"no-cache"},signal:AbortSignal.timeout(30000)});
    const bytes=Buffer.from(await r.arrayBuffer()),collected_at=clock();
    if(!r.ok||r.url!==url||!String(r.headers.get("content-type")||"").toLowerCase().includes("json"))throw new Error("invalid_nse_offerdocs_response:"+index);
    if(bytes.length>8_000_000)throw new Error("nse_offerdocs_response_too_large:"+index);
    const payload=JSON.parse(bytes.toString("utf8"));if(!Array.isArray(payload)||payload.length===0||payload.length>10000)throw new Error("invalid_nse_offerdocs_payload:"+index);
    const response_sha256=sha256(bytes);
    const rows=projectNseDraftRows(payload,{year,index,response_sha256,collected_at,source_url:url});
    source_responses.push({index,url,requested_at,collected_at,http_status:r.status,bytes:bytes.length,response_sha256,total_rows:payload.length,selected_rows:rows.length});
    selected.push(...rows);
  }
  const companies=buildNseDraftCompanies(selected);
  if(!companies.length)throw new Error("no_nse_drhp_companies");
  return {schema_version:"1.0.0",collector_version:"1.0.0",generated_at:clock(),
    source:{authority:"National Stock Exchange of India",section:"Issuer Offer documents",landing_url:NSE_OFFER_PAGE,api_base:NSE_OFFER_API_BASE},
    coverage:{year,scope:"NSE equity and SME issuer-offer-document API rows with an explicit 2026 DRHP date and official NSE archive attachment.",companies:companies.length,
      filing_records:companies.reduce((n,c)=>n+c.filings.length,0),source_rows:source_responses.reduce((n,s)=>n+s.total_rows,0),full_universe_complete:false,
      limitations:"NSE issuer-offer-document coverage supplements SEBI. Absence is not withdrawal evidence; non-NSE filings and other years may be absent."},
    source_responses,companies};
}
async function run(){
  const args=process.argv.slice(2),output=args.find(a=>a.startsWith("--output="))?.slice(9)||"data/nse-drhp-filings.json";
  const year=Number(args.find(a=>a.startsWith("--year="))?.slice(7)||DEFAULT_YEAR);
  if(args.some(a=>!a.startsWith("--output=")&&!a.startsWith("--year="))||!Number.isInteger(year))throw new Error("invalid_arguments");
  const data=await collectNseDraftOffers({year});fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(data,null,2)+"\n");
  console.log(JSON.stringify({nse_drhp_companies:data.companies.length,filings:data.coverage.filing_records,source_rows:data.coverage.source_rows,abakkus:data.companies.some(c=>/\babakkus\b/i.test(c.issuer_name))}));
}
if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url)run().catch(e=>{console.error(e);process.exit(1);});
