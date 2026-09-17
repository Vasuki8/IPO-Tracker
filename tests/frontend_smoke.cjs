#!/usr/bin/env node
'use strict';

// Run against the repository served over HTTP. Chromium is installed separately
// so the static site does not need an npm project or production dependencies.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { chromium } = require('playwright');

const BASE_URL = new URL(process.env.BASE_URL || 'http://127.0.0.1:8000/');
const ARTIFACT_DIR = path.resolve(process.env.SMOKE_ARTIFACT_DIR || 'artifacts/frontend');
const DESKTOP = { width: 1440, height: 900 };
const results = [];
const qualityFiles = ['completeness.json', 'missing_queue.json'];
const collator = new Intl.Collator('en', { sensitivity: 'base' });
let browser;
let publicPayload;
let records;
let byId;

const url = (relative) => new URL(relative, BASE_URL).href;
const rowIds = (page) =>
  page.locator('#ipoRows tr').evaluateAll((rows) => rows.map((row) => row.dataset.id));
const fileRequested = (requests, name) =>
  requests.filter((request) => new URL(request.url).pathname.endsWith('/data/' + name));

async function ready(page) {
  await page.locator('#freshness.loaded').waitFor();
  await page.locator('#ipoRows tr').first().waitFor();
}

async function openDirectory(page, query = '') {
  const response = await page.goto(url(query), { waitUntil: 'networkidle' });
  assert.ok(response?.ok(), 'The dashboard document must load successfully');
  await ready(page);
}

async function navigate(page, view) {
  const menu = page.locator('#menuToggle');
  if ((await menu.isVisible()) && (await menu.getAttribute('aria-expanded')) !== 'true')
    await menu.click();
  await page.locator(`.main-nav [data-view="${view}"]`).click();
  await page.locator(view === 'watchlist' ? '#view-explore' : `#view-${view}`).waitFor();
  await page.waitForLoadState('networkidle');
}

async function noOverflow(page, label) {
  const size = await page.evaluate(() => ({
    viewport: window.innerWidth,
    document: document.documentElement.scrollWidth,
    body: document.body.scrollWidth,
  }));
  assert.ok(
    size.document <= size.viewport + 1 && size.body <= size.viewport + 1,
    `${label} has horizontal page overflow: ${JSON.stringify(size)}`,
  );
  console.log(
    `  FIT ${label}: viewport ${size.viewport}px, document ${size.document}px, body ${size.body}px`,
  );
}

async function screenshot(page, name) {
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({
    path: path.join(ARTIFACT_DIR, `${name}.png`),
    fullPage: true,
    animations: 'disabled',
  });
}

async function run(name, check, viewport = DESKTOP) {
  const slug = name.replace(/[^a-z0-9]+/gi, '-').toLowerCase();
  const started = Date.now();
  const context = await browser.newContext({
    viewport,
    reducedMotion: 'reduce',
    timezoneId: 'Asia/Kolkata',
  });
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  const page = await context.newPage();
  page.setDefaultTimeout(15_000);
  page.setDefaultNavigationTimeout(30_000);
  const pageErrors = [];
  const requests = [];
  const consoleMessages = [];
  page.on('pageerror', (error) => pageErrors.push(error.stack || String(error)));
  page.on('request', (request) =>
    requests.push({ url: request.url(), type: request.resourceType() }),
  );
  page.on('console', (message) => {
    if (['warning', 'error'].includes(message.type()))
      consoleMessages.push(`${message.type()}: ${message.text()}`);
  });
  let failure;
  console.log(`RUN ${name}`);
  try {
    await check(page, requests);
    assert.deepEqual(pageErrors, [], 'No uncaught browser errors are allowed');
  } catch (error) {
    failure = error;
    await screenshot(page, `failure-${slug}`).catch(() => {});
    await fs
      .writeFile(
        path.join(ARTIFACT_DIR, `failure-${slug}.html`),
        await page.content().catch(() => ''),
      )
      .catch(() => {});
  } finally {
    await context.tracing.stop(
      failure ? { path: path.join(ARTIFACT_DIR, `failure-${slug}-trace.zip`) } : {},
    );
    const result = {
      name,
      status: failure ? 'failed' : 'passed',
      durationMs: Date.now() - started,
      viewport,
      pageUrl: page.url(),
      pageErrors,
      consoleMessages,
      requests,
      ...(failure ? { error: failure.stack || String(failure) } : {}),
    };
    results.push(result);
    await fs.writeFile(path.join(ARTIFACT_DIR, 'results.json'), JSON.stringify(results, null, 2));
    await context.close();
    console.log(`${failure ? 'FAIL' : 'PASS'} ${name} (${result.durationMs}ms)`);
    if (failure) console.error(failure.stack || failure);
  }
}

async function main() {
  await fs.mkdir(ARTIFACT_DIR, { recursive: true });
  const response = await fetch(url('data/ipos-summary.json'));
  assert.ok(response.ok, 'The actual public IPO summary must be available');
  publicPayload = await response.json();
  records = publicPayload.ipos;
  assert.ok(
    Array.isArray(records) && records.length >= 50,
    'Smoke tests require the shipped IPO dataset',
  );
  byId = new Map(records.map((record) => [String(record.id), record]));
  const launchOptions = { headless: true };
  if (process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH)
    launchOptions.executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH;
  if (process.env.PLAYWRIGHT_CHROMIUM_ARGS) {
    const args = JSON.parse(process.env.PLAYWRIGHT_CHROMIUM_ARGS);
    assert.ok(
      Array.isArray(args) && args.every((value) => typeof value === 'string'),
      'PLAYWRIGHT_CHROMIUM_ARGS must be a JSON array of strings',
    );
    launchOptions.args = args;
  }
  browser = await chromium.launch(launchOptions);
  console.log(
    `Chromium ${browser.version()} | ${records.length} actual IPO records | ${BASE_URL.href}`,
  );

  await run('Initial directory and lazy quality loading', async (page, requests) => {
    await openDirectory(page);
    assert.equal(
      await page.locator('#ipoRows tr').count(),
      25,
      'The default page contains 25 rows',
    );
    assert.equal(await page.locator('#pageSize').inputValue(), '25');
    assert.ok(
      (await page.locator('#stats button').count()) >= 4,
      'Market overview cards are available',
    );
    for (const name of [...qualityFiles, 'ipos.json'])
      assert.equal(
        fileRequested(requests, name).length,
        0,
        `${name} must not load on directory entry`,
      );
    assert.equal(fileRequested(requests, 'ipos-summary.json').length, 1);
    await navigate(page, 'calendar');
    await navigate(page, 'watchlist');
    for (const name of qualityFiles)
      assert.equal(
        fileRequested(requests, name).length,
        0,
        `${name} must remain lazy outside Data & sources`,
      );
    await navigate(page, 'quality');
    await page.locator('#qualityDashboard .quality-panel').waitFor();
    assert.ok(
      (await page.locator('#sourceHealth .health-item').count()) > 0,
      'Source health is rendered',
    );
    for (const name of qualityFiles)
      assert.equal(
        fileRequested(requests, name).length,
        1,
        `${name} loads when Data & sources opens`,
      );
    await navigate(page, 'explore');
    await navigate(page, 'quality');
    for (const name of qualityFiles)
      assert.equal(
        fileRequested(requests, name).length,
        1,
        `${name} is reused when returning to Data & sources`,
      );
  });

  await run('Pagination and page size survive reload', async (page) => {
    await openDirectory(page);
    const first = await rowIds(page);
    await page.locator('#nextPage').click();
    const second = await rowIds(page);
    assert.equal(second.length, 25);
    assert.ok(
      second.every((id) => !first.includes(id)),
      'The next page shows different records',
    );
    assert.equal(new URL(page.url()).searchParams.get('page'), '2');
    await page.reload({ waitUntil: 'networkidle' });
    await ready(page);
    assert.deepEqual(await rowIds(page), second);
    await page.locator('#pageSize').selectOption('50');
    assert.equal(await page.locator('#ipoRows tr').count(), 50);
    assert.equal(
      await page.locator('#prevPage').isDisabled(),
      true,
      'Changing page size returns to page one',
    );
    assert.equal(new URL(page.url()).searchParams.get('limit'), '50');
    await page.reload({ waitUntil: 'networkidle' });
    await ready(page);
    assert.equal(await page.locator('#pageSize').inputValue(), '50');
    assert.equal(await page.locator('#ipoRows tr').count(), 50);
  });

  await run('Controls remain usable while the IPO snapshot loads', async (page) => {
    let release;
    const gate = new Promise((resolve) => {
      release = resolve;
    });
    await page.route('**/data/ipos-summary.json', async (route) => {
      await gate;
      await route.continue().catch(() => {});
    });
    try {
      await page.goto(url(''), { waitUntil: 'domcontentloaded' });
      await page.locator('#search').fill('limited');
      await page.waitForFunction(() => new URL(location.href).searchParams.get('q') === 'limited');
      assert.equal(
        await page.locator('#empty').isVisible(),
        false,
        'Loading is not presented as an empty search result',
      );
      assert.equal(await page.locator('#exportCsv').isDisabled(), true);
      await page.locator('.main-nav [data-view="calendar"]').click();
      await page.locator('#nextMonth').click();
      assert.equal(
        await page.locator('#calendarEvents [role="status"]').isVisible(),
        true,
        'The calendar announces its pending snapshot',
      );
      assert.equal(
        await page.locator('#calendarEvents .empty h3').count(),
        0,
        'A pending snapshot is not presented as an empty calendar',
      );
      await page.locator('.main-nav [data-view="explore"]').click();
    } finally {
      release();
    }
    await ready(page);
    assert.equal(await page.locator('#search').inputValue(), 'limited');
    assert.equal(await page.locator('#ipoRows tr').count(), 25);
  });

  await run('Combined filters sorting reload and reset', async (page) => {
    await openDirectory(page);
    // Pick a populated historical cohort from real records, independent of the
    // current bidding window or a particular company's continued availability.
    const oldDate = new Date(Date.now() - 2 * 86400_000).toISOString().slice(0, 10);
    const groups = new Map();
    for (const record of records) {
      if (
        !record.listingDate ||
        record.listingDate >= oldDate ||
        !/limited/i.test(record.company || '')
      )
        continue;
      const year = (record.openDate || record.listingDate || '').slice(0, 4);
      if (!['Mainboard', 'SME'].includes(record.board) || !/^\d{4}$/.test(year)) continue;
      const key = `${record.board}:${year}`;
      groups.set(key, (groups.get(key) || 0) + 1);
    }
    const cohort = [...groups].sort((a, b) => b[1] - a[1])[0];
    assert.ok(cohort && cohort[1] >= 3, 'The dataset contains a useful historical filter cohort');
    const [board, year] = cohort[0].split(':');
    await page.locator('#search').fill('limited');
    await page.locator('#boardFilter').selectOption(board);
    await page.locator('#yearFilter').selectOption(year);
    await page.locator('#tabs [data-status="listed"]').click();
    await page.locator('#sortFilter').selectOption('company');
    const ids = await rowIds(page);
    assert.ok(ids.length >= 3, 'Combined filters retain the selected historical cohort');
    const companies = [];
    for (const id of ids) {
      const record = byId.get(id);
      assert.ok(record, `Visible IPO ${id} exists in the actual dataset`);
      assert.equal(record.board, board);
      assert.equal(
        (record.openDate || record.listingDate || record.lifecycle?.stageDate || '').slice(0, 4),
        year,
      );
      assert.match(`${record.company || ''} ${record.symbol || ''}`, /limited/i);
      companies.push(record.company);
    }
    assert.deepEqual(
      companies,
      [...companies].sort(collator.compare),
      'Company A–Z sorts the filtered results',
    );
    assert.equal(
      await page.locator('#ipoRows .badge-listed').count(),
      ids.length,
      'Every filtered result has listed status',
    );
    const parameters = { q: 'limited', board, year, status: 'listed', sort: 'company' };
    for (const [key, value] of Object.entries(parameters))
      assert.equal(new URL(page.url()).searchParams.get(key), value);
    const filteredUrl = page.url();
    await page.reload({ waitUntil: 'networkidle' });
    await ready(page);
    assert.equal(page.url(), filteredUrl);
    assert.deepEqual(await rowIds(page), ids);
    assert.equal(await page.locator('#search').inputValue(), 'limited');
    assert.equal(await page.locator('#boardFilter').inputValue(), board);
    assert.equal(await page.locator('#yearFilter').inputValue(), year);
    assert.equal(await page.locator('#sortFilter').inputValue(), 'company');
    assert.equal(
      await page.locator('#tabs [data-status="listed"]').getAttribute('aria-pressed'),
      'true',
    );
    await page.locator('#clearFilters').click();
    assert.equal(new URL(page.url()).search, '');
    assert.equal(await page.locator('#search').inputValue(), '');
    for (const selector of ['#boardFilter', '#yearFilter'])
      assert.equal(await page.locator(selector).inputValue(), 'all');
    assert.equal(await page.locator('#sortFilter').inputValue(), 'recent');
    assert.equal(
      await page.locator('#tabs [data-status="all"]').getAttribute('aria-pressed'),
      'true',
    );
    assert.equal(await page.locator('#ipoRows tr').count(), 25);
    assert.equal(await page.locator('#clearFilters').isVisible(), false);
    await page.locator('#search').fill('no matching company for smoke test');
    await page.locator('#boardFilter').selectOption(board);
    await page.locator('#yearFilter').selectOption(year);
    await page.locator('#sortFilter').selectOption('company');
    await page.locator('#stats [data-stat-status="listed"]').click();
    assert.equal(
      await page.locator('#search').inputValue(),
      '',
      'Global overview cards clear the directory search',
    );
    for (const selector of ['#boardFilter', '#yearFilter'])
      assert.equal(await page.locator(selector).inputValue(), 'all');
    assert.equal(await page.locator('#sortFilter').inputValue(), 'recent');
    assert.equal(
      await page.locator('#tabs [data-status="listed"]').getAttribute('aria-pressed'),
      'true',
    );
    assert.ok(
      (await page.locator('#ipoRows tr').count()) > 0,
      'The overview opens its complete status category',
    );
  });

  await run('CSV export preserves negative returns as numbers', async (page) => {
    let record = records.find(
      (ipo) => typeof ipo.listing?.gainPct === 'number' && ipo.listing.gainPct < 0,
    );
    if (!record) {
      // This regression must still run when the current collector snapshot has
      // no price-performance coverage. Only this isolated browser test receives
      // a controlled return; no repository data or other test data is changed.
      const original = records.find((ipo) => ipo.listingDate) || records[0];
      record = { ...original, listing: { ...original.listing, gainPct: -12.5 } };
      await page.route('**/data/ipos-summary.json', (route) =>
        route.fulfill({
          json: { ...publicPayload, ipos: [record] },
        }),
      );
      console.log(
        '  FIXTURE CSV numeric regression: isolated -12.5% return; live snapshot has no negative return value',
      );
    }
    await openDirectory(page, '?q=' + encodeURIComponent(record.company));
    const pendingDownload = page.waitForEvent('download');
    await page.locator('#exportCsv').click();
    const download = await pendingDownload;
    const csv = await fs.readFile(await download.path(), 'utf8');
    const rows = csv.replace(/^\uFEFF/, '').split('\r\n');
    const parse = (line) => [...line.matchAll(/(?:^|,)(?:"((?:[^"]|"")*)"|([^,]*))/g)];
    const data = rows
      .slice(1)
      .map(parse)
      .find(
        (cells) =>
          cells[0]?.[1]?.replace(/""/g, '"') === record.company &&
          cells[1]?.[1] === (record.symbol || ''),
      );
    assert.ok(data, 'The selected IPO is present in the downloaded CSV');
    assert.equal(
      data[11][2],
      String(record.listing.gainPct),
      'Negative numeric returns are not changed into apostrophe-prefixed text',
    );
    assert.equal(Number(data[11][2]), record.listing.gainPct);
    await download.saveAs(path.join(ARTIFACT_DIR, 'negative-return-export.csv'));
  });

  await run('Watchlist add persistence and removal', async (page) => {
    await openDirectory(page);
    const firstRow = page.locator('#ipoRows tr').first();
    const id = await firstRow.getAttribute('data-id');
    await firstRow.locator('[data-action="save"]').click();
    assert.equal(
      await firstRow.locator('[data-action="save"]').getAttribute('aria-pressed'),
      'true',
    );
    assert.equal(
      await firstRow
        .locator('[data-action="save"]')
        .evaluate((element) => element === document.activeElement),
      true,
      'Saving retains action focus after the row rerenders',
    );
    assert.deepEqual(
      await page.evaluate(() => JSON.parse(localStorage.getItem('ipoTrackerWatchlist'))),
      [id],
    );
    await navigate(page, 'watchlist');
    assert.deepEqual(await rowIds(page), [id]);
    await page.reload({ waitUntil: 'networkidle' });
    await ready(page);
    assert.deepEqual(await rowIds(page), [id]);
    await page.locator('#ipoRows [data-action="save"]').click();
    assert.equal(await page.locator('#ipoRows tr').count(), 0);
    assert.equal(await page.locator('#empty').isVisible(), true);
    assert.equal(
      await page.locator('#emptyReset').evaluate((element) => element === document.activeElement),
      true,
      'Removing the last saved row moves focus to the empty-state action',
    );
    assert.equal((await page.locator('#watchlistCount').textContent()).trim(), '0');
    await page.reload({ waitUntil: 'networkidle' });
    await page.locator('#freshness.loaded').waitFor();
    assert.equal(await page.locator('#ipoRows tr').count(), 0);
    assert.deepEqual(
      await page.evaluate(() => JSON.parse(localStorage.getItem('ipoTrackerWatchlist'))),
      [],
    );
  });

  await run('Comparison minimum maximum and Escape', async (page) => {
    await openDirectory(page);
    const buttons = page.locator('#ipoRows [data-action="compare"]');
    await buttons.nth(0).click();
    assert.equal(
      await page.locator('#openCompare').isDisabled(),
      true,
      'One IPO cannot open a comparison',
    );
    await buttons.nth(1).click();
    assert.equal(await page.locator('#openCompare').isEnabled(), true);
    await page.locator('#openCompare').click();
    await page.locator('#compareDialog[open]').waitFor();
    assert.equal(
      await page.locator('#compareBody thead th').count(),
      3,
      'Two company columns plus the field label',
    );
    await page.keyboard.press('Escape');
    await page.locator('#compareDialog').waitFor({ state: 'hidden' });
    await buttons.nth(2).click();
    await buttons.nth(3).click();
    assert.equal(
      await page.locator('#ipoRows [data-action="compare"][aria-pressed="true"]').count(),
      3,
    );
    assert.equal(
      await buttons.nth(3).getAttribute('aria-pressed'),
      'false',
      'A fourth IPO is rejected',
    );
    assert.equal(await page.locator('#compareNames [data-remove-compare]').count(), 3);
    await page.locator('#openCompare').click();
    assert.equal(
      await page.locator('#compareBody thead th').count(),
      4,
      'Three company columns plus the field label',
    );
    await screenshot(page, 'desktop-comparison');
    await page.keyboard.press('Escape');
    await page.locator('#compareDialog').waitFor({ state: 'hidden' });
    await page.locator('#clearCompare').click();
    assert.equal(await page.locator('#compareTray').isVisible(), false);
    assert.equal(
      await page.locator('#ipoRows [data-action="compare"][aria-pressed="true"]').count(),
      0,
    );
    assert.equal(
      await buttons.first().evaluate((element) => element === document.activeElement),
      true,
      'Clearing the comparison restores a directory action',
    );
  });

  await run('Quick view Escape restores keyboard focus', async (page, requests) => {
    await openDirectory(page);
    const trigger = page.locator('#ipoRows [data-action="preview"]').first();
    const id = await trigger.getAttribute('data-id');
    await trigger.click();
    await page.locator('#detailDialog[open] .company-profile').waitFor();
    assert.equal((await page.locator('#dialogTitle').textContent()).trim(), byId.get(id).company);
    assert.equal(
      fileRequested(requests, 'ipos.json').length,
      0,
      'Embedded profiles avoid the full master dataset',
    );
    await screenshot(page, 'desktop-quick-view');
    await page.keyboard.press('Escape');
    await page.locator('#detailDialog').waitFor({ state: 'hidden' });
    await page.waitForFunction(
      (recordId) =>
        document.activeElement?.dataset.action === 'preview' &&
        document.activeElement?.dataset.id === recordId,
      id,
    );
    assert.equal(await trigger.evaluate((element) => element === document.activeElement), true);
  });

  await run('Subscription freshness stays coherent in profile and quick view', async (page) => {
    const summary = records.find((record) => record.id === 'veegaland');
    assert.ok(summary?.profilePath, 'The published Veegaland regression profile exists');
    const response = await fetch(url(summary.profilePath));
    assert.ok(response.ok);
    const html = await response.text();
    const embedded = html.match(
      /(<script[^>]+id=["']ipo-profile-data["'][^>]*>)([\s\S]*?)(<\/script>)/i,
    );
    assert.ok(embedded, 'The actual profile embeds its published record');
    const profile = JSON.parse(embedded[2]).ipo;
    const canonical = {
      ...(profile.subscription || {}),
      capturedAt: profile.subscriptionAsOf,
      source: profile.subscriptionSource,
    };
    const history = [...(profile.subscriptionHistory || [])].sort(
      (a, b) => Date.parse(a.capturedAt) - Date.parse(b.capturedAt),
    );
    const last = history.at(-1);
    const currentTime = Date.parse(canonical.capturedAt);
    const historyTime = Date.parse(last?.capturedAt);
    const expected =
      Number.isFinite(currentTime) && Number.isFinite(historyTime) && historyTime > currentTime
        ? last
        : canonical;
    const multiple = (value) =>
      value == null
        ? '—'
        : `${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}×`;
    const inspect = async (root, snapshot, label) => {
      const shown = await root.evaluate((element) => {
        const kpi = [...element.querySelectorAll('.company-kpi')].find(
          (node) => node.querySelector('.company-kpi-label')?.textContent.trim() === 'Subscription',
        );
        const section = element.querySelector('#company-subscription');
        return {
          kpi: kpi?.querySelector('.company-kpi-value')?.textContent.trim(),
          categories: Object.fromEntries(
            [...section.querySelectorAll('.subscription-card')].map((node) => [
              node.querySelector('span').textContent.trim(),
              node.querySelector('strong').textContent.trim(),
            ]),
          ),
          source: section.querySelector('.company-meta-chip').textContent.trim(),
          timestamp: section.querySelector('.company-data-note').textContent.trim(),
        };
      });
      assert.equal(
        shown.kpi,
        multiple(snapshot.total),
        `${label}: KPI uses the freshest observation`,
      );
      for (const [key, category] of [
        ['qib', 'QIB'],
        ['nii', 'NII / HNI'],
        ['retail', 'Retail / Individual'],
        ['total', 'Total'],
      ]) {
        assert.equal(
          shown.categories[category],
          multiple(snapshot[key]),
          `${label}: ${category} comes from the same observation`,
        );
      }
      assert.equal(shown.source, snapshot.source || 'Source not available');
      if (snapshot.capturedAt) {
        const timestamp = new Intl.DateTimeFormat('en-IN', {
          timeZone: 'Asia/Kolkata',
          dateStyle: 'medium',
          timeStyle: 'short',
        }).format(new Date(snapshot.capturedAt));
        assert.ok(
          shown.timestamp.includes(timestamp),
          `${label}: timestamp matches the displayed observation`,
        );
      }
      console.log(`  SNAPSHOT ${label}: ${shown.kpi}, ${shown.source}, ${shown.timestamp}`);
    };
    const inspectBoth = async (snapshot, label) => {
      await page.goto(url(summary.profilePath), { waitUntil: 'networkidle' });
      await page.locator('#companyPage .company-profile').waitFor();
      await inspect(page.locator('#companyPage'), snapshot, `${label} profile`);
      await openDirectory(page, '?q=' + encodeURIComponent(summary.company));
      await page.locator('#ipoRows [data-action="preview"]').first().click();
      await page.locator('#detailDialog[open] .company-profile').waitFor();
      await inspect(page.locator('#detailDialog'), snapshot, `${label} quick view`);
      await page.keyboard.press('Escape');
      await page.locator('#detailDialog').waitFor({ state: 'hidden' });
    };
    await inspectBoth(expected, 'Published Veegaland');

    // The actual record catches older history overriding newer canonical data.
    // A single controlled newer row verifies the converse and catches category
    // mixing: absent QIB/NII/retail values must remain absent in that observation.
    const newer = {
      capturedAt: new Date(
        Math.max(currentTime || 0, historyTime || 0, Date.now()) + 60_000,
      ).toISOString(),
      total: 12.34,
      source: 'Controlled newer snapshot',
    };
    const fixture = { ...profile, subscriptionHistory: [...history, newer] };
    const fixtureHtml = html.replace(
      embedded[0],
      embedded[1] + JSON.stringify({ ipo: fixture }).replace(/</g, '\\u003c') + embedded[3],
    );
    await page.route('**/' + summary.profilePath, (route) =>
      route.fulfill({
        body: fixtureHtml,
        contentType: 'text/html; charset=utf-8',
      }),
    );
    await inspectBoth(newer, 'Isolated newer-history fixture');
  });

  await run('Permanent profile navigation preserves directory query', async (page, requests) => {
    await openDirectory(page);
    const id = await page.locator('#ipoRows tr').first().getAttribute('data-id');
    const record = byId.get(id);
    await page.locator('#search').fill(record.company);
    await page.locator('#boardFilter').selectOption(record.board);
    await page.locator('#sortFilter').selectOption('company');
    const before = page.url();
    const expectedIds = await rowIds(page);
    await page.locator('#ipoRows .company-name-link').first().click();
    await page.locator('#companyPage .company-profile').waitFor();
    assert.equal(new URL(page.url()).pathname, new URL(record.profilePath, BASE_URL).pathname);
    assert.equal(
      (await page.locator('#companyPage .company-hero-name').textContent()).trim(),
      record.company,
    );
    assert.equal(fileRequested(requests, 'ipos.json').length, 0);
    const sourceNav = page.locator('#companyPage [data-company-target="company-sources"]');
    await sourceNav.click();
    await page.waitForFunction(() => {
      const rect = document.getElementById('company-sources')?.getBoundingClientRect();
      return rect && rect.top < window.innerHeight && rect.bottom > 0;
    });
    await page.locator('.company-route-back').click();
    await ready(page);
    assert.equal(page.url(), before, 'The profile back link restores the full directory query');
    assert.deepEqual(await rowIds(page), expectedIds);
    assert.equal(await page.locator('#search').inputValue(), record.company);
  });

  const calendarMonth = records.find((record) => record.openDate)?.openDate.slice(0, 7);
  await run(
    'Small mobile navigation scroll and keyboard focus',
    async (page) => {
      await openDirectory(page);
      await page.locator('#menuToggle').click();
      const links = page.locator('#sidebar a');
      assert.equal(
        await links.first().evaluate((element) => element === document.activeElement),
        true,
      );
      for (let index = 1; index < (await links.count()); index++) await page.keyboard.press('Tab');
      assert.equal(
        await links.last().evaluate((element) => element === document.activeElement),
        true,
      );
      const position = await links.last().boundingBox();
      assert.ok(
        position && position.y >= 0 && position.y + position.height <= 361,
        'The final menu link is reachable in a short viewport',
      );
      assert.ok(
        await page.locator('#sidebar').evaluate((element) => element.scrollTop > 0),
        'The sidebar scrolls to reach lower links',
      );
      await page.keyboard.press('Tab');
      assert.equal(
        await links.first().evaluate((element) => element === document.activeElement),
        true,
        'Tab stays inside the open menu',
      );
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#menuToggle').getAttribute('aria-expanded'), 'false');
      assert.equal(
        await page.locator('#menuToggle').evaluate((element) => element === document.activeElement),
        true,
      );
      await noOverflow(page, 'short mobile navigation');
    },
    { width: 320, height: 360 },
  );
  for (const [label, viewport] of [
    ['desktop', DESKTOP],
    ['mobile', { width: 390, height: 844 }],
    ['small-mobile', { width: 320, height: 844 }],
  ]) {
    await run(
      `Responsive surfaces ${label}`,
      async (page) => {
        await openDirectory(page);
        await noOverflow(page, `${label} directory`);
        await screenshot(page, `${label}-directory`);
        const profileHref = await page
          .locator('#ipoRows .company-name-link')
          .first()
          .getAttribute('href');
        await navigate(page, 'calendar');
        await page.goto(url(`?view=calendar&month=${calendarMonth}`), { waitUntil: 'networkidle' });
        await page.locator('#calendarEvents .calendar-day').first().waitFor();
        await noOverflow(page, `${label} calendar`);
        await screenshot(page, `${label}-calendar`);
        await navigate(page, 'quality');
        await page.locator('#qualityDashboard .quality-panel').waitFor();
        await noOverflow(page, `${label} data and sources`);
        await screenshot(page, `${label}-quality`);
        await page.goto(url(profileHref), { waitUntil: 'networkidle' });
        await page.locator('#companyPage .company-profile').waitFor();
        await noOverflow(page, `${label} company profile`);
        await screenshot(page, `${label}-profile`);
      },
      viewport,
    );
  }

  const failed = results.filter((result) => result.status === 'failed');
  console.log(
    `\n${results.length - failed.length}/${results.length} smoke checks passed. Artifacts: ${ARTIFACT_DIR}`,
  );
  if (failed.length) process.exitCode = 1;
}

main()
  .catch(async (error) => {
    console.error(error.stack || error);
    process.exitCode = 1;
    await fs.mkdir(ARTIFACT_DIR, { recursive: true });
    await fs.writeFile(path.join(ARTIFACT_DIR, 'setup-error.txt'), error.stack || String(error));
  })
  .finally(async () => {
    await browser?.close();
  });
