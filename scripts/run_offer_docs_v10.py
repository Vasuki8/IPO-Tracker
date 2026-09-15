#!/usr/bin/env python3
"""Compatibility alias for legacy offer parser version 10.

The implementation now lives in :mod:`legacy_offer_parser`; this module keeps
historical imports and parser-version assertions stable while avoiding another
copy of the parser stack.
"""
import legacy_offer_parser as _canonical
import run_offer_docs_v9 as v9
from legacy_offer_parser import *  # noqa: F401,F403

PARSER_VERSION = 10
_explicit_ab_total = _canonical._explicit_ab_total


if __name__ == "__main__":
    raise SystemExit(main())
