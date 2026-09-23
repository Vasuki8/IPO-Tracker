import path from "node:path";
import { pathToFileURL } from "node:url";

const HOME = "https://www.bseindices.com/";
const USER_AGENT =
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";
const TARGETS = [
  "GetLatestNotices",
  "GetNoticesadvancesearch_newcomb",
  "NoticesAsiaDownload",
  "DisplayNoticecircular"
];

function normalize(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

export function extractMainScript(html) {
  const scripts = [...String(html ?? "").matchAll(
    /<script\b[^>]*\bsrc=["']([^"']+)["'][^>]*>/ig
  )].map((match) => match[1].trim());
  return scripts.find((src) => /(^|\/)main-[A-Z0-9_-]+\.js(?:\?|$)/i.test(src)) ?? null;
}

export function extractEndpointContexts(source, radius = 900) {
  const text = String(source ?? "");
  const contexts = [];
  for (const target of TARGETS) {
    let start = 0;
    let count = 0;
    while (count < 4) {
      const index = text.indexOf(target, start);
      if (index < 0) break;
      const from = Math.max(0, index - radius);
      const to = Math.min(text.length, index + target.length + radius);
      contexts.push({
        target,
        offset: index,
        context: normalize(text.slice(from, to))
      });
      start = index + target.length;
      count += 1;
    }
  }
  return contexts;
}

async function fetchText(url, accept) {
  const response = await fetch(url, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": accept,
      "accept-language": "en-US,en;q=0.9",
      "referer": HOME
    },
    signal: AbortSignal.timeout(20000)
  });
  if (!response.ok) throw new Error("HTTP " + response.status + " " + url);
  return response.text();
}

async function run() {
  const html = await fetchText(HOME, "text/html,application/xhtml+xml");
  const mainScript = extractMainScript(html);
  if (!mainScript) throw new Error("BSE Index main bundle not found");
  const bundleUrl = new URL(mainScript, HOME).href;
  const source = await fetchText(bundleUrl, "application/javascript,text/javascript,*/*;q=0.1");
  const contexts = extractEndpointContexts(source);

  console.log(JSON.stringify({
    bse_notice_api_context: {
      bundle_url: bundleUrl,
      bundle_bytes: source.length,
      context_count: contexts.length,
      contexts
    }
  }, null, 2));
}

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run().catch((error) => {
  console.error(error);
  process.exit(1);
});
