// Browser regression checks. Requires Playwright + Chromium in the test environment.
// Run: node scripts/test-ui.mjs (UI_SCREENSHOT_DIR optionally retains previews).
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { readFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const root = fileURLToPath(new URL("../", import.meta.url));
const data = JSON.parse(
  await readFile(path.join(root, "data/ipos.json"), "utf8"),
);
const sourceRecord = data.records.find(
  (row) => row.price_band?.evidence?.length && row.documents?.length,
);
const groupedRecord = data.records.find(
  (row) =>
    row.documents?.some((doc) =>
      /sebi|prospectus|issuer/i.test(doc.type || ""),
    ) && row.documents?.some((doc) => /nse|bse|exchange/i.test(doc.type || "")),
);
assert.ok(
  sourceRecord,
  "Published corpus must retain at least one price-band source for browser checks",
);
const server = createServer(async (req, res) => {
  try {
    const pathname = new URL(req.url, "http://localhost").pathname;
    const file = path.resolve(
      root,
      "." + (pathname === "/" ? "/index.html" : pathname),
    );
    if (!file.startsWith(root)) {
      res.writeHead(403);
      res.end();
      return;
    }
    const content = await readFile(file);
    const types = {
      ".js": "text/javascript",
      ".css": "text/css",
      ".html": "text/html",
      ".json": "application/json",
      ".svg": "image/svg+xml",
    };
    res.writeHead(200, {
      "Content-Type": types[path.extname(file)] || "application/octet-stream",
    });
    res.end(content);
  } catch {
    res.writeHead(404);
    res.end();
  }
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const base = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const screenshotDir = process.env.UI_SCREENSHOT_DIR;
async function screenshot(name, fullPage = false) {
  if (screenshotDir) {
    await mkdir(screenshotDir, { recursive: true });
    await page.screenshot({ path: path.join(screenshotDir, name), fullPage });
  }
}
async function loaded() {
  await page.waitForSelector("#results:not([hidden])");
}
try {
  await page.goto(base);
  await loaded();
  assert.equal(
    await page.locator("#ipoRows tr").count(),
    Math.min(20, data.records.length),
  );
  assert.equal(
    await page.locator("#metricTotal").textContent(),
    data.records.length.toLocaleString("en-IN"),
  );
  assert.equal(
    await page.locator("#ipoRows .company-name").first().textContent(),
    data.records[0].issuer_name,
  );
  await screenshot("ipo-desktop.png");
  if (data.records.length > 20) {
    await page.locator("#nextPage").click();
    assert.equal(
      await page.locator("#pageLabel").textContent(),
      `2 / ${Math.ceil(data.records.length / 20)}`,
    );
    await page.locator("#previousPage").click();
  }
  await page.locator("#searchInput").fill(sourceRecord.issuer_name);
  assert.equal(await page.locator("#ipoRows tr").count(), 1);
  await page.locator("#ipoRows .company-name").first().click();
  await page.waitForSelector("#detailView:not([hidden])");
  assert.equal(
    await page.locator("#detailName").textContent(),
    sourceRecord.issuer_name,
  );
  assert.equal(
    await page.locator("#documentList .document").count(),
    sourceRecord.documents.length,
  );
  await page.locator("#evidenceList summary").first().click();
  assert.ok(
    (await page
      .locator("#evidenceList details[open] .evidence-source a")
      .count()) > 0,
  );
  await screenshot("ipo-detail.png", true);
  await page.reload();
  await page.waitForSelector("#detailView:not([hidden])");
  assert.equal(
    await page.locator("#detailName").textContent(),
    sourceRecord.issuer_name,
  );
  await page.locator(".back-link").click();
  await page.waitForSelector("#homeView:not([hidden])");
  assert.equal(
    await page.locator("#searchInput").inputValue(),
    sourceRecord.issuer_name,
  );
  await page.locator("#resetFilters").click();
  assert.ok(
    groupedRecord,
    "Corpus should include a record with filing and exchange sources",
  );
  await page.goto(`${base}/#ipo/${encodeURIComponent(groupedRecord.id)}`);
  await page.waitForSelector("#detailView:not([hidden])");
  assert.equal(
    await page.locator("#documentList .document").count(),
    groupedRecord.documents.length,
  );
  assert.equal(await page.locator(".document-group").count(), 2);
  const filingCount = groupedRecord.documents.filter((doc) =>
    /sebi|prospectus|issuer/i.test(doc.type || ""),
  ).length;
  await page.locator('[data-document-category="filings"]').click();
  assert.equal(
    await page.locator("#documentList .document").count(),
    filingCount,
  );
  assert.equal(
    await page
      .locator('[data-document-category="filings"]')
      .getAttribute("aria-pressed"),
    "true",
  );
  assert.equal(
    new URL(page.url()).hash,
    `#ipo/${encodeURIComponent(groupedRecord.id)}`,
  );
  await page.locator('[data-document-category="all"]').click();
  assert.equal(
    await page.locator("#documentList .document").count(),
    groupedRecord.documents.length,
  );
  await page.locator('[data-detail-section="documents"]').click();
  assert.equal(
    new URL(page.url()).hash,
    `#ipo/${encodeURIComponent(groupedRecord.id)}`,
  );
  await page.locator(".back-link").click();
  await page.waitForSelector("#homeView:not([hidden])");
  await page.locator('#boardFilter [data-board="sme"]').click();
  assert.ok(
    (await page.locator("#ipoRows .company-meta").allTextContents()).every(
      (text) => text.startsWith("SME"),
    ),
  );
  await page.locator("#yearFilter").selectOption("2026");
  await page.locator('#statusFilter [data-status="open"]').click();
  assert.ok(
    (await page.locator("#ipoRows .status").allTextContents()).every(
      (text) => text === "Open",
    ),
  );
  await page.reload();
  await loaded();
  assert.equal(await page.locator("#yearFilter").inputValue(), "2026");
  assert.equal(
    await page.locator('#boardFilter [aria-pressed="true"]').textContent(),
    "SME",
  );
  await page.locator("#searchInput").fill("zzzz-no-issuer-zzzz");
  assert.equal(await page.locator("#emptyState").isVisible(), true);
  await page.locator("#emptyReset").click();
  await page.locator("#sortFilter").selectOption("name");
  const sorted = [...data.records].sort((a, b) =>
    a.issuer_name.localeCompare(b.issuer_name, "en", { sensitivity: "base" }),
  );
  assert.equal(
    await page.locator("#ipoRows .company-name").first().textContent(),
    sorted[0].issuer_name,
  );
  await page.locator("#sortFilter").selectOption("newest");
  await page.keyboard.press("/");
  assert.equal(
    await page
      .locator("#searchInput")
      .evaluate((el) => el === document.activeElement),
    true,
  );
  await page.locator(".primary-nav [data-methodology]").click();
  assert.equal(await page.locator("#sourcesDialog").isVisible(), true);
  await page.keyboard.press("Escape");
  assert.equal(await page.locator("#sourcesDialog").isVisible(), false);
  for (const width of [1440, 1024, 820, 390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      ),
      false,
      `Horizontal page overflow at ${width}px`,
    );
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => scrollTo(0, 0));
  await page.locator("#pageTitle").click();
  await screenshot("ipo-mobile.png");
  assert.equal(await page.locator(".desktop-table").isVisible(), false);
  assert.equal(await page.locator("#mobileCards").isVisible(), true);
  await page.locator("#mobileCards .company-name").first().click();
  await page.waitForSelector("#detailView:not([hidden])");
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
    false,
  );
  await screenshot("ipo-mobile-detail.png", true);
  await page.goBack();
  await page.waitForSelector("#homeView:not([hidden])");

  // Controlled edge cases never enter published data.
  const verified = (value) => ({
    value,
    status: "verified",
    evidence: [
      {
        url: "https://www.sebi.gov.in/",
        document_type: "Test official source",
        publication_date: "2026-09-01",
        collected_at: "2026-09-02T10:00:00Z",
      },
    ],
    corrections: [],
  });
  const missing = {
    value: null,
    status: "missing",
    evidence: [],
    corrections: [],
  };
  const complete = {
    ...structuredClone(data.records[0]),
    id: "ui-complete",
    issuer_name:
      "A test issuer with an exceptionally long company name for responsive layout <script>window.injected=true</script>",
    price_band: verified({ min: 99.25, max: 101.75 }),
    issue_price: missing,
    market_lot: verified(10),
    minimum_bid_quantity: missing,
    issue_size_inr: verified(50000000),
    open_date: verified("2026-09-20"),
    close_date: verified("2026-09-23"),
    listing_date: verified("2026-09-28"),
  };
  const conflict = {
    ...structuredClone(complete),
    id: "ui-conflict",
    issuer_name: "B conflict fixture",
    market_lot: { ...verified(10), status: "conflict" },
    minimum_bid_quantity: verified(20),
  };
  const provisional = {
    ...structuredClone(complete),
    id: "ui-provisional",
    issuer_name: "C provisional fixture",
    price_band: { ...verified({ min: 10, max: 20 }), status: "provisional" },
  };
  const absent = {
    ...structuredClone(complete),
    id: "ui-missing",
    issuer_name: "D missing fixture",
    price_band: missing,
    issue_price: missing,
    market_lot: missing,
    minimum_bid_quantity: missing,
    issue_size_inr: missing,
    open_date: missing,
    close_date: missing,
    listing_date: missing,
    documents: [],
    status: null,
  };
  complete.documents = [
    {
      type: "Unsafe URL fixture",
      url: "javascript:alert(1)",
      publication_date: null,
    },
  ];
  await page.route("**/data/ipos.json", (route) =>
    route.fulfill({
      json: { ...data, records: [complete, conflict, provisional, absent] },
    }),
  );
  await page.goto(base);
  await loaded();
  assert.match(await page.locator("#ipoRows").textContent(), /₹99.25–₹101.75/);
  assert.match(
    await page.locator("#ipoRows tr").nth(0).textContent(),
    /Complete/,
  );
  assert.match(
    await page.locator("#ipoRows tr").nth(1).textContent(),
    /Conflict/,
  );
  assert.match(
    await page.locator("#ipoRows tr").nth(2).textContent(),
    /Provisional/,
  );
  assert.match(
    await page.locator("#ipoRows tr").nth(3).textContent(),
    /Status unavailable/,
  );
  assert.equal(await page.evaluate(() => window.injected), undefined);
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      ),
      false,
    );
  }
  await page.locator("#mobileCards .company-name").first().click();
  await page.waitForSelector("#detailView:not([hidden])");
  assert.equal(await page.locator("#documentList a").count(), 0);
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
    false,
  );
  await page.goto(`${base}/#ipo/ui-conflict`);
  await page.waitForSelector("#detailView:not([hidden])");
  assert.equal(await page.locator("#detailLot").textContent(), "20 shares");
  assert.match(
    await page.locator("#evidenceList").textContent(),
    /Market lot evidence/,
  );
  assert.match(
    await page.locator("#evidenceList").textContent(),
    /This unresolved quantity is not used/,
  );
  await page.goto(`${base}/#ipo/ui-missing`);
  await page.waitForSelector("#detailView:not([hidden])");
  assert.equal(await page.locator("#detailPrice").textContent(), "—");
  assert.match(
    await page.locator("#documentList").textContent(),
    /No source documents/,
  );
  await page.unroute("**/data/ipos.json");
  await page.route("**/data/ipos.json", (route) =>
    route.fulfill({ status: 503, body: "Unavailable" }),
  );
  await page.goto(base);
  await page.waitForSelector("#errorState:not([hidden])");
  assert.equal(await page.locator("#results").isVisible(), false);
  await page.unroute("**/data/ipos.json");
  await page.locator("#retryLoad").click();
  await loaded();
  await page.route("**/data/ipos.json", (route) =>
    route.fulfill({ json: { records: [] } }),
  );
  await page.goto(base);
  await loaded();
  assert.match(
    await page.locator("#emptyTitle").textContent(),
    /No IPO records/,
  );
  await page.unroute("**/data/ipos.json");
  await page.route("**/data/ipos.json", (route) =>
    route.fulfill({ json: { wrong: [] } }),
  );
  await page.goto(base);
  await page.waitForSelector("#errorState:not([hidden])");
  assert.deepEqual(errors, []);
  console.log(
    "UI browser checks passed: real data, filters, pagination, direct links/back, source evidence, mobile 320–1440px, fractional prices, missing/provisional/conflict, escaping, invalid URLs, loading/error/retry/empty.",
  );
} finally {
  await browser.close();
  server.close();
}
