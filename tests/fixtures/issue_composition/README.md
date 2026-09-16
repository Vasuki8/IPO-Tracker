# Final offer clause fixtures

These bounded excerpts retain actual cover-narrative line wraps, Indian and
international share-count grouping, footnote marks, and million/lakh units.
PDF pages are physical page numbers, as used by the production extractor.
Source PDFs and rendered pages were inspected; no PDF binaries are committed.

| Fixture | Final Prospectus source | Page | Verified composition |
| --- | --- | --- | --- |
| `annu-final-offer.txt` | [ANNU, dated 29 August 2026](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1788150561832.pdf) | 2; table confirmed on 1 | Entirely fresh: 17,683,000 shares, ₹175.062 crore; OFS not applicable. |
| `arcil-final-offer.txt` | [ARCIL, dated 11 September 2026](https://nsearchives.nseindia.com/corporate/FP_INE148G01016_15SEP2026.pdf) | 3; table confirmed on 1 | Entirely OFS: 52,731,946 shares, ₹732.974 crore; fresh issue not applicable. |
| `mpimanipal-final-offer.txt` | [Manipal, dated 11 September 2026](https://nsearchives.nseindia.com/corporate/FP_INE241U01028_15SEP2026.pdf) | 3; price-band definition on 11 | Fresh: 9,439,528 shares/₹320 crore; OFS: 14,306,785 shares/₹485 crore; total ₹805 crore at ₹339. |
| `skyways-final-offer.txt` | [Skyways, dated 27 August 2026](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787916423171.pdf) | 2; table confirmed on 1 | Fresh: 28,898,300 shares/₹398.7965 crore; OFS: 13,333,300 shares/₹183.9995 crore; total ₹582.796 crore at ₹138. |

Manipal's price-band definition is reflowed from its page-11 table, preserving
the original words and values. This ensures the generic `Price Of` matcher
cannot treat the ₹322 floor as a second final offer price.
