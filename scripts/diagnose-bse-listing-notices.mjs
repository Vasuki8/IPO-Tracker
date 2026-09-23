import { pathToFileURL } from "node:url";
import path from "node:path";

export const BSE_NOTICES_URL = "https://www.bseindia.com/markets/MarketInfo/NoticesCirculars.aspx";
const USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";

function decodeHtml(value) {
  return String(value ?? "")
    .replace(/&amp;/gi, "&")
    .replace(/&nbsp;/gi, " ")
    .replace(/&#39;/g, "'")
    .replace(/&quot;/gi, '"')
    .replace(/\s+/g, " ")
    .trim();
}

function stripTags(value) {
  return decodeHtml(String(value ?? "").replace(/<[^>]+>/g, " "));
}

export function parseBseListingNoticeArchive(html) {
  const source = String(html ?? "");
  const notices = [];
  const anchorPattern = /<a\b[^>]*href=["']([^"']*DispNewNoticesCirculars\.aspx\?page=([^"'&]+)[^"']*)["'][^>]*>([\s\S]*?)<\/a>/ig;

  for (const match of source.matchAll(anchorPattern)) {
    const subject = stripTags(match[3]);
    if (!/^Listing of Equity Shares of\s+/i.test(subject)) continue;

    const noticeNo = decodeURIComponent(match[2]).trim();
    const before = source.slice(0, match.index);
    const rowStart = before.lastIndexOf("<tr");
    const after = source.slice((match.index ?? 0) + match[0].length);
    const rowEndOffset = after.search(/<\/tr\s*>/i);
    const rowEnd = rowEndOffset >= 0
      ? (match.index ?? 0) + match[0].length + rowEndOffset + 5
      : Math.min(source.length, (match.index ?? 0) + match[0].length + 1000);
    const rowHtml = source.slice(rowStart >= 0 ? rowStart : Math.max(0, (match.index ?? 0) - 600), rowEnd);
    const rowText = stripTags(rowHtml);

    const segmentMatch = rowText.match(/\b(SME|Equity)\b/i);
    const company = subject.replace(/^Listing of Equity Shares of\s+/i, "").trim();

    notices.push({
      notice_no: noticeNo,
      subject,
      company,
      segment: segmentMatch ? segmentMatch[1].toUpperCase() : null,
      url: new URL(match[1].replace(/&amp;/g, "&"), BSE_NOTICES_URL).href,
      row_text: rowText
    });
  }

  return [...new Map(notices.map((notice) => [notice.notice_no, notice])).values()];
}

export function parseBseArchiveNavigation(html) {
  const source = String(html ?? "");
  const queryLinks = [];
  for (const match of source.matchAll(/href=["']([^"']*NoticesCirculars\.aspx\?[^"']+)["']/ig)) {
    const href = decodeHtml(match[1]);
    queryLinks.push(new URL(href, BSE_NOTICES_URL).href);
  }

  const hiddenInputs = [];
  for (const match of source.matchAll(/<input\b[^>]*type=["']hidden["'][^>]*>/ig)) {
    const tag = match[0];
    const name = tag.match(/\bname=["']([^"']+)["']/i)?.[1] ?? null;
    const value = tag.match(/\bvalue=["']([^"']*)["']/i)?.[1] ?? "";
    if (name) hiddenInputs.push({ name: decodeHtml(name), value: decodeHtml(value) });
  }

  const pagecontValues = [...new Set(
    queryLinks.map((url) => {
      try { return new URL(url).searchParams.get("pagecont"); } catch { return null; }
    }).filter((value) => value !== null)
  )];

  return {
    query_links: [...new Set(queryLinks)],
    pagecont_values: pagecontValues,
    hidden_input_names: [...new Set(hiddenInputs.map((item) => item.name))]
  };
}

async function fetchArchive(subject) {
  const url = new URL(BSE_NOTICES_URL);
  url.searchParams.set("id", "0");
  url.searchParams.set("txtscripcd", "");
  url.searchParams.set("pagecont", "");
  url.searchParams.set("subject", subject);

  const response = await fetch(url, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "text/html,application/xhtml+xml",
      "accept-language": "en-US,en;q=0.9",
      "referer": "https://www.bseindia.com/"
    },
    signal: AbortSignal.timeout(20000)
  });
  if (!response.ok) throw new Error("HTTP " + response.status + " for " + url.href);
  return { url: url.href, html: await response.text() };
}

async function run() {
  const { url, html } = await fetchArchive("Listing of Equity Shares of");
  const notices = parseBseListingNoticeArchive(html);
  const navigation = parseBseArchiveNavigation(html);
  const noticeDates = notices
    .map((item) => item.notice_no.match(/^(\d{8})-/)?.[1] ?? null)
    .filter(Boolean)
    .sort();

  console.log(JSON.stringify({
    bse_listing_notice_archive_diagnostic: {
      url,
      response_bytes: Buffer.byteLength(html),
      matching_notices: notices.length,
      earliest_notice_date: noticeDates[0] ?? null,
      latest_notice_date: noticeDates.at(-1) ?? null,
      segments: notices.reduce((acc, item) => {
        const key = item.segment ?? "UNKNOWN";
        acc[key] = (acc[key] ?? 0) + 1;
        return acc;
      }, {}),
      pagecont_values: navigation.pagecont_values.slice(0, 20),
      query_link_count: navigation.query_links.length,
      hidden_input_names: navigation.hidden_input_names.slice(0, 40),
      sample_notices: notices.slice(0, 20).map(({ row_text, ...item }) => item),
      page_head: stripTags(html).slice(0, 300)
    }
  }, null, 2));
}

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;

if (isMain) run().catch((error) => {
  console.error(error);
  process.exit(1);
});
