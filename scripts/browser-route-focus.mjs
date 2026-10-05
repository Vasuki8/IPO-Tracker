// Force delayed native hashchange delivery after popstate; never weaken focus assertions.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { directoryDataset } from "./fixtures/browser-data.mjs";
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const root = fileURLToPath(new URL("../", import.meta.url));
const fixture = directoryDataset();
const server = createServer(async (req, res) => {
  try {
    const pathname = new URL(req.url, "http://localhost").pathname;
    if (pathname === "/data/ipos.json") { res.writeHead(200,{"Content-Type":"application/json"}).end(JSON.stringify(fixture)); return; }
    const file = path.resolve(root, "." + (pathname === "/" ? "/index.html" : pathname));
    if (!file.startsWith(root)) { res.writeHead(403).end(); return; }
    const types={".html":"text/html",".js":"text/javascript",".css":"text/css",".svg":"image/svg+xml"};
    res.writeHead(200,{"Content-Type":types[path.extname(file)]||"application/octet-stream"}).end(await readFile(file));
  } catch { res.writeHead(404).end(); }
});
await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
const base=`http://127.0.0.1:${server.address().port}/`;
let browser;
let journeys=0;
try {
  browser=await chromium.launch({headless:true});
  for (const width of [320,390,1440]) {
    const page=await browser.newPage({viewport:{width,height:844}});
    const errors=[]; page.on("pageerror", e=>errors.push(e.message));
    await page.addInitScript(() => {
      window.heldRouteEvents=[];
      window.holdRouteEvents=false;
      addEventListener("hashchange", event => {
        if (!window.holdRouteEvents) return;
        event.stopImmediatePropagation();
        window.heldRouteEvents.push({oldURL:event.oldURL,newURL:event.newURL});
      }, true);
    });
    try {
      await page.goto(base); await page.waitForSelector("#results:not([hidden])");
      for (let repeat=0; repeat<3; repeat++) {
        await page.evaluate(()=>{window.holdRouteEvents=true;});
        const link=width<820?"#mobileCards .company-name":"#ipoRows .company-name";
        await page.locator(link).first().click();
        await page.waitForSelector("#detailView:not([hidden])");
        await page.waitForFunction(()=>window.heldRouteEvents.length>0);
        await page.locator("#evidenceList summary").first().click();
        await page.evaluate(()=>{window.retainedEvidenceNode=document.querySelector("#evidenceList details");});
        const route=page.url();
        await page.locator(".skip-link").focus(); await page.keyboard.press("Enter");
        assert.equal(await page.evaluate(()=>document.activeElement.id),"main","skip link initially focuses main");
        await page.evaluate(()=>{
          window.holdRouteEvents=false;
          for(const init of window.heldRouteEvents.splice(0)) dispatchEvent(new HashChangeEvent("hashchange",init));
          dispatchEvent(new PopStateEvent("popstate",{state:history.state}));
        });
        assert.equal(page.url(),route,"duplicate notifications preserve route");
        assert.equal(await page.evaluate(()=>document.activeElement.id),"main","late duplicate route must not steal keyboard focus");
        assert.equal(await page.evaluate(()=>retainedEvidenceNode===document.querySelector("#evidenceList details")&&retainedEvidenceNode.open),true,
          "late duplicate route must not reset research state");
        await page.keyboard.press("Tab");
        assert.equal(await page.evaluate(()=>document.querySelector("#main").contains(document.activeElement)),true);
        await page.goBack(); await page.waitForSelector("#homeView:not([hidden])");
        assert.equal(await page.evaluate(()=>document.activeElement.id),"searchInput","real back navigation focuses search");
        await page.goForward(); await page.waitForSelector("#detailView:not([hidden])");
        assert.equal(await page.evaluate(()=>document.activeElement.id),"detailName","real forward navigation focuses detail");
        await page.goBack(); await page.waitForSelector("#homeView:not([hidden])");
        journeys++;
      }
      // Same hash but a different query must still process popstate and restore filters.
      await page.evaluate(()=>{history.pushState(null,"","?board=sme");dispatchEvent(new PopStateEvent("popstate"));});
      assert.equal(await page.locator('[data-board="sme"]').getAttribute("aria-pressed"),"true");
      await page.goBack();
      await page.waitForFunction(()=>document.querySelector('[data-board="all"]').getAttribute("aria-pressed")==="true");
      // Retry/reload at an identical URL must not be swallowed by route deduplication.
      await page.goto(base+"#ipo/"+fixture.records[0].id);
      await page.waitForSelector("#detailView:not([hidden])");
      const replacement=structuredClone(fixture); replacement.records[0].issuer_name="Reloaded fixture issuer";
      await page.route("**/data/ipos.json",route=>route.fulfill({json:replacement}));
      await page.evaluate(()=>loadData());
      assert.equal(await page.locator("#detailName").textContent(),"Reloaded fixture issuer");
      assert.deepEqual(errors,[]);
    } finally { await page.close(); }
  }
  console.log(JSON.stringify({route_focus:{journeys,widths:[320,390,1440],delayed_native_event:true,
    duplicate_notifications:true,evidence_preserved:true,back_forward:true,query_only:true,same_url_reload:true}}));
} finally { await browser?.close(); await new Promise(resolve=>server.close(resolve)); }
