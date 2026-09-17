# Objects-of-issue table fixtures

These excerpts preserve `pdftotext -layout -fixed 3` spacing and one-based PDF page markers from the exact final prospectuses. Purpose and amount spans are tested against these physical lines. Footnote markers, percentage columns and wrapped purposes remain in their source form.

| Issuer | PDF pages | PDF SHA-256 | Source |
|---|---|---|---|
| Priority | 96–97 | `cd3026b4bc426e5ba3a455e10ef4b6d0de0d0b393ee0db3590dba6cd45e8efed` | https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/1788323000985.pdf |
| Deepa | 105–106 | `a35182d0baae9ffac56d913f8381af7e876bdea5a7dc5d9459d2f808fb181798` | https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/1788759187148.pdf |
| Sheel | 24, 117–118 | `903e8c345fd7718c443a1624cdd1f4a07a418df02cc602072aa86f3b2f4917a6` | https://nsearchives.nseindia.com/emerge/corporates/content/SheelBiotechLimited_PROSP.pdf |
| Dhanlaxmi | 89 | `fd0dcf154e87d220c5b2e405023d9f9befb24929ad73f450c0783b1d430bc7cc` | https://nsearchives.nseindia.com/emerge/corporates/content/DhanlaxmiCropScienceLimited_PROSP.pdf |
| Capillary | 27 | `885b8cf8bcd3b47ea07e064139dcb98762edb3d36ec8956c7e8206b5f3fc4fa9` | https://nsearchives.nseindia.com/corporate/FP_INE0ILV01024_20NOV2025.pdf |
| Alpine | 130 | `207f35afa6d43583eca64f55e727b12077812fb667d283d3d6e99eec9a04c4ee` | https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786621533716.pdf |
| Solarworld | 23–24 | `5b011cca00df1e764c6e613e773455a304260145b733b1be410a778f77a6e51d` | https://nsearchives.nseindia.com/corporate/FP_INE0TY101024_26SEP2025.pdf |

Priority's summary table ends before a deployment table and later repeated debt narrative. Deepa's next table is a fiscal deployment schedule, whose ₹900 million cell is not another allocation. Sheel's early net-proceeds summary contains three allocations; its later gross-proceeds table adds the explicitly disclosed issue expenses. The three non-expense amounts reconcile exactly, including the narrow working-capital label variation. Sheel has an explicit percentage column and its total continues on the next PDF page. Dhanlaxmi has wrapped column headers, explicit letter row markers and an `Up to` qualifier; its total closes the allocation table before net-proceeds reconciliation and a deployment schedule.

Capillary has a same-page purpose continuation containing only `purposes*`; this is part of the allocation row, not a new column header. Alpine has a floating standalone `(1)` immediately before its third allocation and must remain unresolved until that annotation is bound safely. Solarworld repeats its complete column header on the next page before the quoted total; unsupported pagination must not promote an unclosed table prefix.
