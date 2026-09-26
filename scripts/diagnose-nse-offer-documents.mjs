const PAGE="https://www.nseindia.com/companies-listing/corporate-filings-offer-documents?symbol=CCCL&tabIndex=equity";
const UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function cookies(headers){return (headers.getSetCookie?.()||[headers.get("set-cookie")].filter(Boolean)).map(x=>x.split(";")[0]).join("; ");}
async function fetchText(url,cookie){
  const r=await fetch(url,{headers:{"user-agent":UA,accept:"text/html,application/javascript,*/*","accept-language":"en-US,en;q=0.9",referer:PAGE,...(cookie?{cookie}:{})},signal:AbortSignal.timeout(30000)});
  const t=await r.text(); return {r,t};
}
const landing=await fetchText(PAGE,"");
const cookie=cookies(landing.r.headers);
console.log(JSON.stringify({page_status:landing.r.status,page_url:landing.r.url,page_bytes:Buffer.byteLength(landing.t),contains_abakkus:/Abakkus Asset Manager/i.test(landing.t),contains_offer_header:/Status Of draft offer document/i.test(landing.t)}));
const scripts=[...landing.t.matchAll(/<script\b[^>]*src=["']([^"']+)["']/gi)].map(m=>new URL(m[1],PAGE).href);
console.log(JSON.stringify({scripts:scripts.length,script_urls:scripts.slice(-30)}));
const hits=[];
for(const url of scripts.slice(-40)){
  try{
    const {r,t}=await fetchText(url,cookie);
    if(!r.ok||t.length>5000000)continue;
    const relevant=/offer.?document|draft.?offer|corporate.?filing|ipo.?document|public.?issue/i.test(t);
    if(!relevant)continue;
    const api=[...t.matchAll(/["'`]([^"'`]*(?:\/api\/|api\/)[^"'`]{0,180})["'`]/gi)].map(m=>m[1]).filter(x=>/offer|draft|corporate|issue|ipo/i.test(x));
    const fragments=[...new Set(api)].slice(0,80);
    hits.push({url,status:r.status,bytes:Buffer.byteLength(t),fragments});
  }catch(e){hits.push({url,error:String(e)})}
  await sleep(80);
}
console.log(JSON.stringify({relevant_scripts:hits},null,2));
