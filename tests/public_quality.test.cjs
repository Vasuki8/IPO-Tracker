'use strict';
const assert = require('node:assert/strict');
const test = require('node:test');
const Q = require('../public-quality.js');
const contract = (fields) => ({version:1,fields,sources:[]});

test('legacy values and returns cannot escape through compatibility records', () => {
  const raw = {priceBand:{min:1,max:2},lotSize:100,issueSizeCr:9,listing:{issuePrice:10,gainPct:90}};
  const out = Q.sanitize(raw);
  assert.equal(out.priceBand,null); assert.equal(out.issueSizeCr,null);
  assert.equal(out.listing.issuePrice,undefined); assert.equal(out.listing.gainPct,undefined);
  assert.equal(raw.listing.gainPct,90); assert.equal(raw.lotSize,100);
});
test('provisional expiry uses IST and is re-evaluated for cached records', () => {
  const raw = {priceBand:{min:100,max:110},publicQuality:contract({priceBand:{state:'provisional',until:'2026-09-17'}})};
  assert.equal(Q.sanitize(raw,new Date('2026-09-17T18:29:59Z')).priceBand.max,110);
  assert.equal(Q.sanitize(raw,new Date('2026-09-17T18:30:00Z')).priceBand,null);
  assert.equal(raw.priceBand.max,110);
  raw.publicQuality.fields.priceBand.until='tomorrow';
  assert.equal(Q.sanitize(raw).priceBand,null);
});
test('field-specific states retain zero and block disputed dependent values', () => {
  const raw = {issueSizeCr:120,subscription:{total:0},listing:{issuePrice:50,gainPct:10},
    publicQuality:contract({issueSizeCr:{state:'under_review'},subscription:{state:'reported'},'listing.issuePrice':{state:'under_review'},listing:{state:'reported'}})};
  const out = Q.sanitize(raw); assert.equal(out.issueSizeCr,null);
  assert.equal(out.subscription.total,0); assert.equal(out.listing.gainPct,undefined);
});
test('a newer collection or history row never replaces accepted subscription values or source time', () => {
  const raw={subscription:{total:2},subscriptionObservedAt:'2026-09-17T20:18:25+05:30',
    subscriptionCollectedAt:'2026-09-17T23:14:02+05:30',subscriptionSource:'Example (secondary)',
    subscriptionHistory:[{total:999,capturedAt:'2026-09-18T10:00:00+05:30'}]};
  const snap=Q.snapshot(raw); assert.equal(snap.total,2);assert.equal(snap.observedAt,raw.subscriptionObservedAt);
  assert.equal(snap.collectedAt,raw.subscriptionCollectedAt);assert.equal(snap.authority,'Secondary source');
  const text=Q.freshness(snap);assert.match(text,/Source reported at/);assert.match(text,/Checked at/);
  raw.subscriptionTimeBasis='collection-only';assert.equal(Q.snapshot(raw).observedAt,null);
  assert.match(Q.freshness(Q.snapshot(raw)),/Source time unavailable/);
});
test('source links and authority resist malformed URLs and unofficial host lookalikes', () => {
  const raw={publicQuality:{version:1,fields:{lotSize:{state:'final_verified',source:0}},sources:[{sourceUrl:'javascript:alert(1)'}]}};
  assert.doesNotMatch(Q.note(raw,'lotSize'), /href=/);
  raw.publicQuality.sources[0].sourceUrl='https://example.com/" onmouseover="bad';
  assert.doesNotMatch(Q.note(raw,'lotSize'), /" onmouseover=/);
  assert.equal(Q.sourceAuthority('NSE','https://nseindia.com.fake.test'), 'Source authority unverified');
  assert.equal(Q.sourceAuthority('NSE','https://www.nseindia.com/'), 'Official exchange');
});
test('new or malformed contract versions fail closed without an aggregate verification badge', () => {
  const raw={lotSize:100,publicQuality:{version:999,fields:{lotSize:{state:'final_verified'}}}};
  assert.equal(Q.sanitize(raw).lotSize,null);
  assert.doesNotMatch(Q.overview(raw),/>verified</i);
});

test('shared profile renders timeline and withheld fields without requiring browser navigation', () => {
  const fs = require('node:fs');
  const vm = require('node:vm');
  const path = require('node:path');
  const context = vm.createContext({
    console, URL, Intl, Date, Set, WeakSet, WeakMap, IPOQuality:Q,
    document:{addEventListener(){},baseURI:'https://example.test/IPO-Tracker/'},
    window:{addEventListener(){}},localStorage:{getItem(){return '[]';}},
  });
  for (const file of ['company-page.js','company.js'])
    vm.runInContext(fs.readFileSync(path.join(__dirname,'..',file),'utf8'), context, {filename:file});
  context.fixture = {id:'test',company:'Test issuer',openDate:'2026-01-01',closeDate:'2026-01-05',
    issueSizeCr:12345,publicQuality:contract({issueSizeCr:{state:'under_review'},
      openDate:{state:'reported'},closeDate:{state:'reported'},financials:{state:'under_review'}})};
  const html=vm.runInContext('companyProfileHtml(fixture, {standalone:true})',context);
  assert.match(html,/company-timeline/);assert.match(html,/Under review/);
  assert.doesNotMatch(html,/12,345/);assert.match(html,/Test issuer/);
});
