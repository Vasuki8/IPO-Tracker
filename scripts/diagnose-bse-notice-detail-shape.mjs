import path from "node:path";
import { pathToFileURL } from "node:url";

const URL = "https://www.bseindices.com/AsiaIndexAPI/api/DisplayNoticecircular/w?NoticeId=20260225-13";
const USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";

function summarize(value, depth = 0) {
  if (depth > 2) return typeof value;
  if (value === null) return null;
  if (Array.isArray(value)) {
    return {
      type: "array",
      length: value.length,
      sample: value.slice(0, 2).map((item) => summarize(item, depth + 1))
    };
  }
  if (typeof value === "object") {
    return {
      type: "object",
      keys: Object.keys(value),
      fields: Object.fromEntries(
        Object.entries(value).slice(0, 20).map(([key, item]) => [
          key,
          typeof item === "string"
            ? { type: "string", length: item.length, prefix: item.slice(0, 220).replace(/\s+/g, " ") }
            : summarize(item, depth + 1)
        ])
      )
    };
  }
  return { type: typeof value, value: String(value).slice(0, 220) };
}

async function run() {
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
  const data = String(payload?.Data ?? "");
  const plain = data
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
  const marker = plain.toLowerCase().indexOf("with reference");
  const wording = marker >= 0 ? plain.slice(marker, marker + 650) : plain.slice(0, 650);
  console.log(JSON.stringify({
    bse_notice_detail_shape: summarize(payload),
    bse_notice_detail_wording: wording
  }, null, 2));
}

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run().catch((error) => {
  console.error(error);
  process.exit(1);
});
