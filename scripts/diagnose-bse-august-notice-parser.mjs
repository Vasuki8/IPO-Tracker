import { parseBseSmeAdditionNoticeHtml } from "./audit-bse-sme-addition-notices.mjs";

const URL = "https://www.bseindices.com/AsiaIndexAPI/api/DisplayNoticecircular/w?NoticeId=20260813-16";
const USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";

function normalize(html) {
  return String(html ?? "")
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;|&apos;/gi, "'")
    .replace(/&rsquo;|&lsquo;/gi, "'")
    .replace(/&ndash;|&mdash;/gi, "-")
    .replace(/&#10;|&#13;/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
}

const response = await fetch(URL, {
  headers: {
    "user-agent": USER_AGENT,
    "accept": "application/json,*/*",
    "accept-language": "en-US,en;q=0.9",
    "referer": "https://www.bseindices.com/notices"
  },
  signal: AbortSignal.timeout(20000)
});
if (!response.ok) throw new Error("HTTP " + response.status);
const payload = await response.json();
const raw = String(payload?.Data ?? "");
const plain = normalize(raw);
const marker = plain.toLowerCase().indexOf("with reference");
const snippet = marker >= 0 ? plain.slice(marker, marker + 900) : plain.slice(0, 900);
const parsed = parseBseSmeAdditionNoticeHtml(raw);
const start = plain.match(/With reference to Notice No\.?\s*([0-9]{8}-[0-9]+)/i);
const ticker = plain.match(/\(Exchange ticker\s*-\s*([0-9]{6})\s*\)/i);
const listed = /\blisted\s+on\s+BSE\b/i.test(plain);
const effective = plain.match(/\beffective\s+(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s*,?\s*)?([A-Za-z]+\s+\d{1,2},\s*\d{4})/i);

console.log(JSON.stringify({
  response_keys: Object.keys(payload || {}),
  data_length: raw.length,
  snippet,
  intermediate: {
    start: start?.[0] ?? null,
    ticker: ticker?.[0] ?? null,
    listed,
    effective: effective?.[0] ?? null
  },
  parsed
}, null, 2));
