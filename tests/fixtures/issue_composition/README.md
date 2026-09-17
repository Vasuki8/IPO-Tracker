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
| `orkla-final-offer.txt` | [Orkla, dated 31 October 2025](https://www.orklaindia.com/wp-content/uploads/sites/3/2025/11/Orkla-India-Limited-Prospectus.pdf) | 3; tables confirmed on 21 (printed 16) | Entirely OFS: 22,843,004 shares, quoted ₹1,667.33 crore. The ₹69 employee discount prevents uniform ₹730 valuation. |
| `vmm-final-offer.txt` | [Vishal Mega Mart, dated 13 December 2024](https://nsearchives.nseindia.com/corporate/FP_INE01EA01019_16DEC2024.pdf) | 3 | Entirely OFS: 1,025,641,025 shares, quoted ₹8,000 crore at ₹78. The single seller owns the entire OFS quantity. |
| `sbifunds-final-offer.txt` | [SBI Funds Management, dated 16 July 2026](https://www.sebi.gov.in/sebi_data/attachdocs/jul-2026/1784286127716.pdf) | 3; table confirmed on 1 | Entirely OFS: 170,956,631 shares, quoted ₹9,795.321 crore. The first seller's 99,501,649 shares are not the entire OFS. Employee discount: ₹54. |
| `emmvee-final-offer.txt` | [Emmvee, dated 14 November 2025](https://nsearchives.nseindia.com/corporate/FP_INE1C6T01020_14NOV2025.pdf) | 3 and 11 (printed 6); table confirmed on 21 (printed 16) | Fresh: 98,795,483 shares/₹2,143.862 crore; OFS: 34,845,069 shares/₹756.138 crore; total ₹2,900 crore at ₹217. The mixed-offer cover lists two owned OFS quantities: 17,422,535 and 17,422,534 shares, each quoted at ₹378.069 crore. |

Manipal's price-band definition is reflowed from its page-11 table, preserving
the original words and values. This ensures the generic `Price Of` matcher
cannot treat the ₹322 floor as a second final offer price.

Orkla's PDF SHA-256 is `1a3e82f54f7b624901b47632b9c5307da6c2905455278a311cd9db3872d2e7fe`.
Its 30,000 employee shares are a reservation subject to finalisation of the
basis of allotment. The fixture supports the quoted aggregate, not an inferred
employee allotment or a more precise discount-adjusted amount.

Vishal Mega Mart's PDF SHA-256 is `b0d2d33458dee51af4fc4aa5908d16154103468f3d535130c4b93f203b57a9f0`.
SBI Funds Management's is `3df0687af1bfe755eb08360ee47bf8334da9cafef23b96beb4b40c0c55f4f70e`.
These two offers place the whole-offer alias before `THROUGH AN OFFER FOR SALE`.
The share counts attached to named sellers corroborate the initial total; their
prices and employee reservations do not supply canonical amounts.

Emmvee's PDF SHA-256 is `85eb9319dc01027821813c71d3702164911442a14547ad72cc04270ea6612eda`.
The fixture preserves exact lines from physical PDF3 and PDF11 of the complete
511-page production extraction, whose text SHA-256 is
`294f180e7910ddc09fe7729a3d30c1ed597673bc9bce55e166d09ef1fb51eacf`.
The `EQUITY SHARES^` carets and both sellers' names and quoted amounts are
unchanged. PDF11 independently states the aggregate OFS; it must agree with
the complete PDF3 seller list. PDF21 corroborates the composition and the
separate ₹1,621.294 crore and ₹438.711 crore objects allocations; it is not an
additional composition parser window or fixture layout.
