import assert from "node:assert/strict";
import fs from "node:fs";
import {NORMAL_IPO_LIFECYCLE_STATUSES,buildIpoLifecycleIndex,buildPreIpoView,canonicalLifecycleIssuer,mergeOfficialDraftSources} from "../assets/drhp-lifecycle.js";

assert.deepEqual(NORMAL_IPO_LIFECYCLE_STATUSES,["upcoming","open","closed","listed"]);
assert.equal(canonicalLifecycleIssuer("Example & Co. Ltd."),"example and co");
assert.equal(canonicalLifecycleIssuer("Example and Co Limited"),"example and co");

const syntheticSebi={companies:[
 {issuer_name:"Shared Draft Limited",filings:[{issuer_name:"Shared Draft Limited",filing_type:"DRHP",filing_date:"2026-09-01",filing_url:"https://www.sebi.gov.in/filings/public-issues/sep-2026/shared_1.html"}]},
 {issuer_name:"Listed Draft Limited",filings:[{issuer_name:"Listed Draft Limited",filing_type:"DRHP",filing_date:"2026-08-01",filing_url:"https://www.sebi.gov.in/filings/public-issues/aug-2026/listed_1.html"}]}
]};
const syntheticNse={companies:[
 {issuer_name:"Shared Draft Limited",board_hints:["Mainboard"],isins:[],symbols:[],latest_processing_status:"Under Process",filings:[{issuer_name:"Shared Draft Limited",board:"Mainboard",filing_type:"DRHP",filing_date:"2026-09-01",filing_url:"https://nsearchives.nseindia.com/corporate/shared.zip",processing_status:"Under Process",issue_open_date:null,issue_close_date:null}]},
 {issuer_name:"Abakkus Asset Manager Limited",board_hints:["Mainboard"],isins:[],symbols:[],latest_processing_status:"Under Process",filings:[{issuer_name:"Abakkus Asset Manager Limited",board:"Mainboard",filing_type:"DRHP",filing_date:"2026-09-22",filing_url:"https://nsearchives.nseindia.com/corporate/abakkus.zip",processing_status:"Under Process",issue_open_date:null,issue_close_date:null}]},
 {issuer_name:"Dated Transition Limited",board_hints:["Mainboard"],isins:[],symbols:[],filings:[{issuer_name:"Dated Transition Limited",board:"Mainboard",filing_type:"DRHP",filing_date:"2026-09-10",filing_url:"https://nsearchives.nseindia.com/corporate/dated.zip",issue_open_date:"2026-10-01",issue_close_date:"2026-10-05"}]}
]};
const syntheticIpos={records:[{id:"listed-draft",issuer_name:"Listed Draft Limited",status:"listed"}]};
const before=JSON.stringify([syntheticSebi,syntheticNse,syntheticIpos]);
const mergedSynthetic=mergeOfficialDraftSources(syntheticSebi,syntheticNse);
const shared=mergedSynthetic.companies.find(c=>c.issuer_name==="Shared Draft Limited");
assert.equal(shared.filing_count,1);assert.deepEqual(shared.source_authorities,["NSE","SEBI"]);assert.equal(shared.latest_filing_url,"https://www.sebi.gov.in/filings/public-issues/sep-2026/shared_1.html");
const syntheticView=buildPreIpoView(mergedSynthetic,syntheticIpos);
assert.deepEqual(syntheticView.companies.map(c=>c.issuer_name).sort(),["Abakkus Asset Manager Limited","Shared Draft Limited"]);
assert.equal(syntheticView.transitioned.length,2);assert.equal(syntheticView.lifecycle_gaps.length,1);
assert.equal(JSON.stringify([syntheticSebi,syntheticNse,syntheticIpos]),before,"reconciliation must be read-only");

const sebi=JSON.parse(fs.readFileSync("data/drhp-filings.json","utf8"));
const nse=JSON.parse(fs.readFileSync("data/nse-drhp-filings.json","utf8"));
const ipos=JSON.parse(fs.readFileSync("data/ipos.json","utf8"));
const merged=mergeOfficialDraftSources(sebi,nse),view=buildPreIpoView(merged,ipos),index=buildIpoLifecycleIndex(ipos);
assert.equal(view.counts.pre_ipo_companies+view.counts.transitioned_companies,view.counts.source_companies);
assert.ok(view.counts.pre_ipo_companies>0);assert.ok(view.counts.transitioned_companies>0);
const abakkusNse=nse.companies.find(c=>/\babakkus\b/i.test(c.issuer_name));assert.ok(abakkusNse,"official NSE draft source must retain Abakkus");
assert.equal(abakkusNse.latest_filing_date,"2026-09-22");assert.equal(abakkusNse.latest_processing_status,"Under Process");
assert.ok(abakkusNse.filings.every(f=>!f.issue_open_date&&!f.issue_close_date));
const abakkus=view.companies.find(c=>/\babakkus\b/i.test(c.issuer_name));assert.ok(abakkus,"Abakkus must be visible in DRHP Filed / Pre-IPO until it enters the normal IPO lifecycle");
assert.equal(abakkus.lifecycle_stage,"drhp_filed_pre_ipo");assert.ok(abakkus.source_authorities.includes("NSE"));
for(const c of view.companies){
  assert.equal((index.get("name:"+canonicalLifecycleIssuer(c.issuer_name))||[]).length,0,"visible pre-IPO company must not have a normal lifecycle name match");
  assert.ok((c.filings||[]).every(f=>!f.issue_open_date&&!f.issue_close_date),"visible pre-IPO company must not have official issue dates");
}
console.log(JSON.stringify({drhp_lifecycle_tests:{source_companies:view.counts.source_companies,pre_ipo_companies:view.counts.pre_ipo_companies,transitioned_companies:view.counts.transitioned_companies,lifecycle_gaps:view.counts.lifecycle_gaps,pre_ipo_filings:view.counts.pre_ipo_filings,abakkus_visible:true,dual_source:true}}));
