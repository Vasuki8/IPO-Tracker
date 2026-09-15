#!/usr/bin/env python3
"""Compatibility alias for legacy offer parser version 11."""
import legacy_offer_parser as _canonical
from legacy_offer_parser import *  # noqa: F401,F403

PARSER_VERSION = 11
_explicit_ab_total = _canonical._explicit_ab_total
_explicit_combined_ownership = _canonical._explicit_combined_ownership


if __name__ == "__main__":
    raise SystemExit(main())
