// Historical release check: run against a checkout/deployment of this admission batch.
const {chromium}=require('playwright');
const fs=require('node:fs/promises');
const path=require('node:path');
const assert=require('node:assert/strict');
(async()=>{
  const base=new URL(process.env.BASE_URL || 'http://127.0.0.1:8006/');
  const output=process.env.SMOKE_ARTIFACT_DIR || '.cache/universe-continuation/browser';
  await fs.mkdir(output,{recursive:true});
  const reviewed=JSON.parse(await fs.readFile(path.join(__dirname,'admission-review.json'),'utf8')).records;
  const summary=await (await fetch(new URL('data/ipos-summary.json',base))).json();
  const browser=await chromium.launch({headless:true,...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH}:{})});
  const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'});
  const errors=[],masterRequests=[],results=[];
  page.on('pageerror',e=>errors.push(String(e)));
  page.on('request',r=>{if(new URL(r.url()).pathname.endsWith('/data/ipos.json'))masterRequests.push(r.url());});
  try{
    for(const want of reviewed){
      const brief=summary.ipos.find(r=>r.id===want.id);assert.ok(brief,want.id);
      for(const width of [1440,375,320]){
        await page.setViewportSize({width,height:900});
        await page.goto(new URL(brief.profilePath,base).href,{waitUntil:'networkidle'});
        await page.locator('#companyPage .company-profile').waitFor();
        assert.equal(await page.locator('#companyPage h1').innerText(),want.issuerName);
        const record=JSON.parse(await page.locator('#ipo-profile-data').textContent()).ipo;
        for(const row of [brief,record]){
          assert.equal(row.symbol,want.identity.symbol);assert.equal(row.status,'closed');assert.equal(row.board,'SME');
          assert.equal(row.openDate,want.identity.openDate);assert.equal(row.closeDate,want.identity.closeDate);
          for(const key of ['listingDate','priceBand','lotSize','issueSizeCr','financials','subscription','marketLot','minimumBidQuantity'])assert.ok(row[key]==null,`${want.id}: ${key} invented`);
        }
        assert.ok(await page.locator(`a[href="${want.sourceUrl}"]`).count());
        const text=await page.locator('#companyPage').innerText();assert.match(text,/Source record timestamp\s+Not available/);
        assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),want.id+' overflow');
        if(want.id==='complete-sports-and-management-india')await page.screenshot({path:path.join(output,`long-name-${width}.png`),fullPage:true});
        results.push({id:want.id,width,profile:'passed'});
      }
      await page.goto(new URL('?q='+encodeURIComponent(want.identity.symbol),base).href,{waitUntil:'networkidle'});
      await page.locator(`a[href="${brief.profilePath}"]`).first().waitFor();
    }
    assert.deepEqual(errors,[]);assert.deepEqual(masterRequests,[]);
    await fs.writeFile(path.join(output,'result.json'),JSON.stringify({status:'passed',baseUrl:base.href,profiles:reviewed.length,results,errors,masterRequests},null,2)+'\n');
    console.log(JSON.stringify({status:'passed',profiles:reviewed.length,viewportChecks:results.length,directorySearches:reviewed.length}));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
