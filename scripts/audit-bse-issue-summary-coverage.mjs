import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import { normalizeIssuerName, matchIndexCompany } from "./audit-bse-sme-ipo-index.mjs";

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
export const BSE_ISSUE_SUMMARY_URL="https://www.bseindia.com/markets/PublicIssues/Issuesummary.aspx";
const BSE_HOME="https://www.bseindia.com/";
const USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";
export const DEFAULT_MAX_PAGES=120;
const MAX_PAGE_BYTES=6*1024*1024;
const MAX_TOTAL_BYTES=220*1024*1024;
export const sha256=value=>createHash("sha256").update(value).digest("hex");

function decode(value){
  return String(value??"")
    .replace(/&amp;/gi,"&").replace(/&nbsp;|&#160;/gi," ")
    .replace(/&quot;/gi,'"').replace(/&#39;|&apos;/gi,"'")
    .replace(/&#(d+);/g,(_,n)=>String.fromCodePoint(Number(n)));
}
function text(value){
  return decode(String(value??"").replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi," ")
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi," ")
    .replace(/<[^>]+>/g," ")).replace(/\s+/g," ").trim();
}
function validDate(value){
  const raw=String(value??"").trim();
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
function isIssueSummaryPath(pathname){
  return /\/markets\/publicissues\/issuesummary(?:\.aspx)?\/?$/i.test(String(pathname??""));
}
function officialSummaryUrl(value){
  try{
    const u=new URL(String(value),BSE_ISSUE_SUMMARY_URL);
    const allowedPath=isIssueSummaryPath(u.pathname)||/\/markets\/publicissues\/displayipo\.aspx$/i.test(u.pathname);
    return u.protocol==="https:"&&["www.bseindia.com","bseindia.com"].includes(u.hostname.toLowerCase())&&allowedPath?u.href:null;
  }catch{return null;}
}
function rowCells(row){
  return [...String(row).matchAll(/<t[dh]\b[^>]*>([\s\S]*?)<\/t[dh]>/gi)].map(m=>text(m[1]));
}

function shellFingerprint(html){
  const source=String(html??"");
  const title=text(source.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i)?.[1]??"");
  const scripts=[...source.matchAll(/<script\b[^>]*\bsrc\s*=\s*(["'])(.*?)\1[^>]*>/gi)]
    .map(m=>{try{return new URL(decode(m[2]),BSE_ISSUE_SUMMARY_URL).href;}catch{return null;}})
    .filter(Boolean);
  const forms=[...source.matchAll(/<form\b[^>]*>/gi)].map(m=>attr(m[0],"action")).filter(Boolean);
  return{
    title:title||null,
    text_head:text(source).slice(0,500),
    script_sources:[...new Set(scripts)].slice(0,20),
    form_actions:[...new Set(forms)].slice(0,10),
    displayipo_mentions:(source.match(/DisplayIPO/gi)||[]).length,
    aspnet_viewstate:/__VIEWSTATE/i.test(source)
  };
}
function bundleHints(source){
  const textSource=String(source??"");
  const hints=[],seen=new Set();
  for(const match of textSource.matchAll(/["'`](.{1,260}?)["'`]/g)){
    const value=match[1].replace(/\\\//g,"/").trim();
    if(!/(ipo|issue|publicissue|api|summary)/i.test(value))continue;
    if(!/[A-Za-z]/.test(value)||seen.has(value))continue;
    seen.add(value);hints.push(value);
    if(hints.length>=40)break;
  }
  const endpoint_assignments={};
  for(const key of ["GetPublicIssue_par","IPO_HomePageDetail"]){
    const m=textSource.match(new RegExp(key+"\\s*:\\s*[\"']([^\"']+)[\"']"));
    endpoint_assignments[key]=m?.[1]??null;
  }
  const contexts={};
  for(const key of ["GetPublicIssue_par","IPO_HomePageDetail","issueDropdownData","ddlyear","rowsPerPage"]){
    const list=[];let from=0;
    while(list.length<4){
      const i=textSource.indexOf(key,from);if(i<0)break;
      list.push(textSource.slice(Math.max(0,i-240),Math.min(textSource.length,i+520)));
      from=i+key.length;
    }
    contexts[key]=list;
  }
  return{hints,endpoint_assignments,contexts};
}
async function diagnoseShell(fetchImpl,html,headers,outputDir){
  const fingerprint=shellFingerprint(html),bundles=[];
  for(const [index,url] of fingerprint.script_sources.entries()){
    let u;try{u=new URL(url);}catch{continue;}
    if(!["www.bseindia.com","bseindia.com"].includes(u.hostname.toLowerCase()))continue;
    if(!/\.js(?:\?|$)/i.test(u.pathname+u.search))continue;
    try{
      const response=await fetchImpl(u.href,{headers:{...headers,accept:"application/javascript,text/javascript,*/*;q=0.5"},redirect:"follow",signal:AbortSignal.timeout(30000)});
      const bytes=await readBounded(response,12*1024*1024);
      const file="raw/shell-bundle-"+String(index+1).padStart(2,"0")+".js";
      fs.writeFileSync(path.join(outputDir,file),bytes);
      bundles.push({url:u.href,http_status:response.status,bytes:bytes.length,sha256:sha256(bytes),file,hints:bundleHints(bytes.toString("utf8"))});
    }catch(error){bundles.push({url:u.href,error:String(error?.message||error)});}
    if(bundles.length>=8)break;
  }
  const apiBase="https://api.bseindia.com/BseIndiaAPI/api";
  const apiSpecs=[
    {key:"ipo_year",url:apiBase+"/IPOYear/w"},
    {key:"ipo_tracker_2026",url:apiBase+"/IPOTrackerN/w?Fromdt=2026"},
    {key:"ipo_year_2026_rows",url:apiBase+"/MoreCompanyN/w?Fromdt=2026&company=&flag=7&type=2"},
    {key:"public_issue_table",url:apiBase+"/GetPublicIssue_par_updated/w?flag=1"}
  ];
  const api_probes=[];
  for(const [index,spec] of apiSpecs.entries()){
    try{
      const response=await fetchImpl(spec.url,{headers:{"user-agent":USER_AGENT,accept:"application/json,text/plain,*/*","accept-language":"en-US,en;q=0.9",referer:BSE_ISSUE_SUMMARY_URL},redirect:"follow",signal:AbortSignal.timeout(30000)});
      const bytes=await readBounded(response,12*1024*1024);
      const file="raw/api-probe-"+String(index+1).padStart(2,"0")+"-"+spec.key+".txt";
      fs.writeFileSync(path.join(outputDir,file),bytes);
      let parsed=null;try{parsed=JSON.parse(bytes.toString("utf8"));}catch{}
      const table=Array.isArray(parsed?.Table)?parsed.Table:null;
      api_probes.push({
        key:spec.key,url:spec.url,final_url:response.url||spec.url,http_status:response.status,
        content_type:response.headers.get("content-type"),bytes:bytes.length,sha256:sha256(bytes),file,
        json_keys:parsed&&typeof parsed==="object"?Object.keys(parsed).slice(0,20):null,
        table_rows:table?.length??null,first_row:table?.[0]??null,
        text_head:parsed?null:bytes.toString("utf8").slice(0,600)
      });
    }catch(error){api_probes.push({key:spec.key,url:spec.url,error:String(error?.message||error)});}
  }
  return{...fingerprint,bundles,api_probes};
}
function parseDetailLink(href){
  const url=officialSummaryUrl(decode(href));
  if(!url||!/\/DisplayIPO\.aspx$/i.test(new URL(url).pathname))return null;
  const u=new URL(url);
  const startRaw=u.searchParams.get("startdt");
  return{
    url,
    issue_no:/^\d+$/.test(u.searchParams.get("IPONo")||"")?u.searchParams.get("IPONo"):null,
    internal_id:/^\d+$/.test(u.searchParams.get("id")||"")?u.searchParams.get("id"):null,
    idtype:/^\d+$/.test(u.searchParams.get("idtype")||"")?u.searchParams.get("idtype"):null,
    issue_type:(u.searchParams.get("type")||"").trim().toUpperCase()||null,
    status_code:(u.searchParams.get("status")||"").trim().toUpperCase()||null,
    start_date:validDate(startRaw),
    start_date_raw:startRaw
  };
}
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
    const startDates=[...new Set(uniqueLinks.map(x=>x.detail.start_date).filter(Boolean))].sort();
    const types=[...new Set(uniqueLinks.map(x=>x.detail.issue_type).filter(Boolean))].sort();
    const statuses=[...new Set(uniqueLinks.map(x=>x.detail.status_code).filter(Boolean))].sort();
    rows.push({
      issuer_name:issuer,
      issue_no:issueNos.length===1?issueNos[0]:null,
      issue_no_conflict:issueNos.length>1?issueNos:[],
      issue_start_dates:startDates,
      issue_types:types,
      status_codes:statuses,
      cells,
      stage_links:uniqueLinks.map(item=>({label:item.label,...item.detail}))
    });
  }
  return rows;
}

function attr(tag,name){
  const m=String(tag).match(new RegExp("\\b"+name+"\\s*=\\s*([\"'])(.*?)\\1","i"));
  return m?decode(m[2]):null;
}
export function parseAspNetState(html){
  const hidden={};
  for(const m of String(html??"").matchAll(/<input\b[^>]*>/gi)){
    const type=(attr(m[0],"type")||"").toLowerCase();
    const name=attr(m[0],"name");
    if(type==="hidden"&&name)hidden[name]=attr(m[0],"value")||"";
  }
  const events=[];
  const re=/__doPostBack\(\s*['"]([^'"]+)['"]\s*,\s*['"]([^'"]*)['"]\s*\)/gi;
  for(const m of String(html??"").matchAll(re)){
    if(/^Page\$(?:\d+|Next|Prev|First|Last)$/i.test(m[2]))events.push({target:decode(m[1]),argument:decode(m[2])});
  }
  const unique=[...new Map(events.map(e=>[e.target+"|"+e.argument,e])).values()];
  return{hidden,pager_events:unique};
}
export function chooseNextPagerEvent(html,currentPage){
  const state=parseAspNetState(html);
  const exact=state.pager_events.find(e=>e.argument.toLowerCase()===("page$"+(currentPage+1)).toLowerCase());
  if(exact)return{...exact,state};
  const next=state.pager_events.find(e=>e.argument.toLowerCase()==="page$next");
  return next?{...next,state}:null;
}
export function buildPostBackBody(html,event){
  const state=parseAspNetState(html),params=new URLSearchParams();
  for(const [name,value] of Object.entries(state.hidden))params.set(name,value);
  params.set("__EVENTTARGET",event.target);
  params.set("__EVENTARGUMENT",event.argument);
  const buttonNames=Object.keys(state.hidden).filter(name=>/__EVENTTARGET|__EVENTARGUMENT/.test(name));
  void buttonNames;
  return params;
}
function cookieHeader(headers){
  const values=typeof headers.getSetCookie==="function"?headers.getSetCookie():[headers.get("set-cookie")].filter(Boolean);
  return values.map(v=>v.split(";")[0]).filter(Boolean).join("; ");
}
async function readBounded(response,max=MAX_PAGE_BYTES){
  const declared=Number(response.headers.get("content-length"));
  if(Number.isFinite(declared)&&declared>max)throw new Error("bse_issue_summary_page_size_limit");
  const chunks=[];let total=0;
  for await(const chunk of response.body){
    total+=chunk.length;
    if(total>max)throw new Error("bse_issue_summary_page_size_limit");
    chunks.push(Buffer.from(chunk));
  }
  return Buffer.concat(chunks);
}
async function fetchBsePage(fetchImpl,url,options={}){
  const response=await fetchImpl(url,{redirect:"follow",signal:AbortSignal.timeout(30000),...options});
  const final=officialSummaryUrl(response.url||url);
  if(!response.ok||!final||!isIssueSummaryPath(new URL(final).pathname)){
    await response.body?.cancel();
    throw new Error("invalid_bse_issue_summary_response:"+response.status+":"+(response.url||url));
  }
  return{response,bytes:await readBounded(response)};
}
export async function collectBseIssueSummary({
  outputDir,fetchImpl=fetch,clock=()=>new Date().toISOString(),maxPages=DEFAULT_MAX_PAGES
}={}){
  if(!outputDir)throw new Error("outputDir is required");
  if(!Number.isInteger(maxPages)||maxPages<1||maxPages>200)throw new Error("invalid maxPages");
  fs.mkdirSync(path.join(outputDir,"raw"),{recursive:true});
  let cookie="";
  try{
    const home=await fetchImpl(BSE_HOME,{headers:{"user-agent":USER_AGENT,accept:"text/html"},signal:AbortSignal.timeout(20000)});
    if(home.ok)cookie=cookieHeader(home.headers);
    await home.body?.cancel();
  }catch{}
  const headers={"user-agent":USER_AGENT,accept:"text/html,application/xhtml+xml","accept-language":"en-US,en;q=0.9",referer:BSE_HOME,...(cookie?{cookie}:{})};
  const pages=[],observations=[];let html=null,totalBytes=0,exhausted=false;
  for(let page=1;page<=maxPages;page++){
    const requestedAt=clock();
    let fetched;
    if(page===1)fetched=await fetchBsePage(fetchImpl,BSE_ISSUE_SUMMARY_URL,{headers});
    else{
      const event=chooseNextPagerEvent(html,page-1);
      if(!event){exhausted=true;break;}
      const body=buildPostBackBody(html,event);
      fetched=await fetchBsePage(fetchImpl,BSE_ISSUE_SUMMARY_URL,{
        method:"POST",headers:{...headers,"content-type":"application/x-www-form-urlencoded"},body
      });
    }
    const responseCookie=cookieHeader(fetched.response.headers);
    if(responseCookie){
      cookie=[cookie,responseCookie].filter(Boolean).join("; ");
      headers.cookie=cookie;
    }
    totalBytes+=fetched.bytes.length;
    if(totalBytes>MAX_TOTAL_BYTES)throw new Error("bse_issue_summary_total_size_limit");
    html=fetched.bytes.toString("utf8");
    const rows=parseBseIssueSummaryRows(html);
    if(page===1&&!rows.length){
      const shellFile="raw/page-001-shell.html";
      fs.writeFileSync(path.join(outputDir,shellFile),fetched.bytes);
      const diagnostic=await diagnoseShell(fetchImpl,html,headers,outputDir);
      fs.writeFileSync(path.join(outputDir,"shell-diagnostic.json"),JSON.stringify(diagnostic,null,2)+"\n");
      console.log(JSON.stringify({bse_issue_summary_shell_diagnostic:diagnostic}));
      throw new Error("bse_issue_summary_no_issue_rows");
    }
    const rowFingerprint=sha256(Buffer.from(JSON.stringify(rows.map(r=>[r.issuer_name,r.issue_no,r.issue_start_dates,r.stage_links.map(x=>x.url)]))));
    if(pages.some(p=>p.row_fingerprint===rowFingerprint))throw new Error("bse_issue_summary_pagination_did_not_advance");
    const file="raw/page-"+String(page).padStart(3,"0")+".html";
    fs.writeFileSync(path.join(outputDir,file),fetched.bytes);
    const next=chooseNextPagerEvent(html,page);
    pages.push({
      page,requested_at:requestedAt,collected_at:clock(),http_status:fetched.response.status,
      content_type:fetched.response.headers.get("content-type"),http_date:fetched.response.headers.get("date"),
      bytes:fetched.bytes.length,sha256:sha256(fetched.bytes),file,row_fingerprint:rowFingerprint,
      parsed_rows:rows.length,next_event:next?{target:next.target,argument:next.argument}:null
    });
    observations.push(...rows.map((row,rowIndex)=>({...row,page,row_index:rowIndex})));
    if(!next){exhausted=true;break;}
  }
  const manifest={
    schema_version:"1.0.0",collector_version:"1.0.0",status:"complete",
    source_url:BSE_ISSUE_SUMMARY_URL,started_at:pages[0]?.requested_at??clock(),completed_at:clock(),
    run_id:process.env.GITHUB_RUN_ID||null,source_commit_sha:process.env.GITHUB_SHA||null,
    max_pages:maxPages,pages_fetched:pages.length,exhausted,total_response_bytes:totalBytes,
    pages,observations,
    scope_note:"Read-only BSE Issue Summary collection. startdt query parameters are issue-start observations, not listing-date authority. DisplayIPO type/status codes and directory presence are discovery evidence only; no IPO is imported from this collector."
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
function groupIssues(observations){
  const groups=new Map();
  for(const row of observations){
    const key=row.issue_no?"issue:"+row.issue_no:"row:"+row.page+":"+row.row_index+":"+normalizeIssuerName(row.issuer_name);
    if(!groups.has(key))groups.set(key,[]);
    groups.get(key).push(row);
  }
  return [...groups].map(([key,rows])=>{
    const issuers=[...new Set(rows.map(r=>r.issuer_name))];
    const startDates=[...new Set(rows.flatMap(r=>r.issue_start_dates))].sort();
    const types=[...new Set(rows.flatMap(r=>r.issue_types))].sort();
    const statuses=[...new Set(rows.flatMap(r=>r.status_codes))].sort();
    const urls=[...new Map(rows.flatMap(r=>r.stage_links).map(link=>[link.url,link])).values()];
    return{
      issue_key:key,issue_no:rows[0].issue_no,issuer_name:issuers.length===1?issuers[0]:null,
      issuer_name_conflict:issuers.length>1?issuers:[],issue_start_dates:startDates,issue_types:types,status_codes:statuses,
      pages:[...new Set(rows.map(r=>r.page))],row_observations:rows.length,stage_links:urls
    };
  });
}
export function buildBseIssueSummaryAudit(collection,recoveryRecords){
  if(collection?.schema_version!=="1.0.0"||!Array.isArray(collection.observations)||!Array.isArray(recoveryRecords))throw new Error("invalid_bse_issue_summary_audit_input");
  const issues=groupIssues(collection.observations);
  const years={};let exact=0,prefix=0,ambiguous=0,unmatched=0,crossYear=0;
  const reconciled=issues.map(issue=>{
    for(const date of issue.issue_start_dates){const y=date.slice(0,4);years[y]=(years[y]||0)+1;}
    if(!issue.issuer_name){
      ambiguous++;
      return{...issue,match_type:"issue_identity_conflict",matched:null,auto_import_allowed:false};
    }
    const selection=matchIndexCompany(issue.issuer_name,recoveryRecords);
    if(selection.match_type==="exact")exact++;
    else if(selection.match_type==="prefix")prefix++;
    else if(selection.match_type.startsWith("ambiguous"))ambiguous++;
    else unmatched++;
    let cross_year_offer_listing=false;
    if(selection.match?.record?.listing_date?.value&&issue.issue_start_dates.length===1){
      cross_year_offer_listing=selection.match.record.listing_date.value.slice(0,4)!==issue.issue_start_dates[0].slice(0,4);
      if(cross_year_offer_listing)crossYear++;
    }
    return{
      ...issue,match_type:selection.match_type,matched:selection.match?{
        recovery_year:selection.match.year,id:selection.match.record.id,issuer_name:selection.match.record.issuer_name,
        listing_date:selection.match.record.listing_date?.value??null,board:selection.match.record.board??null,
        bse_scrip_code:selection.match.record.bse_scrip_code??null,nse_symbol:selection.match.record.nse_symbol??null
      }:null,cross_year_offer_listing,auto_import_allowed:false
    };
  });
  const allDates=issues.flatMap(i=>i.issue_start_dates).sort();
  const pageMinDates=collection.pages.map(p=>{
    const dates=collection.observations.filter(o=>o.page===p.page).flatMap(o=>o.issue_start_dates).sort();
    return dates[0]??null;
  });
  const monotonic=pageMinDates.filter(Boolean).every((date,i,arr)=>i===0||date<=arr[i-1]);
  const typeCounts={},statusCounts={};
  for(const issue of issues){
    for(const type of issue.issue_types)typeCounts[type]=(typeCounts[type]||0)+1;
    for(const status of issue.status_codes)statusCounts[status]=(statusCounts[status]||0)+1;
  }
  return{
    schema_version:"1.0.0",audit_version:"1.0.0",status:"complete",
    generated_at:collection.completed_at,source_url:collection.source_url,source_commit_sha:collection.source_commit_sha,
    coverage:{
      pages_fetched:collection.pages_fetched,max_pages:collection.max_pages,exhausted:collection.exhausted,
      total_response_bytes:collection.total_response_bytes,row_observations:collection.observations.length,
      unique_issue_groups:issues.length,unique_issuer_names:new Set(issues.map(i=>normalizeIssuerName(i.issuer_name)).filter(Boolean)).size,
      earliest_issue_start_date:allDates[0]??null,latest_issue_start_date:allDates.at(-1)??null,
      issue_start_year_counts:Object.fromEntries(Object.entries(years).sort()),page_date_order_nonincreasing:monotonic,
      issue_type_codes:typeCounts,status_codes:statusCounts,
      issue_groups_without_issue_no:issues.filter(i=>!i.issue_no).length,
      issue_identity_conflicts:issues.filter(i=>i.issuer_name_conflict.length).length,
      full_historical_universe_complete:false,
      completeness_note:collection.exhausted?
        "ASP.NET pagination exhausted for the returned BSE Issue Summary directory. Directory exhaustiveness is not equivalent to complete Indian IPO-universe coverage; issue-summary rows are discovery observations and may include repeat/FPO or non-IPO classifications requiring issuer-specific review.":
        "Collection hit the bounded page limit before pagination exhausted. Historical coverage is partial."
    },
    reconciliation:{
      recovery_records:recoveryRecords.length,exact_matches:exact,prefix_matches:prefix,ambiguous_matches:ambiguous,
      unmatched:unmatched,cross_year_offer_listing:crossYear,auto_imported:0
    },
    source_pages:collection.pages.map(({row_fingerprint,...p})=>p),
    issues:reconciled,
    review_candidates:reconciled.filter(i=>!["exact"].includes(i.match_type)).map(i=>({
      issue_no:i.issue_no,issuer_name:i.issuer_name,match_type:i.match_type,issue_start_dates:i.issue_start_dates,
      issue_types:i.issue_types,status_codes:i.status_codes,pages:i.pages,stage_links:i.stage_links,auto_import_allowed:false
    })),
    notes:[
      "startdt is retained as the issue-start observation supplied by BSE DisplayIPO links; it is not treated as listing-date authority.",
      "BSE DisplayIPO type codes are retained literally. They are not used to infer IPO versus FPO because official BSE links can use non-intuitive codes.",
      "Prefix matches are diagnostic only; they require issuer-specific review before any import.",
      "No repository IPO/recovery data is modified by this audit."
    ]
  };
}
export function runBseIssueSummaryAudit({inputDir,root=ROOT,output}){
  const collection=JSON.parse(fs.readFileSync(path.join(inputDir,"collection.json"),"utf8"));
  for(const page of collection.pages){
    const bytes=fs.readFileSync(path.join(inputDir,page.file));
    if(bytes.length!==page.bytes||sha256(bytes)!==page.sha256)throw new Error("bse_issue_summary_source_hash_mismatch:"+page.page);
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
        const collection=await collectBseIssueSummary({outputDir:args["output-dir"],maxPages:args["max-pages"]?Number(args["max-pages"]):DEFAULT_MAX_PAGES});
        console.log(JSON.stringify({bse_issue_summary_collection:{pages:collection.pages_fetched,exhausted:collection.exhausted,rows:collection.observations.length,bytes:collection.total_response_bytes}}));
      }else if(args.input&&args.output){
        const report=runBseIssueSummaryAudit({inputDir:args.input,output:args.output,root:args.root||ROOT});
        console.log(JSON.stringify({bse_issue_summary_audit:{status:report.status,...report.coverage,...report.reconciliation}}));
      }else throw new Error("--output-dir or --input/--output required");
    }catch(error){console.error(error);process.exitCode=1;}
  })();
}
