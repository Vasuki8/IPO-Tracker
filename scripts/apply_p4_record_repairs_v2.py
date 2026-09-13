#!/usr/bin/env python3
"""Apply source-backed P4 repairs with duplicate-id-safe record selection.

The original repair functions remain authoritative for identity guards, source
stamps, fill-only term repairs and dataAvailability decisions. Version 2 changes
only how a target row is selected: every candidate sharing an id is retained and
exact company/symbol/open-date identity must produce one unique match.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import apply_p4_record_repairs as base  # noqa: E402

DATA_FILE = base.DATA_FILE


def select_unique_identity(
    records: list[dict[str, Any]],
    record_id: str,
    entry: dict[str, Any],
) -> dict[str, Any] | None:
    matches = [
        record
        for record in records
        if isinstance(record, dict) and base._identity_matches(record_id, record, entry)
    ]
    return matches[0] if len(matches) == 1 else None


def main() -> int:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = [row for row in payload.get("ipos") or [] if isinstance(row, dict)]

    repaired = resolved = ambiguous_or_missing = 0
    for record_id, entry in base.VERIFIED_IDENTITY_REPAIRS.items():
        record = select_unique_identity(records, record_id, entry)
        if record is None:
            ambiguous_or_missing += 1
            print(f"P4 repair v2: missing/ambiguous record {record_id}")
            continue
        changed = base.apply_identity_repair(record_id, record, entry)
        if changed:
            repaired += 1
            print(f"P4 repair v2: {record_id} changed={','.join(changed)}")

    for record_id, entry in base.AVAILABILITY_RESOLUTIONS.items():
        record = select_unique_identity(records, record_id, entry)
        if record is None:
            ambiguous_or_missing += 1
            print(f"P4 availability v2: missing/ambiguous record {record_id}")
            continue
        changed = base.apply_availability_resolution(record_id, record, entry)
        if changed:
            resolved += 1
            print(f"P4 availability v2: {record_id} resolved={','.join(changed)}")

    payload.setdefault("meta", {}).setdefault("sourceHealth", {})["P4-verified-record-repairs"] = {
        "ok": ambiguous_or_missing == 0,
        "selectorVersion": 2,
        "identityRepairEntries": len(base.VERIFIED_IDENTITY_REPAIRS),
        "identityRecordsUpdated": repaired,
        "availabilityEntries": len(base.AVAILABILITY_RESOLUTIONS),
        "availabilityRecordsUpdated": resolved,
        "missingOrAmbiguous": ambiguous_or_missing,
        "checkedAt": base.core.now_ist().isoformat(timespec="seconds"),
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "P4 verified repairs v2: "
        f"repaired={repaired}, availability_resolved={resolved}, "
        f"missing_or_ambiguous={ambiguous_or_missing}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
