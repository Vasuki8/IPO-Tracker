#!/usr/bin/env python3
"""Run validated priority offer-document fallbacks with the current parser."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import enrich_issuer_offer_docs as base  # noqa: E402
import run_offer_docs_v11 as parser_v11  # noqa: E402

# Route validated fallbacks through the current parser while retaining the base
# module's exact-host, PDF-magic, issuer-identity and fill-only merge gates.
base.parser_v4 = parser_v11
base.PARSER_VERSION = parser_v11.PARSER_VERSION
base._extract_targeted_full_text = parser_v11.extract_targeted_pdf_text

_ORIGINAL_MERGE = base.merge_issuer_enrichment


def merge_validated_offer_enrichment(
    record,
    parsed,
    doc,
    *,
    pdf_hash,
    pages_read,
    page_count,
):
    """Reuse the safe fill-only merge but preserve non-issuer provenance exactly."""
    changed = _ORIGINAL_MERGE(
        record,
        parsed,
        doc,
        pdf_hash=pdf_hash,
        pages_read=pages_read,
        page_count=page_count,
    )

    extraction_source = str(doc.get("extractionSource") or "").strip()
    document_source = str(doc.get("documentSource") or "").strip()
    source_name = str(doc.get("sourceName") or "").strip()
    source_kind = str(doc.get("sourceKind") or "").strip()
    source_page = str(doc.get("sourcePage") or doc.get("url") or "")
    url = str(doc.get("url") or "")

    if extraction_source and isinstance(record.get("issuerDocumentExtraction"), dict):
        record["issuerDocumentExtraction"]["source"] = extraction_source

    if document_source:
        for item in record.get("documents") or []:
            if isinstance(item, dict) and str(item.get("url") or "") == url:
                item["source"] = document_source

    if source_name or source_kind:
        for source in record.get("sources") or []:
            if not isinstance(source, dict) or str(source.get("url") or "") != source_page:
                continue
            if source_name:
                source["name"] = source_name
            if source_kind:
                source["kind"] = source_kind

    return changed


base.merge_issuer_enrichment = merge_validated_offer_enrichment

# Most entries are issuer-hosted PDFs. Some priority records deliberately use
# official exchange or registrar mirrors when the SEBI PDF host is unavailable.
# Every fallback still goes through exact-host, PDF-magic, issuer-identity and
# fill-only gates before any value is merged.
base.ISSUER_DOCUMENTS.update(
    {
        "om-galaxy-limited": {
            "company": "OM Galaxy Limited",
            "url": "https://omgalaxymould.com/wp-content/uploads/2026/09/Project-Om_-RHP_with_RFS.pdf",
            "host": "omgalaxymould.com",
            "type": "RHP",
            "title": "Red Herring Prospectus",
            "sourcePage": "https://omgalaxymould.com/",
        },
        "injecto-polymers-limited": {
            "company": "Injecto Polymers Limited",
            "url": "https://ipostatus.integratedregistry.in/PDFFILES/INJECTORHP.pdf",
            "host": "ipostatus.integratedregistry.in",
            "type": "RHP",
            "title": "Red Herring Prospectus",
            "sourcePage": "https://ipostatus.integratedregistry.in/RegistrarsToSTANew.aspx",
            "extractionSource": "Registrar website",
            "documentSource": "Integrated Registry",
            "sourceName": "Integrated Registry offer document",
            "sourceKind": "registrar-filing",
        },
        "manika": {
            "company": "Manika Plastech Limited",
            "url": "https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/1788774340354.pdf",
            "host": "www.sebi.gov.in",
            "type": "RHP",
            "title": "Red Herring Prospectus",
            "sourcePage": "https://www.sebi.gov.in/filings/public-issues/sep-2026/manika-plastech-limited-rhp_104296.html",
            "extractionSource": "SEBI",
            "documentSource": "SEBI",
            "sourceName": "SEBI Red Herring Prospectus",
            "sourceKind": "regulatory-filing",
        },
        "shakti-polytarp-limited": {
            "company": "Shakti Polytarp Limited",
            "url": "https://shaktipolytarp.com/wp-content/uploads/2025/10/DRHP_Shakti_29092025.pdf",
            "host": "shaktipolytarp.com",
            "type": "DRHP",
            "title": "Draft Red Herring Prospectus",
            "sourcePage": "https://shaktipolytarp.com/ipo-drhp-and-industry-report/",
        },
        "vama-wovenfab-limited": {
            "company": "Vama Wovenfab Limited",
            "url": "https://vamawoven.com/wp-content/uploads/2026/09/RHP_VamaWovenfabLimited-2.pdf",
            "host": "vamawoven.com",
            "type": "RHP",
            "title": "Red Herring Prospectus",
            "sourcePage": "https://vamawoven.com/rhp/",
        },
        "sunshine": {
            "company": "Sunshine Pictures Limited",
            "url": "https://www.bseindia.com/downloads/ipo/361148/ipo_T3/Prospectus_20260821184134.pdf",
            "host": "www.bseindia.com",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://www.bseindia.com/downloads/ipo/361148/ipo_T3/Prospectus_20260821184134.pdf",
            "extractionSource": "BSE",
            "documentSource": "BSE",
            "sourceName": "BSE final Prospectus",
            "sourceKind": "exchange-filing",
        },
        "symbiotec": {
            "company": "Symbiotec Pharmalab Limited",
            "url": "https://nsearchives.nseindia.com/corporate/FP_INE899I01028_31AUG2026.pdf",
            "host": "nsearchives.nseindia.com",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://nsearchives.nseindia.com/corporate/FP_INE899I01028_31AUG2026.pdf",
            "extractionSource": "NSE",
            "documentSource": "NSE",
            "sourceName": "NSE final Prospectus",
            "sourceKind": "exchange-filing",
        },
        "pranav": {
            "company": "Pranav Constructions Limited",
            "url": "https://www.bseindia.com/downloads/ipo/335516/IPO%20Open/6RHPSigned_20260903150028.pdf",
            "host": "www.bseindia.com",
            "type": "RHP",
            "title": "Red Herring Prospectus",
            "sourcePage": "https://www.bseindia.com/downloads/ipo/335516/IPO%20Open/6RHPSigned_20260903150028.pdf",
            "extractionSource": "BSE",
            "documentSource": "BSE",
            "sourceName": "BSE Red Herring Prospectus",
            "sourceKind": "exchange-filing",
        },
        "augmont": {
            "company": "Augmont Enterprises Limited",
            "url": "https://nsearchives.nseindia.com/corporate/FP_INE16W401027_27AUG2026.pdf",
            "host": "nsearchives.nseindia.com",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://nsearchives.nseindia.com/corporate/FP_INE16W401027_27AUG2026.pdf",
            "extractionSource": "NSE",
            "documentSource": "NSE",
            "sourceName": "NSE final Prospectus",
            "sourceKind": "exchange-filing",
        },
        "tempsens": {
            "company": "Tempsens Instruments (India) Limited",
            "url": "https://nsearchives.nseindia.com/corporate/FP_INE1KZI01025_25AUG2026.pdf",
            "host": "nsearchives.nseindia.com",
            "type": "Prospectus",
            "title": "Prospectus",
            "sourcePage": "https://nsearchives.nseindia.com/corporate/FP_INE1KZI01025_25AUG2026.pdf",
            "extractionSource": "NSE",
            "documentSource": "NSE",
            "sourceName": "NSE final Prospectus",
            "sourceKind": "exchange-filing",
        },
    }
)


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
