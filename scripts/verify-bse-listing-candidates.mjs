import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import { parseBseListingNotice } from "./extract-bse-ipo-fields.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const MAX_CANDIDATES = 15;
export const VERIFIER_VERSION = "1.1.0";
const MAX_RESPONSE_BYTES = 2 * 1024 * 1024;
const HOME = "https://www.bseindia.com/";
const USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";
export const sha256 = (value) => createHash("sha256").update(value).digest("hex");

export function noticeText(html) {
  return String(html ?? "")
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, " ")
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;|&#160;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;|&apos;/gi, "'")
    .replace(/\s+/g, " ").trim();
}
export function issuerKey(value) {
  return String(value ?? "").toLowerCase().replace(/&/g, " and ")
    .replace(/\bltd\b/g, "limited").replace(/[^a-z0-9]+/g, " ").trim();
}
export function strictDate(value) {
  const raw = String(value ?? "").trim();
  const months = ["january","february","march","april","may","june","july","august","september","october","november","december"];
  let y, m, d;
  const iso = raw.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  const words = raw.match(/^([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})$/);
  if (iso) [, y, m, d] = iso.map(Number);
  else if (words) { y = Number(words[3]); m = months.indexOf(words[1].toLowerCase()) + 1; d = Number(words[2]); }
  else return null;
  if (y < 2020 || y > 2099 || m < 1 || m > 12 || d < 1 || d > 31) return null;
  const date = new Date(Date.UTC(y, m - 1, d));
  if (date.getUTCFullYear() !== y || date.getUTCMonth() !== m - 1 || date.getUTCDate() !== d) return null;
  return date.toISOString().slice(0, 10);
}
export function listingUrl(noticeNo) {
  if (!/^\d{8}-\d+$/.test(noticeNo)) throw new Error("invalid_listing_notice_number");
  return HOME + "markets/MarketInfo/DispNewNoticesCirculars.aspx?page=" + noticeNo;
}
export function validateBatch(batch) {
  if (batch?.schema_version !== "1.0.0" || !Array.isArray(batch.candidates) ||
      !batch.candidates.length || batch.candidates.length > MAX_CANDIDATES) {
    throw new Error("candidate_batch_must_contain_1_to_15_issuers");
  }
  const codes = new Set(), names = new Set(), notices = new Set();
  for (const c of batch.candidates) {
    if (!c || typeof c.issuer_name !== "string" || !issuerKey(c.issuer_name) ||
        !/^\d{6}$/.test(c.bse_scrip_code) || strictDate(c.listing_date) !== c.listing_date ||
        c.listing_notice_url !== listingUrl(c.listing_notice_no)) throw new Error("invalid_candidate_identity");
    if (codes.has(c.bse_scrip_code) || names.has(issuerKey(c.issuer_name)) || notices.has(c.listing_notice_no)) {
      throw new Error("duplicate_or_conflicting_candidate_identity");
    }
    codes.add(c.bse_scrip_code); names.add(issuerKey(c.issuer_name)); notices.add(c.listing_notice_no);
  }
  return batch.candidates;
}
const unique = (values) => [...new Set(values)];
function scalarMatches(text, pattern) {
  return [...text.matchAll(pattern)].map((m) => ({ value: Number(m[1].replace(/,/g, "")), source_value: m[0] }));
}

// An index reference is never sufficient. The issuer-specific listing response must
// independently confirm every identity component before any market terms are usable.
export function verifyListingHtml(html, candidate, asOf = new Date().toISOString()) {
  const body = noticeText(html);
  const parsed = parseBseListingNotice(body);
  const reasons = [];
  // Header identity excludes historical regulatory notices cited in the body.
  const noticeNos = unique([...body.matchAll(/\bNotice\s+No\.?\s*:?\s*(\d{8}-\d+)\s+Notice Date\b/gi)].map((m) => m[1]));
  const tableIssuer = body.match(/\bName of the company\s+(.{1,180}?)\s+Registered Office\b/i)?.[1] ?? null;
  const bodyIssuer = body.match(/\bthe Equity Shares of\s+(.{1,180}?)\s+shall be listed\b/i)?.[1] ?? null;
  const issuerMentions = [parsed.company, tableIssuer, bodyIssuer].filter(Boolean);
  const issuerNames = unique(issuerMentions.map(issuerKey));
  const issuerName = tableIssuer ?? parsed.company ?? bodyIssuer;
  const publicationRaw = body.match(/\bNotice Date\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\s+Category\b/i)?.[1] ?? null;
  let publicationDate = null;
  if (publicationRaw) {
    const [day, month, year] = publicationRaw.split(/\s+/);
    const m = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"].indexOf(month.toLowerCase()) + 1;
    publicationDate = strictDate(`${year}-${String(m).padStart(2,"0")}-${day.padStart(2,"0")}`);
  }
  const codes = unique([...body.matchAll(/\b(?:Scrip|Security)\s+Code\s*[:\-]?\s*(\d{6})\b/gi)].map((m) => m[1]));
  const dateMatches = [...body.matchAll(/\be(?:ff|\s+)ective\s+from\s+(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s*,?\s*)?([A-Za-z]+\s+\d{1,2},\s*\d{4})/gi)];
  const dates = unique(dateMatches.map((m) => strictDate(m[1])));
  if (!issuerName && !noticeNos.length && !codes.length && !dates.length && !parsed.board) {
    return { status: "unavailable", reasons: ["notice_content_missing"],
      observed_identity: { issuer_name: null, notice_numbers: [], scrip_codes: [], listing_dates: [], board: null },
      facts: null, response_text: body };
  }
  if (issuerNames.length !== 1 || issuerNames[0] !== issuerKey(candidate.issuer_name)) reasons.push("issuer_mismatch_or_missing");
  if (noticeNos.length !== 1 || noticeNos[0] !== candidate.listing_notice_no) reasons.push("notice_number_mismatch_or_missing");
  if (codes.length !== 1 || codes[0] !== candidate.bse_scrip_code) reasons.push("scrip_code_mismatch_or_missing");
  if (dates.length !== 1 || dates[0] == null || dates[0] !== candidate.listing_date) reasons.push("listing_date_mismatch_or_missing");
  if (dates[0] && dates[0] > asOf.slice(0, 10)) reasons.push("listing_date_in_future");
  if (parsed.board !== "SME") reasons.push("sme_segment_not_confirmed");
  if (!/\bEquity Shares\b[\s\S]*?\b(?:listed|admitted)\b/i.test(body)) reasons.push("equity_listing_statement_missing");

  const lots = scalarMatches(body, /\bMarket Lot\s+([0-9][0-9,.]*(?:\s*(?:[-–—]|to)\s*[0-9][0-9,.]*)?)/gi);
  const prices = scalarMatches(body, /\bIssue Price for the current Public issue\s+Rs\.?\s*([0-9][0-9,.]*(?:\s*(?:[-–—]|to)\s*[0-9][0-9,.]*)?)/gi);
  const facts = {};
  for (const [field, matches] of [["market_lot", lots], ["issue_price", prices]]) {
    const values = unique(matches.map((m) => m.value));
    if (values.length > 1 || values.some((v) => !Number.isFinite(v) || v <= 0 || (field === "market_lot" && !Number.isSafeInteger(v)))) {
      reasons.push(field + "_conflict_or_invalid");
    } else if (matches.length) facts[field] = matches[0];
  }
  return {
    status: reasons.length ? "rejected" : "verified", reasons,
    observed_identity: { issuer_name: issuerName, notice_numbers: noticeNos, scrip_codes: codes, listing_dates: dates, board: parsed.board, publication_date: publicationDate, publication_date_raw: publicationRaw },
    facts: reasons.length ? null : { listing_date: { value: dates[0], source_value: dateMatches[0][0] }, ...facts },
    response_text: body
  };
}

async function readBounded(response) {
  const declared = Number(response.headers.get("content-length"));
  if (declared > MAX_RESPONSE_BYTES) throw new Error("response_size_limit");
  const chunks = []; let size = 0;
  for await (const chunk of response.body) {
    size += chunk.length;
    if (size > MAX_RESPONSE_BYTES) throw new Error("response_size_limit");
    chunks.push(Buffer.from(chunk));
  }
  return Buffer.concat(chunks);
}
export async function verifyBatch(batch, { fetchImpl = fetch, evidenceDir = null, now = () => new Date().toISOString() } = {}) {
  const candidates = validateBatch(batch);
  const results = [];
  let cookie = "";
  try {
    const home = await fetchImpl(HOME, { headers: { "user-agent": USER_AGENT }, signal: AbortSignal.timeout(15000) });
    if (home.ok) cookie = (home.headers.getSetCookie?.() || []).map((v) => v.split(";")[0]).join("; ");
    await home.body?.cancel();
  } catch { /* Session priming is optional; notice failures are reported individually. */ }
  if (evidenceDir) fs.mkdirSync(evidenceDir, { recursive: true });
  for (const candidate of candidates) {
    const result = { candidate, status: "unavailable", collected_at: null, source_url: candidate.listing_notice_url };
    try {
      const response = await fetchImpl(candidate.listing_notice_url, {
        headers: { "user-agent": USER_AGENT, accept: "text/html,application/xhtml+xml", referer: HOME, ...(cookie ? { cookie } : {}) },
        signal: AbortSignal.timeout(20000), redirect: "error"
      });
      result.http_status = response.status;
      result.content_type = response.headers.get("content-type");
      if (!response.ok) { await response.body?.cancel(); throw new Error("http_" + response.status); }
      const bytes = await readBounded(response);
      result.collected_at = now();
      result.response_sha256 = sha256(bytes);
      result.response_bytes = bytes.length;
      result.evidence_file = candidate.listing_notice_no + ".html";
      if (evidenceDir) fs.writeFileSync(path.join(evidenceDir, result.evidence_file), bytes);
      Object.assign(result, verifyListingHtml(bytes.toString("utf8"), candidate, result.collected_at));
    } catch (error) {
      result.collected_at = now(); result.error = String(error?.message || error);
    }
    results.push(result);
  }
  const stats = { attempted: results.length, verified: 0, rejected: 0, unavailable: 0 };
  for (const r of results) stats[r.status] += 1;
  return {
    schema_version: "1.0.0", verifier_version: VERIFIER_VERSION, generated_at: now(),
    run_id: process.env.GITHUB_RUN_ID || null, commit_sha: process.env.GITHUB_SHA || null,
    input_report: batch.input_report ?? null,
    status: stats.verified === stats.attempted ? "complete" : stats.verified ? "partial" : "failed",
    stats, results,
    scope_note: "Read-only verification of at most 15 pinned issuer-specific BSE listing notices. This report never materializes IPOs. Index evidence is not listing authority."
  };
}
async function run() {
  const args = Object.fromEntries(process.argv.slice(2).map((a) => { const i = a.indexOf("="); if (i < 0) throw new Error("arguments_require_equals"); return [a.slice(0, i), a.slice(i + 1)]; }));
  if (!args["--input"] || !args["--output"] || Object.keys(args).some((k) => !["--input", "--output", "--evidence-dir"].includes(k))) throw new Error("use --input=<batch.json> --output=<report.json> [--evidence-dir=<dir>]");
  const report = await verifyBatch(JSON.parse(fs.readFileSync(path.resolve(ROOT, args["--input"]), "utf8")), { evidenceDir: args["--evidence-dir"] });
  const output = path.resolve(args["--output"]);
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify({ bse_listing_verification: report.stats, status: report.status }));
  if (report.status !== "complete") process.exitCode = 1;
}
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) run().catch((e) => { console.error(e); process.exitCode = 1; });
