// User-facing regressions use synthetic fixed fixtures and controlled date boundaries.
import assert from "node:assert/strict";
import { productDataset } from "./fixtures/browser-data.mjs";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { readFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const root = fileURLToPath(new URL("../", import.meta.url));
const data = productDataset();
const server = createServer(async (req, res) => {
  try {
    const pathname = new URL(req.url, "http://localhost").pathname;
    if (pathname === "/data/ipos.json") { res.writeHead(200, {"Content-Type":"application/json"}).end(JSON.stringify(data)); return; }
    const file = path.resolve(root, "." + (pathname === "/" ? "/index.html" : pathname));
    if (!file.startsWith(root)) { res.writeHead(403).end(); return; }
    const types = { ".js": "text/javascript", ".css": "text/css", ".html": "text/html", ".json": "application/json", ".svg": "image/svg+xml" };
    res.writeHead(200, { "Content-Type": types[path.extname(file)] || "application/octet-stream" });
    res.end(await readFile(file));
  } catch { res.writeHead(404).end(); }
});
await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
const base = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ headless: true });
const failures = [];
const verified = value => ({ value, status: "verified", evidence: [], corrections: [] });
async function check(name, run) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.clock.install({ time: new Date("2026-09-30T12:00:00Z") });
  async function home() { await page.goto(base); await page.waitForSelector("#results:not([hidden])"); }
  async function detail(id) { await page.goto(`${base}/#ipo/${id}`); await page.waitForSelector("#detailView:not([hidden])"); }
  async function screenshot(file) {
    if (!process.env.UI_SCREENSHOT_DIR) return;
    await mkdir(process.env.UI_SCREENSHOT_DIR, { recursive: true });
    await page.screenshot({ path: path.join(process.env.UI_SCREENSHOT_DIR, file), fullPage: true });
  }
  try { await run({page, home, detail, screenshot}); assert.deepEqual(errors, []); console.log(`PASS ${name}`); }
  catch (error) { failures.push(name); console.error(`FAIL ${name}: ${error.message}`); }
  finally { await page.close(); }
}
try {
  await check("Open now excludes expired offers and preserves reported status evidence", async ({page, home, detail, screenshot}) => {
    await home();
    assert.equal(await page.locator("#metricOpen").textContent(), "6");
    await page.locator('[data-metric="open"]').click();
    assert.equal(await page.locator("#ipoRows tr").count(), 6);
    assert.doesNotMatch(await page.locator("#ipoRows").textContent(), /Fixture Expired/);
    await screenshot("open-now-fixed.png");
    await detail("fixture-expired");
    assert.match(await page.locator("#detailStatus").textContent(), /Bidding closed/);
    assert.match(await page.locator("#detailStatusNote").textContent(), /22 Sept 2026/);
    assert.match(await page.locator("#detailStatusNote").textContent(), /reported Open/i);
    assert.match(await page.locator("#evidenceList").textContent(), /Reported lifecycle status/);
    assert.equal(await page.locator("#detailStatus .status--listed").count(), 0);
    await screenshot("axiom-fixed.png");
  });
  await check("Status uses verified dates and Indian market day without inferring listing", async ({page, home}) => {
    const original = data.records.find(r => r.id === "fixture-expired");
    const fixture = (id, status, opening, closing, closeStatus = "verified") => ({...structuredClone(original), id, issuer_name:id, status,
      open_date:verified(opening), close_date:{...verified(closing),status:closeStatus}});
    const records = [
      fixture("closed-yesterday", "open", "2026-09-20", "2026-09-29"),
      fixture("closes-today", "open", "2026-09-20", "2026-09-30"),
      fixture("future-opening", "open", "2026-10-01", "2026-10-03"),
      fixture("unresolved-close", "open", "2026-09-20", "2026-09-29", "conflict"),
      fixture("reported-listed", "listed", "2026-09-20", "2026-09-29"),
    ];
    await page.route("**/data/ipos.json", route => route.fulfill({json:{...data,records}}));
    await home();
    assert.equal(await page.locator("#metricOpen").textContent(), "2");
    assert.equal(await page.locator("#metricUpcoming").textContent(), "1");
    assert.equal(await page.locator("#metricListed").textContent(), "1");
    await page.clock.setFixedTime(new Date("2026-09-30T19:00:00Z")); // Already 1 October in India.
    await page.reload(); await page.waitForSelector("#results:not([hidden])");
    assert.equal(await page.locator("#metricOpen").textContent(), "2");
    await page.locator('[data-metric="open"]').click();
    assert.doesNotMatch(await page.locator("#ipoRows").textContent(), /closes-today/);
    assert.match(await page.locator("#ipoRows").textContent(), /future-opening/);
  });
  await check("Pricing disagreement is visible in list, detail and evidence coverage", async ({page, home, detail, screenshot}) => {
    await home(); await page.locator("#searchInput").fill("Fixture Price Conflict");
    assert.match(await page.locator("#ipoRows tr").textContent(), /Price conflict/);
    await detail("fixture-price-conflict");
    assert.match(await page.locator("#detailPrice").textContent(), /Price conflict/);
    assert.equal(await page.locator("#detailCoverage").textContent(), "Conflict");
    assert.match(await page.locator("#detailPriceNote").textContent(), /₹60/);
    assert.match(await page.locator("#detailPriceNote").textContent(), /₹131–₹138/);
    const priceRows = page.locator("#evidenceList details").filter({hasText:/^(Price band|Final issue price)/});
    assert.equal(await priceRows.count(), 2);
    assert.ok((await priceRows.locator("summary").allTextContents()).every(text=>text.includes("Conflict")));
    await screenshot("pricing-fixed.png");
  });
  await check("Open tabs refresh bidding status across Indian midnight without navigation", async ({page, home, detail}) => {
    await page.clock.setSystemTime(new Date("2026-09-30T18:29:00Z"));
    await home();
    await page.locator('[data-metric="open"]').click();
    assert.equal(await page.locator("#metricOpen").textContent(), "6");
    await page.clock.runFor(120000);
    assert.equal(await page.locator("#metricOpen").textContent(), "4");
    assert.equal(await page.locator("#ipoRows tr").count(), 4);
    assert.doesNotMatch(await page.locator("#ipoRows").textContent(), /Fixture Closes Today/);
    await page.clock.setSystemTime(new Date("2026-09-30T18:29:00Z"));
    const closing = data.records.find(r=>r.status==="open" && r.close_date?.value==="2026-09-30");
    assert.ok(closing);
    await detail(closing.id);
    assert.equal(await page.locator("#detailStatus").textContent(), "Open");
    await page.locator("#evidenceList summary").first().click();
    await page.clock.runFor(120000);
    assert.match(await page.locator("#detailStatus").textContent(), /Bidding closed/);
    assert.match(await page.locator("#detailStatusNote").textContent(), /reported Open/);
    assert.equal(await page.locator("#evidenceList details").first().getAttribute("open"), "");
    for (const event of ["focus", "visibilitychange"]) {
      await page.clock.setSystemTime(new Date("2026-09-30T18:29:00Z"));
      await home();
      assert.equal(await page.locator("#metricOpen").textContent(), "6");
      await page.clock.setSystemTime(new Date("2026-10-01T01:00:00Z"));
      await page.evaluate(name => (name === "focus" ? window : document).dispatchEvent(new Event(name)), event);
      assert.equal(await page.locator("#metricOpen").textContent(), "4", `${event} refreshes a resumed tab`);
    }
  });
  await check("Compatible prices and missing final prices do not acquire a false conflict", async ({page, home}) => {
    const original = data.records.find(r=>r.id === "fixture-price-conflict");
    const records = [131,138,null].map((value,i)=>({...structuredClone(original),id:`price-${i}`,issuer_name:`price-${i}`,issue_price: value==null ? {value:null,status:"missing"} : verified(value)}));
    await page.route("**/data/ipos.json",route=>route.fulfill({json:{...data,records}}));
    await home();
    assert.doesNotMatch(await page.locator("#ipoRows").textContent(), /Price conflict/);
  });
  await check("Trading lot and minimum IPO bid are labelled and both accessible", async ({page, home, detail, screenshot}) => {
    await detail("fixture-trading-lot");
    assert.equal(await page.locator("#detailLotLabel").textContent(), "Trading lot");
    assert.equal(await page.locator("#detailLot").textContent(), "1 share");
    const minimum = page.locator("#evidenceList details").filter({has:page.locator("summary",{hasText:"Minimum IPO bid"})});
    assert.match(await minimum.locator("summary").textContent(), /150 shares.*Verified/);
    await screenshot("lot-quantities-fixed.png");
    await detail("fixture-price-conflict");
    assert.equal(await page.locator("#detailLotLabel").textContent(), "Minimum IPO bid");
    await home(); await page.locator("#searchInput").fill("Fixture Trading Lot");
    assert.match(await page.locator("#ipoRows").textContent(), /Trading lot/);
    await page.setViewportSize({width:390,height:844});
    assert.match(await page.locator("#mobileCards").textContent(), /Trading lot/);
  });
  await check("Company search advertises the available capability", async ({page, home}) => {
    await home();
    assert.equal(await page.locator("#searchInput").getAttribute("placeholder"), "Search a company…");
    assert.doesNotMatch(await page.locator("label.search").textContent(), /sector/i);
    await page.locator("#searchInput").fill("Fixture Bank");
    assert.match(await page.locator("#ipoRows").textContent(), /Fixture Bank/);
  });
  await check("Unclassified boards remain discoverable and filter survives reload", async ({page, home, screenshot}) => {
    await home();
    const unknown=data.records.filter(r=>!["mainboard","sme"].includes(String(r.board||"").toLowerCase()));
    assert.equal(await page.locator('[data-board="unknown"]').count(),1);
    await page.locator('[data-board="unknown"]').click();
    assert.match(await page.locator("#resultCount").textContent(),new RegExp(`of ${unknown.length} IPOs`));
    assert.ok((await page.locator("#ipoRows .company-meta").allTextContents()).every(text=>text.startsWith("Board unavailable")));
    assert.match(await page.locator("#filterSummary").textContent(),/Board unavailable/);
    await page.reload(); await page.waitForSelector("#results:not([hidden])");
    assert.equal(await page.locator('[data-board="unknown"]').getAttribute("aria-pressed"),"true");
    await screenshot("board-unavailable-fixed.png");
    for(const width of [320,390,820,1440]){
      await page.setViewportSize({width,height:844});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`Overflow at ${width}px`);
    }
  });
  assert.deepEqual(failures, [], "All product logic journeys must pass");
} finally { await browser.close(); await new Promise(resolve=>server.close(resolve)); }
