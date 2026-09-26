import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const DRHP_LIST_URL = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&smid=10&ssid=15";
export const DRHP_AJAX_URL = "https://www.sebi.gov.in/sebiweb/ajax/home/getnewslistinfo.jsp";
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
  return new Date(iso + "T00:00:00Z").toISOString().slice(0,10) === iso ? iso : null;
}
export function canonicalIssuer(value) {
  return norm(value).toLowerCase().replace(/&/g," and ").replace(/\bltd\.?\b/g," limited ")
    .replace(/[^a-z0-9]+/g," ").replace(/\blimited\s*$/g,"").replace(/\s+/g," ").trim();
}
function absoluteUrl(raw, base = DRHP_LIST_URL) {
  try { return new URL(decode(raw), base).href; } catch { return null; }
}
function filingType(label) {
  const text = norm(label);
  if (/\b(?:addendum|corrigendum)\b/i.test(text)) return null;
  const m = text.match(/\b(UDRHP(?:[-\s]*(?:I{1,4}|V|\d+))?|DRHP)\b/i);
  return m ? m[1].toUpperCase().replace(/\s+/g,"-") : null;
}
function escapeRegex(value) {
  return String(value).replace(/[.*+?^$()|[\]\\{}]/g, "\\$&");
}
function issuerFromLabel(label, type) {
  const text = strip(String(label).split(/<br\s*\/?\s*>/i)[0]);
  if (!text) return null;
  return norm(text.replace(new RegExp("\\s*[-–—]?\\s*" + escapeRegex(type) + "\\s*$","i"),""));
}
function firstFilingHref(row) {
  for (const m of row.matchAll(/<a\b[^>]*href\s*=\s*(["'])([^"']+)\1[^>]*>/gi)) {
    const href = absoluteUrl(m[2]);
    if (href && /sebi\.gov\.in\/filings\/public-issues\//i.test(href)) return href;
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
    if (href && /sebi\.gov\.in\/sebi_data\/commondocs\//i.test(href) && /\.pdf(?:$|\?)/i.test(href)) return href;
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
    const type = filingType(title) || filingType(decodeURIComponent(new URL(url).pathname));
    if (!type) continue;
    const issuer_name = issuerFromLabel(title || decodeURIComponent(new URL(url).pathname), type);
    if (!issuer_name) continue;
    entries.push({ issuer_name, filing_type:type, filing_date, filing_url:url, draft_abridged_url:draftAbridgedUrl(row) });
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
async function fetchBytes(url, options = {}) {
  const response = await fetch(url, { redirect:"follow", signal:AbortSignal.timeout(35000),
    headers:{ "user-agent":USER_AGENT, "accept":"text/html,*/*", "cache-control":"no-cache", ...(options.headers || {}) }, ...options });
  if (!response.ok) throw new Error(`SEBI DRHP fetch failed: ${response.status} ${url}`);
  return { response, bytes:Buffer.from(await response.arrayBuffer()) };
}
export async function collectDrhpYear({ year=DEFAULT_YEAR, maxPages=DEFAULT_MAX_PAGES } = {}) {
  if (!Number.isInteger(year) || year < 2000 || year > 2100 || !Number.isInteger(maxPages) || maxPages < 2) throw new Error("invalid_drhp_collection_options");
  const generated_at = new Date().toISOString(), source_pages = [], selected = [];
  const first = await fetchBytes(DRHP_LIST_URL);
  const firstText = first.bytes.toString("utf8"), firstRows = parseDrhpRows(firstText), firstStats = listingStats(firstText);
  source_pages.push({ page:1, url:DRHP_LIST_URL, collected_at:generated_at, bytes:first.bytes.length, sha256:hash(first.bytes), observed_records:firstStats.total_records });
  selected.push(...firstRows.filter(r => r.filing_date.startsWith(year + "-")));
  let stop_reason = null, stopped_after_page = 1;
  for (let page=2; page<=maxPages; page++) {
    const body = paginationBody(page);
    const fetched = await fetchBytes(DRHP_AJAX_URL,{ method:"POST",
      headers:{ "content-type":"application/x-www-form-urlencoded; charset=UTF-8", "x-requested-with":"XMLHttpRequest", "referer":DRHP_LIST_URL }, body });
    const fragment = parseAjaxFragment(fetched.bytes.toString("utf8")), rows = parseDrhpRows(fragment), stats = listingStats(fragment);
    const collected_at = new Date().toISOString();
    source_pages.push({ page, url:DRHP_AJAX_URL, collected_at, bytes:fetched.bytes.length, sha256:hash(fetched.bytes), observed_records:stats.total_records, request_do_direct:page-1 });
    selected.push(...rows.filter(r => r.filing_date.startsWith(year + "-")));
    stopped_after_page = page;
    const dated = [...String(fragment).matchAll(/\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\b/gi)]
      .map(m => parseSebiDate(m[0])).filter(Boolean);
    if (dated.length && dated.every(d => Number(d.slice(0,4)) < year)) { stop_reason = "first_page_strictly_older_than_year"; break; }
  }
  if (!stop_reason) throw new Error("drhp_year_boundary_not_reached_within_page_budget");
  const companies = buildCompanies(selected);
  if (!companies.length) throw new Error("no_drhp_companies_for_year");
  return {
    schema_version:"1.0.0", generated_at,
    source:{ authority:"Securities and Exchange Board of India", section:"Draft Offer Documents filed with SEBI", listing_url:DRHP_LIST_URL, ajax_url:DRHP_AJAX_URL },
    coverage:{ year, scope:"Explicit DRHP/UDRHP filings only; addenda, corrigenda and rows without an explicit DRHP/UDRHP filing marker are excluded.",
      pages_fetched:source_pages.length, stopped_after_page, stop_reason, official_listing_records_observed:firstStats.total_records,
      filing_records:selected.length, companies:companies.length },
    source_pages, companies
  };
}
async function run() {
  const args=process.argv.slice(2);
  if (args.some(a => !a.startsWith("--output=") && !a.startsWith("--year=") && !a.startsWith("--max-pages="))) throw new Error("invalid_arguments");
  const output=args.find(a=>a.startsWith("--output="))?.slice(9) || path.join(ROOT,"data","drhp-filings.json");
  const year=Number(args.find(a=>a.startsWith("--year="))?.slice(7) || DEFAULT_YEAR);
  const maxPages=Number(args.find(a=>a.startsWith("--max-pages="))?.slice(12) || DEFAULT_MAX_PAGES);
  const result=await collectDrhpYear({year,maxPages});
  fs.mkdirSync(path.dirname(output),{recursive:true});
  fs.writeFileSync(output,JSON.stringify(result,null,2)+"\n");
  console.log(JSON.stringify({drhp_companies:result.companies.length,filings:result.coverage.filing_records,pages:result.coverage.pages_fetched,year}));
}
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) await run();
