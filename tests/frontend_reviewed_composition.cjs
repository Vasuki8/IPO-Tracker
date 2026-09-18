'use strict';
// Real served values, no request interception or synthetic profile replacement.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { chromium } = require('playwright');

async function main() {
  const base = new URL(process.env.BASE_URL || 'http://127.0.0.1:8000/');
  const dir = path.resolve(process.env.SMOKE_ARTIFACT_DIR || 'artifacts/frontend');
  await fs.mkdir(dir, {recursive:true});
  let response;
  for (let attempt=0; attempt<40; attempt++) {
    try { response=await fetch(new URL('data/ipos-summary.json',base)); if(response.ok) break; }
    catch(error) { if(attempt===39) throw error; }
    await new Promise(resolve=>setTimeout(resolve,250));
  }
  assert.ok(response && response.ok);
  const {ipos} = await response.json();
  const record = ipos.find(row => row.id === 'emmvee');
  assert.equal(record.issueSizeCr, 2900);
  assert.equal(record.publicQuality.fields.issueSizeCr.state, 'final_verified');
  const browser = await chromium.launch({headless:true,
    ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH} : {}),
    args: process.env.PLAYWRIGHT_CHROMIUM_ARGS ? JSON.parse(process.env.PLAYWRIGHT_CHROMIUM_ARGS) : []});
  const errors = [], canonicalRequests = [], results = [];
  const page = await browser.newPage({viewport:{width:1440,height:900}});
  page.on('pageerror', error => errors.push(String(error)));
  page.on('request', request => { if (new URL(request.url()).pathname.endsWith('/data/ipos.json')) canonicalRequests.push(request.url()); });
  try {
    await page.goto(new URL('?q=Emmvee',base).href,{waitUntil:'networkidle'});
    await page.locator('#freshness.loaded').waitFor();
    const row = page.locator('#ipoRows tr[data-id="emmvee"]');
    assert.match(await row.locator('[data-label="Issue size"] .metric').textContent(), /2,900/);
    results.push('directory accepted amount');
    const downloadPromise=page.waitForEvent('download');
    await page.locator('#exportCsv').click();
    const download=await downloadPromise;
    const lines=(await fs.readFile(await download.path(),'utf8')).replace(/^\uFEFF/,'').split('\r\n');
    const parse=line=>[...line.matchAll(/(?:^|,)(?:"((?:[^"]|"")*)"|([^,]*))/g)].map(cell=>(cell[1]??cell[2]).replace(/""/g,'"'));
    const headers=parse(lines[0]),values=parse(lines[1]);
    assert.equal(Number(values[headers.indexOf('Issue size crore INR')]),2900);
    assert.equal(values[headers.indexOf('Issue size evidence state')],'final_verified');
    results.push('CSV accepted amount and evidence state');
    await row.locator('[data-action="compare"]').click();
    await page.locator('#search').fill('Teamtech');
    await page.locator('#ipoRows tr[data-id="teamtech"] [data-action="compare"]').click();
    await page.locator('#openCompare').click();
    const comparison=page.locator('#compareBody tbody tr').filter({has:page.locator('th',{hasText:/^Issue size$/})});
    assert.match(await comparison.locator('td').first().textContent(),/2,900/);
    results.push('comparison accepted amount');
    await page.keyboard.press('Escape');
    await page.goto(new URL(record.profilePath,base).href,{waitUntil:'networkidle'});
    await page.locator('#companyPage .company-profile').waitFor();
    const profile=JSON.parse(await page.locator('#ipo-profile-data').textContent()).ipo;
    for (const [field,value] of Object.entries({issueSizeCr:2900,freshIssueCr:2143.862,ofsCr:756.138})) {
      assert.equal(profile[field],value);
      assert.equal(profile.publicQuality.fields[field].state,'final_verified');
    }
    assert.equal(profile.issueComposition.freshShares,98795483);
    assert.equal(profile.issueComposition.ofsShares,34845069);
    for (const width of [1440,375,320]) {
      await page.setViewportSize({width,height:900});
      const text=await page.locator('#companyPage').innerText();
      assert.match(text,/2,143\.86/); assert.match(text,/756\.14/);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,`Emmvee profile overflow at ${width}px`);
      await page.screenshot({path:path.join(dir,`reviewed-emmvee-${width}.png`),fullPage:true});
    }
    results.push('profile source-linked composition at 1440/375/320px');
    await page.goto(new URL('ipo/teamtech/',base).href,{waitUntil:'networkidle'});
    await page.locator('#companyPage .company-profile').waitFor();
    const team=JSON.parse(await page.locator('#ipo-profile-data').textContent()).ipo;
    assert.equal(team.publicQuality.fields.objectsOfIssue.state,'under_review');
    assert.ok(!team.objectsOfIssue?.length);
    assert.match(await page.locator('#companyPage').innerText(),/Under review/);
    results.push('Teamtech remains withheld');
    assert.deepEqual(errors,[]); assert.deepEqual(canonicalRequests,[]);
    await fs.writeFile(path.join(dir,'reviewed-composition.json'),JSON.stringify({baseUrl:base.href,status:'passed',results,errors,canonicalRequests},null,2));
    console.log('PASS reviewed composition: '+results.join('; '));
  } finally { await browser.close(); }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
