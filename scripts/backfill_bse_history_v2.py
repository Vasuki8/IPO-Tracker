#!/usr/bin/env python3
"""Phase 4.5A historical BSE backfill using exchange-detail parser v2."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# Importing v2 first patches enrich_exchange_details.parse_detail_html in this
# process. backfill_bse_history imports that same module object and therefore
# reuses all of its existing archive/matching/cooldown logic with the v2 parser.
import enrich_exchange_details_v2 as detail_v2  # noqa: E402,F401
import backfill_bse_history as base  # noqa: E402

base.detail.parse_detail_html = detail_v2.parse_detail_html

history_form_payload = base.history_form_payload
history_index = base.history_index
fetch_history_index = base.fetch_history_index
is_candidate = base.is_candidate
mark_attempt = base.mark_attempt


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
