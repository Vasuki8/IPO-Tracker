'use strict';
// Inspect real generated profiles and quick views. No response interception.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {chromium} = require('playwright');

async function main() {
  const root = path.resolve(__dirname, '..');
  const base = new URL(process.env.BASE_URL || 'http://127.0.0.1:8000/');
  const out = path.resolve(process.env.SMOKE_ARTIFACT_DIR || 'artifacts/frontend');
  await fs.mkdir(out, {recursive:true});
  const retained = JSON.parse(await fs.readFile(path.join(root,'tests/public_intermediary_reviews_retained.json'),'utf8')).ipos;
  // Read source records in the test process only, never in the browser.
  const canonical = JSON.parse(await fs.readFile(path.join(root,'data/ipos.json'),'utf8')).ipos;
  const fields = {snehaa:['leadManagers'], sacheerome:['leadManagers','registrar']};
  const browser = await chromium.launch({headless:true,
    ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH} : {}),
    args: process.env.PLAYWRIGHT_CHROMIUM_ARGS ? JSON.parse(process.env.PLAYWRIGHT_CHROMIUM_ARGS) : []});
  const page = await browser.newPage({viewport:{width:1440,height:900}, reducedMotion:'reduce'});
  page.setDefaultTimeout(15000);
  const errors=[], canonicalRequests=[], results=[];
  page.on('pageerror',e=>errors.push(String(e)));
  page.on('request',r=>{if(new URL(r.url()).pathname.endsWith('/data/ipos.json'))canonicalRequests.push(r.url());});
  try {
    for (const fixture of retained) {
      const raw=canonical.find(r=>r.id===fixture.id);
      assert.ok(raw, 'Retained issuer is still in the release inventory');
      const active=fields[fixture.id].filter(f=>JSON.stringify(raw[f])===JSON.stringify(fixture[f]) &&
        raw.staticFieldProvenance?.[f]?.sha256===fixture.staticFieldProvenance[f].sha256 &&
        ['company','symbol','openDate'].every(k=>raw[k]===fixture[k]));
      const bad=fields[fixture.id].flatMap(f=>Array.isArray(fixture[f])?fixture[f]:[fixture[f]]);
      for (const width of [1440,390,320]) {
        await page.setViewportSize({width,height:900});
        await page.goto(new URL(raw.profilePath,base).href,{waitUntil:'networkidle'});
        const profile=page.locator('#companyPage .company-profile'); await profile.waitFor();
        const payload=JSON.parse(await page.locator('#ipo-profile-data').textContent()).ipo;
        for (const field of active) {
          assert.ok(payload[field]==null || payload[field].length===0);
          const decision=payload.publicQuality.fields[field];
          assert.equal(decision.state,'under_review');
          assert.equal(payload.publicQuality.sources[decision.source].sha256,fixture.staticFieldProvenance[field].sha256);
          assert.match(await profile.locator(`[data-quality-field="${field}"]`).first().textContent(),/Under review/);
        }
        for(const value of bad) assert.ok(!(await profile.innerText()).includes(value),`${fixture.id}: unsupported role leaked`);
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
        await page.screenshot({path:path.join(out,`source-holds-${fixture.id}-${width}.png`),fullPage:true});
        await page.goto(new URL('?q='+encodeURIComponent(fixture.company),base).href,{waitUntil:'networkidle'});
        await page.locator('#freshness.loaded').waitFor();
        await page.locator(`#ipoRows tr[data-id="${fixture.id}"] [data-action="preview"]`).click();
        const modal=page.locator('#detailDialog[open] .company-profile'); await modal.waitFor();
        for (const field of active) assert.match(await modal.locator(`[data-quality-field="${field}"]`).first().textContent(),/Under review/);
        for (const value of bad) assert.ok(!(await modal.innerText()).includes(value));
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
        await page.keyboard.press('Escape');
        results.push({id:fixture.id,width,activeFieldsChecked:active,profileAndQuickView:'passed'});
      }
    }
    assert.deepEqual(errors,[]); assert.deepEqual(canonicalRequests,[]);
    await fs.writeFile(path.join(out,'source-holds.json'),JSON.stringify({status:'passed',baseUrl:base.href,results,errors,canonicalRequests},null,2));
    console.log('PASS source holds: profiles and quick views at 1440/390/320px');
  } finally { await browser.close(); }
}
main().catch(e=>{console.error(e);process.exitCode=1;});
