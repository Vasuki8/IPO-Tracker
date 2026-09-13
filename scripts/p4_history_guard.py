#!/usr/bin/env python3
"""Guard the IPO database from non-equity rows in NSE's broad history feed.

NSE's live and upcoming endpoints are IPO-scoped, but /public-past-issues can
contain debt/NCD public issues alongside equity IPOs.  This module deliberately
uses conservative, explicit classification signals. Unknown rows are retained;
only rows with strong non-equity evidence are excluded.

The guard also remembers excluded identities so an old debt row that was already
merged into data/ipos.json can be removed after the normal core refresh. Exact
symbol/date matching prevents deleting a genuine equity IPO merely because the
same issuer later sold debt securities.
"""
from __future__ import annotations

import json
import re
from typing import Any

_NON_EQUITY_PATTERNS = (
    re.compile(r"\bNCD\b", re.I),
    re.compile(r"\bDEBT\b", re.I),
    re.compile(r"\bBONDS?\b", re.I),
    re.compile(r"\bDEBENTURES?\b", re.I),
    re.compile(r"\bZERO[ -]+COUPON\b", re.I),
    re.compile(r"\bNON[ -]+CONVERTIBLE\b", re.I),
    re.compile(r"\bSECURED[ -]+REDEEMABLE\b", re.I),
    re.compile(r"\bUNSECURED[ -]+REDEEMABLE\b", re.I),
)

_SECURITY_FIELDS = (
    "securityType",
    "secType",
    "securityCategory",
    "instrumentType",
    "series",
)
_ISSUE_FIELDS = (
    "issueType",
    "typeOfIssue",
    "issueCategory",
    "category",
)
_DESCRIPTOR_FIELDS = (
    "securityName",
    "issueName",
    "companyName",
    "company",
    "issuerName",
    "name",
)

_state: dict[str, Any] = {
    "seen": 0,
    "kept": 0,
    "excluded": [],
}


def _text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).upper()


def _joined(row: dict[str, Any], fields: tuple[str, ...]) -> str:
    return " | ".join(_text(row.get(field)) for field in fields if row.get(field) not in (None, ""))


def _has_non_equity_marker(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in _NON_EQUITY_PATTERNS)


def classify_nse_historical_issue(row: dict[str, Any]) -> str:
    """Return equity-ipo, non-equity or unknown for one NSE history row.

    Explicit debt/security descriptors always win. Unknown rows are intentionally
    kept because silently dropping an unclassified equity IPO is worse than
    leaving it for later validation.
    """
    row = row or {}
    security = _joined(row, _SECURITY_FIELDS)
    issue = _joined(row, _ISSUE_FIELDS)
    descriptor = _joined(row, _DESCRIPTOR_FIELDS)
    combined = " | ".join(value for value in (security, issue, descriptor) if value)

    if _has_non_equity_marker(combined):
        return "non-equity"

    security_tokens = {
        _text(row.get(field))
        for field in _SECURITY_FIELDS
        if row.get(field) not in (None, "")
    }
    if any(token in {"EQ", "EQUITY", "EQUITY SHARE", "EQUITY SHARES"} for token in security_tokens):
        return "equity-ipo"
    if "EQUITY" in security:
        return "equity-ipo"

    # IPO is accepted only after the stronger debt checks above have passed.
    if re.search(r"\bIPO\b", issue, re.I):
        return "equity-ipo"

    return "unknown"


def reset_state() -> None:
    _state["seen"] = 0
    _state["kept"] = 0
    _state["excluded"] = []


def state_snapshot() -> dict[str, Any]:
    return {
        "seen": int(_state.get("seen") or 0),
        "kept": int(_state.get("kept") or 0),
        "excluded": list(_state.get("excluded") or []),
    }


def excluded_identity(row: dict[str, Any], core: Any) -> dict[str, Any]:
    normalized = core.normalize_nse_record(row, "historical")
    return {
        "matchKey": normalized.get("matchKey"),
        "company": normalized.get("company"),
        "symbol": normalized.get("symbol"),
        "openDate": normalized.get("openDate"),
        "closeDate": normalized.get("closeDate"),
        "securityType": next((row.get(k) for k in _SECURITY_FIELDS if row.get(k) not in (None, "")), None),
        "issueType": next((row.get(k) for k in _ISSUE_FIELDS if row.get(k) not in (None, "")), None),
    }


def record_matches_excluded(record: dict[str, Any], identity: dict[str, Any], core: Any) -> bool:
    """Match only the exact debt issue identity, never issuer name alone."""
    record_key = record.get("matchKey") or core.canonical_company(str(record.get("company") or ""))
    if not record_key or record_key != identity.get("matchKey"):
        return False

    record_symbol = _text(record.get("symbol"))
    excluded_symbol = _text(identity.get("symbol"))
    if record_symbol and excluded_symbol:
        return record_symbol == excluded_symbol

    open_date = identity.get("openDate")
    close_date = identity.get("closeDate")
    return bool(
        open_date
        and close_date
        and record.get("openDate") == open_date
        and record.get("closeDate") == close_date
    )


def install(core: Any) -> None:
    """Install a one-time wrapper around NSEClient.past()."""
    if getattr(core.NSEClient.past, "_p4_ipo_guard", False):
        return

    original_past = core.NSEClient.past

    def guarded_past(self: Any, start: Any, end: Any) -> list[dict[str, Any]]:
        rows = list(original_past(self, start, end) or [])
        kept: list[dict[str, Any]] = []
        excluded: list[dict[str, Any]] = []
        for row in rows:
            if classify_nse_historical_issue(row) == "non-equity":
                excluded.append(excluded_identity(row, core))
            else:
                kept.append(row)

        _state["seen"] = int(_state.get("seen") or 0) + len(rows)
        _state["kept"] = int(_state.get("kept") or 0) + len(kept)
        _state.setdefault("excluded", []).extend(excluded)
        if excluded:
            print(
                f"P4 NSE history guard {start}..{end}: "
                f"kept={len(kept)} excluded_non_equity={len(excluded)}"
            )
        return kept

    guarded_past._p4_ipo_guard = True  # type: ignore[attr-defined]
    core.NSEClient.past = guarded_past


def prune_excluded_from_data(core: Any) -> int:
    """Remove legacy rows that still exactly match excluded non-equity issues."""
    snapshot = state_snapshot()
    excluded = snapshot["excluded"]
    if not excluded:
        return 0

    payload = json.loads(core.DATA_FILE.read_text(encoding="utf-8"))
    records = [row for row in payload.get("ipos") or [] if isinstance(row, dict)]

    by_key: dict[str, list[dict[str, Any]]] = {}
    for identity in excluded:
        key = str(identity.get("matchKey") or "")
        if key:
            by_key.setdefault(key, []).append(identity)

    kept_records: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    for record in records:
        key = record.get("matchKey") or core.canonical_company(str(record.get("company") or ""))
        matches = by_key.get(str(key), [])
        identity = next(
            (item for item in matches if record_matches_excluded(record, item, core)),
            None,
        )
        if identity is None:
            kept_records.append(record)
            continue
        removed.append(
            {
                "company": record.get("company"),
                "symbol": record.get("symbol"),
                "openDate": record.get("openDate"),
                "closeDate": record.get("closeDate"),
            }
        )

    payload["ipos"] = kept_records
    meta = payload.setdefault("meta", {})
    meta["recordCount"] = len(kept_records)
    meta.setdefault("sourceHealth", {})["NSE-history-IPO-filter"] = {
        "ok": True,
        "seen": snapshot["seen"],
        "kept": snapshot["kept"],
        "excludedNonEquity": len(excluded),
        "legacyRowsRemoved": len(removed),
        "removed": removed[:25],
        "checkedAt": core.now_ist().isoformat(timespec="seconds"),
    }
    core.DATA_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        "P4 NSE history guard: "
        f"seen={snapshot['seen']} kept={snapshot['kept']} "
        f"excluded_non_equity={len(excluded)} legacy_removed={len(removed)}"
    )
    return len(removed)
