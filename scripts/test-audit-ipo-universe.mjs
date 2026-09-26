import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { AUDIT_POLICY, specificSourceKey, parseUniverseSource, reconcileObservation, buildUniverseAudit, runUniverseAudit, compactUniverseAudit } from './audit-ipo-universe.mjs';
import { UNIVERSE_SOURCES, sha256, collectUniverseSources } from './collect-ipo-universe-sources.mjs';
const when='2026-09-25T04:19:36.443Z';
const src=id=>({...UNIVERSE_SOURCES.find(s=>s.id===id),collected_at:when});
const nse=(extras={})=>({company:'Example Limited',symbol:'EXAMPLE',securityType:'EQ',listingDate:'24-SEP-2026',ipoStartDate:'21-SEP-2026',...extras});
const parse=(id,data)=>parseUniverseSource(src(id),typeof data==='string'?data:JSON.stringify(data));
assert.equal(parse('nse_past',[nse()]).rows[0].outcome,'listed');
assert.equal(parse('nse_past',[nse({listingDate:'28-SEP-2026'})]).rows[0].outcome,'listing_scheduled');
assert.equal(parse('nse_past',[nse({listingDate:'-',ipoStartDate:'28-SEP-2026',status:'Forthcoming'})]).rows[0].outcome,'upcoming');
assert.equal(parse('nse_past',[nse({listingDate:'31-FEB-2026'})]).rows[0].listing_date,null);
assert.equal(parse('nse_past',[nse({listingDate:'-',status:'Withdrawn'})]).rows[0].outcome,'withdrawn');
assert.equal(parse('nse_past',[nse({listingDate:'-',status:undefined})]).rows[0].outcome,null);
assert.equal(parse('nse_past',[nse({listingDate:'01-JAN-2019'})]).exclusions[0].reason,'outside_window');
assert.equal(parse('nse_past',[nse({securityType:'BE'})]).exclusions[0].reason,'series_requires_scope_review');
assert.equal(parse('nse_past',[nse({company:'Example Limited-FPO'})]).exclusions[0].reason,'explicit_non_ipo_offer');
assert.equal(parse('nse_current',[]).rows.length,0);
assert.throws(()=>parse('nse_past',{error:'denied'}),/array/);
assert.throws(()=>parse('nse_past','not JSON'));
assert.equal(parse('bse_summary','<html><body>LIVE BSE</body></html>').parser_status,'unavailable');
assert.equal(parse('bse_summary','<html><body>LIVE BSE</body></html>').gaps[0],'no_issue_rows_html_shell');
const bseSummaryHtml='<table><tr><td>Example Limited</td><td><a href="/markets/publicIssues/DisplayIPO.aspx?IPONo=7001&amp;id=1&amp;idtype=1&amp;startdt=29%2F04%2F2025&amp;status=H&amp;type=IPO">View Detail</a></td></tr></table>';
const bseSummary=parse('bse_summary',bseSummaryHtml);
assert.equal(bseSummary.parser_status,'parsed');
assert.equal(bseSummary.rows.length,1);
assert.equal(bseSummary.rows[0].issuer_name,'Example Limited');
assert.equal(bseSummary.rows[0].observation_date,'2025-04-29');
assert.match(bseSummary.rows[0].issuer_source_url,/IPONo=7001/);
assert.ok(bseSummary.gaps.includes('bse_summary_first_page_only_dedicated_audit_required'));
assert.throws(()=>parse('bse_sme_index',[]),/Table/);
const index=parse('bse_sme_index',{Table:[{SCRIP_CODE:543999,SCRIPNAME:'EXAMPLE LIMI',TransDate:'2026-08-31T00:00:00'}]}).rows[0];
assert.equal(index.identity_requires_review,true);assert.equal(index.listing_date,null);
assert.equal(index.source_observed_at,'2026-08-31T00:00:00');
const listing=(title,href='https://www.sebi.gov.in/filings/public-issues/sep-2026/example-limited-rhp_100.html',date='Sep 23, 2026')=>`1 to 25 of 100 records <table><tr><td>${date}</td><td><a href="${href}" title="${title} &lt;br&gt;&lt;a href='other.pdf'&gt;abridged&lt;/a&gt;">${title}<br><a href="other.pdf">Wrong Other Issuer - Abridged Prospectus</a></a></td></tr></table>`;
const rhp=parse('sebi_rhp',listing('Example Limited - RHP'));
assert.equal(rhp.rows[0].issuer_name,'Example Limited');assert.equal(rhp.rows[0].filing_stage,'rhp');assert.equal(rhp.rows[0].outcome,null);
assert.equal(rhp.rows[0].publication_date,'2026-09-23');assert.equal(rhp.pagination.total,100);assert.ok(rhp.gaps.includes('pagination_not_exhausted'));
assert.equal(parse('sebi_draft',listing('Example Limited - DRHP')).rows[0].filing_stage,'draft');
assert.equal(parse('sebi_draft',listing('Example Limited - UDRHP-I')).rows[0].filing_stage,'draft');
assert.equal(parse('sebi_final',listing('Example Limited – Prospectus')).rows[0].outcome,null);
assert.equal(parse('sebi_rhp',listing('Example Limited - Addendum to RHP')).exclusions[0].reason,'supplemental_filing');
assert.equal(parse('sebi_rhp',listing('Example Limited')).exclusions[0].reason,'ambiguous_filing_title');
assert.equal(parse('sebi_rhp',listing('Example Limited - DRHP')).exclusions[0].reason,'filing_stage_mismatch');
assert.equal(parse('sebi_rhp',listing('Example Limited - RHP',undefined,'Feb 30, 2026')).rows.length,0);
assert.equal(parse('sebi_rhp',listing('Example Limited - RHP','https://www.sebi.gov.in.evil.test/filings/public-issues/x.html')).rows.length,0);
assert.throws(()=>parse('sebi_rhp','Access denied'),/no SEBI/);
for(const url of ['https://www.nseindia.com/api/public-past-issues','https://www.bseindia.com/markets/PublicIssues/Issuesummary.aspx','https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes'])assert.equal(specificSourceKey(url),null);
assert.equal(specificSourceKey('https://www.bseindia.com/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=20220112-10'),'bse-notice:20220112-10');
assert.equal(specificSourceKey('https://www.bseindia.com.evil.test/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=20220112-10'),null);
const c=parse('nse_past',[nse()]).rows[0];
const r={id:'example',issuer_name:'Example Limited',board:'Mainboard',nse_symbol:'EXAMPLE',listing_date:{value:'2026-09-24'},documents:[]};
const p={...r};delete p.nse_symbol;
assert.equal(reconcileObservation(c,[r],[p]).classification,'already_present');
assert.equal(reconcileObservation(c,[],[]).classification,'missing_exact_identity');
assert.equal(reconcileObservation(index,[],[]).classification,'identity_review_required');
assert.equal(reconcileObservation(c,[{...r,issuer_name:'Other Limited'}],[p]).classification,'identity_review_required');
assert.equal(reconcileObservation({...c,nse_symbol:'WRONG'},[r],[p]).classification,'identity_review_required');
assert.equal(reconcileObservation(c,[r,r],[p]).classification,'identity_review_required');
assert.equal(reconcileObservation(c,[r],[]).classification,'identity_review_required');
assert.equal(reconcileObservation(c,[{...r,listing_date:{value:'2026-09-23'}}],[p]).classification,'field_conflict');
assert.equal(reconcileObservation(c,[r],[p],[{issuer_name:'Example Ltd',reason:'unresolved'}]).classification,'held_conflict');
assert.equal(reconcileObservation({...c,issuer_name:'Example (India) Limited'},[r],[p]).classification,'identity_review_required');
assert.equal(reconcileObservation({...c,issuer_name:'New Limited',nse_symbol:null,issuer_source_url:'https://www.nseindia.com/api/public-past-issues'},[r],[p]).classification,'missing_exact_identity');
const bytes=Buffer.from(JSON.stringify([nse(),nse()]));
const observation={...src('nse_past'),status:'collected',sha256:sha256(bytes)};
const input={sources:[observation],bodies:{nse_past:bytes},recovery:[r],published:[p],generatedAt:when};
const before=JSON.stringify(input);
const report=buildUniverseAudit(input);
assert.equal(report.summary.observations,2);assert.equal(report.summary.unique_issuer_names,1);assert.equal(report.summary.already_present,1);
assert.equal(report.summary.imported_records,0);assert.equal(report.full_universe_complete,false);assert.equal(report.coverage_status,'partial');
assert.equal(JSON.stringify(input),before,'pure audit must not mutate baseline or source objects');
assert.deepEqual(buildUniverseAudit(input),report,'fixed clock produces deterministic report');
assert.equal(buildUniverseAudit({...input,bodies:{nse_past:Buffer.from('[]')}}).sources[0].error,'source hash mismatch');
assert.equal(buildUniverseAudit({...input,sources:[]}).audit_execution,'failed');
assert.throws(()=>buildUniverseAudit({...input,sources:[observation,observation]}),/duplicate source/);
assert.equal(buildUniverseAudit({...input,holds:[{issuer_name:'Held Limited'}]}).summary.retained_held_issuers,1);
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'universe-test-'));
try {
  const calls=[]; const mock=async(url)=>{calls.push(url);return new Response(url.includes('all-upcoming-issues-ipo')?'landing':'[]',{status:200,headers:{'content-type':'application/json'}});};
  const collected=await collectUniverseSources({outputDir:temp,fetchImpl:mock,now:()=>when});
  assert.equal(calls.length,9);assert.equal(collected.sources.length,8);assert.ok(collected.sources.every(s=>s.status==='collected'));
  for(const s of collected.sources)assert.equal(sha256(fs.readFileSync(path.join(temp,s.file))),s.sha256);
  const failed=await collectUniverseSources({outputDir:temp,fetchImpl:async()=>{throw new Error('offline');},now:()=>when});
  assert.equal(failed.sources.filter(s=>s.status==='fetch_error').length,8);
  const http=await collectUniverseSources({outputDir:temp,fetchImpl:async()=>new Response('denied',{status:403}),now:()=>when});
  assert.equal(http.sources.filter(s=>s.status==='http_error').length,8);assert.ok(http.sources.every(s=>s.file&&s.sha256),'failed response bytes still retained');
} finally {fs.rmSync(temp,{recursive:true,force:true});}
console.log('Official-universe source, date, identity, ambiguity, pagination, hash, isolation and collection-failure regressions passed.');

// Source-shape fixtures from the first bounded operational observation.
const real=JSON.parse(fs.readFileSync(new URL('./fixtures/ipo-universe-source-contract.json',import.meta.url),'utf8'));
for(const fixture of real.fixtures){
  assert.equal(sha256(Buffer.from(fixture.body)),fixture.fixture_sha256);
  const result=parse(fixture.source_id,fixture.body);
  if(fixture.source_id==='nse_past'){
    assert.equal(result.rows.length,2);assert.equal(result.rows[0].outcome,null);
    assert.equal(result.exclusions[0].reason,'explicit_non_ipo_offer');
  }else if(fixture.source_id==='bse_sme_index'){
    assert.equal(result.rows.length,2);assert.equal(result.rows[0].identity_requires_review,true);
  }else if(fixture.source_id.startsWith('sebi_')){
    assert.equal(result.rows.length,1);assert.equal(result.rows[0].filing_stage,fixture.source_id.slice(5));
    assert.equal(result.rows[0].outcome,null);assert.doesNotMatch(result.rows[0].issuer_name,/abridged/i);
  }else if(fixture.source_id==='bse_summary'){
    assert.equal(result.parser_status,'unavailable');
    assert.ok(result.gaps.includes('no_issue_rows_html_shell'));
  }else assert.fail('unexpected source fixture '+fixture.source_id);
}
console.log('Six retained official-source shape fixtures passed.');

assert.equal(parse('sebi_rhp',listing('Different Issuer Limited - RHP')).rows[0].identity_requires_review,true);
assert.equal(compactUniverseAudit(report).review_candidates.length,0);
assert.equal(compactUniverseAudit(report).full_report_sha256,sha256(Buffer.from(JSON.stringify(report,null,2)+'\n')));
assert.equal(compactUniverseAudit(report).full_universe_complete,false);
