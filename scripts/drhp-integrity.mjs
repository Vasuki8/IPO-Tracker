import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {buildCompanies,canonicalIssuer,officialSebiUrl,DRHP_LIST_URL} from './sync-sebi-drhp.mjs';
const hash=v=>createHash('sha256').update(JSON.stringify(v)).digest('hex');
const assert=(ok,why)=>{if(!ok)throw new Error(why);};
const stamp=v=>typeof v==='string'&&Number.isFinite(Date.parse(v))&&new Date(v).toISOString()===v;
export function validateDrhpData(data,{allowLegacyCounts=false}={}) {
  assert(data?.schema_version==='1.0.0'&&stamp(data.generated_at),'invalid_drhp_schema_or_timestamp');
  assert(data.source?.listing_url===DRHP_LIST_URL&&data.coverage?.year===2026&&data.coverage.stop_reason==='first_page_strictly_older_than_year','invalid_drhp_scope');
  assert(Array.isArray(data.source_pages)&&data.source_pages.length===data.coverage.pages_fetched&&data.source_pages.length>=2,'invalid_drhp_pages');
  assert(Array.isArray(data.companies)&&data.companies.length>0,'empty_drhp_data');
  const urls=new Set(),names=new Set();let count=0;
  for(const c of data.companies){
    const key=canonicalIssuer(c.issuer_name);assert(key&&!names.has(key),'duplicate_drhp_company');names.add(key);
    assert(c.filing_count===c.filings?.length&&c.filing_count>0,'invalid_drhp_company_count');
    for(const f of c.filings){
      assert(canonicalIssuer(f.issuer_name)===key&&officialSebiUrl(f.filing_url),'invalid_drhp_filing_identity_or_url');
      assert(!urls.has(f.filing_url),'duplicate_drhp_filing_url');urls.add(f.filing_url);count++;
      assert(/^(?:DRHP|UDRHP(?:-?(?:I{1,4}|V|\d+))?)$/.test(f.filing_type),'invalid_drhp_type');
      assert(/^2026-\d\d-\d\d$/.test(f.filing_date)&&Number.isFinite(Date.parse(f.filing_date))&&new Date(f.filing_date).toISOString().slice(0,10)===f.filing_date&&f.filing_date<=data.generated_at.slice(0,10),'invalid_drhp_date');
      assert(!f.draft_abridged_url||officialSebiUrl(f.draft_abridged_url,'/sebi_data/commondocs/'),'unsafe_abridged_url');
    }
    const latest=[...c.filings].sort((a,b)=>b.filing_date.localeCompare(a.filing_date))[0];
    assert(c.latest_filing_url===latest.filing_url&&c.latest_filing_date===latest.filing_date&&c.latest_filing_type===latest.filing_type,'drhp_latest_filing_mismatch');
  }
  assert(data.coverage.companies===data.companies.length,'drhp_company_count_mismatch');
  assert((allowLegacyCounts&&!data.collector_version)||data.coverage.filing_records===count,'drhp_filing_count_mismatch');
  return {companies:names.size,filings:count};
}
/** Filing history is append-preserving. Absence from a changing index is not withdrawal evidence. */
export function mergeDrhpSnapshots(previous,incoming) {
  validateDrhpData(incoming,{allowLegacyCounts:true});
  if(previous){validateDrhpData(previous,{allowLegacyCounts:true});assert(incoming.generated_at>=previous.generated_at,'stale_drhp_snapshot');}
  const latest=new Map(incoming.companies.flatMap(c=>c.filings).map(f=>[f.filing_url,structuredClone(f)]));
  const prior=previous?.companies.flatMap(c=>c.filings)||[];
  const retained=[];
  for(const f of prior){
    const seen=latest.get(f.filing_url);
    if(seen){assert(canonicalIssuer(seen.issuer_name)===canonicalIssuer(f.issuer_name)&&seen.filing_type===f.filing_type&&seen.filing_date===f.filing_date,'drhp_filing_conflict');continue;}
    const copy=structuredClone(f);copy.not_seen_in_latest_scan=true;
    copy.retained_snapshot_evidence||={snapshot_generated_at:previous.generated_at,snapshot_projection_sha256:hash(previous),
      source_pages:previous.source_pages,note:'Retained filing from earlier source-backed dataset; no specific source row is inferred for legacy entries.'};
    latest.set(f.filing_url,copy);retained.push(f.filing_url);
  }
  for(const f of incoming.companies.flatMap(c=>c.filings))if(latest.has(f.filing_url)&&!f.not_seen_in_latest_scan)latest.get(f.filing_url).not_seen_in_latest_scan=false;
  const data=structuredClone(incoming);data.collector_version='2.0.0';
  data.collection_started_at ||= incoming.generated_at;
  data.collection_completed_at ||= [...incoming.source_pages.map(p=>p.collected_at),incoming.generated_at].sort().at(-1);data.companies=buildCompanies([...latest.values()]);
  const totals=[...new Set(data.source_pages.map(p=>p.observed_records).filter(Number.isInteger))];
  data.coverage={...data.coverage,filing_records:latest.size,companies:data.companies.length,
    latest_scan_unique_filings:incoming.coverage.latest_scan_unique_filings??incoming.companies.reduce((n,c)=>n+c.filings.filter(f=>!f.not_seen_in_latest_scan).length,0),
    retained_not_seen_latest:data.companies.flatMap(c=>c.filings).filter(f=>f.not_seen_in_latest_scan).length,
    pagination_consistent:totals.length===1,observed_source_totals:totals,full_universe_complete:false,
    limitations:'2026 explicit DRHP/UDRHP observations only. Changing pagination may omit rows; past filings are retained, not presumed withdrawn. Unlabelled filings, other years and exchange-only sources are outside coverage.'};
  validateDrhpData(data);return data;
}
if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url){
  const args=process.argv.slice(2);assert(args.length===3&&args.every(a=>/^--(?:current|incoming|output)=/.test(a)),'use --current= --incoming= --output=');
  const arg=k=>args.find(a=>a.startsWith('--'+k+'='))?.split('=').slice(1).join('=');
  const previous=JSON.parse(fs.readFileSync(arg('current'))), incoming=JSON.parse(fs.readFileSync(arg('incoming')));
  const merged=mergeDrhpSnapshots(previous,incoming);fs.writeFileSync(arg('output'),JSON.stringify(merged,null,2)+'\n');
  console.log(JSON.stringify({drhp_publication:validateDrhpData(merged),retained_not_seen_latest:merged.coverage.retained_not_seen_latest}));
}
