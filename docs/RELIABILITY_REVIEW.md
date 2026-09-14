# Data and automation repair — 14 September 2026

The implementation follows the agreed order: correct existing data, strengthen validation/tests, stabilize automation/queues, close P4, then expand P5 and performance. P4 is not complete; the code deliberately keeps later collection gated.

| Result | Evidence |
| --- | --- |
| Source-document attempts | 72 attempted; 70 read; 2 blocked |
| Financial corrections | 32 records changed using bounded annual-table extraction |
| Correction migration | 440 field changes across 75 records, including provenance and audit history |
| Semantic validation | 0 errors after migration; 928 review items across 60 records remain |
| Regression suite | 433 tests pass together with the committed dependency lock |
| Queue persistence | All 1,040 actionable rows retained; previous output stopped at 300 |
| Phase gates | P4 has 124 actionable records plus 9 higher-priority records; P5 has 907 records and remains gated |
| Performance coverage | 1,286 dated listed records; no confirmed final issue-price or quote coverage yet |

These measurements describe the reviewed migration snapshot, not a guarantee that every populated disclosure is accurate. Later collectors rebuild the reports from current data.

The Sonaselection regression uses its [SEBI abridged prospectus](https://www.sebi.gov.in/sebi_data/commondocs/sep-2026/Sonaselection%20India%20Limited%20%20-%20AP_p.pdf): FY2025 revenue is ₹315.952 crore and FY2024 is ₹120.979 crore. The previous extraction swapped those years and confused a return-on-net-worth percentage with a currency value. Source page/row/header, original units, normalized values and the PDF hash accompany accepted metrics. Role parsing also excludes contact names, former names, table headings and issuer-company fragments.

Legacy financial layouts that cannot be parsed safely remain explicit review work. Mixed interim/annual columns are not silently reclassified. Invalid intermediary fragments are quarantined with before/after history. Distinct withdrawal events receive distinct IDs; four listing dates preceding their issue openings are preserved outside the accepted listing-date field for verification.

The P4 closeout examined all 113 original lot-size targets in SEBI Other Documents: three documents matched, none yielded an accepted new lot, and two downloads were incomplete. NSE returned no usable lots for 25 targets. Both official BSE archive hosts returned HTTP 403. The official NSE quote probe also returned HTTP 403. None of these outcomes was converted into an availability exclusion or successful completion.

One collection/publication workflow replaces 27 independent writing workflows. It preserves collected artifacts, checks the source commit, tests current main, merges independent changes and retains conflicts. Document values/evidence and subscription values/source timestamps merge atomically. Source attempts and the complete queue persist. P3 maintenance still follows core collection with a six-hour fallback.

P5 history expansion and official-price performance collection are implemented behind the correctness gate. Returns require a confirmed final issue price; later daily opening prices cannot substitute for listing-day prices. Benchmark comparisons require matching benchmark identities and dates. Missing inputs remain null. See [operations](OPERATIONS.md) for the supported commands and recovery procedure.
