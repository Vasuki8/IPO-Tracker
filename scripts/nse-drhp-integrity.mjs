import fs from "node:fs";
import path from "node:path";
import {createHash} from "node:crypto";
import {pathToFileURL} from "node:url";
import {buildNseDraftCompanies,canonicalNseDraftIssuer,NSE_OFFER_API_BASE,NSE_OFFER_PAGE,officialNseArchiveUrl} from "./sync-nse-drhp-offers.mjs";
const assert=(ok,why)=>{if(!ok)throw new Error(why);},hash=v=>createHash("sha256").update(JSON.stringify(v)).digest("hex");
const stamp=v=>typeof v==="string"&&Number.isFinite(Date.parse(v))&&new Date(v).toISOString()===v;
export function validateNseDrhpData(data,{allowLegacy=false}={}){
  assert(data?.schema_version==="1.0.0"&&stamp(data.generated_at),"invalid_nse_drhp_schema");
  assert(data.source?.landing_url===NSE_OFFER_PAGE&&data.source?.api_base===NSE_OFFER_API_BASE&&data.coverage?.year===2026,"invalid_nse_drhp_source");
  assert(Array.isArray(data.source_responses)&&data.source_responses.length===2&&new Set(data.source_responses.map(x=>x.index)).size===2,"invalid_nse_drhp_responses");
  assert(Array.isArray(data.companies)&&data.companies.length>0,"empty_nse_drhp");
  const names=new Set(),urls=new Set();let filings=0;
  for(const c of data.companies){
    const key=canonicalNseDraftIssuer(c.issuer_name);assert(key&&!names.has(key),"duplicate_nse_drhp_company");names.add(key);
    assert(Array.isArray(c.filings)&&c.filing_count===c.filings.length&&c.filings.length>0,"invalid_nse_drhp_company");
    for(const f of c.filings){assert(canonicalNseDraftIssuer(f.issuer_name)===key&&officialNseArchiveUrl(f.filing_url)&&!urls.has(f.filing_url),"invalid_nse_drhp_filing");urls.add(f.filing_url);filings++;
      assert(/^2026-\d\d-\d\d$/.test(f.filing_date)&&f.filing_type==="DRHP","invalid_nse_drhp_date_type");}
  }
  assert(data.coverage.companies===data.companies.length,"nse_drhp_company_count_mismatch");
  assert((allowLegacy&&!data.merge_version)||data.coverage.filing_records===filings,"nse_drhp_filing_count_mismatch");
  return {companies:names.size,filings};
}
export function mergeNseDrhpSnapshots(previous,incoming){
  validateNseDrhpData(incoming,{allowLegacy:true});if(previous){validateNseDrhpData(previous,{allowLegacy:true});assert(incoming.generated_at>=previous.generated_at,"stale_nse_drhp_snapshot");}
  const latest=new Map(incoming.companies.flatMap(c=>c.filings).map(f=>[f.filing_url,structuredClone(f)]));
  for(const old of previous?.companies.flatMap(c=>c.filings)||[]){
    const fresh=latest.get(old.filing_url);
    if(fresh){assert(canonicalNseDraftIssuer(fresh.issuer_name)===canonicalNseDraftIssuer(old.issuer_name)&&fresh.filing_date===old.filing_date&&fresh.board===old.board,"nse_drhp_filing_conflict");continue;}
    const copy=structuredClone(old);copy.not_seen_in_latest_scan=true;copy.retained_snapshot_evidence||={snapshot_generated_at:previous.generated_at,snapshot_sha256:hash(previous),note:"Retained official NSE draft filing; absence from a later API response is not withdrawal evidence."};latest.set(copy.filing_url,copy);
  }
  const data=structuredClone(incoming);data.merge_version="1.0.0";data.companies=buildNseDraftCompanies([...latest.values()]);
  data.coverage={...data.coverage,filing_records:latest.size,companies:data.companies.length,latest_scan_filings:incoming.coverage.filing_records,
    retained_not_seen_latest:data.companies.flatMap(c=>c.filings).filter(f=>f.not_seen_in_latest_scan).length,full_universe_complete:false};
  validateNseDrhpData(data);return data;
}
if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url){
 const args=process.argv.slice(2),arg=k=>args.find(a=>a.startsWith("--"+k+"="))?.split("=").slice(1).join("=");
 assert(args.length===3&&arg("current")&&arg("incoming")&&arg("output"),"use --current= --incoming= --output=");
 const current=fs.existsSync(arg("current"))?JSON.parse(fs.readFileSync(arg("current"))):null,incoming=JSON.parse(fs.readFileSync(arg("incoming")));
 const merged=mergeNseDrhpSnapshots(current,incoming);fs.writeFileSync(arg("output"),JSON.stringify(merged,null,2)+"\n");console.log(JSON.stringify({nse_drhp_publication:validateNseDrhpData(merged),retained_not_seen_latest:merged.coverage.retained_not_seen_latest}));
}
