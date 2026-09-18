'use strict';
// Exercise served candidate profiles and their real quick-view loader.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {chromium} = require('playwright');

const EXPECTED = {
  snehaa: {leadManagers:['FAST TRACK FINSEC PRIVATE LIMITED'], registrar:'SKYLINE FINANCIAL SERVICES PRIVATE LIMITED'},
  sacheerome: {leadManagers:['GYR CAPITAL ADVISORS PRIVATE LIMITED'], registrar:'MUFG INTIME INDIA PRIVATE LIMITED'},
};
const FIELDS = ['leadManagers', 'registrar'];
const SOURCE_KEYS = ['sourceUrl', 'documentDate', 'sha256', 'parserVersion', 'checkedAt'];
const embedded = html => JSON.parse(html.match(/<script\b[^>]*id="ipo-profile-data"[^>]*>([\s\S]*?)<\/script>/)[1]).ipo;
function decisions(record) {
  return Object.fromEntries(Object.entries(record.publicQuality.fields).map(([field, decision]) => {
    const result = {...decision};
    if ('source' in result) {
      result.sourceEvidence = record.publicQuality.sources[result.source];
      delete result.source;
    }
    return [field, result];
  }));
}
async function main() {
  const root = path.resolve(__dirname, '..');
  const candidate = path.resolve(process.env.REVIEWED_CANDIDATE_ROOT || root);
  const base = new URL(process.env.BASE_URL || 'http://127.0.0.1:8002/');
  const out = path.resolve(process.env.SMOKE_ARTIFACT_DIR || 'artifacts/frontend/reviewed-intermediaries');
  await fs.mkdir(out, {recursive:true});
  // Canonical/proof files are read by the test process only, never the browser.
  const canonical = JSON.parse(await fs.readFile(path.join(candidate,'data/ipos.json'),'utf8')).ipos;
  const retained = JSON.parse(await fs.readFile(path.join(root,'tests/public_intermediary_reviews_retained.json'),'utf8')).ipos;
  let response;
  for (let attempt=0; attempt<40; attempt++) {
    try { response=await fetch(new URL('data/ipos-summary.json',base)); if(response.ok) break; }
    catch(error) { if(attempt===39) throw error; }
    await new Promise(resolve=>setTimeout(resolve,250));
  }
  assert.ok(response?.ok, 'Candidate HTTP server must be ready');
  const browser = await chromium.launch({headless:true,
    ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH} : {}),
    args: process.env.PLAYWRIGHT_CHROMIUM_ARGS ? JSON.parse(process.env.PLAYWRIGHT_CHROMIUM_ARGS) : []});
  const page = await browser.newPage({viewport:{width:1440,height:900}, reducedMotion:'reduce'});
  page.setDefaultTimeout(15000);
  const errors=[], canonicalRequests=[], results=[];
  page.on('pageerror',error=>errors.push(String(error)));
  page.on('request',request=>{if(new URL(request.url()).pathname.endsWith('/data/ipos.json'))canonicalRequests.push(request.url());});
  try {
    for (const [id, expected] of Object.entries(EXPECTED)) {
      const row = canonical.find(record=>record.id===id);
      assert.ok(row, id+': reviewed issuer must remain present');
      const baseline = embedded(await fs.readFile(path.join(root,row.profilePath,'index.html'),'utf8'));
      const old = retained.find(record=>record.id===id);
      const unsupported = FIELDS.flatMap(field=>Array.isArray(old[field])?old[field]:[old[field]])
        .filter(value=>value && !Object.values(expected).flat().includes(value));
      async function checkRendered(container) {
        const offer = container.locator('#company-offer-intel');
        const text = await offer.innerText();
        for (const value of Object.values(expected).flat()) assert.ok(text.includes(value), id+': expected legal name absent');
        for (const value of unsupported) assert.ok(!text.includes(value), id+': unsupported joined/former role leaked');
        for (const field of FIELDS) {
          const note = container.locator(`[data-quality-field="${field}"]`).first();
          const proof = row.staticFieldProvenance[field];
          assert.match(await note.innerText(), /Final Prospectus verified/);
          assert.equal(await note.locator('a').getAttribute('href'),proof.sourceUrl.split('#')[0]+'#page='+proof.evidence.page);
        }
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
      }
      for (const width of [1440,375,320]) {
        await page.setViewportSize({width,height:900});
        await page.goto(new URL(row.profilePath,base).href,{waitUntil:'networkidle'});
        const profile = page.locator('#companyPage .company-profile'); await profile.waitFor();
        const payload = JSON.parse(await page.locator('#ipo-profile-data').textContent()).ipo;
        for (const field of FIELDS) {
          assert.deepEqual(payload[field], expected[field]);
          const proof=row.staticFieldProvenance[field], decision=payload.publicQuality.fields[field];
          assert.equal(decision.state,'final_verified');
          assert.equal(decision.page,proof.evidence.page);
          assert.deepEqual(payload.publicQuality.sources[decision.source],
            Object.fromEntries(SOURCE_KEYS.filter(key=>key in proof).map(key=>[key,proof[key]])));
        }
        const previous=decisions(baseline), current=decisions(payload);
        for (const [field, decision] of Object.entries(previous)) {
          if (!FIELDS.includes(field)) assert.deepEqual(current[field], decision,id+': unrelated field decision changed: '+field);
        }
        await checkRendered(profile);
        await page.screenshot({path:path.join(out,`reviewed-${id}-profile-${width}.png`),fullPage:true});
        await page.goto(new URL('?q='+encodeURIComponent(row.company),base).href,{waitUntil:'networkidle'});
        await page.locator('#freshness.loaded').waitFor();
        await page.locator(`#ipoRows tr[data-id="${id}"] [data-action="preview"]`).click();
        const modal=page.locator('#detailDialog[open] .company-profile'); await modal.waitFor();
        await checkRendered(modal);
        await page.screenshot({path:path.join(out,`reviewed-${id}-quick-view-${width}.png`),fullPage:true});
        await page.keyboard.press('Escape');
        results.push({id,width,profileAndQuickView:'passed',fields:FIELDS});
      }
    }
    await page.goto(new URL('ipo/teamtech/',base).href,{waitUntil:'networkidle'});
    await page.locator('#companyPage .company-profile').waitFor();
    const held=JSON.parse(await page.locator('#ipo-profile-data').textContent()).ipo;
    assert.equal(held.publicQuality.fields.objectsOfIssue.state,'under_review');
    assert.ok(!held.objectsOfIssue?.length);
    assert.deepEqual(errors,[]); assert.deepEqual(canonicalRequests,[]);
    await fs.writeFile(path.join(out,'reviewed-intermediaries.json'),JSON.stringify({status:'passed',baseUrl:base.href,results,errors,canonicalRequests},null,2));
    console.log('PASS reviewed intermediary profiles and quick views at 1440/375/320px; unrelated holds preserved');
  } finally { await browser.close(); }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
