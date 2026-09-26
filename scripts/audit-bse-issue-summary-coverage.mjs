import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import { normalizeIssuerName, matchIndexCompany } from "./audit-bse-sme-ipo-index.mjs";

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
export const BSE_ISSUE_SUMMARY_URL="https://www.bseindia.com/markets/PublicIssues/Issuesummary";
export const BSE_API_BASE="https://api.bseindia.com/BseIndiaAPI/api";
export const PROJECT_YEARS=[2020,2021,2022,2023,2024,2025,2026];
const BSE_HOME="https://www.bseindia.com/";
const USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";
const MAX_RESPONSE_BYTES=15*1024*1024;
const MAX_TOTAL_BYTES=220*1024*1024;
export const sha256=value=>createHash("sha256").update(value).digest("hex");

function decode(value){
  return String(value??"")
    .replace(/&amp;/gi,"&").replace(/&nbsp;|&#160;/gi," ")
    .replace(/&quot;/gi,'"').replace(/&#39;|&apos;/gi,"'")
    .replace(/&#(\d+);/g,(_,n)=>String.fromCodePoint(Number(n)));
}
function text(value){
  return decode(String(value??"").replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi," ")
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi," ")
    .replace(/<[^>]+>/g," ")).replace(/\s+/g," ").trim();
}
export function strictDate(value){
  const raw=String(value??"").trim();
  const timestamp=raw.match(/^(\d{4}-\d{2}-\d{2})T/);
  if(timestamp)return strictDate(timestamp[1]);
  let y,m,d;
  const dmy=raw.match(/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})$/);
  const iso=raw.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if(dmy){d=Number(dmy[1]);m=Number(dmy[2]);y=Number(dmy[3]);}
  else if(iso){y=Number(iso[1]);m=Number(iso[2]);d=Number(iso[3]);}
  else return null;
  const dt=new Date(Date.UTC(y,m-1,d));
  if(dt.getUTCFullYear()!==y||dt.getUTCMonth()!==m-1||dt.getUTCDate()!==d)return null;
  return dt.toISOString().slice(0,10);
}
function bseCodeFromImage(value){
  try{
    const u=new URL(String(value));
    if(u.protocol!=="https:"||!["www.bseindia.com","bseindia.com"].includes(u.hostname.toLowerCase()))return null;
    const parts=u.pathname.split("/").filter(Boolean);
    const code=[...parts].reverse().find(part=>/^\d{6}$/.test(part));
    return code??null;
  }catch{return null;}
}
function rowCells(row){
  return [...String(row).matchAll(/<t[dh]\b[^>]*>([\s\S]*?)<\/t[dh]>/gi)].map(m=>text(m[1]));
}
function officialDisplayIpoUrl(value){
  try{
    const u=new URL(decode(value),"https://www.bseindia.com/markets/PublicIssues/Issuesummary");
    return u.protocol==="https:"&&["www.bseindia.com","bseindia.com"].includes(u.hostname.toLowerCase())&&
      /\/markets\/publicissues\/displayipo\.aspx$/i.test(u.pathname)?u.href:null;
  }catch{return null;}
}
function parseDetailLink(href){
  const url=officialDisplayIpoUrl(href);
  if(!url)return null;
  const u=new URL(url);
  const startRaw=u.searchParams.get("startdt");
  return{
    url,
    issue_no:/^\d+$/.test(u.searchParams.get("IPONo")||"")?u.searchParams.get("IPONo"):null,
    internal_id:/^\d+$/.test(u.searchParams.get("id")||"")?u.searchParams.get("id"):null,
    idtype:/^\d+$/.test(u.searchParams.get("idtype")||"")?u.searchParams.get("idtype"):null,
    issue_type:(u.searchParams.get("type")||"").trim().toUpperCase()||null,
    status_code:(u.searchParams.get("status")||"").trim().toUpperCase()||null,
    start_date:strictDate(startRaw),
    start_date_raw:startRaw
  };
}
// Retained for the generic first-page audit and old source-shape fixtures.
export function parseBseIssueSummaryRows(html){
  const rows=[];
  for(const match of String(html??"").matchAll(/<tr\b[^>]*>([\s\S]*?)<\/tr>/gi)){
    const row=match[1];
    const links=[...row.matchAll(/<a\b[^>]*href\s*=\s*(["'])(.*?)\1[^>]*>([\s\S]*?)<\/a>/gi)]
      .map(m=>({href:m[2],label:text(m[3])}))
      .map(item=>({...item,detail:parseDetailLink(item.href)}))
      .filter(item=>item.detail);
    if(!links.length)continue;
    const cells=rowCells(row);
    const issuer=cells.find(cell=>cell&&!/^\d+$/.test(cell)&&!/^(?:view detail|view advertisements?|in-principle stage|listing stage|abridged prospectus|advertisement)$/i.test(cell))||null;
    if(!issuer)continue;
    const uniqueLinks=[...new Map(links.map(item=>[item.detail.url,item])).values()];
    const issueNos=[...new Set(uniqueLinks.map(x=>x.detail.issue_no).filter(Boolean))];
    rows.push({
      issuer_name:issuer,
      issue_no:issueNos.length===1?issueNos[0]:null,
      issue_no_conflict:issueNos.length>1?issueNos:[],
      issue_start_dates:[...new Set(uniqueLinks.map(x=>x.detail.start_date).filter(Boolean))].sort(),
      issue_types:[...new Set(uniqueLinks.map(x=>x.detail.issue_type).filter(Boolean))].sort(),
      status_codes:[...new Set(uniqueLinks.map(x=>x.detail.status_code).filter(Boolean))].sort(),
      cells,
      stage_links:uniqueLinks.map(item=>({label:item.label,...item.detail}))
    });
  }
  return rows;
}

function officialApiUrl(value){
  try{
    const u=new URL(String(value));
    if(u.protocol!=="https:"||u.hostname.toLowerCase()!=="api.bseindia.com"||!u.pathname.startsWith("/BseIndiaAPI/api/"))return null;
    return u.href;
  }catch{return null;}
}
export function bseApiHeaders(){
  return{
    "user-agent":USER_AGENT,
    accept:"application/json,text/plain,*/*",
    "accept-language":"en-US,en;q=0.9",
    referer:BSE_ISSUE_SUMMARY_URL,
    "sec-fetch-site":"same-site",
    "sec-fetch-mode":"cors",
    "sec-fetch-dest":"empty",
    "sec-ch-ua":'"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "sec-ch-ua-mobile":"?0",
    "sec-ch-ua-platform":'"Linux"'
  };
}
async function readBounded(response,max=MAX_RESPONSE_BYTES){
  const declared=Number(response.headers.get("content-length"));
  if(Number.isFinite(declared)&&declared>max)throw new Error("bse_issue_summary_response_size_limit");
  const chunks=[];let total=0;
  for await(const chunk of response.body){
    total+=chunk.length;
    if(total>max)throw new Error("bse_issue_summary_response_size_limit");
    chunks.push(Buffer.from(chunk));
  }
  return Buffer.concat(chunks);
}
async function fetchJsonEvidence(fetchImpl,url,outputDir,file,clock){
  const official=officialApiUrl(url);
  if(!official)throw new Error("untrusted_bse_issue_summary_api_url");
  const requested_at=clock();
  const response=await fetchImpl(official,{headers:bseApiHeaders(),redirect:"follow",signal:AbortSignal.timeout(30000)});
  const final=officialApiUrl(response.url||official);
  const bytes=await readBounded(response);
  if(!response.ok||!final)throw new Error("bse_issue_summary_api_fetch_failed:"+response.status+":"+(response.url||official));
  let payload;try{payload=JSON.parse(bytes.toString("utf8"));}catch{throw new Error("bse_issue_summary_api_invalid_json");}
  if(!Array.isArray(payload?.Table))throw new Error("bse_issue_summary_api_missing_table");
  fs.writeFileSync(path.join(outputDir,file),bytes);
  return{
    payload,
    evidence:{
      url:official,final_url:final,http_status:response.status,content_type:response.headers.get("content-type"),
      http_date:response.headers.get("date"),requested_at,collected_at:clock(),bytes:bytes.length,sha256:sha256(bytes),file
    }
  };
}
export function parseBseYearList(payload){
  if(!Array.isArray(payload?.Table))throw new Error("bse_ipo_year_table_missing");
  const years=[...new Set(payload.Table.map(row=>Number(row?.year)).filter(y=>Number.isInteger(y)&&y>=1900&&y<=2100))].sort((a,b)=>b-a);
  if(!years.length)throw new Error("bse_ipo_year_list_empty");
  return years;
}
export function parseBseYearSummary(payload,year){
  const row=Array.isArray(payload?.Table)?payload.Table[0]:null;
  if(!row)throw new Error("bse_year_summary_missing:"+year);
  const nums=Object.fromEntries(["TotalIPO","NoOfIpo","NoOfSMEIpo","IPOWithPositiveListingGain","IPOWithListingLosses","IPOWithPositiveListingDayGains","IPOWithListingDayLosses"].map(key=>[key,Number(row[key])]));
  if(Object.values(nums).some(v=>!Number.isSafeInteger(v)||v<0)||nums.NoOfIpo+nums.NoOfSMEIpo!==nums.TotalIPO)throw new Error("invalid_bse_year_summary:"+year);
  return{year,...nums,time:row.Time??null};
}
export function parseBseYearRows(payload,year){
  if(!Array.isArray(payload?.Table))throw new Error("bse_year_rows_missing:"+year);
  return payload.Table.map((row,index)=>{
    const issuer_name=String(row?.CompanyName??"").replace(/\s+/g," ").trim();
    const listing_date=strictDate(row?.ListedOn);
    const issue_price=Number(row?.IssuePrice);
    if(!issuer_name||!listing_date||listing_date.slice(0,4)!==String(year)||!Number.isFinite(issue_price)||issue_price<=0){
      throw new Error("invalid_bse_year_row:"+year+":"+index);
    }
    return{
      issuer_name,listing_date,issue_price,
      bse_scrip_code:bseCodeFromImage(row?.IMAGE),
      image_url:typeof row?.IMAGE==="string"?row.IMAGE:null,
      listing_day_close:Number.isFinite(Number(row?.ListingDayClose))?Number(row.ListingDayClose):null,
      listing_day_gain:Number.isFinite(Number(row?.ListingDayGain))?Number(row.ListingDayGain):null,
      current_price:Number.isFinite(Number(row?.CurrentPrice))?Number(row.CurrentPrice):null,
      gain_loss:Number.isFinite(Number(row?.GainLoss))?Number(row.GainLoss):null,
      source_period_marker:row?.Time??null,
      source_row_index:index
    };
  });
}
export function parseCurrentIssueRows(payload){
  if(!Array.isArray(payload?.Table))throw new Error("bse_current_issue_table_missing");
  return payload.Table.map((row,index)=>({
    issuer_name:String(row?.Scrip_Name??"").replace(/\s+/g," ").trim()||null,
    issue_no:Number.isSafeInteger(Number(row?.IPO_NO))?String(Number(row.IPO_NO)):null,
    start_date:strictDate(row?.Start_Dt),end_date:strictDate(row?.End_Dt),
    issue_type:String(row?.IR_FLAG_FULL??row?.IR_flag??"").trim()||null,
    status_code:String(row?.Status??"").trim()||null,
    exchange_platform:String(row?.eXCHANGE_PLATFORM??"").trim()||null,
    price_band:String(row?.Price_Band??"").trim()||null,
    source_row_index:index
  })).filter(row=>row.issuer_name);
}

export async function collectBseIssueSummary({
  outputDir,fetchImpl=fetch,clock=()=>new Date().toISOString(),projectYears=PROJECT_YEARS
}={}){
  if(!outputDir)throw new Error("outputDir is required");
  const years=[...new Set(projectYears.map(Number))].filter(y=>Number.isInteger(y)).sort();
  if(!years.length||years.some(y=>y<2020||y>2026))throw new Error("invalid_project_years");
  fs.mkdirSync(path.join(outputDir,"raw"),{recursive:true});
  let totalBytes=0;
  const sources=[];
  const addBytes=evidence=>{totalBytes+=evidence.bytes;if(totalBytes>MAX_TOTAL_BYTES)throw new Error("bse_issue_summary_total_size_limit");sources.push(evidence);};

  const yearResult=await fetchJsonEvidence(fetchImpl,BSE_API_BASE+"/IPOYear/w",outputDir,"raw/ipo-years.json",clock);
  addBytes(yearResult.evidence);
  const availableYears=parseBseYearList(yearResult.payload);
  const collectedYears=years.filter(year=>availableYears.includes(year));
  if(collectedYears.length!==years.length)throw new Error("bse_issue_summary_project_year_missing:"+years.filter(y=>!availableYears.includes(y)).join(","));

  const yearly=[];
  for(const year of collectedYears){
    const tracker=await fetchJsonEvidence(fetchImpl,BSE_API_BASE+"/IPOTrackerN/w?Fromdt="+year,outputDir,"raw/ipo-tracker-"+year+".json",clock);
    addBytes(tracker.evidence);
    const rowsResult=await fetchJsonEvidence(fetchImpl,BSE_API_BASE+"/MoreCompanyN/w?Fromdt="+year+"&company=&flag=7&type=2",outputDir,"raw/ipo-year-"+year+".json",clock);
    addBytes(rowsResult.evidence);
    const summary=parseBseYearSummary(tracker.payload,year);
    const rows=parseBseYearRows(rowsResult.payload,year);
    if(rows.length!==summary.TotalIPO)throw new Error("bse_issue_summary_year_count_mismatch:"+year+":"+rows.length+":"+summary.TotalIPO);
    yearly.push({year,summary,rows,tracker_source:tracker.evidence,rows_source:rowsResult.evidence});
  }

  const current=await fetchJsonEvidence(fetchImpl,BSE_API_BASE+"/GetPublicIssue_par_updated/w?flag=1",outputDir,"raw/current-public-issues.json",clock);
  addBytes(current.evidence);
  const currentIssues=parseCurrentIssueRows(current.payload);
  const manifest={
    schema_version:"2.0.0",collector_version:"2.0.0",status:"complete",source_page:BSE_ISSUE_SUMMARY_URL,
    api_base:BSE_API_BASE,started_at:sources[0]?.requested_at??clock(),completed_at:clock(),
    run_id:process.env.GITHUB_RUN_ID||null,source_commit_sha:process.env.GITHUB_SHA||null,
    available_years:availableYears,project_years:years,collected_years:collectedYears,
    coverage_exhaustion:{
      method:"official_year_index_plus_per_year_total_reconciliation",
      year_index_exhausted:true,
      each_collected_year_row_count_matches_official_total:true,
      html_pagination_applicable:false
    },
    total_response_bytes:totalBytes,sources,
    yearly,current_issues:{source:current.evidence,rows:currentIssues},
    scope_note:"Read-only BSE Public Issues Angular API collection. IPOYear defines the source's available years. For each project year, MoreCompanyN flag=7/type=2 is reconciled exactly to IPOTrackerN.TotalIPO. Rows are discovery observations only; no IPO is imported from this collector."
  };
  fs.writeFileSync(path.join(outputDir,"collection.json"),JSON.stringify(manifest,null,2)+"\n");
  return manifest;
}
function loadRecovery(root=ROOT){
  const records=[];
  for(const year of fs.readdirSync(path.join(root,"data","recovery")).filter(x=>/^20\d{2}$/.test(x)).sort()){
    const file=path.join(root,"data","recovery",year,"nse-issue-information.json");
    if(!fs.existsSync(file))continue;
    const data=JSON.parse(fs.readFileSync(file,"utf8"));
    records.push(...(data.records||[]).map(record=>({year:Number(year),record})));
  }
  return records;
}
export function buildBseIssueSummaryAudit(collection,recoveryRecords){
  if(collection?.schema_version!=="2.0.0"||!Array.isArray(collection.yearly)||!Array.isArray(recoveryRecords))throw new Error("invalid_bse_issue_summary_audit_input");
  const yearReports=[],reviewCandidates=[];
  let exact=0,prefix=0,ambiguous=0,unmatched=0,listingDateConflicts=0;
  const seenIssuerYears=new Set();
  for(const yearBlock of collection.yearly){
    let yearExact=0,yearPrefix=0,yearAmbiguous=0,yearUnmatched=0,yearConflicts=0;
    const results=yearBlock.rows.map(row=>{
      const selection=matchIndexCompany(row.issuer_name,recoveryRecords);
      if(selection.match_type==="exact"){exact++;yearExact++;}
      else if(selection.match_type==="prefix"){prefix++;yearPrefix++;}
      else if(selection.match_type.startsWith("ambiguous")){ambiguous++;yearAmbiguous++;}
      else{unmatched++;yearUnmatched++;}
      const retainedListing=selection.match?.record?.listing_date?.value??null;
      const listing_date_conflict=Boolean(retainedListing&&retainedListing!==row.listing_date);
      if(listing_date_conflict){listingDateConflicts++;yearConflicts++;}
      const key=yearBlock.year+"|"+normalizeIssuerName(row.issuer_name);
      const duplicate_in_source=seenIssuerYears.has(key);
      seenIssuerYears.add(key);
      const result={
        ...row,source_year:yearBlock.year,match_type:selection.match_type,
        matched:selection.match?{recovery_year:selection.match.year,id:selection.match.record.id,issuer_name:selection.match.record.issuer_name,
          listing_date:retainedListing,board:selection.match.record.board??null,bse_scrip_code:selection.match.record.bse_scrip_code??null,nse_symbol:selection.match.record.nse_symbol??null}:null,
        listing_date_conflict,duplicate_in_source,auto_import_allowed:false
      };
      if(selection.match_type!=="exact"||listing_date_conflict||duplicate_in_source)reviewCandidates.push(result);
      return result;
    });
    yearReports.push({
      year:yearBlock.year,official_total:yearBlock.summary.TotalIPO,mainboard_total:yearBlock.summary.NoOfIpo,
      sme_total:yearBlock.summary.NoOfSMEIpo,parsed_rows:yearBlock.rows.length,
      exact_matches:yearExact,prefix_matches:yearPrefix,ambiguous_matches:yearAmbiguous,unmatched:yearUnmatched,
      listing_date_conflicts:yearConflicts,results
    });
  }
  const currentIssueTypeCounts={},currentPlatformCounts={};
  for(const row of collection.current_issues.rows){
    if(row.issue_type)currentIssueTypeCounts[row.issue_type]=(currentIssueTypeCounts[row.issue_type]||0)+1;
    if(row.exchange_platform)currentPlatformCounts[row.exchange_platform]=(currentPlatformCounts[row.exchange_platform]||0)+1;
  }
  return{
    schema_version:"2.0.0",audit_version:"2.0.0",status:"complete",generated_at:collection.completed_at,
    source_page:collection.source_page,api_base:collection.api_base,source_commit_sha:collection.source_commit_sha,
    coverage:{
      available_years:collection.available_years,project_years:collection.project_years,collected_years:collection.collected_years,
      earliest_available_year:Math.min(...collection.available_years),latest_available_year:Math.max(...collection.available_years),
      project_window_exhausted:collection.project_years.every(y=>collection.collected_years.includes(y)),
      official_year_index_exhausted:collection.coverage_exhaustion.year_index_exhausted,
      per_year_totals_reconciled:collection.coverage_exhaustion.each_collected_year_row_count_matches_official_total,
      total_response_bytes:collection.total_response_bytes,
      historical_rows:collection.yearly.reduce((n,y)=>n+y.rows.length,0),
      current_issue_rows:collection.current_issues.rows.length,
      full_indian_ipo_universe_complete:false,
      completeness_note:"The official BSE source is exhausted for its returned year index and reconciled per-year totals, but it is a BSE historical listing/performance source, not a complete Indian IPO universe or issuer-specific offer authority."
    },
    reconciliation:{
      recovery_records:recoveryRecords.length,exact_matches:exact,prefix_matches:prefix,ambiguous_matches:ambiguous,
      unmatched,listing_date_conflicts:listingDateConflicts,auto_imported:0
    },
    current_issue_surface:{rows:collection.current_issues.rows.length,issue_type_counts:currentIssueTypeCounts,platform_counts:currentPlatformCounts},
    year_reports:yearReports,
    review_candidates:reviewCandidates,
    source_receipts:collection.sources,
    notes:[
      "IPOYear is used to establish the official BSE year list; project scope remains 2020–2026.",
      "MoreCompanyN flag=7/type=2 supplies the page's 'IPOs in the year' rows and is accepted only when its row count exactly equals IPOTrackerN.TotalIPO for that year.",
      "Issue price and listing date in this audit are discovery/reconciliation fields only; they are not auto-imported.",
      "Prefix matches, unmatched rows, duplicates and listing-date conflicts require issuer-specific official review before any data change.",
      "GetPublicIssue_par_updated flag=1 is retained as a current-issues side surface and is not mixed into historical-year counts.",
      "No repository IPO/recovery data is modified by this audit."
    ]
  };
}
export function runBseIssueSummaryAudit({inputDir,root=ROOT,output}){
  const collection=JSON.parse(fs.readFileSync(path.join(inputDir,"collection.json"),"utf8"));
  for(const source of collection.sources){
    const bytes=fs.readFileSync(path.join(inputDir,source.file));
    if(bytes.length!==source.bytes||sha256(bytes)!==source.sha256)throw new Error("bse_issue_summary_source_hash_mismatch:"+source.file);
  }
  const report=buildBseIssueSummaryAudit(collection,loadRecovery(root));
  fs.writeFileSync(output,JSON.stringify(report,null,2)+"\n");
  return report;
}
if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url){
  const args=Object.fromEntries(process.argv.slice(2).map(arg=>{const i=arg.indexOf("=");if(i<1)throw new Error("arguments_must_use_equals");return[arg.slice(2,i),arg.slice(i+1)];}));
  (async()=>{
    try{
      if(args["output-dir"]){
        const collection=await collectBseIssueSummary({outputDir:args["output-dir"]});
        console.log(JSON.stringify({bse_issue_summary_collection:{
          available_years:collection.available_years,project_years:collection.project_years,
          rows:collection.yearly.reduce((n,y)=>n+y.rows.length,0),current_issues:collection.current_issues.rows.length,
          bytes:collection.total_response_bytes
        }}));
      }else if(args.input&&args.output){
        const report=runBseIssueSummaryAudit({inputDir:args.input,output:args.output,root:args.root||ROOT});
        console.log(JSON.stringify({bse_issue_summary_audit:{status:report.status,...report.coverage,...report.reconciliation,current_issue_surface:report.current_issue_surface}}));
      }else throw new Error("--output-dir or --input/--output required");
    }catch(error){console.error(error);process.exitCode=1;}
  })();
}
