const HOME="https://www.bseindia.com/";
const URL="https://www.bseindia.com/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=20260122-19";
const UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";

function cookies(headers){
  const vals=typeof headers.getSetCookie==="function"?headers.getSetCookie():[headers.get("set-cookie")].filter(Boolean);
  return vals.map(v=>v.split(";")[0]).filter(Boolean).join("; ");
}
function text(html){
  return String(html??"")
    .replace(/<script[\s\S]*?<\/script>/gi," ")
    .replace(/<style[\s\S]*?<\/style>/gi," ")
    .replace(/<[^>]+>/g," ")
    .replace(/&nbsp;/gi," ")
    .replace(/&amp;/gi,"&")
    .replace(/&#39;|&apos;/gi,"'")
    .replace(/&quot;/gi,'"')
    .replace(/\s+/g," ")
    .trim();
}
const home=await fetch(HOME,{headers:{"user-agent":UA,"accept":"text/html"},signal:AbortSignal.timeout(15000)});
const cookie=cookies(home.headers);
const r=await fetch(URL,{headers:{"user-agent":UA,"accept":"text/html,application/xhtml+xml,*/*","referer":HOME,...(cookie?{"cookie":cookie}:{})},signal:AbortSignal.timeout(20000)});
const html=await r.text();
const body=text(html);
const anchors=["Subject","ARITAS VINYL","effective","listed","admitted","Market Lot","Issue Price"];
const contexts={};
for(const needle of anchors){
  const i=body.toLowerCase().indexOf(needle.toLowerCase());
  contexts[needle]=i<0?null:body.slice(Math.max(0,i-280),Math.min(body.length,i+850));
}
console.log(JSON.stringify({status:r.status,bytes:html.length,contexts},null,2));
