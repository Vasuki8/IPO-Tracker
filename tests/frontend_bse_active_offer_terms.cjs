'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {chromium} = require('playwright');

const expected = {
  'fx-multitech-limited': {company:'FX MULTITECH LIMITED', price:{min:110,max:116}, market:1200, minimum:2400, until:'2026-09-23'},
  'robokidz-eduventures-limited': {company:'ROBOKIDZ EDUVENTURES LIMITED', price:{min:100,max:106}, market:1200, minimum:2400, until:'2026-09-23'},
  'himalaya-nutravedics-india-limited': {company:'Himalaya Nutravedics India Limited', price:{min:100,max:106}, market:1200, minimum:2400, until:'2026-09-24'},
  's-k-offset-limited': {company:'S. K. OFFSET LIMITED', price:{min:119,max:125}, market:1000, minimum:2000, until:'2026-09-25'},
};
const fields = ['priceBand','marketLot','minimumBidQuantity'];
const parseCsv = line => [...line.matchAll(/(?:^|,)(?:"((?:[^"]|"")*)"|([^,]*))/g)].map(cell=>(cell[1]??cell[2]).replace(/""/g,'"'));

async function main() {
  const base = new URL(process.env.BASE_URL || 'http://127.0.0.1:8006/');
  const out = path.resolve(process.env.SMOKE_ARTIFACT_DIR || 'artifacts/frontend/bse-active-offer');
  await fs.mkdir(out,{recursive:true});
  const browser = await chromium.launch({headless:true,
    ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH} : {}),
    args:process.env.PLAYWRIGHT_CHROMIUM_ARGS ? JSON.parse(process.env.PLAYWRIGHT_CHROMIUM_ARGS) : []});
  const page = await browser.newPage({viewport:{width:1440,height:900}, reducedMotion:'reduce'});
  await page.clock.install({time:new Date('2026-09-19T06:00:00Z')});
  page.setDefaultTimeout(15000);
  const errors=[], unexpectedRequests=[], results=[];
  page.on('pageerror', error=>errors.push(String(error)));
  page.on('request',request=>{
    const url=new URL(request.url());
    if(url.pathname.endsWith('/data/ipos.json') || url.origin!==base.origin) unexpectedRequests.push(request.url());
  });
  try {
    const summary=await (await fetch(new URL('data/ipos-summary.json',base))).json();
    for (const [id,want] of Object.entries(expected)) {
      const brief=summary.ipos.find(row=>row.id===id);
      assert.deepEqual(brief.priceBand,want.price);
      assert.equal(brief.marketLot,want.market); assert.equal(brief.minimumBidQuantity,want.minimum);
      assert.ok(brief.lotSize==null && brief.issueSizeCr==null && brief.symbol==null);
      for (const width of [1440,375,320]) {
        await page.setViewportSize({width,height:900});
        await page.goto(new URL(`ipo/${id}/`,base).href,{waitUntil:'networkidle'});
        await page.locator('#companyPage .company-profile').waitFor();
        const record=JSON.parse(await page.locator('#ipo-profile-data').textContent()).ipo;
        assert.deepEqual(record.priceBand,want.price);
        assert.equal(record.marketLot,want.market); assert.equal(record.minimumBidQuantity,want.minimum);
        assert.ok(record.lotSize==null && record.issueSizeCr==null && record.symbol==null);
        assert.ok(record.minimumApplicationAmount==null && record.issueComposition==null);
        for(const field of fields) {
          const d=record.publicQuality.fields[field], source=record.publicQuality.sources[d.source];
          assert.equal(d.state,'provisional'); assert.equal(d.until,want.until);
          assert.ok(source.observedAt==null); assert.match(source.collectedAt,/2026-09-19T05:33:/);
          assert.match(source.sha256,/^[a-f0-9]{64}$/);
          assert.match(source.sourceUrl,/^https:\/\/beta\.bseindia\.com\/markets\/publicIssues\/DisplayIPO\.aspx\?/);
          const note=page.locator(`[data-quality-field="${field}"]`).first();
          assert.match(await note.innerText(),/Provisional disclosure/);
          assert.match(await note.getAttribute('title'),/Source time unavailable; collected/);
        }
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
        await page.screenshot({path:path.join(out,`${id}-${width}.png`),fullPage:true});
        await page.goto(new URL('?q='+encodeURIComponent(want.company),base).href,{waitUntil:'networkidle'});
        await page.locator('#freshness.loaded').waitFor();
        const row=page.locator(`#ipoRows tr[data-id="${id}"]`);
        assert.match(await row.innerText(),/Provisional disclosure/);
        await row.locator('[data-action="preview"]').click();
        const modal=page.locator('#detailDialog[open] .company-profile'); await modal.waitFor();
        for(const field of fields) assert.match(await modal.locator(`[data-quality-field="${field}"]`).first().innerText(),/Provisional disclosure/);
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
        await page.keyboard.press('Escape');
        if(width===1440) {
          const downloaded=page.waitForEvent('download'); await page.locator('#exportCsv').click();
          const csv=(await fs.readFile(await (await downloaded).path(),'utf8')).replace(/^\uFEFF/,'').split('\r\n');
          const headers=parseCsv(csv[0]), values=parseCsv(csv[1]), value=label=>{
            assert.ok(headers.includes(label),'Missing CSV column: '+label); return values[headers.indexOf(label)];
          };
          assert.equal(value('Price minimum INR'),String(want.price.min)); assert.equal(value('Price maximum INR'),String(want.price.max));
          assert.equal(value('Market lot shares'),String(want.market)); assert.equal(value('Minimum bid quantity shares'),String(want.minimum));
          for(const label of ['Lot size shares','Issue size crore INR','One lot at cap INR']) assert.equal(value(label),'');
          for(const label of ['Price band evidence state','Market lot evidence state','Minimum bid quantity evidence state']) assert.equal(value(label),'provisional');
          const source=record.publicQuality.sources[record.publicQuality.fields.marketLot.source].sourceUrl;
          assert.equal(value('Market lot source URL'),source); assert.equal(value('Minimum bid quantity source URL'),source);
          await row.locator('[data-action="compare"]').click();
          const otherId=id==='fx-multitech-limited'?'s-k-offset-limited':'fx-multitech-limited';
          await page.locator('#search').fill(expected[otherId].company);
          await page.locator(`#ipoRows tr[data-id="${otherId}"] [data-action="compare"]`).click();
          await page.locator('#openCompare').click();
          const comparison=page.locator('#compareBody');
          for(const field of fields) assert.equal(await comparison.locator(`[data-quality-field="${field}"]`).count(),2);
          assert.match(await comparison.innerText(),/Market lot/); assert.match(await comparison.innerText(),/Minimum bid quantity/);
          assert.match(await comparison.innerText(),/Provisional disclosure/);
          await page.keyboard.press('Escape');
        }
        results.push({id,width,profileAndQuickView:'passed'});
      }
    }
    const vive=summary.ipos.find(row=>row.id==='vivekanand-cotspin-limited');
    for(const field of fields) assert.ok(vive[field]==null);
    await page.goto(new URL(vive.profilePath,base).href,{waitUntil:'networkidle'});
    const rejected=JSON.parse(await page.locator('#ipo-profile-data').textContent()).ipo;
    for(const field of fields) assert.ok(rejected[field]==null);
    const expired=await page.evaluate(()=>IPOQuality.sanitize({priceBand:{min:110,max:116},marketLot:1200,minimumBidQuantity:2400,
      publicQuality:{version:1,sources:[],fields:Object.fromEntries(['priceBand','marketLot','minimumBidQuantity'].map(f=>[f,{state:'provisional',until:'2026-09-23'}]))}},new Date('2026-09-23T18:30:00Z')));
    for(const field of fields) assert.equal(expired[field],null);
    assert.deepEqual(errors,[]); assert.deepEqual(unexpectedRequests,[]);
    await fs.writeFile(path.join(out,'bse-active-offer-browser.json'),JSON.stringify({status:'passed',baseUrl:base.href,results,errors,unexpectedRequests},null,2));
    console.log('PASS BSE active offers: four issuers, separate quantities, mobile/desktop, source clocks, CSV, comparisons, unresolved fifth issuer and expiry');
  } finally { await browser.close(); }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
