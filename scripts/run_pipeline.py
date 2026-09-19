"""One operational entrypoint with bounded, independently reported stages.

Canonical static IPO data follows a Final-Prospectus-only source policy. Market
and exchange collectors remain responsible for discovery, lifecycle, subscription
and post-listing data; their offer terms are observations, not canonical static
fields.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from accepted_data_guard import assert_preserved

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/ipos.json"
MEANINGFUL_FIELDS = (
    "id", "symbol", "company", "openDate", "closeDate", "listingDate", "priceBand",
    "lotSize", "issueSizeCr", "issueComposition", "leadManagers", "registrar",
    "financials", "shareholding", "subscription", "listing", "performance",
    "activeOfferTerms", "dataCorrections", "staticFieldProvenance",
    "documentFieldProvenance", "subscriptionHistory", "universeAdmission",
    "sourceObservationHistory",
)
PIPELINE_REPORTS: dict[str, dict] = {}
LAST_SUPPORT_REBUILD_HASH: str | None = None
DEADLINE: float | None = None


def content_hash(payload):
    rows = [{field: row.get(field) for field in MEANINGFUL_FIELDS} for row in payload.get("ipos", [])]
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def support_hash(payload):
    rows = payload.get("ipos") or []
    return hashlib.sha256(json.dumps(rows, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def _load_bytes(raw: bytes):
    return json.loads(raw)


def step(script, *args, timeout=600):
    if DEADLINE is not None:
        remaining = DEADLINE - time.monotonic()
        if remaining <= 20:
            report = {"stage": script, "status": "deferred", "exitCode": None, "durationSeconds": 0, "checkedAt": datetime.now(timezone.utc).isoformat(), "diagnostics": "Pipeline time budget exhausted; retained for a later run"}
            PIPELINE_REPORTS[script] = report
            print(json.dumps(report), flush=True)
            return report
        timeout = min(timeout, remaining - 10)
    before_bytes = DATA.read_bytes()
    before_payload = _load_bytes(before_bytes)
    before_hash = content_hash(before_payload)
    start = time.monotonic()
    try:
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        log = result.stdout or ""
        exit_code = result.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode(errors="replace")
        log = str(stdout) + "\nStage exceeded its bounded run budget"
        exit_code = 124
    try:
        after_bytes = DATA.read_bytes()
        if after_bytes == before_bytes:
            payload = before_payload
            changed = False
        else:
            payload = _load_bytes(after_bytes)
            assert_preserved(before_payload, payload)
            changed = content_hash(payload) != before_hash
    except (ValueError, OSError, json.JSONDecodeError) as error:
        DATA.write_bytes(before_bytes)
        payload = before_payload
        changed = False
        exit_code = 1
        log += "\nRestored the previous valid dataset after an incomplete write"
        log += "\n" + str(error)
    blocked = bool(re.search(r"403|Forbidden|ConnectTimeout|ConnectionError|source_blocked|[\"']failed[\"']\s*:\s*[1-9]", log, re.I))
    outcome = "failed" if exit_code else "updated" if changed else "source_blocked" if blocked else "no_change"
    report = {"stage": script, "status": outcome, "exitCode": exit_code, "durationSeconds": round(time.monotonic() - start, 2), "checkedAt": datetime.now(timezone.utc).isoformat(), "diagnostics": log[-1800:]}
    PIPELINE_REPORTS[script] = report
    print(json.dumps(report), flush=True)
    return report


def flush_pipeline_reports():
    if not PIPELINE_REPORTS:
        return False
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    stages = payload.setdefault("meta", {}).setdefault("pipelineStages", {})
    stages.update(PIPELINE_REPORTS)
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def rebuild(force: bool = False):
    global LAST_SUPPORT_REBUILD_HASH
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    current_hash = support_hash(payload)
    if not force and current_hash == LAST_SUPPORT_REBUILD_HASH:
        print("Support artifacts unchanged; skipping duplicate rebuild", flush=True)
        return False
    for script in ("audit_data_completeness.py", "build_missing_queue.py", "validate_data.py", "phase_status.py", "build_performance_summary.py"):
        subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, check=True)
    LAST_SUPPORT_REBUILD_HASH = support_hash(json.loads(DATA.read_text(encoding="utf-8")))
    return True


def discover_and_parse_final_prospectuses(priority_max: int, *, document_limit: int, parse_limit: int):
    step("enrich_sebi_priority_registers_v2.py", "--priority-max", str(priority_max), "--search-limit", str(max(20, document_limit)), timeout=300)
    step("enrich_sebi_document_links.py", "--priority-max", str(priority_max), "--limit", str(max(20, document_limit)), timeout=300)
    step("collect_nse_offer_filings_final_policy.py", "--limit", str(max(50, document_limit * 3)), "--documents-limit", str(document_limit), timeout=600)
    # A newly discovered true Final Prospectus can invalidate legacy/RHP/abridged
    # provenance on a record that was not actionable when this run began. Apply
    # the source policy and rebuild the authoritative queue before parsing so the
    # canonical parser can revalidate that record in this same collection run.
    step("enforce_final_prospectus_policy.py")
    rebuild()
    step("run_offer_documents.py", "--limit", str(parse_limit), "--workers", "4" if parse_limit >= 30 else "2", timeout=2400 if parse_limit >= 30 else 900)
    step("run_issuer_offer_docs.py", "--priority-max", str(priority_max), "--limit", str(max(10, min(parse_limit, 30))), timeout=1200)
    step("enforce_final_prospectus_policy.py")


def maintain_filings():
    rebuild()
    queue = json.loads((ROOT / "data/missing_queue.json").read_text(encoding="utf-8"))
    if not any(row.get("priority", 9) <= 3 for row in queue["queue"]):
        return
    discover_and_parse_final_prospectuses(3, document_limit=10, parse_limit=12)


def run(mode: str):
    global LAST_SUPPORT_REBUILD_HASH
    LAST_SUPPORT_REBUILD_HASH = None
    step("record_integrity.py")
    step("apply_corrections.py")
    step("enforce_final_prospectus_policy.py")
    # Policy enforcement can turn populated legacy values into provenance gaps.
    # Rebuild now so discovery in this same run sees those targets.
    rebuild()

    if mode == "core":
        step("run_update_final_policy.py", "--history-days", "1", "--sebi-pages", "4", timeout=900)
        step("record_integrity.py")
        step("enforce_final_prospectus_policy.py")
        step("normalize_source_health.py")
        maintain_filings()
    if mode in {"subscriptions", "repair"}:
        step("run_priority_subscriptions_v3.py", "--limit", "30", timeout=900)
    if mode in {"maintenance", "repair", "p4"}:
        parse_limit = 100 if mode == "repair" else 40 if mode == "p4" else 20
        discover_and_parse_final_prospectuses(4, document_limit=20, parse_limit=parse_limit)
    if mode in {"maintenance", "filings"}:
        maintain_filings()

    rebuild()
    phase = json.loads((ROOT / "data/phase_status.json").read_text(encoding="utf-8"))
    if mode in {"maintenance", "p5"} and phase["p5"]["status"] == "enabled":
        step("collect_nse_offer_filings_final_policy.py", "--history-days", "10000", "--limit", "100", "--documents-limit", "20", timeout=900)
        step("run_offer_documents.py", "--limit", "100", "--workers", "4", timeout=2400)
        step("run_issuer_offer_docs.py", "--priority-max", "5", "--limit", "30", timeout=1200)
        step("enforce_final_prospectus_policy.py")
        rebuild()
    if mode in {"maintenance", "performance"} and phase["p4"]["status"] == "complete":
        step("collect_price_history.py", "--limit", "30", timeout=600)
        step("performance_tracking.py", "--limit", "20", timeout=300)
    step("record_integrity.py")
    step("enforce_final_prospectus_policy.py")
    rebuild()


def main():
    global DEADLINE
    cli = argparse.ArgumentParser()
    cli.add_argument("--mode", choices=["core", "subscriptions", "filings", "maintenance", "repair", "p4", "p5", "performance"], default="core")
    cli.add_argument("--budget-minutes", type=float, default=60)
    args = cli.parse_args()
    DEADLINE = time.monotonic() + max(1, min(65, args.budget_minutes)) * 60
    try:
        run(args.mode)
    finally:
        flush_pipeline_reports()


if __name__ == "__main__":
    main()
