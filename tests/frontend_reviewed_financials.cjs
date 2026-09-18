'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {chromium} = require('playwright');
async function main() {
  const root=path.resolve(process.env.REVIEWED_CANDIDATE_ROOT || path.join(__dirname,'..'));
  const base=new URL(process.env.BASE_URL || 'http://127.0.0.1:8003/');
  const out=path.resolve(process.env.SMOKE_ARTIFACT_DIR || 'artifacts/frontend/reviewed-financials');
  await fs.mkdir(out,{recursive:true});
  const expected={htel:['FY2026','FY2025','FY2024'],kissht:['FY2025','FY2024','FY2023']};
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'});
  const errors=[], requests=[];page.on('pageerror',e=>errors.push(String(e)));
  page.on('request',r=>{if(new URL(r.url()).pathname.endsWith('/data/ipos.json'))requests.push(r.url());});
  try {
    for(const [id,years] of Object.entries(expected)) {
      const proof=JSON.parse(await fs.readFile(path.join(root,'data/reviewed_correction_evidence',id+'.json'),'utf8')).financials;
      for(const width of [1440,375,320]) {
        await page.setViewportSize({width,height:900});
        await page.goto(new URL('ipo/'+id+'/',base).href,{waitUntil:'networkidle'});
        await page.locator('#companyPage .company-profile').waitFor();
        const record=JSON.parse(await page.locator('#ipo-profile-data').textContent()).ipo;
        assert.equal(proof.value.unit,'₹ crore');
        assert.deepEqual(record.financials,{periods:proof.value.periods});
        assert.equal(record.publicQuality.fields.financials.state,'final_verified');
        assert.deepEqual(record.financials.periods.map(p=>p.period),years);
        async function check(container) {
          const section=container.locator('#company-financials');
          assert.match(await section.innerText(),/Amounts in ₹ crore, except EPS \(₹\) and returns \(%\)/);
          assert.equal(await section.locator('tbody tr').count(),3);
          const note=section.locator('[data-quality-field="financials"]');
          assert.match(await note.innerText(),/Final Prospectus verified/);
          assert.equal(await note.locator('a').getAttribute('href'),proof.sourceUrl+'#page='+proof.evidence.page);
          const rows=await section.locator('tbody tr').allTextContents();
          assert.ok(rows[0].includes(id==='htel'?'₹2.7':'₹33.09'));
          assert.ok(!rows.join(' ').includes('83,531,840'));
          assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
        }
        await check(page.locator('#companyPage .company-profile'));
        await page.screenshot({path:path.join(out,`${id}-profile-${width}.png`),fullPage:true});
        await page.goto(new URL('?q='+encodeURIComponent(proof.identity.company),base).href,{waitUntil:'networkidle'});
        await page.locator('#freshness.loaded').waitFor();
        await page.locator(`#ipoRows tr[data-id="${id}"] [data-action="preview"]`).click();
        const modal=page.locator('#detailDialog[open] .company-profile');await modal.waitFor();
        await check(modal);
        await page.screenshot({path:path.join(out,`${id}-quick-view-${width}.png`),fullPage:true});
        await page.keyboard.press('Escape');
      }
    }
    await page.goto(new URL('ipo/pngsreva/',base).href,{waitUntil:'networkidle'});
    const held=JSON.parse(await page.locator('#ipo-profile-data').textContent()).ipo;
    assert.equal(held.publicQuality.fields.financials.state,'under_review');
    assert.ok(!held.financials?.periods?.length);
    assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
    await fs.writeFile(path.join(out,'reviewed-financials.json'),JSON.stringify({status:'passed',ids:Object.keys(expected),widths:[1440,375,320],unrelatedFinancialReview:'preserved',errors,requests},null,2));
    console.log('PASS reviewed financial profiles and quick views; PNGS review preserved');
  } finally {await browser.close();}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
