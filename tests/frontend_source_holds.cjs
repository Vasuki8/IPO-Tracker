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
    const vinodFixture=JSON.parse(await fs.readFile(path.join(root,'tests/vinod_shareholding_retained.json'),'utf8')).ipos[0];
    const vinod=canonical.find(r=>r.id===vinodFixture.id);
    assert.ok(vinod, 'Reviewed Vinod identity remains in the inventory');
    const vinodActive=JSON.stringify(vinod.shareholding)===JSON.stringify(vinodFixture.shareholding) &&
      vinod.staticFieldProvenance?.shareholding?.sha256===vinodFixture.staticFieldProvenance.shareholding.sha256 &&
      ['company','symbol','openDate'].every(k=>vinod[k]===vinodFixture[k]);
    if(vinodActive) {
      for(const width of [1440,390,320]) {
        await page.setViewportSize({width,height:900});
        await page.goto(new URL(vinod.profilePath,base).href,{waitUntil:'networkidle'});
        const profile=page.locator('#companyPage .company-profile');await profile.waitFor();
        const payload=JSON.parse(await page.locator('#ipo-profile-data').textContent()).ipo;
        assert.ok(payload.shareholding==null);
        assert.equal(payload.publicQuality.fields.shareholding.reason,'pending_source_repair');
        assert.match(await profile.locator('[data-quality-field="shareholding"]').first().innerText(),/Under review/);
        assert.ok(!(await profile.innerText()).includes('93.11'));
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
        await page.screenshot({path:path.join(out,`vinod-hold-${width}.png`),fullPage:true});
        await page.goto(new URL('?q='+encodeURIComponent(vinod.company),base).href,{waitUntil:'networkidle'});
        await page.locator('#freshness.loaded').waitFor();
        const row=page.locator('#ipoRows tr[data-id="vinod"]');
        assert.ok(!(await row.innerText()).includes('93.11'));
        await row.locator('[data-action="preview"]').click();
        const modal=page.locator('#detailDialog[open] .company-profile');await modal.waitFor();
        assert.match(await modal.locator('[data-quality-field="shareholding"]').first().innerText(),/Under review/);
        assert.ok(!(await modal.innerText()).includes('93.11'));
        await page.keyboard.press('Escape');
      }
      const pendingDownload=page.waitForEvent('download');await page.locator('#exportCsv').click();
      const download=await pendingDownload;
      assert.ok(!(await fs.readFile(await download.path(),'utf8')).includes('93.11'));
      results.push({id:'vinod',shareholdingHold:'profile, quick view, directory and CSV passed',widths:[1440,390,320]});
    } else results.push({id:'vinod',shareholdingHold:'different source/value; not declared resolved'});
    // Independently expected active market snapshots, from retained issuer and
    // source fields. Only collection-clock changes are non-resolving rechecks.
    const market = JSON.parse(await fs.readFile(path.join(root,'tests/subscription_reviews_retained.json'),'utf8')).ipos;
    let responsiveMarketChecked=false;
    for (const fixture of market) {
      const raw=canonical.find(r=>r.id===fixture.id);
      const compared=Object.keys(fixture).filter(k=>k!=='status' && k!=='subscriptionHistory' && k!=='subscriptionAsOf' && k!=='subscriptionCollectedAt');
      if(!raw || !compared.every(k=>JSON.stringify(raw[k])===JSON.stringify(fixture[k]))) {
        results.push({id:fixture.id,marketHold:'different snapshot; not declared resolved'}); continue;
      }
      const responsive=!responsiveMarketChecked;
      for(const width of responsive ? [1440,375,320] : [375]) {
        await page.setViewportSize({width,height:900});
        await page.goto(new URL(raw.profilePath,base).href,{waitUntil:'networkidle'});
        await page.locator('#companyPage .company-profile').waitFor();
        const payload=JSON.parse(await page.locator('#ipo-profile-data').textContent()).ipo;
        assert.ok(!payload.subscription);assert.ok(!payload.subscriptionHistory?.length);
        assert.equal(payload.publicQuality.fields.subscription.reason,'subscription_snapshot_conflict');
        const section=page.locator('#company-field-quality .quality-grid > div').filter({has:page.locator('[data-quality-field="subscription"]')});
        assert.match(await section.innerText(),/Under review/);
        assert.match(await section.innerText(),/source or bid-denominator/);
        assert.equal(await page.locator('#company-subscription svg, #company-subscription .subscription-card, #company-subscription table').count(),0);
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
        if(responsive)await page.screenshot({path:path.join(out,`subscription-hold-${width}.png`),fullPage:true});
      }
      await page.goto(new URL('?q='+encodeURIComponent(fixture.company),base).href,{waitUntil:'networkidle'});
      await page.locator('#freshness.loaded').waitFor();
      const row=page.locator(`#ipoRows tr[data-id="${fixture.id}"]`);
      assert.equal(await row.locator('[data-label="Subscription"] .metric').innerText(),'—');
      assert.match(await row.locator('[data-label="Subscription"]').innerText(),/Under review/);
      const pendingDownload=page.waitForEvent('download');await page.locator('#exportCsv').click();
      const download=await pendingDownload;
      const lines=(await fs.readFile(await download.path(),'utf8')).replace(/^\uFEFF/,'').split('\r\n');
      const parse=line=>[...line.matchAll(/(?:^|,)(?:"((?:[^"]|"")*)"|([^,]*))/g)].map(c=>(c[1]??c[2]).replace(/""/g,'"'));
      const headers=parse(lines[0]),values=parse(lines[1]);
      assert.equal(values[headers.indexOf('Subscription multiple')],'');
      await row.locator('[data-action="preview"]').click();
      const modal=page.locator('#detailDialog[open] #company-field-quality .quality-grid > div').filter({has:page.locator('[data-quality-field="subscription"]')});await modal.waitFor();
      assert.match(await modal.innerText(),/Under review/);
      assert.equal(await modal.locator('svg, .subscription-card, table').count(),0);
      await page.keyboard.press('Escape');
      if(responsive) {
        await row.locator('[data-action="compare"]').click();
        await page.locator('#search').fill('Teamtech');
        await page.locator('#ipoRows tr[data-id="teamtech"] [data-action="compare"]').click();
        await page.locator('#openCompare').click();
        const comparison=page.locator('#compareBody tbody tr').filter({has:page.locator('th',{hasText:/^Subscription$/})});
        assert.match(await comparison.locator('td').first().innerText(),/Under review/);
        assert.equal(await comparison.locator('td').first().locator('.metric').innerText(),'—');
        await page.keyboard.press('Escape');
      }
      responsiveMarketChecked=true;
      results.push({id:fixture.id,marketHold:'profile, quick view, directory and CSV passed',responsiveAndComparison:responsive});
    }
    assert.deepEqual(errors,[]); assert.deepEqual(canonicalRequests,[]);
    await fs.writeFile(path.join(out,'source-holds.json'),JSON.stringify({status:'passed',baseUrl:base.href,results,errors,canonicalRequests},null,2));
    console.log('PASS source holds: static and subscription profiles, quick views, directory, CSV and comparison');
  } finally { await browser.close(); }
}
main().catch(e=>{console.error(e);process.exitCode=1;});
