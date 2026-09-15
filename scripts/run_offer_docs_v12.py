#!/usr/bin/env python3
"""Compatibility alias for legacy offer parser version 12."""
import legacy_offer_parser as _canonical
from legacy_offer_parser import *  # noqa: F401,F403

PARSER_VERSION = 12


def apply_enrichment(record, parsed, doc, pdf_hash, pages_read, page_count):
    _canonical.apply_enrichment(record, parsed, doc, pdf_hash, pages_read, page_count)
    extraction = record.get("offerDocumentExtraction")
    if isinstance(extraction, dict):
        extraction["parserVersion"] = PARSER_VERSION
    observation = (record.get("observations") or {}).get("SEBI-offer")
    if isinstance(observation, dict):
        observation["parserVersion"] = PARSER_VERSION


if __name__ == "__main__":
    raise SystemExit(main())
