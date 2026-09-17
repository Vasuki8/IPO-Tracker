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
const TEST_FILTER = process.env.SMOKE_TEST_FILTER ? new RegExp(process.env.SMOKE_TEST_FILTER, 'i') : null;
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

async function screenshot(page, name, fullPage = true) {
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({
    path: path.join(ARTIFACT_DIR, `${name}.png`),
    fullPage,
    animations: 'disabled',
  });
}

async function run(name, check, viewport = DESKTOP) {
  if (TEST_FILTER && !TEST_FILTER.test(name)) return;
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

  await run('Market activity prioritizes actionable issues and preserves recent sorting', async (page) => {
    // Use explicit lifecycle dates to keep every lifecycle state represented even when
    // a future daily snapshot has no open or upcoming IPOs. The rest of the suite
    // continues to exercise the actual published records.
    const reference = new Date(publicPayload.meta.generatedAt || Date.now());
    reference.setUTCHours(12, 0, 0, 0);
    await page.clock.setFixedTime(reference);
    const date = (offset) => new Date(reference.getTime() + offset * 86400_000).toISOString().slice(0, 10);
    const record = (id, dates) => ({
      ...records[0], id, company: `Controlled ${id}`, profilePath: '',
      status: 'upcoming', openDate: null, closeDate: null, listingDate: null,
      lifecycle: { stage: 'drhp', stageDate: date(-30) }, ...dates,
    });
    const fixtures = [
      record('listed', { openDate: date(-7), closeDate: date(-5), listingDate: date(-3) }),
      record('upcoming-far', { openDate: date(10), closeDate: date(12) }),
      record('open-later', { openDate: date(-1), closeDate: date(2) }),
      record('open-unknown-close', { status: 'open', openDate: date(-3) }),
      record('pipeline', {}),
      record('closed', { openDate: date(-180), closeDate: date(-175) }),
      record('upcoming-near', { openDate: date(1), closeDate: date(3) }),
      record('open-soon', { openDate: date(-2), closeDate: date(0) }),
    ];
    await page.route('**/data/ipos-summary.json', (route) => route.fulfill({
      json: { ...publicPayload, ipos: fixtures },
    }));
    await openDirectory(page);
    assert.equal(await page.locator('#sortFilter').inputValue(), 'activity');
    const expectedActivity = ['open-soon', 'open-later', 'open-unknown-close', 'upcoming-near', 'upcoming-far', 'listed', 'closed', 'pipeline'];
    assert.deepEqual(await rowIds(page), expectedActivity, 'Bidding deadlines and upcoming openings precede closed, listed, and undated issues');
    assert.equal(new URL(page.url()).searchParams.has('sort'), false, 'The default market-activity sort needs no query override');
    await page.locator('#sortFilter').selectOption('recent');
    const expectedRecent = ['upcoming-far', 'upcoming-near', 'open-later', 'open-soon', 'open-unknown-close', 'listed', 'pipeline', 'closed'];
    assert.deepEqual(await rowIds(page), expectedRecent, 'Explicit recent sorting remains chronological');
    assert.equal(new URL(page.url()).searchParams.get('sort'), 'recent');
    await page.reload({ waitUntil: 'networkidle' });
    await ready(page);
    assert.equal(await page.locator('#sortFilter').inputValue(), 'recent');
    assert.deepEqual(await rowIds(page), expectedRecent);
    await page.locator('#clearFilters').click();
    assert.equal(await page.locator('#sortFilter').inputValue(), 'activity');
    assert.deepEqual(await rowIds(page), expectedActivity);
    const today = date(0);
    const listed = records.filter((ipo) => ipo.listingDate && ipo.listingDate <= today && (!ipo.closeDate || ipo.closeDate < today))
      .sort((a, b) => b.listingDate.localeCompare(a.listingDate))[0];
    assert.ok(listed, 'The public dataset contains a completed listing');
    const oldCutoff = new Date(Date.parse(listed.listingDate) - 90 * 86400_000).toISOString().slice(0, 10);
    const oldClosed = records.find((ipo) => !ipo.listingDate && ipo.closeDate && ipo.closeDate < oldCutoff);
    assert.ok(oldClosed, 'The dataset contains a substantially older closed record');
    await page.unroute('**/data/ipos-summary.json');
    await page.route('**/data/ipos-summary.json', (route) => route.fulfill({ json: { ...publicPayload, ipos: [oldClosed, listed] } }));
    await openDirectory(page);
    assert.deepEqual(await rowIds(page), [String(listed.id), String(oldClosed.id)], 'An actual recent listing precedes an actual closed issue at least 90 days older');
    console.log(`  RECENCY ${listed.company} listed ${listed.listingDate} before ${oldClosed.company} closed ${oldClosed.closeDate}`);
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
    assert.equal(await page.locator('#sortFilter').inputValue(), 'activity');
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
    assert.equal(await page.locator('#sortFilter').inputValue(), 'activity');
    assert.equal(
      await page.locator('#tabs [data-status="listed"]').getAttribute('aria-pressed'),
      'true',
    );
    assert.ok(
      (await page.locator('#ipoRows tr').count()) > 0,
      'The overview opens its complete status category',
    );
  });

  await run('Active filter chips remove only the selected filter', async (page) => {
    const oldDate = new Date(Date.now() - 2 * 86400_000).toISOString().slice(0, 10);
    const record = records.find((ipo) => ipo.listingDate && ipo.listingDate < oldDate && ['Mainboard', 'SME'].includes(ipo.board));
    assert.ok(record, 'The actual dataset contains a historical IPO for filter interactions');
    const parameters = {
      q: record.company, board: record.board,
      year: (record.openDate || record.listingDate).slice(0, 4), status: 'listed', sort: 'company',
    };
    const keys = { search: 'q', board: 'board', year: 'year', activeStatus: 'status', sort: 'sort' };
    for (const [key, parameter] of Object.entries(keys)) {
      await openDirectory(page, '?' + new URLSearchParams(parameters));
      assert.deepEqual(await page.locator('#activeFilters [data-clear-filter]').evaluateAll((buttons) => buttons.map((button) => button.dataset.clearFilter).sort()), Object.keys(keys).sort());
      await page.locator(`#activeFilters [data-clear-filter="${key}"]`).click();
      const current = new URL(page.url()).searchParams;
      assert.equal(current.has(parameter), false, `${key} removes its query parameter`);
      for (const [other, value] of Object.entries(parameters)) if (other !== parameter) assert.equal(current.get(other), value, `${key} preserves ${other}`);
      assert.equal(await page.locator('#activeFilters [data-clear-filter]').count(), 4);
      assert.equal(await page.evaluate(() => document.activeElement?.matches('#activeFilters [data-clear-filter]')), true, 'Focus moves to a remaining filter chip');
      assert.equal(await page.locator('#search').inputValue(), key === 'search' ? '' : parameters.q);
      assert.equal(await page.locator('#boardFilter').inputValue(), key === 'board' ? 'all' : parameters.board);
      assert.equal(await page.locator('#yearFilter').inputValue(), key === 'year' ? 'all' : parameters.year);
      assert.equal(await page.locator('#sortFilter').inputValue(), key === 'sort' ? 'activity' : 'company');
      assert.equal(await page.locator(`#tabs [data-status="${key === 'activeStatus' ? 'all' : 'listed'}"]`).getAttribute('aria-pressed'), 'true');
      const ids = await rowIds(page);
      await page.reload({ waitUntil: 'networkidle' });
      await ready(page);
      assert.deepEqual(await rowIds(page), ids, `${key} removal survives reload`);
      assert.equal(new URL(page.url()).searchParams.has(parameter), false);
    }
    await openDirectory(page, '?q=' + encodeURIComponent(record.company));
    await page.locator('#activeFilters [data-clear-filter="search"]').click();
    assert.equal(await page.locator('#activeFilters').isVisible(), false);
    assert.equal(await page.locator('#search').evaluate((element) => element === document.activeElement), true, 'Removing the final chip returns focus to search');
  });

  await run('One lot at cap uses published inputs and retains listing-return views', async (page, requests) => {
    const record = records.find((ipo) => Number(ipo.lotSize) > 0 && Number(ipo.priceBand?.max) > 0);
    assert.ok(record, 'The public summary includes a priced IPO with its lot size');
    await openDirectory(page, '?q=' + encodeURIComponent(record.company));
    const row = page.locator('#ipoRows tr[data-id=' + JSON.stringify(String(record.id)) + ']');
    const amount = Number(record.lotSize) * Number(record.priceBand.max);
    assert.equal((await page.locator('#secondaryMetricHeading').textContent()).trim(), '1 lot at cap');
    assert.equal((await row.locator('td[data-label="1 lot at cap"] .metric').textContent()).trim(), `₹${amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`);
    assert.match(await row.locator('td[data-label="1 lot at cap"] .metric-note').textContent(), /shares/);
    assert.equal(fileRequested(requests, 'ipos.json').length, 0, 'Lot pricing uses the public summary without downloading the master dataset');
    const pendingDownload = page.waitForEvent('download');
    await page.locator('#exportCsv').click();
    const csv = await fs.readFile(await (await pendingDownload).path(), 'utf8');
    const rows = csv.replace(/^\uFEFF/, '').split('\r\n').map((line) => [...line.matchAll(/(?:^|,)(?:"((?:[^"]|"")*)"|([^,]*))/g)]);
    const headers = rows[0].map((cell) => (cell[1] ?? cell[2]).replace(/""/g, '"'));
    const costColumn = headers.indexOf('One lot at cap INR');
    const lotColumn = headers.indexOf('Lot size shares');
    assert.ok(costColumn >= 0 && lotColumn >= 0, 'The exported lot size and amount have explicit labels');
    const exported = rows.slice(1).find((cells) => cells[0]?.[1]?.replace(/""/g, '"') === record.company && cells[1]?.[1] === (record.symbol || ''));
    assert.ok(exported);
    assert.equal(exported[costColumn][2], String(amount), 'The exported lot cost remains numeric');
    assert.equal(exported[lotColumn][2], String(record.lotSize));
    await page.locator('#sortFilter').selectOption('return');
    assert.equal((await page.locator('#secondaryMetricHeading').textContent()).trim(), 'Listing return');
    assert.equal(await row.locator('td[data-label="Listing return"]').count(), 1);
    await page.locator('#clearFilters').click();
    await page.locator('#tabs [data-status="listed"]').click();
    assert.equal((await page.locator('#secondaryMetricHeading').textContent()).trim(), 'Listing return');
    assert.equal(await page.locator('#ipoRows td[data-label="1 lot at cap"]').count(), 0);
    await page.locator('#tabs [data-status="all"]').click();
    assert.equal((await page.locator('#secondaryMetricHeading').textContent()).trim(), '1 lot at cap');
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
    const headers = parse(rows[0]).map((cell) => (cell[1] ?? cell[2]).replace(/""/g, '"'));
    const gainColumn = headers.indexOf('Listing gain percent');
    assert.ok(gainColumn >= 0, 'The CSV retains a labeled listing-return column');
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
      data[gainColumn][2],
      String(record.listing.gainPct),
      'Negative numeric returns are not changed into apostrophe-prefixed text',
    );
    assert.equal(Number(data[gainColumn][2]), record.listing.gainPct);
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

  await run('Profile watchlist persists and synchronizes with other tabs and quick view', async (page) => {
    const record = records.find((ipo) => ipo.id === 'veegaland');
    assert.ok(record?.profilePath);
    await page.goto(url(record.profilePath), { waitUntil: 'networkidle' });
    const save = page.locator('#companyPage .company-watchlist-button');
    await save.waitFor();
    assert.equal(await save.getAttribute('aria-pressed'), 'false');
    await save.click();
    assert.equal(await save.getAttribute('aria-pressed'), 'true');
    assert.equal(await save.getAttribute('aria-label'), 'Remove from watchlist');
    assert.deepEqual(await page.evaluate(() => JSON.parse(localStorage.getItem('ipoTrackerWatchlist'))), [String(record.id)]);
    await page.reload({ waitUntil: 'networkidle' });
    await page.locator('#companyPage .company-watchlist-button[aria-pressed="true"]').waitFor();
    const other = await page.context().newPage();
    const otherErrors = [];
    other.on('pageerror', (error) => otherErrors.push(String(error)));
    try {
      await other.goto(url(record.profilePath), { waitUntil: 'networkidle' });
      const otherSave = other.locator('.company-watchlist-button');
      assert.equal(await otherSave.getAttribute('aria-pressed'), 'true');
      await otherSave.click();
      await page.locator('#companyPage .company-watchlist-button[aria-pressed="false"]').waitFor();
      await page.goto(url('?view=watchlist'), { waitUntil: 'networkidle' });
      await page.locator('#freshness.loaded').waitFor();
      assert.equal(await page.locator('#ipoRows tr').count(), 0);
      await otherSave.click();
      await page.locator('#ipoRows tr').first().waitFor();
      assert.deepEqual(await rowIds(page), [String(record.id)], 'An actual storage event adds the saved IPO in an already-open watchlist tab');
      await page.locator('#ipoRows [data-action="preview"]').click();
      await page.locator('#detailDialog[open] .company-watchlist-button[aria-pressed="true"]').waitFor();
      await page.locator('#detailDialog .company-watchlist-button').click();
      assert.equal(await page.locator('#detailDialog .company-watchlist-button').getAttribute('aria-pressed'), 'false');
      assert.equal(await page.locator('#ipoRows tr').count(), 0, 'Removing the IPO inside quick view updates the underlying watchlist');
      assert.equal((await page.locator('#watchlistCount').textContent()).trim(), '0');
      await other.locator('.company-watchlist-button[aria-pressed="false"]').waitFor();
      await page.keyboard.press('Escape');
      await page.locator('#detailDialog').waitFor({ state: 'hidden' });
      await page.waitForFunction(() => document.activeElement?.id === 'emptyReset');
      assert.equal(await page.locator('#emptyReset').evaluate((element) => element === document.activeElement), true, 'Closing quick view restores useful focus after its original row is removed');
      await page.reload({ waitUntil: 'networkidle' });
      await page.locator('#freshness.loaded').waitFor();
      assert.equal(await page.locator('#ipoRows tr').count(), 0);
      assert.deepEqual(await page.evaluate(() => JSON.parse(localStorage.getItem('ipoTrackerWatchlist'))), []);
      assert.deepEqual(otherErrors, [], 'The synchronized profile tab has no uncaught errors');
    } finally {
      await other.close();
    }
  });

  await run('Unavailable watchlist storage reports visit-only saves', async (page) => {
    await page.addInitScript(() => {
      const original = Storage.prototype.setItem;
      Storage.prototype.setItem = function (key, value) {
        if (key === 'ipoTrackerWatchlist') throw new DOMException('Controlled storage denial', 'SecurityError');
        return original.call(this, key, value);
      };
    });
    const record = records.find((ipo) => ipo.id === 'veegaland');
    await page.goto(url(record.profilePath), { waitUntil: 'networkidle' });
    const save = page.locator('#companyPage .company-watchlist-button');
    await save.click();
    assert.equal(await save.getAttribute('aria-pressed'), 'true');
    assert.match(await page.locator('#companyPage .company-save-status').textContent(), /visit only.*could not store/i);
    assert.equal(await page.evaluate(() => localStorage.getItem('ipoTrackerWatchlist')), null);
    await page.reload({ waitUntil: 'networkidle' });
    await page.locator('#companyPage .company-watchlist-button[aria-pressed="false"]').waitFor();
    await openDirectory(page, '?q=' + encodeURIComponent(record.company));
    await page.locator('#ipoRows [data-action="preview"]').click();
    await page.locator('#detailDialog[open] .company-watchlist-button').click();
    assert.equal(await page.locator('#detailDialog .company-watchlist-button').getAttribute('aria-pressed'), 'true');
    assert.match(await page.locator('#detailDialog .company-save-status').textContent(), /visit only.*could not store/i);
    assert.equal((await page.locator('#watchlistCount').textContent()).trim(), '1');
    await page.keyboard.press('Escape');
    await page.locator('#detailDialog').waitFor({ state: 'hidden' });
    await navigate(page, 'watchlist');
    assert.deepEqual(await rowIds(page), [String(record.id)], 'A denied write still supports a truthful temporary watchlist for this visit');
    await page.reload({ waitUntil: 'networkidle' });
    await page.locator('#freshness.loaded').waitFor();
    assert.equal(await page.locator('#ipoRows tr').count(), 0, 'A visit-only save is not falsely reported as persisted after reload');
  });

  await run('Condensed documents preserve source links and complete original titles', async (page) => {
    const record = records.find((ipo) => ipo.id === 'veegaland');
    await page.goto(url(record.profilePath), { waitUntil: 'networkidle' });
    await page.locator('#companyPage .company-profile').waitFor();
    const profile = JSON.parse(await page.locator('#ipo-profile-data').textContent()).ipo;
    const expectedLinks = [...new Set((profile.documents || []).filter((doc) => /^https?:\/\//i.test(doc.url || '')).map((doc) => new URL(doc.url).href))].sort();
    const shownLinks = await page.locator('#company-documents a.company-document-link').evaluateAll((links) => [...new Set(links.map((link) => link.href))].sort());
    assert.deepEqual(shownLinks, expectedLinks, 'Condensing the presentation retains every original document source URL');
    const longest = [...(profile.documents || [])].sort((a, b) => (b.title || '').length - (a.title || '').length)[0];
    assert.ok(longest?.title && longest.title.replace(/\s+/g, ' ').trim().length > 140, 'The actual profile contains a long scraped title for this regression');
    const disclosures = page.locator('#company-documents details.company-document-title');
    const index = await disclosures.evaluateAll((nodes, title) => nodes.findIndex((node) => node.querySelector('p')?.textContent === title), longest.title);
    assert.ok(index >= 0, 'The full original title is retained in a native disclosure');
    const details = disclosures.nth(index);
    assert.equal(await details.evaluate((element) => element.open), false);
    assert.equal(await details.locator('p').isVisible(), false);
    await page.locator('[data-company-target="company-documents"]').click();
    await page.screenshot({ path: path.join(ARTIFACT_DIR, 'mobile-390-condensed-documents-viewport.png'), fullPage: false, animations: 'disabled' });
    await details.locator('summary').click();
    assert.equal(await details.evaluate((element) => element.open), true);
    assert.equal(await details.locator('p').textContent(), longest.title);
    await noOverflow(page, 'Expanded original document title at390px');
    await details.locator('summary').click();
    assert.equal(await details.evaluate((element) => element.open), false);
    console.log(`  DOCUMENT ${longest.title.length} original characters retained behind a closed disclosure; ${expectedLinks.length} source URLs preserved`);
  }, { width: 390, height: 844 });

  await run('Profiles with limited data retain useful mobile layouts', async (page) => {
    const candidates = records.filter((ipo) => ipo.profilePath && !ipo.priceBand && !ipo.issueSizeCr && ipo.subscription?.total == null && !(ipo.documents || []).length)
      .sort((a, b) => Number(a.sourceCount || 0) - Number(b.sourceCount || 0));
    let selected;
    for (const candidate of candidates.slice(0, 8)) {
      await page.goto(url(candidate.profilePath), { waitUntil: 'networkidle' });
      await page.locator('#companyPage .company-profile').waitFor();
      if (await page.locator('.company-profile-sparse').count()) { selected = candidate; break; }
    }
    assert.ok(selected, 'The current dataset includes a profile with limited data');
    const profile = JSON.parse(await page.locator('#ipo-profile-data').textContent()).ipo;
    const actualSources = profile.sources || (profile.source ? [profile.source] : []);
    if (!actualSources.length) {
      assert.ok((await page.locator('.validation').allTextContents()).every((text) => !/^1 source$/i.test(text.trim())), 'A profile without attached sources does not claim one source');
    }
    for (const width of [390, 320]) {
      await page.setViewportSize({ width, height: 844 });
      await page.evaluate(() => window.scrollTo(0, 0));
      await noOverflow(page, `Limited-data profile ${width}px`);
      const heading = await page.locator('.company-hero-name').boundingBox();
      assert.ok(heading && heading.x >= 0 && heading.x + heading.width <= width + 1, 'The company name fits its narrow profile');
      await page.screenshot({ path: path.join(ARTIFACT_DIR, `mobile-${width}-limited-profile-viewport.png`), fullPage: false, animations: 'disabled' });
      await page.locator('[data-company-target="company-sources"]').click();
      await noOverflow(page, `Limited-data profile sources ${width}px`);
      assert.equal(await page.locator('#company-sources').isVisible(), true);
    }
    console.log(`  LIMITED PROFILE ${selected.company}: readable at390px and320px`);
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
  await run('Mobile discovery exposes the first result and every status', async (page) => {
    await openDirectory(page);
    for (const width of [390, 320]) {
      await page.setViewportSize({ width, height: 844 });
      await page.evaluate(() => window.scrollTo(0, 0));
      const firstRow = await page.locator('#ipoRows tr').first().boundingBox();
      assert.ok(firstRow, 'The mobile directory has a visible first result');
      await page.screenshot({ path: path.join(ARTIFACT_DIR, `mobile-${width}-directory-viewport.png`), fullPage: false, animations: 'disabled' });
      if (width === 390) assert.ok(firstRow.y <= 550, `The first 390px result starts at ${Math.round(firstRow.y)}px, beyond the 550px discovery target`);
      const filterLabels = await page.locator('.filter-controls select').evaluateAll((selects) => {
        const context = document.createElement('canvas').getContext('2d');
        return selects.map((select) => {
          const style = getComputedStyle(select);
          context.font = `${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
          const label = select.selectedOptions[0].label;
          return {
            label,
            textWidth: context.measureText(label).width,
            availableWidth: select.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight),
          };
        });
      });
      assert.equal(filterLabels.length, 3, 'Board, year, and sort controls remain available');
      for (const { label, textWidth, availableWidth } of filterLabels) {
        assert.ok(textWidth <= availableWidth + 1,
          `The selected label "${label}" needs ${textWidth.toFixed(1)}px but has only ${availableWidth.toFixed(1)}px at ${width}px`);
      }
      console.log(`  FILTER FIT ${width}px: ${filterLabels.map(({ label, textWidth, availableWidth }) => `${label} ${textWidth.toFixed(1)}/${availableWidth.toFixed(1)}px`).join(', ')}`);
      const controls = page.locator('#tabs [data-status]');
      assert.equal(await controls.count(), 6, 'All six status choices remain available');
      for (const status of ['all', 'open', 'upcoming', 'closed', 'listed', 'pipeline']) {
        const button = page.locator(`#tabs [data-status="${status}"]`);
        const rect = await button.boundingBox();
        assert.ok(rect && rect.x >= -1 && rect.x + rect.width <= width + 1 && rect.y >= 0 && rect.y + rect.height <= 844,
          `${status} is fully visible without horizontal scrolling at ${width}px`);
      }
      for (const status of ['open', 'upcoming', 'closed', 'listed', 'pipeline', 'all']) {
        const button = page.locator(`#tabs [data-status="${status}"]`);
        await button.click();
        assert.equal(await button.getAttribute('aria-pressed'), 'true', `${status} can be selected at ${width}px`);
        assert.equal(await page.locator('#tabs [aria-pressed="true"]').count(), 1);
      }
      const assertDirectoryHeadingClear = async (action) => {
        const heading = await page.locator('#directoryTitle').boundingBox();
        const header = await page.locator('.dashboard-topbar').boundingBox();
        assert.ok(heading && header && heading.y >= header.y + header.height - 1 && heading.y < 844,
          `${action} leaves the directory heading visible below the sticky header at ${width}px`);
      };
      await page.locator('#nextPage').click();
      await assertDirectoryHeadingClear('Pagination');
      await page.locator('#stats [data-stat-status="listed"]').click();
      await assertDirectoryHeadingClear('Market overview navigation');
      await page.locator('#tabs [data-status="all"]').click();
      await page.locator('#ipoRows tr').last().scrollIntoViewIfNeeded();
      const jump = page.locator('#jumpToSearch');
      const jumpRect = await jump.boundingBox();
      assert.ok(jumpRect && jumpRect.y >= 0 && jumpRect.y + jumpRect.height <= 844, 'The search shortcut remains on screen deep in the directory');
      await jump.click();
      assert.equal(await page.locator('#search').evaluate((element) => element === document.activeElement), true, 'The search shortcut focuses the search field');
      const searchRect = await page.locator('#search').boundingBox();
      assert.ok(searchRect && searchRect.y >= 0 && searchRect.y + searchRect.height <= 844, 'The focused search field is visible');
      await noOverflow(page, `mobile discovery ${width}px`);
      console.log(`  DISCOVERY ${width}px: first result ${Math.round(firstRow.y)}px, all six status choices visible and clickable`);
    }
  }, { width: 390, height: 844 });
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
        await screenshot(page, `${label}-directory-viewport`, false);
        const profileHref = await page
          .locator('#ipoRows .company-name-link')
          .first()
          .getAttribute('href');
        await navigate(page, 'calendar');
        await page.goto(url(`?view=calendar&month=${calendarMonth}`), { waitUntil: 'networkidle' });
        await page.locator('#calendarEvents .calendar-day').first().waitFor();
        await noOverflow(page, `${label} calendar`);
        await screenshot(page, `${label}-calendar`);
        await screenshot(page, `${label}-calendar-viewport`, false);
        await navigate(page, 'quality');
        await page.locator('#qualityDashboard .quality-panel').waitFor();
        await noOverflow(page, `${label} data and sources`);
        await screenshot(page, `${label}-quality`);
        await screenshot(page, `${label}-quality-viewport`, false);
        await page.goto(url(profileHref), { waitUntil: 'networkidle' });
        await page.locator('#companyPage .company-profile').waitFor();
        await noOverflow(page, `${label} company profile`);
        await screenshot(page, `${label}-profile`);
        await screenshot(page, `${label}-profile-viewport`, false);
      },
      viewport,
    );
  }

  const failed = results.filter((result) => result.status === 'failed');
  assert.ok(results.length, 'The smoke test filter must select at least one check');
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
