import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { canonicalIssuer, parseSebiDate } from './sync-sebi-documents.mjs';
import { parseNseDate, mapBoard, mapNseStatus } from './sync-nse-live.mjs';
import { UNIVERSE_SOURCES, sha256 } from './collect-ipo-universe-sources.mjs';

export const AUDIT_POLICY = {
  version:'1.0.0', from:'2020-01-01', through:'2026-12-31', as_of:'2026-09-25',
  scope:'Indian Mainboard/SME equity IPO issuer discovery, including draft/RHP/final filings and explicit open/upcoming/closed/listed/withdrawn outcomes.',
  unit:'Normalized issuer identity, not filing count. Repeat offers and name changes require review.',
  exclusions:'Out-of-window dated observations, supplemental/abridged filings and explicitly labelled non-IPO offers are excluded. All non-EQ/SME series and ambiguous filing titles remain unresolved scope-review gaps, not certified non-IPO exclusions.',
  stages:'DRHP/UDRHP, RHP and final prospectus are filing stages only. Never infer listed, completed or withdrawn from a filing stage or source absence.',
  identity:'Exact canonical legal name and compatible exchange/source identifiers only. Never fuzzy-merge, drop India/private, or overwrite conflicts.',
  authority:'Index membership and listing-page observations are discovery only. No auto-import. Independently verify offer identity and issuer-specific official evidence before publication.',
  completeness:'Eight bounded source surfaces are not the full official universe. Pagination, unclassified series, inaccessible/empty HTML, unknown date range and missing sources prevent any full-coverage claim.'
};
const clean = s => String(s??'').replace(/\s+/g,' ').trim();
const decode = s => String(s??'').replace(/&amp;/gi,'&').replace(/&nbsp;/gi,' ').replace(/&#39;|&apos;/gi,"'").replace(/&quot;/gi,'"').replace(/&#(\d+);/g,(_,n)=>String.fromCodePoint(Number(n)));
const text = s => clean(decode(String(s??'').replace(/<[^>]*>/g,' ')));
const compare = (a,b) => a < b ? -1 : a > b ? 1 : 0;
function validDate(value) {
  const d=String(value||'');
  if(!/^\d{4}-\d{2}-\d{2}$/.test(d)) return null;
  const dt=new Date(d+'T00:00:00Z');
  return Number.isFinite(+dt)&&dt.toISOString().slice(0,10)===d?d:null;
}
function official(url, hosts) {
  try {const u=new URL(url); return u.protocol==='https:'&&!u.username&&!u.password&&hosts.includes(u.hostname.toLowerCase());} catch {return false;}
}
export function specificSourceKey(url) {
  try {
    const u=new URL(url);
    if(!official(url,['www.sebi.gov.in','www.nseindia.com','www.bseindia.com','bseindia.com','nsearchives.nseindia.com','archives.nseindia.com'])) return null;
    if(u.hostname==='www.sebi.gov.in'&&/^\/filings\/public-issues\/.+\.html$/i.test(u.pathname)) return u.origin+u.pathname;
    if(/bseindia\.com$/.test(u.hostname)&&/\/DispNewNoticesCirculars\.aspx$/i.test(u.pathname)&&/^\d{8}-\d+$/.test(u.searchParams.get('page')||'')) return 'bse-notice:'+u.searchParams.get('page');
    if(/bseindia\.com$/.test(u.hostname)&&/\/DisplayIPO\.aspx$/i.test(u.pathname)&&/^\d+$/.test(u.searchParams.get('IPONo')||'')) return 'bse-issue:'+u.searchParams.get('IPONo');
    if(u.hostname==='www.nseindia.com'&&u.pathname==='/api/ipo-detail'&&u.searchParams.get('symbol')) return 'nse-issue:'+u.searchParams.get('symbol').toUpperCase()+':'+(u.searchParams.get('series')||'').toUpperCase();
    // Shared collection URLs must never join every issuer to every other issuer.
    return null;
  } catch {return null;}
}
function recordKeys(r) {
  const keys=new Set();
  function walk(v) {
    if(typeof v==='string'){const k=specificSourceKey(v);if(k)keys.add(k);}
    else if(v&&typeof v==='object') for(const x of Object.values(v)) walk(x);
  }
  walk(r); return keys;
}
function candidate(source,index,fields) {
  return {source_id:source.id,row_index:index,source_url:source.url,response_sha256:source.sha256,collected_at:source.collected_at,issuer_name:null,nse_symbol:null,bse_scrip_code:null,board:null,filing_stage:null,outcome:null,observation_date:null,publication_date:null,listing_date:null,source_observed_at:null,issuer_source_url:null,issue_kind_confirmed:false,...fields};
}
export function parseUniverseSource(source, body, policy=AUDIT_POLICY) {
  const rows=[], exclusions=[]; let total=0, pagination=null, gaps=[];
  const skip=(i,reason,detail)=>exclusions.push({row_index:i,reason,detail:clean(detail).slice(0,180)});
  const add=(i,fields)=>{
    const c=candidate(source,i,fields);const date=c.observation_date;
    if(date&&(date<policy.from||date>policy.through)){skip(i,'outside_window',date);return;}
    if(!canonicalIssuer(c.issuer_name)){skip(i,'missing_issuer_identity',c.issuer_name);return;}
    rows.push(c);
  };
  if(source.id.startsWith('nse_')) {
    const payload=JSON.parse(body);if(!Array.isArray(payload))throw new Error('expected NSE array');total=payload.length;
    payload.forEach((r,i)=>{
      const series=clean(r.securityType??r.series).toUpperCase();
      if(!['EQ','SME'].includes(series)){skip(i,'series_requires_scope_review',series||'missing');return;}
      if(/(?:-\s*FPO\b|-\s*Rights Issue\b|\bFollow[- ]on Public Offer\b)/i.test(clean(r.company??r.companyName))){skip(i,'explicit_non_ipo_offer',r.company??r.companyName);return;}
      if(!clean(r.symbol)||!clean(r.company??r.companyName)){skip(i,'malformed_equity_row',r.symbol);return;}
      const listing=validDate(parseNseDate(r.listingDate));
      const start=validDate(parseNseDate(r.ipoStartDate??r.issueStartDate));
      const end=validDate(parseNseDate(r.ipoEndDate??r.issueEndDate));
      const explicit=mapNseStatus(r.status)||(/^withdrawn$/i.test(clean(r.status))?'withdrawn':null);
      // Historical feed presence does not prove a listing when listingDate is '-'.
      add(i,{issuer_name:clean(r.company??r.companyName),nse_symbol:clean(r.symbol).toUpperCase(),board:mapBoard(series),outcome:listing?(listing<=policy.as_of?'listed':'listing_scheduled'):explicit,listing_date:listing,observation_date:listing||start||end,raw_status:clean(r.status)||null,review_note:'Equity public-issue feed; verify IPO versus repeat/FPO offering before import.'});
    });
    gaps.push('returned_feed_only_no_independent_total');
    if(exclusions.some(x=>x.reason==='series_requires_scope_review'))gaps.push('unclassified_series_not_silently_excluded_from_coverage');
  } else if(source.id==='bse_sme_index') {
    const payload=JSON.parse(body);if(!Array.isArray(payload?.Table))throw new Error('expected BSE Table array');total=payload.Table.length;
    payload.Table.forEach((r,i)=>{
      const code=clean(r.SCRIP_CODE);if(!/^\d{6}$/.test(code)||!clean(r.SCRIPNAME)){skip(i,'malformed_index_row',code);return;}
      add(i,{issuer_name:clean(r.SCRIPNAME),bse_scrip_code:code,board:'SME',identity_requires_review:!/(?:limited|ltd\.?)$/i.test(clean(r.SCRIPNAME)),source_observed_at:clean(r.TransDate)||null,review_note:'Index names may be truncated; code/name disagreement requires review. Index as-of is not listing date.'});
    });gaps.push('current_index_not_historical_ipo_universe');
  } else if(source.id.startsWith('sebi_')) {
    const p=text(body).match(/(\d+)\s+to\s+(\d+)\s+of\s+(\d+)\s+records/i);
    pagination=p?{first:Number(p[1]),last:Number(p[2]),total:Number(p[3])}:null;
    const trs=[...body.matchAll(/<tr\b[^>]*>([\s\S]*?)<\/tr>/gi)].filter(m=>/\/filings\/public-issues\//i.test(m[1]));total=trs.length;
    if(!total)throw new Error('no SEBI filing rows; HTML shell is not empty coverage');
    const datePattern=/\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\b/i;
    trs.forEach((m,i)=>{
      // Quoted attributes can contain nested HTML; never parse that as row text.
      const anchor=/<a\b(?:[^>"']|"[^"]*"|'[^']*')*>/gi; let found;
      while((found=anchor.exec(m[1]))) {
        const href=found[0].match(/\bhref\s*=\s*(["'])(.*?)\1/i)?.[2];
        if(!href)continue;
        let url;try{url=new URL(decode(href),'https://www.sebi.gov.in').href;}catch{continue;}
        if(!official(url,['www.sebi.gov.in'])||!/^\/filings\/public-issues\/.+\.html$/i.test(new URL(url).pathname))continue;
        const after=m[1].slice(found.index+found[0].length);
        const title=text(after.split(/<br\b|<\/a>/i)[0]);
        if(/abridged|addendum|corrigendum/i.test(title)){skip(i,'supplemental_filing',title);return;}
        const match=title.match(/^(.*?)\s*[–—-]\s*(DRHP|UDRHP(?:\s*[-–]\s*(?:\d+|[IVX]+))?|RHP|Red Herring Prospectus|(?:Final\s+)?Prospectus)\s*\.?$/i);
        if(!match){skip(i,'ambiguous_filing_title',title);return;}
        const stage=/^(?:U?DRHP)/i.test(match[2])?'draft':/^RHP|^Red Herring/i.test(match[2])?'rhp':'final';
        const slug=new URL(url).pathname.split('/').at(-1).replace(/_\d+\.html$/i,'').replace(/-(?:u?drhp(?:-[ivx\d]+)?|rhp|(?:final-)?prospectus)$/i,'').replace(/-/g,' ');
        const sourceNameConflict=canonicalIssuer(slug)!==canonicalIssuer(match[1]);
        const expected=source.id.slice(5);if(stage!==expected){skip(i,'filing_stage_mismatch',title);return;}
        const date=validDate(parseSebiDate(text(m[1]).match(datePattern)?.[0]));
        if(!date){skip(i,'missing_or_invalid_publication_date',title);return;}
        add(i,{issuer_name:clean(match[1]),identity_requires_review:sourceNameConflict,filing_url_issuer_name:slug,filing_stage:stage,publication_date:date,observation_date:date,issuer_source_url:url,source_title:title,review_note:'Board, offer type and outcome require issuer-specific evidence; a filing does not establish an IPO listing.'});return;
      }
      skip(i,'missing_official_filing_anchor',text(m[1]));
    });
    if(!pagination||pagination.first!==1||pagination.last<pagination.total)gaps.push('pagination_not_exhausted');
    if(exclusions.some(x=>['ambiguous_filing_title','filing_stage_mismatch','missing_official_filing_anchor'].includes(x.reason)))gaps.push('filing_rows_require_manual_review');
  } else if(source.id==='bse_summary') {
    // Do not use broad title/token matching from the diagnostic as issuer authority.
    const links=[...body.matchAll(/DisplayIPO\.aspx\?/gi)];total=links.length;
    gaps.push(links.length?'bse_summary_identity_adapter_pending':'no_issue_rows_html_shell');
  } else throw new Error('unsupported source adapter');
  return {rows,exclusions,raw_rows:total,pagination,gaps,parser_status:source.id==='bse_summary'?'unusable':'parsed'};
}
function hits(c, records, sourceKeys) {
  const key=canonicalIssuer(c.issuer_name);const specific=specificSourceKey(c.issuer_source_url);
  return records.flatMap((r,index)=>{
    const reasons=[];
    if(key&&canonicalIssuer(r.issuer_name)===key)reasons.push('exact_name');
    if(c.nse_symbol&&r.nse_symbol&&clean(r.nse_symbol).toUpperCase()===c.nse_symbol)reasons.push('nse_symbol');
    if(c.bse_scrip_code&&r.bse_scrip_code&&String(r.bse_scrip_code)===c.bse_scrip_code)reasons.push('bse_code');
    if(specific&&sourceKeys[index].has(specific))reasons.push('issuer_source_identity');
    return reasons.length?[{id:r.id,issuer_name:r.issuer_name,board:r.board,nse_symbol:r.nse_symbol||null,bse_scrip_code:r.bse_scrip_code||null,listing_date:r.listing_date?.value||null,reasons}]:[];
  });
}
export function reconcileObservation(c,recovery,published,holds=[],keys=null) {
  const r=hits(c,recovery,keys?.recovery||recovery.map(recordKeys));const p=hits(c,published,keys?.published||published.map(recordKeys));
  const matchingHolds=holds.filter(h=>canonicalIssuer(h.issuer_name)===canonicalIssuer(c.issuer_name)||(c.bse_scrip_code&&String(h.bse_scrip_code)===c.bse_scrip_code));
  const compatible=x=>canonicalIssuer(x.issuer_name)===canonicalIssuer(c.issuer_name)&&(!c.nse_symbol||!x.nse_symbol||x.nse_symbol===c.nse_symbol)&&(!c.bse_scrip_code||!x.bse_scrip_code||x.bse_scrip_code===c.bse_scrip_code)&&(!c.board||!x.board||x.board===c.board);
  let classification=matchingHolds.length?'held_conflict':c.identity_requires_review?'identity_review_required':!r.length&&!p.length?'missing_exact_identity':r.length===1&&p.length===1&&r[0].id===p[0].id&&compatible(r[0])&&compatible(p[0])?'already_present':'identity_review_required';
  const conflicts=[...r,...p].filter(x=>c.listing_date&&x.listing_date&&x.listing_date!==c.listing_date).map(x=>({id:x.id,field:'listing_date',retained:x.listing_date,observed:c.listing_date}));
  if(classification==='already_present'&&conflicts.length) classification='field_conflict';
  return {...c,classification,recovery_matches:r,published_matches:p,holds:matchingHolds,field_conflicts:conflicts,auto_import_allowed:false};
}
export function buildUniverseAudit({sources,bodies,recovery,published,holds=[],baseline={},policy=AUDIT_POLICY,generatedAt=new Date().toISOString()}) {
  if(!Array.isArray(recovery)||!Array.isArray(published))throw new Error('baseline record arrays required');
  const results=[],sourceReports=[];
  const keys={recovery:recovery.map(recordKeys),published:published.map(recordKeys)};
  for(const spec of UNIVERSE_SOURCES){
    const matches=sources.filter(s=>s.id===spec.id);
    if(matches.length>1)throw new Error('duplicate source id: '+spec.id);
    const s=matches[0];let parsed={rows:[],exclusions:[],raw_rows:null,pagination:null,gaps:[],parser_status:'unavailable'};
    let error=null;
    try{
      if(!s||s.status!=='collected')throw new Error(s?.status||'source_not_collected');
      if(s.url!==spec.url)throw new Error('unexpected source URL');
      const bytes=bodies[s.id];if(!Buffer.isBuffer(bytes)||sha256(bytes)!==s.sha256)throw new Error('source hash mismatch');
      parsed=parseUniverseSource(s,bytes.toString('utf8'),policy);
    }catch(e){error=e.message;parsed.gaps.push(e.message);}
    sourceReports.push({...spec,collected_at:s?.collected_at||null,http_status:s?.http_status||null,response_sha256:s?.sha256||null,bytes:s?.bytes||0,parser_status:parsed.parser_status,raw_rows:parsed.raw_rows,parsed_observations:parsed.rows.length,pagination:parsed.pagination,gaps:parsed.gaps,error,exclusions:parsed.exclusions});
    results.push(...parsed.rows.map(c=>reconcileObservation(c,recovery,published,holds,keys)));
  }
  const groups=new Map();
  for(const r of results){const k=canonicalIssuer(r.issuer_name);if(!groups.has(k))groups.set(k,[]);groups.get(k).push(r);}
  const issuers=[...groups].sort(([a],[b])=>compare(a,b)).map(([key,observations])=>{
    const classes=new Set(observations.map(x=>x.classification));
    const identifiers=['nse_symbol','bse_scrip_code'].some(f=>new Set(observations.map(x=>x[f]).filter(Boolean)).size>1);
    const matchedIds=new Set(observations.flatMap(x=>[...x.recovery_matches,...x.published_matches].map(m=>m.id)));
    const classification=classes.has('held_conflict')?'held_conflict':identifiers||matchedIds.size>1||classes.has('identity_review_required')?'identity_review_required':classes.has('field_conflict')?'field_conflict':classes.has('already_present')?'already_present':'missing_exact_identity';
    return {issuer_key:key,issuer_name:observations[0].issuer_name,classification,auto_import_allowed:false,observations};
  });
  const counts=Object.fromEntries(['already_present','missing_exact_identity','identity_review_required','field_conflict','held_conflict'].map(k=>[k,issuers.filter(x=>x.classification===k).length]));
  const seen=new Set(issuers.flatMap(g=>g.observations.flatMap(x=>x.published_matches.map(m=>m.id))));
  const usable=sourceReports.filter(s=>s.parser_status==='parsed').length;
  const duplicateIds=records=>[...new Set(records.filter((r,i)=>records.findIndex(x=>x.id===r.id)!==i).map(x=>x.id))];
  return {schema_version:'1.0.0',audit_execution:usable?'completed':'failed',coverage_status:'partial',full_universe_complete:false,generated_at:generatedAt,policy,baseline:{...baseline,recovery_records:recovery.length,published_records:published.length,duplicate_recovery_ids:duplicateIds(recovery),duplicate_public_ids:duplicateIds(published)},summary:{source_surfaces:UNIVERSE_SOURCES.length,usable_sources:usable,retained_held_issuers:holds.length,observations:results.length,unique_issuer_names:issuers.length,...counts,baseline_records_not_observed:published.filter(r=>!seen.has(r.id)).length,imported_records:0},sources:sourceReports,issuers,retained_holds:holds,notes:['Exact-missing observations are review candidates, not certified missing IPOs; aliases, repeat offerings and incomplete source windows still require independent review.','Not observed in this bounded audit does not mean delisted, withdrawn, removed, or invalid.','Source completeness remains partial even with zero unmatched identities.']};
}
// Durable compact report: full matching rows and original bytes stay in the run artifact.
export function compactUniverseAudit(report) {
  return {
    schema_version:report.schema_version, audit_execution:report.audit_execution,
    coverage_status:report.coverage_status, full_universe_complete:false,
    generated_at:report.generated_at, full_report_sha256:sha256(Buffer.from(JSON.stringify(report,null,2)+'\n')),
    policy:report.policy, baseline:report.baseline, summary:report.summary,
    sources:report.sources.map(({exclusions,...source})=>({...source,excluded_counts:Object.fromEntries([...new Set(exclusions.map(x=>x.reason))].sort().map(reason=>[reason,exclusions.filter(x=>x.reason===reason).length]))})),
    review_candidates:report.issuers.filter(x=>x.classification!=='already_present').map(g=>({
      issuer_key:g.issuer_key,issuer_name:g.issuer_name,classification:g.classification,auto_import_allowed:false,
      observations:g.observations.map(o=>({source_id:o.source_id,row_index:o.row_index,nse_symbol:o.nse_symbol,bse_scrip_code:o.bse_scrip_code,filing_stage:o.filing_stage,outcome:o.outcome,observation_date:o.observation_date,issuer_source_url:o.issuer_source_url,matched_ids:[...new Set([...o.recovery_matches,...o.published_matches].map(m=>m.id))],field_conflicts:o.field_conflicts}))
    })), retained_holds:report.retained_holds, notes:report.notes
  };
}
export function runUniverseAudit({inputDir,root=process.cwd(),output,policy=null}) {
  const manifest=JSON.parse(fs.readFileSync(path.join(inputDir,'sources.json'),'utf8'));
  policy=policy||{...AUDIT_POLICY,as_of:manifest.completed_at.slice(0,10)};
  const inputs=[];
  const read=file=>{const bytes=fs.readFileSync(path.join(root,file));inputs.push({path:file,sha256:sha256(bytes)});return JSON.parse(bytes);};
  const pub=read('data/ipos.json');const recovery=[];
  for(let y=2020;y<=2026;y++)recovery.push(...read(`data/recovery/${y}/nse-issue-information.json`).records);
  const holds=[read('docs/verification/bse-parser-v1.5-repair-and-live-publication-2026-09-25.json').remaining_hold].filter(Boolean);
  const bodies={};
  for(const s of manifest.sources){
    if(!s.file)continue;
    if(s.file!==`raw/${s.id}.txt`||!UNIVERSE_SOURCES.some(x=>x.id===s.id))throw new Error('unsafe source artifact path');
    bodies[s.id]=fs.readFileSync(path.join(inputDir,s.file));
  }
  const report=buildUniverseAudit({sources:manifest.sources,bodies,recovery,published:pub.records,holds,policy,baseline:{dataset_generated_at:pub.generated_at,inputs,collection_run_id:manifest.run_id,source_commit_sha:manifest.source_commit_sha}});
  fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');fs.writeFileSync(output.replace(/\.json$/,'')+'-compact.json',JSON.stringify(compactUniverseAudit(report),null,2)+'\n');return report;
}
if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url){
  const args=Object.fromEntries(process.argv.slice(2).map(x=>{const p=x.indexOf('=');return [x.slice(2,p),x.slice(p+1)];}));
  try{if(!args.input||!args.output)throw new Error('--input and --output required');const r=runUniverseAudit({inputDir:args.input,output:args.output,root:args.root||process.cwd()});console.log(JSON.stringify({audit_execution:r.audit_execution,coverage_status:r.coverage_status,...r.summary}));if(r.audit_execution==='failed')process.exitCode=1;}catch(e){console.error(e);process.exitCode=1;}
}
