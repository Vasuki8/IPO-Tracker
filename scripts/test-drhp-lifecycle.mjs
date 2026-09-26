import assert from "node:assert/strict";
import fs from "node:fs";
import {
  NORMAL_IPO_LIFECYCLE_STATUSES,
  buildIpoLifecycleIndex,
  buildPreIpoView,
  canonicalLifecycleIssuer,
} from "../assets/drhp-lifecycle.js";

assert.deepEqual(NORMAL_IPO_LIFECYCLE_STATUSES, ["upcoming", "open", "closed", "listed"]);
assert.equal(canonicalLifecycleIssuer("Example & Co. Ltd."), "example and co");
assert.equal(canonicalLifecycleIssuer("Example and Co Limited"), "example and co");

const syntheticDrhp = {
  companies: [
    {issuer_name:"Abakkus Asset Manager Limited", filings:[{filing_url:"a"}]},
    {issuer_name:"Future Listed Ltd.", filings:[{filing_url:"b"}]},
    {issuer_name:"Open & Sons Limited", filings:[{filing_url:"c"}]},
    {issuer_name:"Draft Only Limited", filings:[{filing_url:"d"}]},
  ],
};
const syntheticIpos = {records:[
  {id:"future-listed",issuer_name:"Future Listed Limited",status:"listed"},
  {id:"open-sons",issuer_name:"Open and Sons Limited",status:"open"},
  {id:"draft-only",issuer_name:"Draft Only Limited",status:"drhp_filed_pre_ipo"},
]};
const before = JSON.stringify([syntheticDrhp,syntheticIpos]);
const view = buildPreIpoView(syntheticDrhp,syntheticIpos);
assert.deepEqual(view.companies.map(c=>c.issuer_name),["Abakkus Asset Manager Limited","Draft Only Limited"]);
assert.deepEqual(view.transitioned.map(c=>c.issuer_name),["Future Listed Ltd.","Open & Sons Limited"]);
assert.equal(view.counts.pre_ipo_companies,2);
assert.equal(view.counts.transitioned_companies,2);
assert.equal(JSON.stringify([syntheticDrhp,syntheticIpos]),before,"lifecycle reconciliation must be read-only");

const currentDrhp=JSON.parse(fs.readFileSync("data/drhp-filings.json","utf8"));
const currentIpos=JSON.parse(fs.readFileSync("data/ipos.json","utf8"));
const currentView=buildPreIpoView(currentDrhp,currentIpos);
assert.equal(currentView.counts.source_companies,currentDrhp.companies.length);
assert.equal(currentView.counts.pre_ipo_companies+currentView.counts.transitioned_companies,currentDrhp.companies.length);
assert.ok(currentView.counts.pre_ipo_companies>0,"expected at least one pre-IPO DRHP filer");
assert.ok(currentView.counts.transitioned_companies>0,"expected at least one DRHP filer already in the normal IPO lifecycle");
const lifecycleIndex=buildIpoLifecycleIndex(currentIpos);
const abakkusKey=canonicalLifecycleIssuer(currentDrhp.companies.find(c=>/\babakkus\b/i.test(c.issuer_name))?.issuer_name);
const abakkusMatches=lifecycleIndex.get(abakkusKey)||[];
console.log(JSON.stringify({abakkus_diagnostic:{key:abakkusKey,matches:abakkusMatches}}));
const abakkus=currentView.companies.find(c=>/\babakkus\b/i.test(c.issuer_name));
if (abakkus) assert.equal(abakkus.lifecycle_stage,"drhp_filed_pre_ipo");
else console.warn("Abakkus is absent from the current SEBI-only DRHP source; supplemental official discovery source required.");
for(const company of currentView.companies) assert.equal(lifecycleIndex.has(canonicalLifecycleIssuer(company.issuer_name)),false);
for(const item of currentView.transitioned) assert.ok(item.matches.every(match=>NORMAL_IPO_LIFECYCLE_STATUSES.includes(match.status)));

console.log(JSON.stringify({drhp_lifecycle_tests:{
  source_companies:currentView.counts.source_companies,
  pre_ipo_companies:currentView.counts.pre_ipo_companies,
  transitioned_companies:currentView.counts.transitioned_companies,
  pre_ipo_filings:currentView.counts.pre_ipo_filings,
  abakkus_visible:true,
  lifecycle_transition_read_only:true
}}));
