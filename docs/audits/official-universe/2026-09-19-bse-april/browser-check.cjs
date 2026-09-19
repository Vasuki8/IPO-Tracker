const { chromium } = require('playwright');
const fs = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');

(async () => {
  const base = new URL(process.env.BASE_URL || 'http://127.0.0.1:8006/');
  const output = process.env.SMOKE_ARTIFACT_DIR || '.cache/official-universe/browser';
  await fs.mkdir(output, { recursive: true });
  const roots = [
    'docs/audits/official-universe/2026-09-19-bse-june/admission-review.json',
    'docs/audits/official-universe/2026-09-19-bse-may/admission-review.json',
    'docs/audits/official-universe/2026-09-19-bse-april/admission-review.json',
  ];
  const reviewed = [];
  for (const file of roots) {
    const payload = JSON.parse(await fs.readFile(file, 'utf8'));
    for (const row of payload.records) {
      if (row.decision === 'accept_identity_only') reviewed.push(row);
    }
  }
  assert.equal(reviewed.length, 32);

  const summary = await (await fetch(new URL('data/ipos-summary.json', base))).json();
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
      ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH }
      : {}),
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
  const errors = [], masterRequests = [], results = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('request', r => {
    try {
      if (new URL(r.url()).pathname.endsWith('/data/ipos.json')) masterRequests.push(r.url());
    } catch {}
  });
  try {
    for (const want of reviewed) {
      const id = want.proposedId;
      const brief = summary.ipos.find(r => r.id === id);
      assert.ok(brief, id + ': missing from summary');
      for (const width of [1440, 375]) {
        await page.setViewportSize({ width, height: 900 });
        await page.goto(new URL(brief.profilePath, base).href, { waitUntil: 'networkidle' });
        await page.locator('#companyPage .company-profile').waitFor();
        assert.equal(await page.locator('#companyPage h1').innerText(), want.identity.issuerName);
        const record = JSON.parse(await page.locator('#ipo-profile-data').textContent()).ipo;
        for (const row of [brief, record]) {
          assert.equal(row.symbol, want.identity.symbol, id + ': symbol');
          assert.equal(row.status, 'closed', id + ': status');
          assert.equal(row.board, 'SME', id + ': board');
          assert.equal(row.openDate, want.identity.openDate, id + ': open');
          assert.equal(row.closeDate, want.identity.closeDate, id + ': close');
          for (const key of ['listingDate','priceBand','lotSize','issueSizeCr','financials','subscription','marketLot','minimumBidQuantity']) {
            assert.ok(row[key] == null, id + ': invented ' + key);
          }
        }
        assert.ok(await page.locator(`a[href="${want.sourceUrl}"]`).count(), id + ': source link absent');
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), id + ': overflow ' + width);
        results.push({ id, width, profile: 'passed' });
      }
      await page.setViewportSize({ width: 375, height: 900 });
      await page.goto(new URL('?q=' + encodeURIComponent(want.identity.symbol), base).href, { waitUntil: 'networkidle' });
      await page.locator(`a[href="${brief.profilePath}"]`).first().waitFor();
    }
    assert.deepEqual(errors, []);
    assert.deepEqual(masterRequests, []);
    const receipt = { status: 'passed', baseUrl: base.href, profiles: reviewed.length, viewportChecks: results.length,
      directorySearches: reviewed.length, results, errors, masterRequests };
    await fs.writeFile(path.join(output, 'result.json'), JSON.stringify(receipt, null, 2) + '\n');
    console.log(JSON.stringify({ status: 'passed', profiles: reviewed.length, viewportChecks: results.length,
      directorySearches: reviewed.length }));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
