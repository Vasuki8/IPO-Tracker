import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RECOVERY_ROOT = path.join(ROOT, "data", "recovery");

export const BSE_INDEX_SERVICES_SME_JSON_URL =
  "https://www.bseindices.com/AsiaIndexAPI/api/Codewise_Indices/w?code=76";
export const BSE_INDEX_SERVICES_SME_CONSTITUENTS_URL =
  "https://www.bseindices.com/constituents/code/76";
export const BSE_LEGACY_SME_IPO_URL =
  "https://www.bseindia.com/sensex/IndicesWatch_Weight.aspx?iname=SMEIPO&index_Code=76";

const OFFICIAL_SOURCES = [
  {
    name: "bse_index_services_json",
    format: "json",
    url: BSE_INDEX_SERVICES_SME_JSON_URL,
    referer: "https://www.bseindices.com/"
  },
  {
    name: "bse_index_services_html",
    format: "html",
    url: BSE_INDEX_SERVICES_SME_CONSTITUENTS_URL,
    referer: "https://www.bseindices.com/"
  },
  {
    name: "bse_legacy_index_watch",
    format: "html",
    url: BSE_LEGACY_SME_IPO_URL,
    referer: "https://www.bseindia.com/"
  }
];

const USER_AGENT =
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";

function normalizeText(value) {
  return String(value ?? "")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&#39;/g, "'")
    .replace(/&quot;/gi, "\"")
    .replace(/\s+/g, " ")
    .trim();
}

function stripTags(value) {
  return normalizeText(String(value ?? "").replace(/<[^>]*>/g, " "));
}

function normalizeAsOfDate(value) {
  const raw = normalizeText(value);
  const iso = raw.match(/^(\d{4}-\d{2}-\d{2})/);
  return iso?.[1] ?? null;
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

function chooseLongerCompany(left, right) {
  const a = normalizeText(left);
  const b = normalizeText(right);
  if (!a) return b;
  if (!b) return a;
  return b.length > a.length ? b : a;
}

export function pageFingerprint(html) {
  const source = String(html ?? "");
  const title = stripTags(source.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i)?.[1] ?? "");
  const scripts = [...source.matchAll(/<script\b[^>]*\bsrc=["']([^"']+)["'][^>]*>/ig)]
    .map((match) => normalizeText(match[1]))
    .filter(Boolean)
    .slice(0, 12);
  return {
    title: title || null,
    table_count: (source.match(/<table\b/ig) || []).length,
    row_count: (source.match(/<tr\b/ig) || []).length,
    script_sources: scripts
  };
}

export function extractBundleHints(source) {
  const hints = [];
  const seen = new Set();
  for (const match of String(source ?? "").matchAll(/["'`](.{1,240}?)["'`]/g)) {
    const value = normalizeText(match[1]);
    if (!/(api|constituent|indice|index)/i.test(value)) continue;
    if (!/[a-z]/i.test(value)) continue;
    if (seen.has(value)) continue;
    seen.add(value);
    hints.push(value);
    if (hints.length >= 30) break;
  }
  return hints;
}

async function fetchMainBundleHints(pageUrl, fingerprint) {
  const mainScript = (fingerprint?.script_sources || [])
    .find((value) => /(^|\/)main-[A-Z0-9_-]+\.js(?:\?|$)/i.test(value));
  if (!mainScript) return [];

  try {
    const scriptUrl = new URL(mainScript, pageUrl);
    const pageOrigin = new URL(pageUrl).origin;
    if (scriptUrl.origin !== pageOrigin) return [];

    const response = await fetch(scriptUrl, {
      headers: {
        "user-agent": USER_AGENT,
        "accept": "application/javascript,text/javascript,*/*;q=0.1"
      },
      signal: AbortSignal.timeout(20000)
    });
    if (!response.ok) return ["bundle_http_" + response.status];
    return extractBundleHints(await response.text());
  } catch (error) {
    return ["bundle_error:" + String(error?.message || error)];
  }
}

export function parseBseSmeIpoJson(payload) {
  const data = typeof payload === "string" ? JSON.parse(payload) : payload;
  const table = Array.isArray(data?.Table) ? data.Table : [];
  const rows = [];

  for (const item of table) {
    const scripCode = String(item?.SCRIP_CODE ?? "").replace(/\D/g, "");
    const company = normalizeText(item?.SCRIPNAME);
    if (!/^\d{6}$/.test(scripCode) || !company) continue;

    rows.push({
      scrip_code: scripCode,
      company,
      isin: null,
      close_price: null,
      macro_sector: normalizeText(item?.Industry_name) || null,
      as_of_date: normalizeAsOfDate(item?.TransDate),
      row_format: "index_services_json"
    });
  }

  return [...new Map(rows.map((row) => [row.scrip_code, row])).values()];
}

export function parseBseSmeIpoIndex(html) {
  const rows = [];

  for (const rowMatch of String(html ?? "").matchAll(/<tr\b[^>]*>([\s\S]*?)<\/tr>/ig)) {
    const cells = [...rowMatch[1].matchAll(/<t[dh]\b[^>]*>([\s\S]*?)<\/t[dh]>/ig)]
      .map((match) => stripTags(match[1]));
    if (cells.length < 3) continue;

    const legacyScripCode = cells[0].replace(/\D/g, "");
    const legacyIsin = cells[2].replace(/\s+/g, "").toUpperCase();

    if (/^\d{6}$/.test(legacyScripCode) && /^INE[A-Z0-9]{9}$/i.test(legacyIsin)) {
      rows.push({
        scrip_code: legacyScripCode,
        company: cells[1],
        isin: legacyIsin,
        close_price: cells[3] || null,
        macro_sector: null,
        as_of_date: null,
        row_format: "legacy_index_watch"
      });
      continue;
    }

    const indexServicesScripCode = cells[1].replace(/\D/g, "");
    if (/^\d{6}$/.test(indexServicesScripCode) && cells[0]) {
      rows.push({
        scrip_code: indexServicesScripCode,
        company: cells[0],
        isin: null,
        close_price: null,
        macro_sector: cells[2] || null,
        as_of_date: null,
        row_format: "index_services_html"
      });
    }
  }

  return [...new Map(rows.map((row) => [row.scrip_code, row])).values()];
}

export function mergeIndexRows(rowsBySource) {
  const byScripCode = new Map();

  for (const item of rowsBySource) {
    for (const row of item.rows || []) {
      const source = { name: item.name, url: item.url };
      const current = byScripCode.get(row.scrip_code);

      if (!current) {
        byScripCode.set(row.scrip_code, {
          ...row,
          official_sources: [source]
        });
        continue;
      }

      const sourceKey = source.name + "|" + source.url;
      const existingSourceKeys = new Set(
        (current.official_sources || []).map((entry) => entry.name + "|" + entry.url)
      );

      byScripCode.set(row.scrip_code, {
        ...current,
        company: chooseLongerCompany(current.company, row.company),
        isin: current.isin || row.isin || null,
        close_price: current.close_price || row.close_price || null,
        macro_sector: current.macro_sector || row.macro_sector || null,
        as_of_date: current.as_of_date || row.as_of_date || null,
        row_format: current.row_format === row.row_format
          ? current.row_format
          : "merged_official_formats",
        official_sources: existingSourceKeys.has(sourceKey)
          ? current.official_sources
          : [...current.official_sources, source]
      });
    }
  }

  return [...byScripCode.values()].sort((a, b) =>
    a.scrip_code.localeCompare(b.scrip_code)
  );
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
    if (!(current.startsWith(target) || target.startsWith(current))) return false;
    const longer=current.length>=target.length?current:target;
    const shorter=current.length>=target.length?target:current;
    const remainder=longer.slice(shorter.length).trim();
    return remainder.length<=3 || remainder==="limited";
  });
  if (prefix.length === 1) return { match: prefix[0], match_type: "prefix" };
  if (prefix.length > 1) return { match: null, match_type: "ambiguous_prefix" };

  return { match: null, match_type: "none" };
}

async function fetchOfficialSource(source) {
  try {
    const response = await fetch(source.url, {
      headers: {
        "user-agent": USER_AGENT,
        "accept": source.format === "json"
          ? "application/json,*/*"
          : "text/html,application/xhtml+xml",
        "accept-language": "en-US,en;q=0.9",
        "referer": source.referer
      },
      signal: AbortSignal.timeout(20000)
    });

    if (!response.ok) {
      return {
        ...source,
        ok: false,
        status: response.status,
        response_bytes: 0,
        rows: [],
        fingerprint: null,
        bundle_hints: [],
        error: "HTTP " + response.status
      };
    }

    const body = await response.text();

    if (source.format === "json") {
      let payload;
      try {
        payload = JSON.parse(body);
      } catch {
        return {
          ...source,
          ok: false,
          status: response.status,
          response_bytes: body.length,
          rows: [],
          fingerprint: null,
          bundle_hints: [],
          error: "invalid_json"
        };
      }

      return {
        ...source,
        ok: true,
        status: response.status,
        response_bytes: body.length,
        rows: parseBseSmeIpoJson(payload),
        fingerprint: {
          json_keys: Object.keys(payload || {}).slice(0, 12),
          table_rows: Array.isArray(payload?.Table) ? payload.Table.length : 0
        },
        bundle_hints: [],
        error: null
      };
    }

    const rows = parseBseSmeIpoIndex(body);
    const fingerprint = pageFingerprint(body);
    return {
      ...source,
      ok: true,
      status: response.status,
      response_bytes: body.length,
      rows,
      fingerprint,
      bundle_hints: rows.length === 0
        ? await fetchMainBundleHints(source.url, fingerprint)
        : [],
      error: null
    };
  } catch (error) {
    return {
      ...source,
      ok: false,
      status: null,
      response_bytes: 0,
      rows: [],
      fingerprint: null,
      bundle_hints: [],
      error: String(error?.message || error)
    };
  }
}

export async function collectBseSmeIpoIndexRows() {
  const attempts = await Promise.all(OFFICIAL_SOURCES.map(fetchOfficialSource));
  const rows = mergeIndexRows(attempts);

  if (rows.length === 0) {
    const detail = attempts
      .map((attempt) =>
        attempt.name + ": " +
        (attempt.error || (
          "HTTP " + attempt.status +
          ", " + attempt.response_bytes + " bytes" +
          ", parsed 0 rows" +
          ", fingerprint=" + JSON.stringify(attempt.fingerprint) +
          ", bundle_hints=" + JSON.stringify(attempt.bundle_hints)
        ))
      )
      .join("; ");
    throw new Error(
      "BSE SME IPO audit found zero parseable constituents across official sources. " + detail
    );
  }

  return { attempts, rows };
}

async function run() {
  const records = recoveryFiles().flatMap((file) => {
    const year = Number(path.basename(path.dirname(file)));
    const recovery = JSON.parse(fs.readFileSync(file, "utf8"));
    return (recovery.records || []).map((record) => ({ year, record }));
  });

  const { attempts, rows: indexRows } = await collectBseSmeIpoIndexRows();
  const stats = {
    source_attempts: attempts.map((attempt) => ({
      name: attempt.name,
      format: attempt.format,
      url: attempt.url,
      ok: attempt.ok,
      status: attempt.status,
      response_bytes: attempt.response_bytes,
      parsed_rows: attempt.rows.length,
      fingerprint: attempt.fingerprint,
      error: attempt.error
    })),
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
    unmatched_candidates: unmatched,
    scope_note:
      "Current BSE SME IPO index membership is a discovery aid, not a complete historical BSE IPO universe. " +
      "Unmatched companies still require issuer-specific official listing evidence before materialization."
  }, null, 2));
}

const isMain = process.argv[1] &&
  pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run().catch((error) => {
  console.error(error);
  process.exit(1);
});
