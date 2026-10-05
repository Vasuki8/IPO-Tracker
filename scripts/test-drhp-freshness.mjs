// Browser regressions for distinct source, lifecycle, and refresh-report freshness.
// Run with PLAYWRIGHT_MODULE pointing at a configured Playwright installation if needed.
import assert from "node:assert/strict";
import { draftDataset, productDataset, failedDraftHealth } from "./fixtures/browser-data.mjs";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const root = path.resolve(fileURLToPath(new URL("../", import.meta.url)));
const sourceData = draftDataset();
const ipoData = productDataset();
const healthData = failedDraftHealth();
const timestamp = value => new Date(value).toLocaleString("en-GB", {
  day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "UTC",
}) + " UTC";
const server = createServer(async (request, response) => {
  try {
    const pathname = new URL(request.url, "http://localhost").pathname;
    const file = path.resolve(root, "." + pathname);
    if (!file.startsWith(root + path.sep)) { response.writeHead(403).end(); return; }
    const content = await readFile(file);
    const types = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml" };
    response.writeHead(200, { "Content-Type": types[path.extname(file)] || "application/octet-stream" }).end(content);
  } catch { response.writeHead(404).end(); }
});
await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
let browser;
const passed = [];
try {
  browser = await chromium.launch({ headless: true });
  async function scenario(name, { source = sourceData, ipo = ipoData, health = healthData } = {}, check) {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    const errors = [];
    page.on("pageerror", error => errors.push(error.message));
    await page.route("**/data/drhp-filings.json", route => route.fulfill({ json: source }));
    await page.route("**/data/ipos.json", route => route.fulfill({ json: ipo }));
    await page.route("**/ops/drhp-collection.json", route => health === null
      ? route.fulfill({ status: 404, body: "Unavailable" }) : route.fulfill({ json: health }));
    try {
      await page.goto(`http://127.0.0.1:${server.address().port}/drhp.html`);
      await page.waitForSelector("#drhpResults:not([hidden])");
      await page.waitForFunction(() => !document.querySelector("#drhpRefreshAttempt")?.textContent.includes("Checking"));
      const state = await page.evaluate(() => ({
        source: document.querySelector("#drhpSourceCollected")?.textContent,
        lifecycle: document.querySelector("#drhpLifecycleGenerated")?.textContent,
        attempt: document.querySelector("#drhpRefreshAttempt")?.textContent,
        note: document.querySelector("#drhpIntegrityNote").textContent,
        latestDateBasis: document.querySelector("#drhpLatestDateBasis")?.textContent,
        cardsText: document.querySelector("#drhpCards")?.textContent,
        visibleCompanies: document.querySelectorAll("#drhpCards .drhp-card").length,
      }));
      assert.ok(state.visibleCompanies > 0, "Refresh health must not hide loaded companies");
      await check(state, page);
      for (const selector of ["#drhpSourceCollected", "#drhpLifecycleGenerated", "#drhpRefreshAttempt"]) {
        assert.equal(await page.locator(selector).isVisible(), true, "Each freshness detail must be visible on mobile");
      }
      assert.deepEqual(errors, [], "Freshness rendering must not raise browser errors");
      passed.push(name);
    } finally { await page.close(); }
  }

  async function rejectedLifecycleScenario(name, ipo) {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    const errors = [];
    page.on("pageerror", error => errors.push(error.message));
    await page.route("**/data/drhp-filings.json", route => route.fulfill({ json: sourceData }));
    await page.route("**/data/ipos.json", route => route.fulfill({ json: ipo }));
    await page.route("**/ops/drhp-collection.json", route => route.fulfill({ json: healthData }));
    try {
      await page.goto(`http://127.0.0.1:${server.address().port}/drhp.html`);
      await page.waitForSelector("#drhpError:not([hidden])");
      assert.equal(await page.locator("#drhpResults").isVisible(), false,
        "Invalid lifecycle data must never expose the pre-IPO result set");
      assert.equal(await page.locator("#drhpError").isVisible(), true);
      assert.deepEqual(errors, [], "Fail-closed lifecycle handling must not raise browser errors");
      passed.push(name);
    } finally { await page.close(); }
  }

  await scenario("failed refresh keeps source and lifecycle timestamps distinct", {}, async state => {
    assert.equal(state.source, `Draft sources last successfully collected: ${timestamp(sourceData.collection_completed_at)}`,
      "The retained draft-source collection timestamp must remain visible separately from newer lifecycle state");
    assert.equal(state.lifecycle, `IPO lifecycle dataset generated: ${timestamp(ipoData.generated_at)}`);
    assert.equal(state.attempt, `Latest reported draft-source refresh: Failed · ${timestamp(healthData.attempted_at)}`);
    assert.match(state.note, /Latest draft-source refresh failed; the last successful evidence set is retained/);
  });
  await scenario("missing health preserves loaded freshness and companies", { health: null }, async state => {
    assert.equal(state.source, `Draft sources last successfully collected: ${timestamp(sourceData.collection_completed_at)}`);
    assert.equal(state.lifecycle, `IPO lifecycle dataset generated: ${timestamp(ipoData.generated_at)}`);
    assert.equal(state.attempt, "Latest reported draft-source refresh: Unavailable");
    assert.match(state.note, /Latest draft-source refresh status is unavailable/);
  });
  await scenario("newer successful report does not redate retained source evidence", {
    health: { ...healthData, status: "success", last_successful_collection_at: healthData.attempted_at },
  }, async state => {
    assert.equal(state.source, `Draft sources last successfully collected: ${timestamp(sourceData.collection_completed_at)}`);
    assert.equal(state.attempt, `Latest reported draft-source refresh: Success · ${timestamp(healthData.attempted_at)}`);
    assert.match(state.note, /Refresh report describes a different collection; displayed companies use the retained draft dataset/);
  });
  await scenario("older success report is identified as different from loaded evidence", {
    health: { ...healthData, status: "success", attempted_at: "2026-09-25T12:00:00Z", last_successful_collection_at: "2026-09-25T12:00:00Z" },
  }, async state => {
    assert.equal(state.source, `Draft sources last successfully collected: ${timestamp(sourceData.collection_completed_at)}`);
    assert.equal(state.attempt, "Latest reported draft-source refresh: Success · 25 Sept 2026, 12:00 UTC");
    assert.match(state.note, /Refresh report describes a different collection/);
  });
  await scenario("matching success report has no false mismatch warning", {
    health: { ...healthData, status: "success", attempted_at: sourceData.collection_completed_at, last_successful_collection_at: sourceData.collection_completed_at },
  }, async state => {
    assert.equal(state.source, `Draft sources last successfully collected: ${timestamp(sourceData.collection_completed_at)}`);
    assert.equal(state.attempt, `Latest reported draft-source refresh: Success · ${timestamp(sourceData.collection_completed_at)}`);
    assert.doesNotMatch(state.note, /different collection|refresh failed|status is unavailable/);
  });
  await scenario("generation fallback never claims successful collection", {
    source: { ...sourceData, collection_completed_at: null }, health: null,
  }, async state => {
    assert.equal(state.source, `Draft dataset generated: ${timestamp(sourceData.generated_at)} · source collection time unavailable`);
    assert.equal(state.lifecycle, `IPO lifecycle dataset generated: ${timestamp(ipoData.generated_at)}`);
  });
  await scenario("dataset generation cannot override an earlier successful collection", {
    source: { ...sourceData, generated_at: ipoData.generated_at },
  }, async state => {
    assert.equal(state.source, `Draft sources last successfully collected: ${timestamp(sourceData.collection_completed_at)}`);
    assert.equal(state.lifecycle, `IPO lifecycle dataset generated: ${timestamp(ipoData.generated_at)}`);
  });
  await scenario("invalid draft collection time and unknown health status remain honest", {
    source: { ...sourceData, collection_completed_at: "invalid" },
    health: { status: "unknown", attempted_at: healthData.attempted_at },
  }, async state => {
    assert.equal(state.source, `Draft dataset generated: ${timestamp(sourceData.generated_at)} · source collection time unavailable`);
    assert.equal(state.lifecycle, `IPO lifecycle dataset generated: ${timestamp(ipoData.generated_at)}`);
    assert.equal(state.attempt, `Latest reported draft-source refresh: Unavailable · ${timestamp(healthData.attempted_at)}`);
    assert.match(state.note, /Latest draft-source refresh status is unavailable/);
  });

  const proxyFiling = {
    filing_type: "DRHP",
    filing_date: "2026-09-22",
    filing_url: "https://www.axiscapital.co.in/contents/Proxy%20Basis%20Limited%20-%20Draft%20Red%20Herring%20Prospectus-1790067639.pdf",
    draft_abridged_url: null,
    source_kind: "official_lead_manager",
    source_authority: "Axis Capital Limited",
    date_basis: "lead_manager_document_earliest_url_timestamp",
  };
  const proxySource = structuredClone(sourceData);
  proxySource.companies[0] = {
    issuer_name: "Proxy Basis Limited",
    filing_count: 1,
    filings: [proxyFiling],
    latest_filing_type: proxyFiling.filing_type,
    latest_filing_date: proxyFiling.filing_date,
    latest_filing_url: proxyFiling.filing_url,
  };
  await scenario("lead-manager timestamp proxy is visible wherever its date is shown", {
    source: proxySource,
  }, async state => {
    assert.equal(state.latestDateBasis, "Date proxy · earliest lead-manager document-URL timestamp");
    assert.match(state.cardsText, /Date proxy · earliest lead-manager document-URL timestamp/);
    assert.match(state.note, /Lead-manager fallback dates are labelled as timestamp proxies/);
  });

  await rejectedLifecycleScenario("missing lifecycle generation clock fails closed", {
    ...ipoData, generated_at: null,
  });
  await rejectedLifecycleScenario("empty lifecycle record set fails closed", {
    ...ipoData, records: [],
  });
  await rejectedLifecycleScenario("unexpected lifecycle schema fails closed", {
    ...ipoData, schema_version: "1.1.0",
  });
  console.log(JSON.stringify({ drhp_freshness_browser_tests: { passed: passed.length, scenarios: passed } }));
} finally {
  await browser?.close();
  await new Promise(resolve => server.close(resolve));
}
