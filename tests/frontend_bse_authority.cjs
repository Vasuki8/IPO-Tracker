'use strict';
// Real generated BSE snapshots, not intercepted requests or synthetic UI data.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {chromium} = require('playwright');

async function main() {
  const base = new URL(process.env.BASE_URL || 'http://127.0.0.1:8000/');
  const out = path.resolve(process.env.SMOKE_ARTIFACT_DIR || 'artifacts/frontend');
  await fs.mkdir(out, {recursive:true});
  const response = await fetch(new URL('data/ipos-summary.json', base));
  assert.ok(response.ok);
  const {ipos} = await response.json();
  const record = ipos.find(r => r.subscriptionSourceUrl?.startsWith('https://beta.bseindia.com/')
    && !r.subscriptionObservedAt && r.subscription && r.subscriptionAuthority === 'official_exchange');
  assert.ok(record, 'A real BSE snapshot must retain unknown observation time');
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:900}});
  const errors = [], canonicalRequests = [], results = [];
  page.on('pageerror',e=>errors.push(String(e)));
  page.on('request',r=>{if(new URL(r.url()).pathname.endsWith('/data/ipos.json'))canonicalRequests.push(r.url());});
  try {
    await page.goto(new URL('?q='+encodeURIComponent(record.company),base).href,{waitUntil:'networkidle'});
    await page.locator('#freshness.loaded').waitFor();
    const row = page.locator(`#ipoRows tr[data-id="${record.id}"]`);
    const note = await row.locator('[data-label="Subscription"] .metric-note').innerText();
    assert.match(note, /Official exchange/); assert.match(note, /Source time unavailable/);
    assert.doesNotMatch(note, /Source reported at/);
    results.push('directory authority and unknown source time');
    const pendingDownload = page.waitForEvent('download');
    await page.locator('#exportCsv').click();
    const download = await pendingDownload;
    const lines = (await fs.readFile(await download.path(),'utf8')).replace(/^\uFEFF/,'').split('\r\n');
    const parse = line => [...line.matchAll(/(?:^|,)(?:"((?:[^"]|"")*)"|([^,]*))/g)].map(c=>(c[1]??c[2]).replace(/""/g,'"'));
    const headers=parse(lines[0]), values=parse(lines[1]);
    assert.equal(values[headers.indexOf('Subscription source authority')], 'Official exchange');
    assert.equal(values[headers.indexOf('Subscription source observation time')], '');
    assert.equal(values[headers.indexOf('Subscription collection time')], record.subscriptionCollectedAt);
    assert.equal(Number(values[headers.indexOf('Subscription multiple')]), record.subscription.total);
    results.push('CSV preserves numbers and distinct clocks');
    await row.locator('[data-action="compare"]').click();
    await page.locator('#search').fill('Teamtech');
    await page.locator('#ipoRows tr[data-id="teamtech"] [data-action="compare"]').click();
    await page.locator('#openCompare').click();
    const comparison = page.locator('#compareBody tbody tr').filter({has:page.locator('th',{hasText:/^Subscription$/})});
    assert.match(await comparison.locator('td').first().innerText(), /Official exchange/);
    assert.match(await comparison.locator('td').first().innerText(), /Source time unavailable/);
    results.push('comparison uses the same authority and freshness');
    await page.keyboard.press('Escape');
    await page.goto(new URL(record.profilePath,base).href,{waitUntil:'networkidle'});
    await page.locator('#companyPage .company-profile').waitFor();
    const profile = JSON.parse(await page.locator('#ipo-profile-data').textContent()).ipo;
    assert.equal(profile.subscriptionAuthority, 'official_exchange');
    assert.equal(profile.subscriptionObservedAt, record.subscriptionObservedAt);
    assert.ok(profile.subscriptionObservedAt == null);
    // The compact directory carries only total; full category values stay in profiles.
    assert.equal(profile.subscription.total, record.subscription.total);
    for (const key of ['subscriptionSourceUrl','subscriptionSource','subscriptionCollectedAt','subscriptionTimeBasis'])
      assert.equal(profile[key], record[key]);
    for (const width of [1440,375,320]) {
      await page.setViewportSize({width,height:900});
      const text = await page.locator('#company-subscription').innerText();
      assert.match(text, /Official exchange/); assert.match(text, /Source time unavailable/);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
      await page.screenshot({path:path.join(out,`bse-authority-${width}.png`),fullPage:true});
    }
    results.push('profile at 1440/375/320px');
    assert.deepEqual(errors,[]); assert.deepEqual(canonicalRequests,[]);
    await fs.writeFile(path.join(out,'bse-authority.json'),JSON.stringify({status:'passed',id:record.id,results,errors,canonicalRequests},null,2));
    console.log('PASS BSE source authority: '+results.join('; '));
  } finally { await browser.close(); }
}
main().catch(e=>{console.error(e);process.exitCode=1;});
