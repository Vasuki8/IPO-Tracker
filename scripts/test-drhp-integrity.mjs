import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {buildCompanies,collectDrhpYear,officialSebiUrl,officialDrhpDocumentUrl,parseDrhpRows,parseSebiDate,DRHP_LIST_URL,DRHP_AJAX_URL} from './sync-sebi-drhp.mjs';
import {validateDrhpData,mergeDrhpSnapshots} from './drhp-integrity.mjs';
const base='https://www.sebi.gov.in/filings/public-issues/';
const filing=(name='Example Limited',id=100)=>({issuer_name:name,filing_type:'DRHP',filing_date:'2026-06-18',filing_url:base+'jun-2026/example-drhp_'+id+'.html',draft_abridged_url:null});
const snapshot=(entries,time)=>({schema_version:'1.0.0',generated_at:time,source:{listing_url:DRHP_LIST_URL},coverage:{year:2026,stop_reason:'first_page_strictly_older_than_year',pages_fetched:2,companies:buildCompanies(entries).length,filing_records:entries.length},source_pages:[{page:1,collected_at:time,observed_records:50},{page:2,collected_at:time,observed_records:48}],companies:buildCompanies(entries)});
const old=snapshot([filing(),filing('Retained Limited',101)],'2026-09-25T01:00:00.000Z');
const fresh=snapshot([filing()],'2026-09-26T01:00:00.000Z');

const milkyBad={issuer_name:'Milky Mist Dairy Foods Limited',filing_type:'DRHP',filing_date:'2026-08-14',
  filing_url:'https://www.axiscapital.co.in/contents/Milky%20Mist%20Dairy%20Foods%20Limited%20-%20DRHP-1753171511-1786688069.pdf',
  draft_abridged_url:null,source_kind:'official_lead_manager',source_authority:'Axis Capital Limited',date_basis:'lead_manager_document_upload_timestamp'};
const eaaaBad={issuer_name:'EAAA India Alternatives Ltd-DRHP (2026)',filing_type:'DRHP',filing_date:'2026-08-14',
  filing_url:'https://www.axiscapital.co.in/contents/EAAA%20India%20Alternatives%20Ltd-DRHP-1786445574-1786687038.pdf',
  draft_abridged_url:null,source_kind:'official_lead_manager',source_authority:'Axis Capital Limited',date_basis:'lead_manager_document_upload_timestamp'};
const eaaaCorrected={issuer_name:'EAAA India Alternatives Ltd',filing_type:'DRHP',filing_date:'2026-08-11',
  filing_url:eaaaBad.filing_url,draft_abridged_url:null,source_kind:'official_lead_manager',source_authority:'Axis Capital Limited',
  date_basis:'lead_manager_document_earliest_url_timestamp',explicit_label_year:2026};
const legacyAxis=snapshot([filing(),milkyBad,eaaaBad],'2026-09-25T02:00:00.000Z');
const correctedAxis=snapshot([filing(),eaaaCorrected],'2026-09-26T02:00:00.000Z');
correctedAxis.collector_version='2.2.0';
const correctedMerge=mergeDrhpSnapshots(legacyAxis,correctedAxis);
assert.equal(correctedMerge.companies.some(c=>c.issuer_name==='Milky Mist Dairy Foods Limited'),false,'old 2025 Axis DRHP mirror is removed from the 2026 union');
const correctedEaaa=correctedMerge.companies.find(c=>c.issuer_name==='EAAA India Alternatives Ltd');
assert.ok(correctedEaaa);
assert.equal(correctedEaaa.latest_filing_date,'2026-08-11');
assert.equal(correctedEaaa.filings[0].date_basis,'lead_manager_document_earliest_url_timestamp');
assert.ok(correctedMerge.corrections.some(c=>c.action==='removed_out_of_scope_axis_fallback'&&c.filing_url===milkyBad.filing_url));
assert.ok(correctedMerge.corrections.some(c=>c.action==='corrected_axis_fallback_projection'&&c.filing_url===eaaaBad.filing_url));
assert.equal(correctedMerge.coverage.corrected_invalid_supplemental_rows,2);
const eaaaPrimary={issuer_name:'EAAA India Alternatives Limited',filing_type:'DRHP',filing_date:'2026-01-22',
  filing_url:'https://www.sebi.gov.in/filings/public-issues/jan-2026/eaaa-india-alternatives-limited-drhp_99257.html',draft_abridged_url:null};
const legacyDuplicate=snapshot([filing(),eaaaBad],'2026-09-25T03:00:00.000Z');
const primaryNow=snapshot([filing(),eaaaPrimary],'2026-09-26T03:00:00.000Z');
primaryNow.collector_version='2.2.0';
const dedupedAxis=mergeDrhpSnapshots(legacyDuplicate,primaryNow);
assert.equal(dedupedAxis.companies.some(c=>/DRHP \(2026\)/.test(c.issuer_name)),false,'malformed Axis mirror identity is retired');
assert.ok(dedupedAxis.companies.some(c=>c.issuer_name==='EAAA India Alternatives Limited'),'primary-source legal issuer remains');
assert.ok(dedupedAxis.corrections.some(c=>c.action==='removed_superseded_axis_mirror_identity'&&c.filing_url===eaaaBad.filing_url));
assert.equal(dedupedAxis.coverage.corrected_invalid_supplemental_rows,1);
const original=JSON.stringify([old,fresh]);
const merged=mergeDrhpSnapshots(old,fresh);
assert.deepEqual(validateDrhpData(merged),{companies:2,filings:2});
assert.equal(merged.coverage.retained_not_seen_latest,1);
assert.equal(merged.coverage.pagination_consistent,false);
assert.equal(merged.coverage.full_universe_complete,false);
assert.equal(JSON.stringify([old,fresh]),original);
assert.deepEqual(mergeDrhpSnapshots(merged,fresh),merged);
assert.throws(()=>mergeDrhpSnapshots(fresh,old),/stale/);
const conflict=structuredClone(fresh);conflict.companies[0].filings[0].filing_date='2026-06-19';conflict.companies[0].latest_filing_date='2026-06-19';assert.throws(()=>mergeDrhpSnapshots(old,conflict),/conflict/);
const wrongCount=structuredClone(merged);wrongCount.coverage.filing_records=99;assert.throws(()=>validateDrhpData(wrongCount),/count/);
const duplicated=structuredClone(merged);duplicated.companies.push(duplicated.companies[0]);assert.throws(()=>validateDrhpData(duplicated),/duplicate/);
for(const url of ['https://evilsebi.gov.in/filings/public-issues/x','https://www.sebi.gov.in.evil.test/filings/public-issues/x','javascript:alert(1)','https://www.sebi.gov.in@evil.test/filings/public-issues/x','http://www.sebi.gov.in/filings/public-issues/x'])assert.equal(officialSebiUrl(url),null);
assert.ok(officialDrhpDocumentUrl('https://www.axiscapital.co.in/contents/Abakkus%20Asset%20Manager%20Limited%20-%20Draft%20Red%20Herring%20Prospectus-1790067639.pdf'));
assert.equal(officialDrhpDocumentUrl('https://www.axiscapital.co.in/contents/not-a-pdf.txt'),null);
assert.equal(parseSebiDate('Jan 99, 2026'),null);
const badTitle=`<tr><td>Sep 20, 2026</td><td><a href="${base}sep-2026/example-drhp_101.html" title="Example Limited - Addendum to DRHP">Example Limited - Addendum to DRHP</a></td></tr>`;
assert.equal(parseDrhpRows(badTitle).length,0,'amendment title beats a misleading URL suffix');
function page(n,year=2026,total=50){
 const rows=Array.from({length:25},(_,i)=>`<tr><td>Jun 18, ${year}</td><td><a href="${base}jun-${year}/example-${i}-drhp_${n*100+i}.html" title="Example ${n}-${i} Limited - DRHP">Example ${n}-${i} Limited - DRHP</a></td></tr>`).join('');
 return `<input name='nextValue' value='${n}'><p>${(n-1)*25+1} to ${n*25} of ${total} records</p><table>${rows}</table>`;
}
const response=(url,text)=>({url,ok:true,status:200,headers:new Headers({'content-type':'text/html'}),arrayBuffer:async()=>Buffer.from(text)});
const out=fs.mkdtempSync(path.join(os.tmpdir(),'drhp-integrity-'));
let calls=0;
const data=await collectDrhpYear({fetchImpl:async(url,opts)=>{calls++;if(calls===2)assert.equal(opts.body.get('doDirect'),'1');return response(url,page(calls,calls===1?2026:2025));},clock:()=>fresh.generated_at,retainSources:out,supplementalSources:false});
assert.equal(data.companies.length,25);assert.equal(data.coverage.filing_records,25);assert.equal(data.coverage.pages_fetched,2);assert.equal(fs.readdirSync(out).length,2);validateDrhpData(data);
let repeat=0;await assert.rejects(()=>collectDrhpYear({fetchImpl:async url=>response(url,page(++repeat===1?1:1)),clock:()=>fresh.generated_at,supplementalSources:false}),/did_not_advance/);
let malformed=0;await assert.rejects(()=>collectDrhpYear({fetchImpl:async url=>response(url,++malformed===1?page(1):'<h1>Access denied</h1>'),clock:()=>fresh.generated_at,supplementalSources:false}),/pagination/);
await assert.rejects(()=>collectDrhpYear({fetchImpl:async()=>response('https://evil.test',page(1)),clock:()=>fresh.generated_at,supplementalSources:false}),/response/);
fs.rmSync(out,{recursive:true});
console.log(JSON.stringify({drhp_integrity_tests:{non_destructive_merge:true,unique_counts:true,source_drift_label:true,stale_and_conflicting_data_rejected:true,pagination_and_raw_retention:true,official_host_guards:true,lead_manager_url_guards:true,legacy_axis_mirror_corrections:true,superseded_axis_identity_removed:true}}));
