import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const DRHP_LIST_URL = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&smid=10&ssid=15";
export const DRHP_AJAX_URL = "https://www.sebi.gov.in/sebiweb/ajax/home/getnewslistinfo.jsp";
export const AXIS_OFFER_DOCS_URL = "https://www.axiscapital.co.in/offer-documents";
export const DEFAULT_YEAR = 2026;
export const DEFAULT_MAX_PAGES = 16;
const USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";
const hash = (value) => createHash("sha256").update(value).digest("hex");
const norm = (value) => String(value ?? "").replace(/\s+/g, " ").trim();

function decode(value) {
  return String(value ?? "")
    .replace(/&nbsp;/gi, " ").replace(/&amp;/gi, "&").replace(/&quot;/gi, '"')
    .replace(/&#39;|&apos;/gi, "'").replace(/&lt;/gi, "<").replace(/&gt;/gi, ">")
    .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)));
}
function strip(value) {
  return norm(decode(String(value ?? "").replace(/<[^>]*>/g, " ")));
}
export function parseSebiDate(value) {
  const m = norm(value).match(/^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),\s+(\d{4})$/i);
  if (!m) return null;
  const months = {jan:"01",feb:"02",mar:"03",apr:"04",may:"05",jun:"06",jul:"07",aug:"08",sep:"09",oct:"10",nov:"11",dec:"12"};
  const iso = `${m[3]}-${months[m[1].toLowerCase()]}-${String(Number(m[2])).padStart(2,"0")}`;
  const date = new Date(iso + "T00:00:00Z");
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0,10) === iso ? iso : null;
}
export function canonicalIssuer(value) {
  return norm(value).toLowerCase().replace(/&/g," and ").replace(/\bltd\.?\b/g," limited ")
    .replace(/[^a-z0-9]+/g," ").replace(/\blimited\s*$/g,"").replace(/\s+/g," ").trim();
}
export function officialSebiUrl(value, prefix = "/filings/public-issues/") {
  try { const u = new URL(value); return u.protocol === "https:" && ["www.sebi.gov.in", "sebi.gov.in"].includes(u.hostname) && !u.username && !u.password && u.pathname.startsWith(prefix) ? u.href : null; } catch { return null; }
}
export function officialAxisUrl(value, prefix = "/contents/") {
  try { const u = new URL(value); return u.protocol === "https:" && ["www.axiscapital.co.in", "axiscapital.co.in"].includes(u.hostname) && !u.username && !u.password && u.pathname.startsWith(prefix) ? u.href : null; } catch { return null; }
}
export function officialDrhpDocumentUrl(value) {
  return officialSebiUrl(value) || (officialAxisUrl(value) && /\.pdf(?:$|\?)/i.test(new URL(value).pathname) ? new URL(value).href : null);
}
function absoluteUrl(raw, base = DRHP_LIST_URL) {
  try { return new URL(decode(raw), base).href; } catch { return null; }
}
function filingType(label) {
  const text = norm(label);
  if (/\b(?:addendum|corrigendum|abridged)\b/i.test(text)) return null;
  const updated = text.match(/\bUpdated Draft Red Herring Prospectus(?:[-\s]*(I{1,4}|V|\d+))?\b/i);
  if (updated) return updated[1] ? "UDRHP-" + updated[1].toUpperCase() : "UDRHP";
  if (/\bDraft Red Herring Prospectus\b/i.test(text)) return "DRHP";
  const m = text.match(/\b(UDRHP(?:[-\s]*(?:I{1,4}|V|\d+))?|DRHP)\b/i);
  return m ? m[1].toUpperCase().replace(/[-\s]+/g,"-") : null;
}
function escapeRegex(value) {
  return String(value).replace(/[.*+?^$()|[\]\\{}]/g, "\\$&");
}
function issuerFromLabel(label, type) {
  const text = strip(String(label).split(/<br\s*\/?\s*>/i)[0]);
  if (!text) return null;
  // Strip the literal filing marker using the source's separator variants,
  // rather than the normalized display type. SEBI uses forms such as
  // "UDRHP 1" and "UDRHP - I"; neither belongs in the issuer name.
  return norm(text
    .replace(/\s*[-–—]?\s*\bUpdated Draft Red Herring Prospectus(?:[-\s]*(?:I{1,4}|V|\d+))?\b\s*$/i,"")
    .replace(/\s*[-–—]?\s*\bDraft Red Herring Prospectus\b\s*$/i,"")
    .replace(/\s*[-–—]?\s*\b(?:UDRHP(?:[-\s]*(?:I{1,4}|V|\d+))?|DRHP)\b\s*$/i,""));
}
function firstFilingHref(row) {
  for (const m of row.matchAll(/<a\b[^>]*href\s*=\s*(["'])([^"']+)\1[^>]*>/gi)) {
    const href = absoluteUrl(m[2]);
    if (officialSebiUrl(href)) return href;
  }
  return null;
}
function outerTitle(row) {
  const m = row.match(/<a\b[^>]*href\s*=\s*(["'])[^"']+\1[^>]*\btitle\s*=\s*(["'])([\s\S]*?)\2[^>]*>/i);
  return m ? m[3] : "";
}
function draftAbridgedUrl(row) {
  for (const m of row.matchAll(/\bhref\s*=\s*(["'])([^"']+)\1/gi)) {
    const href = absoluteUrl(m[2]);
    if (officialSebiUrl(href,"/sebi_data/commondocs/") && /\.pdf(?:$|\?)/i.test(href)) return href;
  }
  return null;
}
export function parseDrhpRows(html) {
  const entries = [];
  for (const match of String(html).matchAll(/<tr\b[^>]*>([\s\S]*?)<\/tr>/gi)) {
    const row = match[1];
    const dateCell = row.match(/<td\b[^>]*>\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4})\s*<\/td>/i);
    if (!dateCell) continue;
    const filing_date = parseSebiDate(dateCell[1]);
    const url = firstFilingHref(row);
    if (!filing_date || !url) continue;
    const title = outerTitle(row) || strip(row);
    // A URL fallback must never override an explicit amendment/corrigendum title.
    if (/\b(?:addendum|corrigendum|errata)\b/i.test(decode(title) + " " + decodeURIComponent(new URL(url).pathname))) continue;
    const type = filingType(title) || filingType(decodeURIComponent(new URL(url).pathname));
    if (!type) continue;
    const issuer_name = issuerFromLabel(title || decodeURIComponent(new URL(url).pathname), type);
    if (!issuer_name) continue;
    entries.push({ issuer_name, filing_type:type, filing_date, filing_url:url, draft_abridged_url:draftAbridgedUrl(row) });
  }
  return entries;
}

export function axisDocumentDate(value) {
  const url = officialAxisUrl(value);
  if (!url) return null;
  const m = new URL(url).pathname.match(/-(\d{10}|\d{13})\.pdf$/i);
  if (!m) return null;
  const raw = Number(m[1]), millis = m[1].length === 13 ? raw : raw * 1000;
  const date = new Date(millis);
  if (!Number.isFinite(date.getTime()) || date.getUTCFullYear() < 2020 || date.getUTCFullYear() > 2100) return null;
  return date.toISOString().slice(0,10);
}
export function parseAxisDrhpRows(html) {
  const entries = [];
  for (const match of String(html).matchAll(/<a\b[^>]*href\s*=\s*(["'])([^"']+)\1[^>]*>([\s\S]*?)<\/a>/gi)) {
    const label = strip(match[3]);
    if (!label || /\b(?:abridged|addendum|corrigendum|red herring prospectus\b(?!.*draft)|prospectus\b(?!.*draft))\b/i.test(label)) continue;
    const type = filingType(label);
    if (!type) continue;
    const href = absoluteUrl(match[2], AXIS_OFFER_DOCS_URL);
    const url = officialAxisUrl(href);
    if (!url || !/\.pdf(?:$|\?)/i.test(new URL(url).pathname)) continue;
    const filing_date = axisDocumentDate(url);
    const issuer_name = issuerFromLabel(label, type);
    if (!filing_date || !issuer_name) continue;
    entries.push({
      issuer_name, filing_type:type, filing_date, filing_url:url, draft_abridged_url:null,
      source_kind:"official_lead_manager", source_authority:"Axis Capital Limited",
      date_basis:"lead_manager_document_upload_timestamp"
    });
  }
  return entries;
}
export function listingStats(html) {
  const text = strip(html);
  const total = text.match(/\bof\s+([0-9,]+)\s+records\b/i);
  const page = String(html).match(/name=['"]nextValue['"]\s+value=['"]?(\d+)/i);
  const totalPage = String(html).match(/name=['"]totalpage['"]\s+value=['"]?(\d+)/i);
  return { total_records: total ? Number(total[1].replace(/,/g,"")) : null,
    page: page ? Number(page[1]) : 1, total_pages: totalPage ? Number(totalPage[1]) : null };
}
export function parseAjaxFragment(text) {
  const [listing] = String(text).trim().split("#@#");
  return listing || "";
}
export function paginationBody(page) {
  return new URLSearchParams({
    nextValue:"1", next:"n", search:"", fromDate:"", toDate:"", fromYear:"", toYear:"", deptId:"",
    sid:"3", ssid:"15", smid:"10", ssidhidden:"15", intmid:"-1", sText:"Filings",
    ssText:"Public Issues", smText:"Draft Offer Documents filed with SEBI", doDirect:String(page - 1)
  });
}
export function buildCompanies(entries) {
  const groups = new Map();
  for (const entry of [...entries].sort((a,b) => b.filing_date.localeCompare(a.filing_date) || a.issuer_name.localeCompare(b.issuer_name))) {
    const key = canonicalIssuer(entry.issuer_name);
    if (!key) continue;
    const group = groups.get(key) || { issuer_name:entry.issuer_name, filings:[] };
    if (!group.filings.some(f => f.filing_url === entry.filing_url)) group.filings.push(entry);
    groups.set(key, group);
  }
  return [...groups.values()].map(group => ({
    issuer_name:group.issuer_name,
    latest_filing_date:group.filings[0].filing_date,
    latest_filing_type:group.filings[0].filing_type,
    latest_filing_url:group.filings[0].filing_url,
    draft_abridged_url:group.filings[0].draft_abridged_url || null,
    filing_count:group.filings.length,
    filings:group.filings
  })).sort((a,b) => b.latest_filing_date.localeCompare(a.latest_filing_date) || a.issuer_name.localeCompare(b.issuer_name));
}
export function pageRange(html) {
  const m=strip(html).match(/\b(\d+)\s+to\s+(\d+)\s+of\s+([\d,]+)\s+records\b/i);
  if(!m)throw new Error("missing_drhp_pagination");
  const [start,end,total]=m.slice(1).map(v=>Number(v.replace(/,/g,"")));
  if(start<1||end<start||end>total||total>10000)throw new Error("invalid_drhp_pagination");
  return {start,end,total};
}
export async function collectDrhpYear({ year=DEFAULT_YEAR, maxPages=DEFAULT_MAX_PAGES,
  fetchImpl=fetch, clock=()=>new Date().toISOString(), retainSources=null, supplementalSources=true } = {}) {
  if (!Number.isInteger(year) || year < 2000 || year > 2100 || !Number.isInteger(maxPages) || maxPages < 2 || maxPages>120) throw new Error("invalid_drhp_collection_options");
  const collection_started_at=clock(), source_pages=[], supplemental_source_pages=[], selected=[], warnings=[];
  if(retainSources)fs.mkdirSync(retainSources,{recursive:true});
  let stop_reason=null, firstTotal=null;
  for(let page=1;page<=maxPages;page++) {
    const url=page===1?DRHP_LIST_URL:DRHP_AJAX_URL;
    const body=page===1?null:paginationBody(page);
    const requested_at=clock();
    const response=await fetchImpl(url,{method:page===1?"GET":"POST",redirect:"follow",signal:AbortSignal.timeout(35000),
      headers:{"user-agent":USER_AGENT,"accept":"text/html,*/*","cache-control":"no-cache",
        ...(body?{"content-type":"application/x-www-form-urlencoded; charset=UTF-8","x-requested-with":"XMLHttpRequest","referer":DRHP_LIST_URL}:{})},...(body?{body}:{})});
    const bytes=Buffer.from(await response.arrayBuffer()), collected_at=clock();
    const file="page-"+String(page).padStart(2,"0")+".html";
    if(retainSources)fs.writeFileSync(path.join(retainSources,file),bytes);
    if(!response.ok||!officialSebiUrl(response.url,"/sebiweb/")||!response.headers.get("content-type")?.includes("text/html"))throw new Error("invalid_drhp_response:"+page);
    const fragment=parseAjaxFragment(bytes.toString("utf8")), range=pageRange(fragment), stats=listingStats(fragment);
    if(range.start!==(page-1)*25+1 || stats.page!==page || range.end!==Math.min(page*25,range.total))throw new Error("drhp_page_did_not_advance:"+page);
    const dates=[...fragment.matchAll(/<td\b[^>]*>\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4})\s*<\/td>/gi)].map(m=>parseSebiDate(m[1]));
    if(dates.length!==range.end-range.start+1||dates.some(d=>!d||d>collected_at.slice(0,10)))throw new Error("invalid_drhp_row_dates:"+page);
    firstTotal??=range.total;
    if(range.total!==firstTotal)warnings.push({code:"source_total_changed",page,first_total:firstTotal,observed_total:range.total});
    const meta={page,url,final_url:response.url,http_status:response.status,requested_at,collected_at,bytes:bytes.length,sha256:hash(bytes),observed_records:range.total,range,request_do_direct:page-1,artifact_file:file};
    source_pages.push(meta);
    for(const row of parseDrhpRows(fragment).filter(r=>r.filing_date.startsWith(year+"-")))selected.push({...row,
      source_evidence:{url,final_url:response.url,response_sha256:meta.sha256,collected_at,page,filing_url:row.filing_url}});
    if(dates.every(d=>Number(d.slice(0,4))<year)){stop_reason="first_page_strictly_older_than_year";break;}
  }
  if(!stop_reason)throw new Error("drhp_year_boundary_not_reached_within_page_budget");
  if (supplementalSources) {
    const requested_at=clock();
    try {
      const response=await fetchImpl(AXIS_OFFER_DOCS_URL,{method:"GET",redirect:"follow",signal:AbortSignal.timeout(35000),
        headers:{"user-agent":USER_AGENT,"accept":"text/html,*/*","cache-control":"no-cache"}});
      const bytes=Buffer.from(await response.arrayBuffer()), collected_at=clock();
      const file="axis-offer-documents.html";
      if(retainSources)fs.writeFileSync(path.join(retainSources,file),bytes);
      if(!response.ok||!officialAxisUrl(response.url,"/offer-documents")||!response.headers.get("content-type")?.includes("text/html"))throw new Error("invalid_axis_offer_documents_response");
      const rows=parseAxisDrhpRows(bytes.toString("utf8")).filter(r=>r.filing_date.startsWith(year+"-")&&r.filing_date<=collected_at.slice(0,10));
      const seenIssuers=new Set(selected.map(r=>canonicalIssuer(r.issuer_name)));
      let added=0;
      for(const row of rows) {
        const key=canonicalIssuer(row.issuer_name);
        if(!key||seenIssuers.has(key))continue;
        selected.push({...row,source_evidence:{url:AXIS_OFFER_DOCS_URL,final_url:response.url,response_sha256:hash(bytes),collected_at,
          source_authority:"Axis Capital Limited",source_role:"Book Running Lead Manager",filing_url:row.filing_url,date_basis:row.date_basis}});
        seenIssuers.add(key);added++;
      }
      supplemental_source_pages.push({source:"axis_capital_offer_documents",authority:"Axis Capital Limited",role:"Book Running Lead Manager",
        url:AXIS_OFFER_DOCS_URL,final_url:response.url,http_status:response.status,requested_at,collected_at,bytes:bytes.length,sha256:hash(bytes),
        artifact_file:file,parsed_current_year_drhps:rows.length,companies_added_as_fallback:added});
    } catch (error) {
      warnings.push({code:"supplemental_source_unavailable",source:"axis_capital_offer_documents",detail:String(error?.message||error).slice(0,180)});
    }
  }
  // Global URL uniqueness: duplicate observations are not additional filings.
  const unique=new Map();
  for(const row of selected){
    const old=unique.get(row.filing_url);
    if(old&&(canonicalIssuer(old.issuer_name)!==canonicalIssuer(row.issuer_name)||old.filing_date!==row.filing_date||old.filing_type!==row.filing_type))throw new Error("conflicting_drhp_filing_identity");
    unique.set(row.filing_url,row);
  }
  const companies=buildCompanies([...unique.values()]);
  if(!companies.length)throw new Error("no_drhp_companies_for_year");
  const supplementalAdded=supplemental_source_pages.reduce((n,p)=>n+(p.companies_added_as_fallback||0),0);
  return {schema_version:"1.0.0",collector_version:"2.1.0",collection_started_at,generated_at:clock(),
    source:{authority:"Securities and Exchange Board of India",section:"Draft Offer Documents filed with SEBI",listing_url:DRHP_LIST_URL,ajax_url:DRHP_AJAX_URL},
    supplemental_sources:[{authority:"Axis Capital Limited",role:"Book Running Lead Manager",listing_url:AXIS_OFFER_DOCS_URL,
      purpose:"Official lead-manager fallback for DRHPs not yet visible in the SEBI draft-offer index."}],
    coverage:{year,scope:"2026 explicit SEBI DRHP/UDRHP observations plus official lead-manager fallback discoveries; addenda, corrigenda, unlabelled SEBI rows, other years and unconfigured lead-manager sources are not covered.",
      pages_fetched:source_pages.length,stopped_after_page:source_pages.length,stop_reason,official_listing_records_observed:firstTotal,
      raw_filing_observations:selected.length,duplicate_observations:selected.length-unique.size,filing_records:unique.size,companies:companies.length,
      supplemental_source_surfaces_checked:supplemental_source_pages.length,supplemental_companies_added:supplementalAdded,
      pagination_consistent:!warnings.some(w=>w.code==="source_total_changed"),warnings,full_universe_complete:false},
    source_pages,supplemental_source_pages,companies};
}
async function run() {
  const args=process.argv.slice(2);
  if (args.some(a => !a.startsWith("--output=") && !a.startsWith("--year=") && !a.startsWith("--max-pages=") && !a.startsWith("--retain-sources="))) throw new Error("invalid_arguments");
  const output=args.find(a=>a.startsWith("--output="))?.slice(9) || path.join(ROOT,"data","drhp-filings.json");
  const year=Number(args.find(a=>a.startsWith("--year="))?.slice(7) || DEFAULT_YEAR);
  const maxPages=Number(args.find(a=>a.startsWith("--max-pages="))?.slice(12) || DEFAULT_MAX_PAGES);
  const retainSources=args.find(a=>a.startsWith("--retain-sources="))?.slice(17)||null;
  const result=await collectDrhpYear({year,maxPages,retainSources});
  fs.mkdirSync(path.dirname(output),{recursive:true});
  fs.writeFileSync(output,JSON.stringify(result,null,2)+"\n");
  console.log(JSON.stringify({drhp_companies:result.companies.length,filings:result.coverage.filing_records,pages:result.coverage.pages_fetched,year}));
}
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) await run();
