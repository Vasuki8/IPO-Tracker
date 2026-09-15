#!/usr/bin/env python3
"""Compatibility shim for the canonical legacy offer-document parser.

The historical v2-v14 wrapper stack has been flattened into
``legacy_offer_parser``. Keep this import surface temporarily so existing tests
and any external/manual invocation of the old v14 entrypoint continue to work
while callers migrate to the canonical module.
"""
from legacy_offer_parser import *  # noqa: F401,F403


if __name__ == "__main__":
    raise SystemExit(main())
