import path from "node:path";
import { pathToFileURL } from "node:url";

const CATALOG_URL = "https://www.bseindices.com/AsiaIndexAPI/api/GetNoticesadvancesearch_newcomb/w";
const DISPLAY_URL = "https://www.bseindices.com/AsiaIndexAPI/api/DisplayNoticecircular/w?NoticeId=";
const DOWNLOAD_URL = "https://www.bseindices.com/AsiaIndexAPI/api/NoticesAsiaDownload/w?NoticeId=";
const USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";

function normalize(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

function summarizeJson(value, depth = 0) {
  if (depth > 2) return typeof value;
  if (value === null) return null;
  if (Array.isArray(value)) {
    return { type: "array", length: value.length, sample: value.slice(0, 2).map((item) => summarizeJson(item, depth + 1)) };
  }
  if (typeof value === "object") {
    return {
      type: "object",
      keys: Object.keys(value).slice(0, 30),
      fields: Object.fromEntries(Object.entries(value).slice(0, 20).map(([key, item]) => [
        key,
        typeof item === "string"
          ? { type: "string", length: item.length, prefix: normalize(item).slice(0, 240) }
          : summarizeJson(item, depth + 1)
      ]))
    };
  }
  return { type: typeof value, value: String(value).slice(0, 240) };
}

async function fetchRaw(url, accept) {
  const response = await fetch(url, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": accept,
      "accept-language": "en-US,en;q=0.9",
      "referer": "https://www.bseindices.com/notices"
    },
    signal: AbortSignal.timeout(20000)
  });
  const buffer = Buffer.from(await response.arrayBuffer());
  const type = response.headers.get("content-type");
  const text = /^text\//i.test(type || "") || /json|javascript|xml|html/i.test(type || "")
    ? buffer.toString("utf8")
    : "";
  let json = null;
  if (text && /json/i.test(type || "")) {
    try { json = JSON.parse(text); } catch {}
  }
  return {
    ok: response.ok,
    status: response.status,
    content_type: type,
    bytes: buffer.length,
    text_prefix: text ? normalize(text).slice(0, 500) : null,
    json_shape: json ? summarizeJson(json) : null,
    magic_hex: buffer.subarray(0, 12).toString("hex")
  };
}

async function run() {
  const catalogResponse = await fetch(CATALOG_URL, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "application/json,*/*",
      "accept-language": "en-US,en;q=0.9",
      "referer": "https://www.bseindices.com/notices"
    },
    signal: AbortSignal.timeout(20000)
  });
  if (!catalogResponse.ok) throw new Error("catalog HTTP " + catalogResponse.status);
  const catalog = await catalogResponse.json();
  const all = Array.isArray(catalog?.Table) ? catalog.Table : [];
  const row = all.find((item) => /^Additions?\s+to\s+the\s+BSE\s+SME\s+IPO\s+INDEX$/i.test(normalize(item?.Subject ?? item?.subject)));
  if (!row) throw new Error("no SME addition notice row found");
  const noticeNo = String(row?.notice_no ?? row?.Notice_no ?? "").trim();
  if (!noticeNo) throw new Error("notice number missing");

  const result = {
    notice_no: noticeNo,
    catalog_row: summarizeJson(row),
    display: await fetchRaw(DISPLAY_URL + encodeURIComponent(noticeNo), "application/json,*/*"),
    download: await fetchRaw(DOWNLOAD_URL + encodeURIComponent(noticeNo), "*/*")
  };
  console.log(JSON.stringify({ bse_current_notice_source_shape: result }, null, 2));
}

const isMain = process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run().catch((error) => { console.error(error); process.exit(1); });
