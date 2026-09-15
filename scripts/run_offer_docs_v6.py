#!/usr/bin/env python3
"""Compatibility alias for legacy offer parser version 6."""
import legacy_offer_parser as _canonical
from legacy_offer_parser import *  # noqa: F401,F403

PARSER_VERSION = 6
_shareholding_score = _canonical._shareholding_score


class _BaseProxy:
    PARSER_VERSION = PARSER_VERSION

    def __getattr__(self, name):
        return getattr(_canonical.base, name)


base = _BaseProxy()


if __name__ == "__main__":
    raise SystemExit(main())
