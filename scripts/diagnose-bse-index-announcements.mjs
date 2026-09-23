import { pathToFileURL } from "node:url";
import path from "node:path";

const HOME = "https://www.bseindices.com/";
const USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";

function uniq(values) {
  return [...new Set(values.filter(Boolean))];
}

export function extractScriptSources(html) {
  return uniq([...String(html ?? "").matchAll(/<script\b[^>]*\bsrc=["']([^"']+)["'][^>]*>/ig)]
    .map((match) => match[1].trim()));
}

export function extractAnnouncementHints(source) {
  const text = String(source ?? "");
  const hints = [];

  for (const match of text.matchAll(/https?:\/\/[^"'\x60\\\s]{4,260}/ig)) {
    const value = match[0];
    if (/(bseindices|asiaindex|notice|announcement|api)/i.test(value)) hints.push(value);
  }

  for (const match of text.matchAll(/\/[A-Za-z0-9_.~!$&()*+,;=:@%/-]{0,180}(?:notice|announcement|asiaindex)[A-Za-z0-9_.~!$&()*+,;=:@%/?-]{0,180}/ig)) {
    hints.push(match[0]);
  }

  for (const match of text.matchAll(/["'\x60]([^"'\x60]{0,160}(?:NoticesAsia|NoticeId|DisplayNoticescircular|announcement|notice)[^"'\x60]{0,220})["'\x60]/ig)) {
    hints.push(match[1].replace(/\s+/g, " ").trim());
  }

  return uniq(hints).slice(0, 120);
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

export async function collectAnnouncementDiagnostics() {
  const html = await fetchText(HOME, "text/html,application/xhtml+xml");
  const pageScripts = extractScriptSources(html);

  const firstParty = pageScripts
    .map((src) => new URL(src, HOME))
    .filter((url) => url.origin === new URL(HOME).origin)
    .slice(0, 12);

  const bundles = [];
  for (const url of firstParty) {
    try {
      const source = await fetchText(url.href, "application/javascript,text/javascript,*/*;q=0.1");
      bundles.push({
        url: url.href,
        bytes: source.length,
        hints: extractAnnouncementHints(source)
      });
    } catch (error) {
      bundles.push({
        url: url.href,
        bytes: 0,
        hints: [],
        error: String(error?.message || error)
      });
    }
  }

  return {
    home_bytes: html.length,
    script_sources: pageScripts,
    bundles
  };
}

async function run() {
  const result = await collectAnnouncementDiagnostics();
  console.log(JSON.stringify({ bse_index_announcement_diagnostic: result }, null, 2));
}

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run().catch((error) => {
  console.error(error);
  process.exit(1);
});
