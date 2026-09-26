import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const DEFAULT_REVIEW = "data/discovery/excluded-event-issuer-historical-ipo-review-2026-09-26.json";
export const DEFAULT_RECEIPT = "data/evidence/historical-ipo-nine-source-receipt-2026-09-26.json";
export const MAX_SOURCE_BYTES = 60 * 1024 * 1024;
export const MAX_TOTAL_BYTES = 500 * 1024 * 1024;
const USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36";

export const sha256 = (value) => createHash("sha256").update(value).digest("hex");
const validHash = (value) => typeof value === "string" && /^[a-f0-9]{64}$/.test(value);
const stamp = (value) => typeof value === "string" && Number.isFinite(Date.parse(value));

export function trustedHistoricalSourceUrl(value) {
  try {
    const url = new URL(String(value));
    if (url.protocol !== "https:" || url.username || url.password) return null;
    const allowed = new Set([
      "nsearchives.nseindia.com",
      "archives.nseindia.com",
      "www.visioninfraindia.com",
      "visioninfraindia.com"
    ]);
    if (!allowed.has(url.hostname.toLowerCase())) return null;
    return url.href;
  } catch {
    return null;
  }
}

function safeFilePart(value) {
  return String(value ?? "").replace(/[^A-Za-z0-9._-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 120);
}

function detectedType(bytes, contentType, sourceUrl) {
  const ct = String(contentType ?? "").toLowerCase();
  if (bytes.subarray(0, 5).toString("ascii") === "%PDF-") return { kind: "pdf", extension: ".pdf" };
  const prefix = bytes.subarray(0, Math.min(bytes.length, 512)).toString("utf8").trimStart().toLowerCase();
  if (ct.includes("text/html") || prefix.startsWith("<!doctype html") || prefix.startsWith("<html")) return { kind: "html", extension: ".html" };
  try {
    const ext = path.extname(new URL(sourceUrl).pathname).toLowerCase();
    if (ext === ".html" || ext === ".htm") return { kind: "html", extension: ".html" };
  } catch {}
  return null;
}

async function readLimitedBody(response, maxBytes = MAX_SOURCE_BYTES) {
  if (!response.body) {
    const bytes = Buffer.from(await response.arrayBuffer());
    if (bytes.length > maxBytes) throw new Error("historical_source_size_limit");
    return bytes;
  }
  const chunks = [];
  let size = 0;
  for await (const chunk of response.body) {
    size += chunk.length;
    if (size > maxBytes) throw new Error("historical_source_size_limit");
    chunks.push(Buffer.from(chunk));
  }
  return Buffer.concat(chunks);
}

export function validateHistoricalReview(review) {
  if (review?.schema_version !== "1.0.0" ||
      review?.status !== "historical_ipo_coverage_verified_import_pending" ||
      review?.result?.historical_ipos_verified !== 9 ||
      !Array.isArray(review.decisions) || review.decisions.length !== 9 ||
      !Array.isArray(review.sources) || review.sources.length < 9) {
    throw new Error("invalid_historical_ipo_review");
  }
  const keys = new Set();
  const urls = new Set();
  for (const source of review.sources) {
    if (!source?.key || keys.has(source.key)) throw new Error("duplicate_or_missing_historical_source_key");
    if (!trustedHistoricalSourceUrl(source.url) || urls.has(source.url)) throw new Error("invalid_or_duplicate_historical_source_url");
    keys.add(source.key);
    urls.add(source.url);
  }
  return { source_keys: keys, source_urls: urls };
}

export async function collectHistoricalIpoEvidence({
  review,
  reviewBytes,
  evidenceDir,
  fetchImpl = fetch,
  clock = () => new Date().toISOString(),
  maxSourceBytes = MAX_SOURCE_BYTES,
  maxTotalBytes = MAX_TOTAL_BYTES
}) {
  validateHistoricalReview(review);
  if (!Buffer.isBuffer(reviewBytes)) reviewBytes = Buffer.from(reviewBytes);
  fs.mkdirSync(evidenceDir, { recursive: true });

  const documents = [];
  let totalBytes = 0;
  for (const source of review.sources) {
    const requestedAt = clock();
    const requestedUrl = trustedHistoricalSourceUrl(source.url);
    if (!requestedUrl) throw new Error("untrusted_historical_source:" + source.key);

    const response = await fetchImpl(requestedUrl, {
      redirect: "follow",
      signal: AbortSignal.timeout(45000),
      headers: {
        "user-agent": USER_AGENT,
        accept: "application/pdf,text/html,application/xhtml+xml;q=0.9,*/*;q=0.5",
        "cache-control": "no-cache"
      }
    });

    const finalUrl = trustedHistoricalSourceUrl(response.url || requestedUrl);
    if (!response.ok || !finalUrl) throw new Error("historical_source_fetch_failed:" + source.key + ":" + response.status);

    const bytes = await readLimitedBody(response, maxSourceBytes);
    totalBytes += bytes.length;
    if (totalBytes > maxTotalBytes) throw new Error("historical_source_total_size_limit");

    const type = detectedType(bytes, response.headers?.get?.("content-type"), finalUrl);
    if (!type) throw new Error("historical_source_type_unrecognized:" + source.key);

    const evidenceFile = safeFilePart(source.key) + type.extension;
    fs.writeFileSync(path.join(evidenceDir, evidenceFile), bytes);
    documents.push({
      key: source.key,
      authority: source.authority,
      document_type: source.document_type,
      source_url: requestedUrl,
      final_url: finalUrl,
      http_status: response.status,
      content_type: response.headers?.get?.("content-type") ?? null,
      detected_type: type.kind,
      response_bytes: bytes.length,
      response_sha256: sha256(bytes),
      requested_at: requestedAt,
      collected_at: clock(),
      evidence_file: evidenceFile,
      page: source.page ?? null,
      evidence_locator: source.evidence_locator ?? null,
      projection_sha256: source.projection_sha256 ?? null
    });
  }

  const receipt = {
    schema_version: "1.0.0",
    collector_version: "1.0.0",
    status: "complete",
    review_path: DEFAULT_REVIEW,
    review_sha256: sha256(reviewBytes),
    collection_started_at: documents[0]?.requested_at ?? clock(),
    collection_completed_at: documents.at(-1)?.collected_at ?? clock(),
    source_documents_expected: review.sources.length,
    source_documents_collected: documents.length,
    total_response_bytes: totalBytes,
    documents,
    workflow_artifact: null,
    publication_import_allowed: false,
    note: "Original source bytes are retained in the associated GitHub Actions artifact. This durable receipt retains exact official URLs, per-document SHA-256 hashes, byte counts and evidence locators. Historical IPO import remains a separate reviewed step."
  };
  validateHistoricalEvidenceReceipt(receipt, review, reviewBytes);
  return receipt;
}

export function validateHistoricalEvidenceReceipt(receipt, review, reviewBytes) {
  const { source_keys } = validateHistoricalReview(review);
  if (!Buffer.isBuffer(reviewBytes)) reviewBytes = Buffer.from(reviewBytes);
  if (receipt?.schema_version !== "1.0.0" || receipt?.collector_version !== "1.0.0" ||
      receipt?.status !== "complete" || receipt.review_path !== DEFAULT_REVIEW ||
      receipt.review_sha256 !== sha256(reviewBytes) || !stamp(receipt.collection_started_at) ||
      !stamp(receipt.collection_completed_at) || !Array.isArray(receipt.documents) ||
      receipt.documents.length !== review.sources.length ||
      receipt.source_documents_expected !== review.sources.length ||
      receipt.source_documents_collected !== review.sources.length) {
    throw new Error("invalid_historical_evidence_receipt");
  }
  const seenKeys = new Set();
  const seenFiles = new Set();
  let total = 0;
  for (const doc of receipt.documents) {
    if (!source_keys.has(doc.key) || seenKeys.has(doc.key) || seenFiles.has(doc.evidence_file) ||
        !trustedHistoricalSourceUrl(doc.source_url) || !trustedHistoricalSourceUrl(doc.final_url) ||
        doc.http_status !== 200 || !["pdf", "html"].includes(doc.detected_type) ||
        !Number.isInteger(doc.response_bytes) || doc.response_bytes <= 0 ||
        !validHash(doc.response_sha256) || !stamp(doc.requested_at) || !stamp(doc.collected_at) ||
        typeof doc.evidence_file !== "string" || !/^[A-Za-z0-9._-]+\.(?:pdf|html)$/.test(doc.evidence_file)) {
      throw new Error("invalid_historical_evidence_document:" + (doc?.key ?? "unknown"));
    }
    seenKeys.add(doc.key);
    seenFiles.add(doc.evidence_file);
    total += doc.response_bytes;
  }
  if (total !== receipt.total_response_bytes) throw new Error("historical_evidence_byte_count_mismatch");
  return { documents: receipt.documents.length, bytes: total };
}

async function run() {
  const args = Object.fromEntries(process.argv.slice(2).map((arg) => {
    const i = arg.indexOf("=");
    if (i < 1) throw new Error("arguments_must_use_equals");
    return [arg.slice(0, i), arg.slice(i + 1)];
  }));
  const reviewPath = args["--review"] || DEFAULT_REVIEW;
  const evidenceDir = args["--evidence-dir"];
  const receiptPath = args["--receipt"];
  if (!evidenceDir || !receiptPath) throw new Error("--evidence-dir and --receipt are required");

  const reviewBytes = fs.readFileSync(path.join(ROOT, reviewPath));
  const review = JSON.parse(reviewBytes);
  const receipt = await collectHistoricalIpoEvidence({ review, reviewBytes, evidenceDir });
  fs.mkdirSync(path.dirname(receiptPath), { recursive: true });
  fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 2) + "\n");
  console.log(JSON.stringify({ historical_ipo_evidence: {
    documents: receipt.source_documents_collected,
    bytes: receipt.total_response_bytes,
    review_sha256: receipt.review_sha256
  }}, null, 2));
}

const isMain = process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (isMain) run().catch((error) => { console.error(error); process.exit(1); });
