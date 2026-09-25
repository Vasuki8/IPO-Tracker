import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';

// Read-only, bounded evidence collection. A response is not a completeness claim.
export const UNIVERSE_SOURCES = [
  {id:'nse_past', authority:'NSE', format:'json', url:'https://www.nseindia.com/api/public-past-issues', scope:'Returned historical public-issues feed; no independent total or full-history guarantee.'},
  {id:'nse_current', authority:'NSE', format:'json', url:'https://www.nseindia.com/api/ipo-current-issue', scope:'Current issues only; not the historical universe.'},
  {id:'nse_upcoming', authority:'NSE', format:'json', url:'https://www.nseindia.com/api/all-upcoming-issues?category=ipo', scope:'Upcoming issues only; no inference of withdrawal from absence.'},
  {id:'bse_summary', authority:'BSE', format:'html', url:'https://www.bseindia.com/markets/PublicIssues/Issuesummary.aspx', scope:'Returned summary page only; unrequested tabs and pagination remain unaudited.'},
  {id:'bse_sme_index', authority:'BSE', format:'json', url:'https://www.bseindices.com/AsiaIndexAPI/api/Codewise_Indices/w?code=76', scope:'Current BSE SME IPO index constituents, not all IPOs or listing-term authority.'},
  {id:'sebi_draft', authority:'SEBI', format:'html', url:'https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&smid=10&ssid=15', scope:'First draft-offer-documents page only; filing stage is not an offer outcome.'},
  {id:'sebi_rhp', authority:'SEBI', format:'html', url:'https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&smid=11&ssid=15', scope:'First red-herring-documents page only; filing stage is not an offer outcome.'},
  {id:'sebi_final', authority:'SEBI', format:'html', url:'https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&smid=12&ssid=15', scope:'First final-offer-documents page only; prospectus filing does not prove listing.'}
];
const HOME = 'https://www.nseindia.com/market-data/all-upcoming-issues-ipo';
const UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36';
export const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');

export async function collectUniverseSources({outputDir, fetchImpl=fetch, now=()=>new Date().toISOString()}={}) {
  if (!outputDir) throw new Error('outputDir is required');
  fs.mkdirSync(path.join(outputDir,'raw'),{recursive:true});
  let cookie = '';
  const started = now();
  const warmup = {url:HOME, status:'not_attempted'};
  try {
    const response = await fetchImpl(HOME,{headers:{'user-agent':UA,accept:'text/html'},signal:AbortSignal.timeout(20000)});
    warmup.http_status = response.status;
    warmup.status = response.ok ? 'success' : 'http_error';
    cookie = (response.headers.getSetCookie?.() || []).map(x=>x.split(';')[0]).join('; ');
    await response.body?.cancel();
  } catch (error) { warmup.status='fetch_error'; warmup.error=String(error.message); }
  const sources = [];
  for (const spec of UNIVERSE_SOURCES) {
    const source = {...spec, requested_at:now(), collected_at:null, status:'fetch_error', file:null, sha256:null, bytes:0};
    try {
      const headers = {'user-agent':UA, accept:spec.format==='json'?'application/json,*/*':'text/html', 'accept-language':'en-US,en;q=0.9', referer:new URL(spec.url).origin+'/'};
      if (spec.authority==='NSE') {headers.referer=HOME; if(cookie) headers.cookie=cookie;}
      const response = await fetchImpl(spec.url,{headers,signal:AbortSignal.timeout(20000)});
      source.http_status=response.status;
      source.final_url=response.url || spec.url;
      source.content_type=response.headers.get('content-type');
      source.http_date=response.headers.get('date');
      source.http_last_modified=response.headers.get('last-modified');
      const bytes=Buffer.from(await response.arrayBuffer());
      if(bytes.length>15000000) throw new Error('source exceeds 15 MB audit bound');
      source.collected_at=now(); source.bytes=bytes.length; source.sha256=sha256(bytes);
      source.file='raw/'+spec.id+'.txt';
      fs.writeFileSync(path.join(outputDir,source.file),bytes);
      const destination=new URL(source.final_url);
      const origin=new URL(spec.url);
      source.status=!response.ok?'http_error':destination.protocol!=='https:'||destination.hostname!==origin.hostname?'unexpected_redirect':'collected';
    } catch (error) {source.error=String(error.message); source.collected_at=now();}
    sources.push(source);
  }
  const manifest={schema_version:'1.0.0',started_at:started,completed_at:now(),run_id:process.env.GITHUB_RUN_ID||null,source_commit_sha:process.env.GITHUB_SHA||null,nse_warmup:warmup,sources,scope_note:'Eight bounded official-source observations. HTTP Date and Last-Modified are transport metadata, not source business observation times. No repository data is modified.'};
  fs.writeFileSync(path.join(outputDir,'sources.json'),JSON.stringify(manifest,null,2)+'\n');
  return manifest;
}
if(process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url){
  const outputDir=process.argv.find(x=>x.startsWith('--output-dir='))?.slice(13);
  collectUniverseSources({outputDir}).then(m=>console.log(JSON.stringify(m.sources.map(s=>({id:s.id,status:s.status,bytes:s.bytes}))))).catch(e=>{console.error(e);process.exitCode=1;});
}
