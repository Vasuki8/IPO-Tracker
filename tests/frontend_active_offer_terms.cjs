'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {chromium} = require('playwright');

const expected = {
  axiomgas: {company:'Axiom Gas Engineering Limited', price:{min:51,max:54}, lot:2000, fresh:9398000, until:'2026-09-22'},
  varmora: {company:'Varmora Granito Limited', price:{min:140,max:148}, lot:101, fresh:null, until:'2026-09-24'},
  poojalogis: {company:'Pooja Logistics Limited', price:{min:109,max:115}, lot:1200, fresh:3846000, until:'2026-09-25'},
};
async function main() {
  const base = new URL(process.env.BASE_URL || 'http://127.0.0.1:8005/');
  const out = path.resolve(process.env.SMOKE_ARTIFACT_DIR || 'artifacts/frontend/active-offer');
  await fs.mkdir(out,{recursive:true});
  const browser = await chromium.launch({headless:true,
    ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH} : {}),
    args:process.env.PLAYWRIGHT_CHROMIUM_ARGS ? JSON.parse(process.env.PLAYWRIGHT_CHROMIUM_ARGS) : []});
  const page = await browser.newPage({viewport:{width:1440,height:900}, reducedMotion:'reduce'});
  // Frozen source cohort; tests remain meaningful after the real issue closes.
  await page.clock.install({time:new Date('2026-09-19T03:00:00Z')});
  page.setDefaultTimeout(15000);
  const errors=[], canonicalRequests=[], results=[];
  page.on('pageerror', error=>errors.push(String(error)));
  page.on('request',request=>{if(new URL(request.url()).pathname.endsWith('/data/ipos.json')) canonicalRequests.push(request.url());});
  try {
    const summary=await (await fetch(new URL('data/ipos-summary.json',base))).json();
    for (const [id, want] of Object.entries(expected)) {
      const brief=summary.ipos.find(row=>row.id===id);
      assert.deepEqual(brief.priceBand,want.price); assert.equal(brief.lotSize,want.lot); assert.ok(brief.issueSizeCr==null);
      for (const width of [1440,375,320]) {
        await page.setViewportSize({width,height:900});
        await page.goto(new URL(`ipo/${id}/`,base).href,{waitUntil:'networkidle'});
        await page.locator('#companyPage .company-profile').waitFor();
        const record=JSON.parse(await page.locator('#ipo-profile-data').textContent()).ipo;
        assert.deepEqual(record.priceBand,want.price); assert.equal(record.lotSize,want.lot);
        assert.equal(record.issueComposition.freshShares ?? null,want.fresh);
        assert.ok(record.issueSizeCr==null && record.marketLot==null && record.minimumApplicationAmount==null);
        assert.equal(record.minimumBidQuantity ?? null,id==='varmora'?101:null);
        for (const field of ['priceBand','lotSize','issueComposition']) {
          const d=record.publicQuality.fields[field], source=record.publicQuality.sources[d.source];
          assert.equal(d.state,'provisional'); assert.equal(d.until,want.until);
          assert.ok(source.observedAt==null); assert.match(source.collectedAt,/2026-09-19/);
          assert.match(source.sha256,/^[a-f0-9]{64}$/); assert.match(source.sourceUrl,/nseindia.com\/api\/ipo-detail/);
          const note=page.locator(`[data-quality-field="${field}"]`).first();
          assert.match(await note.innerText(),/Provisional disclosure/);
          assert.match(await note.getAttribute('title'),/Source time unavailable; collected/);
        }
        const text=await page.locator('#companyPage').innerText();
        if(id==='axiomgas') assert.match(text,/Up to 93,98,000 shares/);
        if(id==='varmora') { assert.match(text,/Up to .*320/); assert.match(text,/Up to 2,62,17,634 shares/); }
        assert.doesNotMatch(text,/726\.31|44\.23/);
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
        await page.screenshot({path:path.join(out,`${id}-${width}.png`),fullPage:true});
        await page.goto(new URL('?q='+encodeURIComponent(want.company),base).href,{waitUntil:'networkidle'});
        await page.locator('#freshness.loaded').waitFor();
        const row=page.locator(`#ipoRows tr[data-id="${id}"]`);
        assert.match(await row.innerText(),/Provisional disclosure/);
        await row.locator('[data-action="preview"]').click();
        const modal=page.locator('#detailDialog[open] .company-profile'); await modal.waitFor();
        assert.match(await modal.locator('[data-quality-field="issueComposition"]').first().innerText(),/Provisional disclosure/);
        await page.keyboard.press('Escape');
        if (width===1440) {
          const downloaded=page.waitForEvent('download'); await page.locator('#exportCsv').click();
          const csv=(await fs.readFile(await (await downloaded).path(),'utf8')).replace(/^\uFEFF/,'').split('\r\n');
          const parse=line=>[...line.matchAll(/(?:^|,)(?:"((?:[^"]|"")*)"|([^,]*))/g)].map(cell=>(cell[1]??cell[2]).replace(/""/g,'"'));
          const headers=parse(csv[0]), values=parse(csv[1]), value=label=>values[headers.indexOf(label)];
          assert.equal(value('Price minimum INR'),String(want.price.min)); assert.equal(value('Price maximum INR'),String(want.price.max));
          assert.equal(value('Lot size shares'),String(want.lot)); assert.equal(value('Issue size crore INR'),'');
          assert.equal(value('Price band evidence state'),'provisional'); assert.equal(value('Lot evidence state'),'provisional');
          await row.locator('[data-action="compare"]').click();
          const otherId=id==='axiomgas'?'varmora':'axiomgas';
          await page.locator('#search').fill(expected[otherId].company);
          await page.locator(`#ipoRows tr[data-id="${otherId}"] [data-action="compare"]`).click();
          await page.locator('#openCompare').click();
          const comparison=page.locator('#compareBody');
          assert.equal(await comparison.locator('[data-quality-field="priceBand"]').count(),2);
          assert.equal(await comparison.locator('[data-quality-field="lotSize"]').count(),2);
          assert.match(await comparison.innerText(),/Provisional disclosure/);
          assert.doesNotMatch(await comparison.innerText(),/726\.31|44\.23/);
          await page.keyboard.press('Escape');
        }
        results.push({id,width,profileAndQuickView:'passed'});
      }
    }
    // Cached composition and bid terms all expire together at the IST boundary.
    const expired=await page.evaluate(()=>IPOQuality.sanitize({priceBand:{min:1,max:2},lotSize:100,
      issueComposition:{freshShares:1000,qualifiers:{freshShares:'up_to'}},publicQuality:{version:1,sources:[],
      fields:Object.fromEntries(['priceBand','lotSize','issueComposition'].map(f=>[f,{state:'provisional',until:'2026-09-22'}]))}},new Date('2026-09-22T18:30:00Z')));
    for(const field of ['priceBand','lotSize','issueComposition']) assert.equal(expired[field],null);
    assert.deepEqual(errors,[]); assert.deepEqual(canonicalRequests,[]);
    await fs.writeFile(path.join(out,'active-offer-browser.json'),JSON.stringify({status:'passed',baseUrl:base.href,results,errors,canonicalRequests},null,2));
    console.log('PASS active offers: three issuers, mobile/desktop profiles, directory, quick views, source clocks, qualifiers and expiry');
  } finally { await browser.close(); }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
