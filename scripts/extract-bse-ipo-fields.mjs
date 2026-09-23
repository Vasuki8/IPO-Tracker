import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const MANIFEST_PATH = path.join(ROOT, "data", "bse-ipo-sources.json");
const USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";

function text(html) {
  return String(html ?? "").replace(/<script[\s\S]*?<\/script>/gi," ").replace(/<style[\s\S]*?<\/style>/gi," ")
    .replace(/<[^>]+>/g," ").replace(/&nbsp;/gi," ").replace(/&amp;/gi,"&").replace(/\s+/g," ").trim();
}
function number(raw) {
  const value=Number(String(raw??"").replace(/,/g,"").trim());
  return Number.isFinite(value)&&value>0?value:null;
}
export function parseBseEquityIssuePage(html) {
  const body=text(html);
  if (!/Security Type\s+Equity/i.test(body)) return null;
  const grab=(label, pattern)=>{const m=body.match(new RegExp(label+"\\s+"+pattern,"i"));return m?.[1]??null;};
  const period=body.match(/Issue Period\s+(\d{2}\s+[A-Za-z]{3}\s+\d{4})\s+to\s+(\d{2}\s+[A-Za-z]{3}\s+\d{4})/i);
  const band=body.match(/Price Band\s+([0-9,.]+)\s*-\s*([0-9,.]+)/i);
  return {
    symbol: grab("Symbol","([A-Z0-9_-]+)"),
    issue_size_shares: number(grab("Issue Size\\s*[–-]?\\s*No\\. of Shares","([0-9,]+)")),
    price_band: band ? { min:number(band[1]), max:number(band[2]) } : null,
    market_lot: number(grab("Market Lot","([0-9,]+)")),
    minimum_bid_quantity: number(grab("Minimum Bid Quantity","([0-9,]+)")),
    open_date_raw: period?.[1]??null,
    close_date_raw: period?.[2]??null
  };
}
export function parseBseListingNotice(html) {
  const body=text(html);
  const company=body.match(/Subject\s+Listing of Equity Shares of\s+(.+?)\s+Attachments/i)?.[1]??null;
  const effective=body.match(/effective from\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})/i)?.[1]??null;
  const lot=number(body.match(/Market Lot\s+([0-9,]+)/i)?.[1]);
  const price=number(body.match(/Issue Price for the current Public issue\s+Rs\.?\s*([0-9,.]+)/i)?.[1]);
  return { company, listing_date_raw:effective, market_lot:lot, issue_price:price };
}
async function fetchPage(url){
  const r=await fetch(url,{headers:{"user-agent":USER_AGENT,"accept":"text/html,*/*","referer":"https://www.bseindia.com/"},signal:AbortSignal.timeout(20000)});
  if(!r.ok) throw new Error("HTTP "+r.status+" "+url); return r.text();
}
async function run(){
  if(!fs.existsSync(MANIFEST_PATH)){console.log(JSON.stringify({bse_detail_stats:{sources:0,parsed:0,errors:0}}));return;}
  const manifest=JSON.parse(fs.readFileSync(MANIFEST_PATH,"utf8"));
  const stats={sources:(manifest.sources||[]).length,parsed:0,errors:0};
  for(const source of manifest.sources||[]){
    try{
      const html=await fetchPage(source.url);
      const parsed=source.kind==="listing_notice"?parseBseListingNotice(html):parseBseEquityIssuePage(html);
      if(parsed){stats.parsed++; console.log(JSON.stringify({issuer_name:source.issuer_name,kind:source.kind,url:source.url,parsed}));}
      else console.log(JSON.stringify({issuer_name:source.issuer_name,kind:source.kind,url:source.url,parsed:null}));
    }catch(e){stats.errors++;console.warn("BSE source unavailable for "+source.issuer_name+": "+e.message);}
  }
  console.log(JSON.stringify({bse_detail_stats:stats},null,2));
}
const isMain=process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url;
if(isMain)run().catch(e=>{console.error(e);process.exit(1);});
