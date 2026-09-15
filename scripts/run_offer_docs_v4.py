#!/usr/bin/env python3
"""Compatibility alias for legacy offer parser version 4."""
import time
import requests
import legacy_offer_parser as _canonical
from legacy_offer_parser import *  # noqa: F401,F403

PARSER_VERSION = 4
_money_cr_near = _canonical._money_cr_near
_ORIGINAL_DOWNLOAD_PDF = _canonical.base.download_pdf


class _BaseProxy:
    PARSER_VERSION = PARSER_VERSION

    def __getattr__(self, name):
        return getattr(_canonical.base, name)


base = _BaseProxy()


def download_pdf(session, url, *, attempts=3, retry_delay=1.0):
    last_error = None
    for attempt in range(1, max(1, attempts) + 1):
        try:
            return _ORIGINAL_DOWNLOAD_PDF(session, url)
        except (requests.RequestException, OSError) as exc:
            last_error = exc
            if attempt >= attempts:
                raise
            time.sleep(retry_delay * attempt)
    raise last_error or RuntimeError("PDF download failed without an error")


if __name__ == "__main__":
    raise SystemExit(main())
