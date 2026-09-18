'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { chromium } = require('playwright');

// Document overflow alone misses text painted across neighboring grid cells.
// Exercise a real secondary-source snapshot and inspect every text line.
async function main() {
  const base = new URL(process.env.BASE_URL || 'http://127.0.0.1:8000/');
  const dir = path.resolve(process.env.SMOKE_ARTIFACT_DIR || 'artifacts/frontend');
  await fs.mkdir(dir, { recursive: true });
  const response = await fetch(new URL('data/ipos-summary.json', base));
  assert.ok(response.ok);
  const payload = await response.json();
  const record = payload.ipos.find(row => row.subscriptionAuthority === 'secondary'
    && row.subscriptionObservedAt && row.subscriptionCollectedAt);
  assert.ok(record, 'A retained real secondary subscription has both clocks');
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    for (const width of [1440, 375, 320]) {
      const page = await browser.newPage({ viewport: { width, height: 900 } });
      const errors = [];
      page.on('pageerror', error => errors.push(String(error)));
      try {
        const address = new URL(base); address.searchParams.set('q', record.company);
        await page.goto(address.href, { waitUntil: 'networkidle' });
        await page.locator('#freshness.loaded').waitFor();
        const cell = page.locator('#ipoRows tr').filter({has: page.locator(`[data-action="preview"][data-id="${record.id}"]`)}).locator('td[data-label="Subscription"]');
        const note = cell.locator('.metric-note');
        await note.scrollIntoViewIfNeeded();
        const bounds = await note.evaluate(element => {
          const box = element.getBoundingClientRect();
          const cell = element.closest('td').getBoundingClientRect();
          const range = document.createRange(); range.selectNodeContents(element);
          const lines = [...range.getClientRects()].map(r => ({left:r.left,right:r.right,top:r.top,bottom:r.bottom}));
          return { text:element.textContent, box:{left:box.left,right:box.right,top:box.top,bottom:box.bottom},
            cell:{left:cell.left,right:cell.right,top:cell.top,bottom:cell.bottom}, lines };
        });
        for (const text of ['Source reported at', 'Checked at', 'Secondary source'])
          assert.ok(bounds.text.includes(text));
        assert.ok(bounds.lines.length > 0);
        for (const line of bounds.lines) {
          for (const boundary of [bounds.box, bounds.cell])
            assert.ok(line.left >= boundary.left - 1 && line.right <= boundary.right + 1
              && line.top >= boundary.top - 1 && line.bottom <= boundary.bottom + 1,
              `Freshness text escapes its own cell at ${width}px: ${JSON.stringify(bounds)}`);
        }
        assert.deepEqual(errors, []);
        results.push({width,recordId:record.id,passed:true,lineCount:bounds.lines.length});
        await page.goto(new URL('?view=quality', base).href, {waitUntil:'networkidle'});
        const sourceButton = page.locator('#sourceHealth .health-item').filter({has:page.getByText('NSE-live',{exact:true})});
        await sourceButton.click();
        const diagnostic = page.locator('#sourceHealthDetail');
        await diagnostic.waitFor({state:'visible'});
        const checkCell = diagnostic.locator('.health-detail-cell').filter({hasText:'Last source check'});
        const sourceCheck = payload.meta.sourceHealth['NSE-live'];
        if (!sourceCheck.checkedAt && !sourceCheck.asOf) assert.ok((await checkCell.textContent()).includes('Not available'));
        assert.ok((await diagnostic.textContent()).includes('does not establish a fresh source observation'));
        const escaped = await page.locator('#sourceHealth .health-item, #sourceHealthDetail .health-detail-cell').evaluateAll(elements => elements.flatMap(element => {
          const box=element.getBoundingClientRect();
          const walker=document.createTreeWalker(element,NodeFilter.SHOW_TEXT);
          const escaped=[];
          while(walker.nextNode()) {
            if(!walker.currentNode.textContent.trim()) continue;
            const range=document.createRange();range.selectNodeContents(walker.currentNode);
            for(const line of range.getClientRects()) if(line.left<box.left-1 || line.right>box.right+1) escaped.push(walker.currentNode.textContent);
          }
          return escaped;
        }));
        assert.deepEqual(escaped,[],`Source diagnostics text overflows at ${width}px`);
        assert.deepEqual(errors, []);
        await page.screenshot({path:path.join(dir,`source-health-${width}.png`),fullPage:true,animations:'disabled'});
      } finally {
        await page.screenshot({path:path.join(dir, `freshness-boundary-${width}.png`),fullPage:true,animations:'disabled'});
        await page.close();
      }
    }
    await fs.writeFile(path.join(dir,'freshness-boundary-results.json'), JSON.stringify(results,null,2));
    console.log('PASS source/check/secondary text remains inside its cell at 1440, 375 and 320px');
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode=1; });
