"""One operational entrypoint with bounded, independently reported stages.

Stage diagnostics are accumulated in memory and flushed once at the end. Support
artifacts are rebuilt only when IPO records have changed since the last rebuild,
so maintenance mode does not repeatedly rescan the same multi-megabyte dataset.
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

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/ipos.json"
MEANINGFUL_FIELDS = (
    "id", "symbol", "company", "openDate", "closeDate", "listingDate", "priceBand",
    "lotSize", "issueSizeCr", "issueComposition", "leadManagers", "registrar",
    "financials", "shareholding", "subscription", "listing", "performance",
)
PIPELINE_REPORTS: dict[str, dict] = {}
LAST_SUPPORT_REBUILD_HASH: str | None = None


def content_hash(payload):
    rows = [{field: row.get(field) for field in MEANINGFUL_FIELDS} for row in payload.get("ipos", [])]
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def support_hash(payload):
    """Fingerprint all IPO record content while ignoring volatile top-level metadata."""
    rows = payload.get("ipos") or []
    return hashlib.sha256(
        json.dumps(rows, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def _load_bytes(raw: bytes):
    return json.loads(raw)


def step(script, *args, timeout=600):
    """Run one collector stage and retain a diagnostic report without extra data writes."""
    before_bytes = DATA.read_bytes()
    before_payload = _load_bytes(before_bytes)
    before_hash = content_hash(before_payload)
    start = time.monotonic()

    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
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
            changed = content_hash(payload) != before_hash
    except (ValueError, OSError, json.JSONDecodeError):
        DATA.write_bytes(before_bytes)
        payload = before_payload
        changed = False
        exit_code = 1
        log += "\nRestored the previous valid dataset after an incomplete write"

    blocked = bool(
        re.search(
            r"403|Forbidden|ConnectTimeout|ConnectionError|source_blocked|[\"']failed[\"']\s*:\s*[1-9]",
            log,
            re.I,
        )
    )
    outcome = "failed" if exit_code else "updated" if changed else "source_blocked" if blocked else "no_change"
    report = {
        "stage": script,
        "status": outcome,
        "exitCode": exit_code,
        "durationSeconds": round(time.monotonic() - start, 2),
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "diagnostics": log[-1800:],
    }
    PIPELINE_REPORTS[script] = report
    print(json.dumps(report), flush=True)
    return report


def flush_pipeline_reports():
    """Persist all stage diagnostics with one canonical dataset rewrite."""
    if not PIPELINE_REPORTS:
        return False
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    stages = payload.setdefault("meta", {}).setdefault("pipelineStages", {})
    stages.update(PIPELINE_REPORTS)
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def rebuild(force: bool = False):
    """Rebuild derived support files once per distinct IPO-record state."""
    global LAST_SUPPORT_REBUILD_HASH
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    current_hash = support_hash(payload)
    if not force and current_hash == LAST_SUPPORT_REBUILD_HASH:
        print("Support artifacts unchanged; skipping duplicate rebuild", flush=True)
        return False

    for script in (
        "audit_data_completeness.py",
        "build_missing_queue.py",
        "validate_data.py",
        "phase_status.py",
        "build_performance_summary.py",
    ):
        subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, check=True)

    # Derived builders do not intentionally mutate IPO records. Re-read before
    # remembering the fingerprint so an unexpected mutation cannot hide work.
    LAST_SUPPORT_REBUILD_HASH = support_hash(json.loads(DATA.read_text(encoding="utf-8")))
    return True


def maintain_filings():
    rebuild()
    queue = json.loads((ROOT / "data/missing_queue.json").read_text(encoding="utf-8"))
    if not any(row.get("priority", 9) <= 3 for row in queue["queue"]):
        return
    step("enrich_sebi_priority_registers_v2.py", "--priority-max", "3", "--search-limit", "20", timeout=300)
    step("enrich_sebi_document_links.py", "--priority-max", "3", "--limit", "20", timeout=300)
    step("enrich_recent_offer_terms.py", "--priority-max", "3", "--limit", "20", timeout=300)
    step("run_offer_documents.py", "--limit", "8", "--workers", "2", timeout=600)
    step("apply_verified_filing_offer_fields.py")


def run(mode: str):
    global LAST_SUPPORT_REBUILD_HASH
    LAST_SUPPORT_REBUILD_HASH = None
    step("record_integrity.py")
    step("apply_corrections.py")

    if mode == "core":
        step("run_update_v2.py", "--history-days", "1", "--sebi-pages", "4", timeout=900)
        step("record_integrity.py")
        step("normalize_source_health.py")
        maintain_filings()

    if mode == "subscriptions":
        step("run_priority_subscriptions_v3.py", "--limit", "30", timeout=900)

    if mode in {"maintenance", "repair"}:
        step(
            "run_offer_documents.py",
            "--limit", "100" if mode == "repair" else "12",
            "--workers", "4" if mode == "repair" else "2",
            timeout=2400 if mode == "repair" else 1500,
        )
        step("collect_final_issue_prices.py", "--history-days", "730", "--max-reports", "36", timeout=600)

    if mode in {"maintenance", "filings"}:
        maintain_filings()

    rebuild()

    if mode in {"maintenance", "p4"}:
        step("enrich_nse_issue_information.py", "--limit", "30", "--history-days", "730", "--retry-days", "7", timeout=600)
        step("backfill_recent_sebi_other_docs_lot_sizes.py", "--limit", "125", "--max-listing-pages", "40", timeout=600)
        step("backfill_recent_nse_lot_sizes.py", "--limit", "25", timeout=500)
        step("backfill_p4_lot_sizes.py", "--history-days", "730", "--limit", "30", "--core-only", "--retry-days", "1", timeout=600)
        rebuild()

    phase = json.loads((ROOT / "data/phase_status.json").read_text(encoding="utf-8"))
    if mode in {"maintenance", "p5"} and phase["p5"]["status"] == "enabled":
        step("collect_final_issue_prices.py", "--history-days", "10000", "--max-reports", "100", timeout=900)
        step("enrich_nse_primary_market_reports_v3.py", "--history-days", "10000", "--max-reports", "100", timeout=900)
        step("backfill_bse_history.py", "--history-days", "10000", "--limit", "40", "--core-only", "--oldest-first", "--retry-days", "7", timeout=600)

    if mode in {"maintenance", "performance"} and phase["p4"]["status"] == "complete":
        step("collect_final_issue_prices.py", "--history-days", "730", "--max-reports", "36", timeout=600)
        step("collect_price_history.py", "--limit", "30", timeout=600)
        step("performance_tracking.py", "--limit", "20", timeout=300)

    step("record_integrity.py")
    rebuild()


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument(
        "--mode",
        choices=["core", "subscriptions", "filings", "maintenance", "repair", "p4", "p5", "performance"],
        default="core",
    )
    args = cli.parse_args()
    try:
        run(args.mode)
    finally:
        flush_pipeline_reports()


if __name__ == "__main__":
    main()
