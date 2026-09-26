/* Read-only DRHP Filed / Pre-IPO directory from official SEBI + NSE draft evidence and the current IPO lifecycle. */
import {buildPreIpoView,mergeOfficialDraftSources} from "./drhp-lifecycle.js";
let DRHP_DATA=null,NSE_DRHP_DATA=null,DRHP_VIEW=null;
const $=selector=>document.querySelector(selector);
function escapeHtml(value){return String(value??"").replace(/[&<>"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"})[char]);}
function safeUrl(value,kind="filing"){
  try{
    const u=new URL(value);if(u.protocol!=="https:"||u.username||u.password)return null;
    if(kind==="source")return ["www.sebi.gov.in","sebi.gov.in","www.nseindia.com","nseindia.com"].includes(u.hostname)?u.href:null;
    if(["www.sebi.gov.in","sebi.gov.in"].includes(u.hostname)&&u.pathname.startsWith("/filings/public-issues/"))return u.href;
    if(u.hostname==="nsearchives.nseindia.com"&&u.pathname.startsWith("/corporate/"))return u.href;
    return null;
  }catch{return null;}
}
function formatDate(value){if(!value)return "—";const d=new Date(value+"T00:00:00Z");return Number.isNaN(d.getTime())?String(value):d.toLocaleDateString("en-GB",{day:"2-digit",month:"short",year:"numeric",timeZone:"UTC"});}
function formatTimestamp(value){if(!value)return "Unavailable";const d=new Date(value);return Number.isNaN(d.getTime())?"Unavailable":d.toLocaleString("en-GB",{day:"2-digit",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit",timeZone:"UTC"})+" UTC";}
function visibleCompanies(){const q=($("#drhpSearch")?.value||"").trim().toLowerCase(),companies=DRHP_VIEW?.companies||[];return q?companies.filter(c=>c.issuer_name.toLowerCase().includes(q)):companies;}
function filingLink(company){const url=safeUrl(company.latest_filing_url);return url?`<a class="drhp-filing-link" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">View official filing ↗</a>`:"Unavailable";}
function sourceLabel(company){return (company.source_authorities||[]).join(" + ")||"Official source";}
function render(){
  if(!DRHP_VIEW)return;const companies=visibleCompanies();$("#drhpVisibleCount").textContent=companies.length;
  $("#drhpRows").innerHTML=companies.map(c=>`<tr>
    <td><strong class="drhp-company-name">${escapeHtml(c.issuer_name)}</strong><span class="secondary">DRHP Filed / Pre-IPO · ${escapeHtml(sourceLabel(c))}</span>${c.latest_processing_status?`<span class="secondary">Draft status: ${escapeHtml(c.latest_processing_status)}</span>`:""}${c.filings?.some(f=>f.not_seen_in_latest_scan)?'<span class="secondary">Includes earlier retained evidence</span>':""}</td>
    <td><span class="source source--verified">${escapeHtml(c.latest_filing_type)}</span></td>
    <td><span class="number">${escapeHtml(formatDate(c.latest_filing_date))}</span></td>
    <td>${filingLink(c)}</td></tr>`).join("");
  $("#drhpCards").innerHTML=companies.map(c=>`<article class="mobile-card drhp-card"><div class="mobile-card__head"><div><strong class="drhp-company-name">${escapeHtml(c.issuer_name)}</strong><div class="company-meta">DRHP Filed / Pre-IPO · ${escapeHtml(c.latest_filing_type)} · ${escapeHtml(formatDate(c.latest_filing_date))}</div><div class="company-meta">${escapeHtml(sourceLabel(c))}${c.latest_processing_status?` · ${escapeHtml(c.latest_processing_status)}`:""}</div></div></div><div class="mobile-card__foot"><span>${c.filing_count>1?`${escapeHtml(c.filing_count)} filing events retained`:"1 filing event retained"}</span>${filingLink(c)}</div></article>`).join("");
  $("#drhpEmpty").hidden=companies.length!==0;
}
function validateSebi(data){
  if(data?.schema_version!=="1.0.0"||data?.coverage?.year!==2026||data?.coverage?.stop_reason!=="first_page_strictly_older_than_year"||!Array.isArray(data.companies)||!data.companies.length||data.coverage.companies!==data.companies.length)return false;
  const urls=new Set();let filings=0;for(const c of data.companies){if(typeof c.issuer_name!=="string"||!Array.isArray(c.filings)||!c.filings.length||c.filing_count!==c.filings.length)return false;for(const f of c.filings){if(!/^U?DRHP/.test(f.filing_type||"")||!safeUrl(f.filing_url)||urls.has(f.filing_url)||!/^2026-\d\d-\d\d$/.test(f.filing_date))return false;urls.add(f.filing_url);filings++;}}return data.coverage.filing_records===filings;
}
function validateNse(data){
  if(data?.schema_version!=="1.0.0"||data?.coverage?.year!==2026||!Array.isArray(data.companies)||!data.companies.length||data.coverage.companies!==data.companies.length||!Array.isArray(data.source_responses))return false;
  const urls=new Set();let filings=0;for(const c of data.companies){if(typeof c.issuer_name!=="string"||!Array.isArray(c.filings)||!c.filings.length||c.filing_count!==c.filings.length)return false;for(const f of c.filings){if(f.filing_type!=="DRHP"||!safeUrl(f.filing_url)||urls.has(f.filing_url)||!/^2026-\d\d-\d\d$/.test(f.filing_date))return false;urls.add(f.filing_url);filings++;}}return data.coverage.filing_records===filings;
}
async function load(){
  $("#drhpLoading").hidden=false;$("#drhpError").hidden=true;$("#drhpResults").hidden=true;
  try{
    const [sebiResponse,nseResponse,ipoResponse]=await Promise.all([
      fetch("data/drhp-filings.json",{cache:"no-store"}),fetch("data/nse-drhp-filings.json",{cache:"no-store"}),fetch("data/ipos.json",{cache:"no-store"})
    ]);
    if(!sebiResponse.ok||!nseResponse.ok||!ipoResponse.ok)throw new Error("Pre-IPO source request failed");
    const [sebi,nse,ipos]=await Promise.all([sebiResponse.json(),nseResponse.json(),ipoResponse.json()]);
    if(!validateSebi(sebi)||!validateNse(nse))throw new Error("Invalid draft-filing source dataset");
    const merged=mergeOfficialDraftSources(sebi,nse),view=buildPreIpoView(merged,ipos);
    if(!view.companies.length)throw new Error("No DRHP Filed / Pre-IPO companies after lifecycle reconciliation");
    DRHP_DATA=sebi;NSE_DRHP_DATA=nse;DRHP_VIEW=view;
    $("#drhpCompanyCount").textContent=view.counts.pre_ipo_companies;$("#drhpFilingCount").textContent=view.counts.pre_ipo_filings;$("#drhpYear").textContent="2026";$("#drhpPages").textContent="SEBI + NSE";
    const last=[sebi.collection_completed_at||sebi.generated_at,nse.generated_at].filter(Boolean).sort().at(-1);
    $("#drhpGenerated").textContent="Latest draft-source collection: "+formatTimestamp(last);
    $("#drhpCoverageNote").textContent=`${view.counts.pre_ipo_companies} pre-IPO companies · ${view.counts.transitioned_companies} draft filers already moved beyond this stage · official SEBI + NSE evidence`;
    const sebiTotals=new Set((sebi.source_pages||[]).map(p=>p.observed_records));
    const retained=(sebi.companies||[]).flatMap(c=>c.filings||[]).filter(f=>f.not_seen_in_latest_scan).length+(nse.companies||[]).flatMap(c=>c.filings||[]).filter(f=>f.not_seen_in_latest_scan).length;
    $("#drhpIntegrityNote").textContent=
      `Lifecycle rule: a company stays here only while official DRHP/UDRHP evidence exists and it has neither an official issue-open/close date nor an IPO Tracker record in Upcoming, Open, Closed, or Listed. ${view.counts.transitioned_companies} source company/companies are therefore hidden here; draft history remains retained. `+
      (view.counts.lifecycle_gaps?`${view.counts.lifecycle_gaps} official issue-date signal(s) are awaiting a matching normal lifecycle record and are hidden rather than mislabelled pre-IPO. `:"")+
      (sebiTotals.size>1?"SEBI pagination totals differed during collection. ":"")+"Neither source is treated as a complete national DRHP register. "+(retained?`${retained} earlier filing observation(s) remain retained despite absence from a later scan. `:"");
    const sourceUrl=safeUrl(sebi.source?.listing_url,"source");if(sourceUrl)$("#sebiSourceLink").href=sourceUrl;
    $("#drhpLoading").hidden=true;$("#drhpResults").hidden=false;render();
    try{const r=await fetch("ops/drhp-collection.json",{cache:"no-store"});if(!r.ok)throw new Error();const h=await r.json();if(["failed","degraded"].includes(h.status))$("#drhpIntegrityNote").textContent+=" Latest draft-source refresh is "+h.status+"; the last successful evidence remains available.";}catch{$("#drhpIntegrityNote").textContent+=" Latest draft-source refresh status is unavailable.";}
  }catch(error){console.error(error);$("#drhpLoading").hidden=true;$("#drhpError").hidden=false;}
}
$("#drhpSearch").addEventListener("input",render);$("#drhpRetry").addEventListener("click",load);load();
