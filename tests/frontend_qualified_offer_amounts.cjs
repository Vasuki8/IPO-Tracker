'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {chromium} = require('playwright');
const expected = {
  axiomgas: {company:'Axiom Gas Engineering Limited', floor:47.9298, cap:50.7492, low:51, high:54,
    source:'https://axiomgas.com/uploads/investors/PB_AP_RHP_MERGED.pdf', qualifier:/Basis of Allotment/},
  varmora: {company:'Varmora Granito Limited', floor:687.047, cap:708.021, low:140, high:148,
    source:'https://www.jmfl.com/Common/getFile/6031', qualifier:/Up to/},
};
async function main() {
  const base = new URL(process.env.BASE_URL || 'http://127.0.0.1:8017/');
  const out = path.resolve(process.env.SMOKE_ARTIFACT_DIR || 'artifacts/frontend/qualified-amounts');
  await fs.mkdir(out,{recursive:true});
  const browser = await chromium.launch({headless:true,
    ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH} : {})});
  const page = await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'});
  await page.clock.install({time:new Date('2026-09-19T14:00:00Z')});
  page.setDefaultTimeout(15000);
  const errors=[],canonicalRequests=[],results=[];
  page.on('pageerror',error=>errors.push(String(error)));
  page.on('request',request=>{if(new URL(request.url()).pathname.endsWith('/data/ipos.json'))canonicalRequests.push(request.url());});
  try {
    const summary=await (await fetch(new URL('data/ipos-summary.json',base))).json();
    assert.ok(!summary.ipos.find(r=>r.id==='poojalogis').issueAmountScenarios);
    for(const [id,want] of Object.entries(expected)) {
      const brief=summary.ipos.find(r=>r.id===id), pair=brief.issueAmountScenarios;
      assert.equal(pair.atFloorCr,want.floor);assert.equal(pair.atCapCr,want.cap);assert.ok(brief.issueSizeCr==null);
      for(const width of [1440,375,320]) {
        await page.setViewportSize({width,height:900});
        await page.goto(new URL(`ipo/${id}/`,base).href,{waitUntil:'networkidle'});
        await page.locator('#companyPage .company-profile').waitFor();
        const record=JSON.parse(await page.locator('#ipo-profile-data').textContent()).ipo;
        assert.deepEqual(record.issueAmountScenarios,pair);assert.ok(record.issueSizeCr==null);
        const decision=record.publicQuality.fields.issueAmountScenarios;
        const source=record.publicQuality.sources[decision.source];
        assert.equal(source.sourceUrl,want.source);assert.equal(source.authority,'issuer_disclosure');
        assert.equal(decision.page,1);assert.equal(decision.unit,'INR crore');assert.ok(source.observedAt==null);
        const card=page.locator('.company-kpi').filter({has:page.locator('[data-quality-field="issueAmountScenarios"]')});
        const text=await card.innerText();
        for(const value of [want.floor,want.cap])assert.ok(text.includes(String(value)),text);
        assert.match(text,/floor/);assert.match(text,/cap/);assert.match(text,want.qualifier);
        assert.match(text,/Provisional disclosure/);assert.doesNotMatch(text,/726\.31/);
        const note=card.locator('[data-quality-field="issueAmountScenarios"]');
        assert.match(await note.getAttribute('title'),/Source time unavailable; collected/);
        assert.equal(await note.locator('a').getAttribute('href'),want.source+'#page=1');
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
        await page.screenshot({path:path.join(out,`${id}-${width}.png`),fullPage:true});
        await page.goto(new URL('?q='+encodeURIComponent(want.company),base).href,{waitUntil:'networkidle'});
        await page.locator('#freshness.loaded').waitFor();
        const row=page.locator(`#ipoRows tr[data-id="${id}"]`);
        assert.match(await row.innerText(),want.qualifier);
        assert.ok((await row.innerText()).includes(String(want.cap)));
        await row.locator('[data-action="preview"]').click();
        const modal=page.locator('#detailDialog[open] .company-profile');await modal.waitFor();
        assert.ok((await modal.innerText()).includes(String(want.floor)));
        assert.match(await modal.innerText(),want.qualifier);
        await page.keyboard.press('Escape');
        if(width===1440) {
          const downloaded=page.waitForEvent('download');await page.locator('#exportCsv').click();
          const csv=(await fs.readFile(await (await downloaded).path(),'utf8')).replace(/^\uFEFF/,'').split('\r\n');
          const parse=line=>[...line.matchAll(/(?:^|,)(?:"((?:[^"]|"")*)"|([^,]*))/g)].map(c=>(c[1]??c[2]).replace(/""/g,'"'));
          const headers=parse(csv[0]),values=parse(csv[1]),value=label=>values[headers.indexOf(label)];
          assert.equal(value('Issue size crore INR'),'');
          assert.equal(value('Whole-offer amount at floor INR crore (provisional)'),String(want.floor));
          assert.equal(value('Whole-offer amount at cap INR crore (provisional)'),String(want.cap));
          assert.equal(value('Floor price INR per share'),String(want.low));
          assert.equal(value('Cap price INR per share'),String(want.high));
          assert.equal(value('Conditional amount evidence state'),'provisional');
          assert.equal(value('Conditional amount source URL'),want.source);
          assert.match(value('Conditional amount qualification'),want.qualifier);
          await row.locator('[data-action="compare"]').click();
          const other=id==='axiomgas'?'varmora':'axiomgas';
          await page.locator('#search').fill(expected[other].company);
          await page.locator(`#ipoRows tr[data-id="${other}"] [data-action="compare"]`).click();
          await page.locator('#openCompare').click();
          const comparison=page.locator('#compareBody');
          assert.equal(await comparison.locator('[data-quality-field="issueAmountScenarios"]').count(),2);
          assert.match(await comparison.innerText(),/Basis of Allotment/);assert.match(await comparison.innerText(),/Up to/);
          assert.doesNotMatch(await comparison.innerText(),/726\.31/);
          await page.keyboard.press('Escape');
        }
        results.push({id,width,directoryProfileQuickView:'passed'});
      }
    }
    const expired=await page.evaluate(()=>{
      const row={issueAmountScenarios:{atFloorCr:47.9298,atCapCr:50.7492},publicQuality:{version:1,sources:[],
        fields:{issueAmountScenarios:{state:'provisional',until:'2026-09-22'}}}};
      return IPOQuality.sanitize(row,new Date('2026-09-22T18:30:00Z')).issueAmountScenarios;
    });
    assert.equal(expired,null);assert.deepEqual(errors,[]);assert.deepEqual(canonicalRequests,[]);
    await fs.writeFile(path.join(out,'qualified-amount-browser.json'),JSON.stringify({status:'passed',baseUrl:base.href,results,
      checks:['conditional source amounts','distinct document source','original scalar null','CSV','comparison','IST expiry','Pooja unresolved'],errors,canonicalRequests},null,2));
    console.log('PASS two reviewed conditional amount documents across desktop/mobile, directory, profiles, quick views, comparison, CSV and expiry');
  } finally {await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
