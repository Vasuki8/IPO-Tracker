import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DATA_PATH = path.join(ROOT, "data", "ipos.json");
export const BSE_ISSUE_SUMMARY_URL = "https://www.bseindia.com/markets/PublicIssues/Issuesummary.aspx";
const USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";

function normalizeText(value) {
  return String(value ?? "").replace(/&amp;/gi, "&").replace(/&#39;/g, "'").replace(/&nbsp;/gi, " ").replace(/\s+/g, " ").trim();
}

function stripTags(value) {
  return normalizeText(String(value ?? "").replace(/<[^>]*>/g, " "));
}

function normalizeName(value) {
  return stripTags(value).toLowerCase()
    .replace(/\b(limited|ltd|private|pvt)\b/g, " ")
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function parseBseIssueSummaryLinks(html) {
  const results = [];
  const pattern = /<a\b[^>]*href=["']([^"']*DisplayIPO\.aspx\?[^"']+)["'][^>]*>([\s\S]*?)<\/a>/ig;
  for (const match of String(html ?? "").matchAll(pattern)) {
    const href = normalizeText(match[1]).replace(/&amp;/g, "&");
    const anchor = stripTags(match[2]);
    const context = stripTags(String(html).slice(Math.max(0, match.index - 900), Math.min(String(html).length, match.index + match[0].length + 250)));
    results.push({
      url: new URL(href, BSE_ISSUE_SUMMARY_URL).href,
      anchor,
      context
    });
  }
  return results;
}

export function matchBseSummaryLink(issuerName, links) {
  const target = normalizeName(issuerName);
  if (!target) return { match: null, reason: "missing_issuer_name" };
  const matches = (links || []).filter((item) => {
    const haystack = normalizeName(item.context);
    if (!haystack || !target) return false;
    return haystack.includes(target);
  });
  const unique = [...new Map(matches.map((item) => [item.url, item])).values()];
  if (unique.length !== 1) {
    return { match: null, reason: unique.length ? "ambiguous_match" : "no_match", candidates: unique };
  }
  return { match: unique[0], reason: null };
}

async function fetchPage(url) {
  const response = await fetch(url, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "text/html,application/xhtml+xml",
      "accept-language": "en-US,en;q=0.9",
      "referer": "https://www.bseindia.com/"
    },
    signal: AbortSignal.timeout(20000)
  });
  if (!response.ok) throw new Error("HTTP " + response.status + " for " + url);
  return response.text();
}

async function run() {
  const data = JSON.parse(fs.readFileSync(DATA_PATH, "utf8"));
  const html = await fetchPage(BSE_ISSUE_SUMMARY_URL);
  const links = parseBseIssueSummaryLinks(html);
  const records = (data.records || []).filter((record) =>
    record.listing_date?.value == null ||
    record.issue_price?.value == null ||
    record.issue_size_inr?.value == null ||
    record.market_lot?.value == null ||
    record.minimum_bid_quantity?.value == null
  );

  const stats = { summary_links: links.length, candidates: records.length, matched: 0, no_match: 0, ambiguous: 0 };
  for (const record of records) {
    const selection = matchBseSummaryLink(record.issuer_name, links);
    if (selection.match) stats.matched += 1;
    else if (selection.reason === "ambiguous_match") stats.ambiguous += 1;
    else stats.no_match += 1;
    console.log(JSON.stringify({
      issuer_name: record.issuer_name,
      result: selection.reason ?? "matched",
      bse_url: selection.match?.url ?? null,
      bse_context: selection.match?.context ?? null
    }));
  }
  console.log(JSON.stringify({ bse_issue_summary_diagnostic: stats }, null, 2));
}

const isMain = process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run().catch((error) => { console.error(error); process.exit(1); });
