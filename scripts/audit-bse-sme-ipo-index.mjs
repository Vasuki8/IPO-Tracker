import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");
export const BSE_SME_IPO_INDEX_URL = "https://www.bseindia.com/sensex/IndicesWatch_Weight.aspx?iname=SMEIPO&index_Code=76";
const USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";

function normalizeText(value) {
  return String(value ?? "")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, " ")
    .trim();
}

function stripTags(value) {
  return normalizeText(String(value ?? "").replace(/<[^>]*>/g, " "));
}

export function normalizeIssuerName(value) {
  return stripTags(value)
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/\b(private|pvt|limited|ltd)\b/g, " ")
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function parseBseSmeIpoIndex(html) {
  const rows = [];
  for (const rowMatch of String(html ?? "").matchAll(/<tr\b[^>]*>([\s\S]*?)<\/tr>/ig)) {
    const cells = [...rowMatch[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/ig)]
      .map((match) => stripTags(match[1]));
    if (cells.length < 3) continue;

    const scripCode = cells[0].replace(/\D/g, "");
    const company = cells[1];
    const isin = cells[2].replace(/\s+/g, "").toUpperCase();

    if (!/^\d{6}$/.test(scripCode)) continue;
    if (!company) continue;
    if (!/^INE[A-Z0-9]{9}$/i.test(isin)) continue;

    rows.push({
      scrip_code: scripCode,
      company,
      isin,
      close_price: cells[3] || null
    });
  }

  return [...new Map(rows.map((row) => [row.scrip_code, row])).values()];
}

function recoveryFiles() {
  if (!fs.existsSync(RECOVERY_ROOT)) return [];
  return fs.readdirSync(RECOVERY_ROOT, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && /^20\d{2}$/.test(entry.name))
    .map((entry) => path.join(RECOVERY_ROOT, entry.name, "nse-issue-information.json"))
    .filter((file) => fs.existsSync(file))
    .sort();
}

export function matchIndexCompany(company, records) {
  const target = normalizeIssuerName(company);
  if (!target) return { match: null, match_type: "none" };

  const exact = records.filter(({ record }) => normalizeIssuerName(record.issuer_name) === target);
  if (exact.length === 1) return { match: exact[0], match_type: "exact" };
  if (exact.length > 1) return { match: null, match_type: "ambiguous_exact" };

  const prefix = records.filter(({ record }) => {
    const current = normalizeIssuerName(record.issuer_name);
    if (!current || Math.min(current.length, target.length) < 12) return false;
    return current.startsWith(target) || target.startsWith(current);
  });
  if (prefix.length === 1) return { match: prefix[0], match_type: "prefix" };
  if (prefix.length > 1) return { match: null, match_type: "ambiguous_prefix" };

  return { match: null, match_type: "none" };
}

async function fetchPage() {
  const response = await fetch(BSE_SME_IPO_INDEX_URL, {
    headers: {
      "user-agent": USER_AGENT,
      "accept": "text/html,application/xhtml+xml",
      "accept-language": "en-US,en;q=0.9",
      "referer": "https://www.bseindia.com/"
    },
    signal: AbortSignal.timeout(20000)
  });
  if (!response.ok) throw new Error("BSE SME IPO index HTTP " + response.status);
  return response.text();
}

async function run() {
  const records = recoveryFiles().flatMap((file) => {
    const year = Number(path.basename(path.dirname(file)));
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    return (recovery.records || []).map((record) => ({ year, record }));
  });

  const html = await fetchPage();
  const indexRows = parseBseSmeIpoIndex(html);
  const stats = {
    response_bytes: html.length,
    index_rows: indexRows.length,
    exact_matches: 0,
    prefix_matches: 0,
    unmatched: 0,
    ambiguous: 0
  };

  const unmatched = [];
  for (const row of indexRows) {
    const selection = matchIndexCompany(row.company, records);
    if (selection.match_type === "exact") stats.exact_matches += 1;
    else if (selection.match_type === "prefix") stats.prefix_matches += 1;
    else if (selection.match_type.startsWith("ambiguous")) stats.ambiguous += 1;
    else {
      stats.unmatched += 1;
      unmatched.push(row);
    }

    console.log(JSON.stringify({
      ...row,
      match_type: selection.match_type,
      matched_issuer: selection.match?.record?.issuer_name ?? null,
      matched_year: selection.match?.year ?? null
    }));
  }

  console.log(JSON.stringify({
    bse_sme_ipo_index_audit: stats,
    unmatched_candidates: unmatched
  }, null, 2));
}

const isMain = process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run().catch((error) => { console.error(error); process.exit(1); });
