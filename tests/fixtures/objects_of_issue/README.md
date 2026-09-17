# Objects-of-issue table fixtures

These excerpts preserve `pdftotext -layout` spacing and one-based PDF page markers from the exact final prospectuses. Purpose and amount spans are tested against these physical lines. Footnote markers, percentage columns and wrapped purposes remain in their source form.

| Issuer | PDF pages | PDF SHA-256 | Source |
|---|---|---|---|
| Priority | 96–97 | `cd3026b4bc426e5ba3a455e10ef4b6d0de0d0b393ee0db3590dba6cd45e8efed` | https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/1788323000985.pdf |
| Deepa | 105–106 | `a35182d0baae9ffac56d913f8381af7e876bdea5a7dc5d9459d2f808fb181798` | https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/1788759187148.pdf |
| Sheel | 24, 117–118 | `903e8c345fd7718c443a1624cdd1f4a07a418df02cc602072aa86f3b2f4917a6` | https://nsearchives.nseindia.com/emerge/corporates/content/SheelBiotechLimited_PROSP.pdf |
| Dhanlaxmi | 89 | `fd0dcf154e87d220c5b2e405023d9f9befb24929ad73f450c0783b1d430bc7cc` | https://nsearchives.nseindia.com/emerge/corporates/content/DhanlaxmiCropScienceLimited_PROSP.pdf |

Priority's summary table ends before a deployment table and later repeated debt narrative. Deepa's next table is a fiscal deployment schedule, whose ₹900 million cell is not another allocation. Sheel's early net-proceeds summary contains three allocations; its later gross-proceeds table adds the explicitly disclosed issue expenses. The three non-expense amounts reconcile exactly, including the narrow working-capital label variation. Sheel has an explicit percentage column and its total continues on the next PDF page. Dhanlaxmi has wrapped column headers, explicit letter row markers and an `Up to` qualifier; its total closes the allocation table before net-proceeds reconciliation and a deployment schedule.
