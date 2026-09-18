# SpectraA: NSE detail and denominator review, 18 September 2026

Review version 1, against accepted baseline
`64697fe1d837e422a6678c51959e647fb7ad6e0b`. This review retains the historical
SpectraA subscription hold and does not accept a numerical correction. It does
establish the exact source layout and prevent a newly reproduced collector error.

## Retained source evidence

The [source receipt](2026-09-18-spectraa-nse-detail-evidence.json) records exact
URLs, HTTP status, response-byte hashes, collection times, document member hashes,
source clocks and review version. Full decoded HTTP response bodies, original ZIP
files, extracted PDF members and review renders are retained locally under
`.cache/spectraa-evidence-20260918/`; these files are ignored rather than publicly
redistributing complete source documents. The committed
`tests/nse_subscription_detail_20260918.json` contains selected literal
identity and category fields from four real responses, with each original body's
receipt. It is a reduced fixture, not a byte-identical copy of the full response.

The subscription fixture is stored directly under `tests/` so this leaf-collector
change does not match the source-preview workflow's broad `tests/fixtures/**`
trigger for unrelated Final Prospectus batch extraction. Its bytes and receipt
hash are unchanged by the move. No workflow or protection rule is changed, and
the earlier broad preview's diagnostic artifacts remain unaccepted.

Direct reads succeeded although the web-reader detail calls had failed. The main
BSE URL returned a JavaScript application shell, and the beta issue index returned
20 DisplayIPO links without an exact SpectraA match. This bounded response check
does not establish missing exchange coverage or an exchange outage.

The [official SME detail API](https://www.nseindia.com/api/ipo-detail?symbol=SPECTRAA&series=SME)
was collected at `2026-09-18T19:38:31.936692+00:00`, HTTP 200, 12,915 bytes,
SHA-256 `bbdc8da8d80c37ed2f03adc1ab8c9bc21b35971d33c2d25836545f0ff0286362`.
Its issuer heading, symbol and issue period match SpectraA Technology Solutions
Limited, SPECTRAA, 17-21 September 2026. Its category bid table contains share
counts and application counts, with no category multiples or category denominators:

| Category | Shares bid | Applications |
| --- | ---: | ---: |
| QIB | 14,400 | 4 |
| NII aggregate | 10,287,600 | 1,613 |
| Individual investors bidding for two lots | 37,226,400 | 15,511 |
| Total | 47,528,400 | 17,128 |

The separate `activeCat` table contains zero offered-share denominators, reported
zero multiples, and a total of 10,302,000 bids that omits the individual-investor
row. Its clock is 18 September 2026, 17:00:00. It cannot represent the complete SME
subscription snapshot above. The separate NSE demand graph carries 17:00:02 IST;
the all-exchange graph carries 17:00:00 IST. Both divide 47,528,400 bids by 2,578,800
shares and display 18.43, explicitly qualifying their contents as bid-position
information rather than necessarily subscription. These clocks are retained as
source metadata, not retroactively assigned to the held canonical snapshot.

## Denominator meaning

The exact detail response links
[post-anchor security parameters](https://nsearchives.nseindia.com/content/ipo/POSTANCHOR_PARAMETERS_SPECTRAA.zip),
[pre-anchor security parameters](https://nsearchives.nseindia.com/content/ipo/PREANCHOR_PARAMETERS_SPECTRAA.zip)
and the [anchor allocation report](https://nsearchives.nseindia.com/content/ipo/ANCHOR_SPECTRAA.zip).
The two post-anchor PDF pages were extracted and visually reviewed, including the
category-table footnote. The anchor report's dated first page was also visually
reviewed. These are active-offer exchange/issuer disclosures, not a Final
Prospectus approval of completed static IPO terms.

The post-anchor table supplies QIB 684,000 shares, NIB 697,200 shares and individual
investors 1,197,600 shares, summing to 2,578,800. QIB excludes 1,024,800 anchor shares;
the NIB allocation includes 182,400 market-maker shares, expressly stated by its
footnote. NIB sub-buckets are 343,200 and 171,600 shares. The 16 September anchor
letter confirms 1,024,800 allocated shares. Thus the graph's total denominator is
traceable; it is not interchangeable with a denominator excluding the
market-maker reservation. No category multiple is calculated or accepted here,
and the graph is not promoted to the headline subscription field.

The PDF identifies the trading security series as EQ while labelling the IPO
SME. The detail API's `series=SME` route is a separate routing convention. The
collector must not mistake the security's trading series for its API route.

## Reproduced defect and bounded prevention

The old client requested EQ first for an SME issue and returned immediately when
`bidDetails` was a list. The
[SpectraA EQ response](https://www.nseindia.com/api/ipo-detail?symbol=SPECTRAA&series=EQ)
has an empty `issueInfo`, zero share denominators, and apparent QIB/NII/total
multiples of 0.00. The old parser therefore produced
`{"qib": 0.0, "nii": 0.0, "retail": null, "total": 0.0}`. Had source access
recovered, this could have replaced the held 18.43 total with an invalid zero
snapshot. It was reproduced from retained bytes without running a canonical
writer.

The leaf collector now requests the route selected by the explicit board and
does not fall back from SME to EQ. Before mutation, the publisher helper requires
matching issuer, symbol and both offer dates, plus each reported headline's own
positive share denominator and valid bid count. The reported multiple must agree
with those counts to the source's two-decimal rounding tolerance. Scientific
notation in share counts is read as a complete numeric token. The guard neither
derives missing multiples nor imports a root/graph total. Valid zero demand on a
positive denominator remains valid. Absent categories remain null, and the
existing whole-snapshot completeness guard still protects previously known facts.

Duplicate headline rows must also agree on every known bid count and denominator,
even when one row has no multiple. Conflicting counts reject the entire snapshot
in either row order; identical counts permit an explicitly reported multiple but
never create one. If no supported headline multiple exists, counts alone still
cannot publish an observation. NII subcategories remain outside the aggregate.

Real [SONA EQ](https://www.nseindia.com/api/ipo-detail?symbol=SONA&series=EQ) and
[JSIPL EQ](https://www.nseindia.com/api/ipo-detail?symbol=JSIPL&series=EQ) responses
exercise the mainboard title-row identity layout, positive denominators and
scientific share notation. Their reported source values pass unchanged in
isolated test records; no current SONA/JSIPL canonical values are adjudicated or
changed by these control tests. Existing low-level parser fixtures remain valid;
the synthetic incomplete-response application test gains the required identity
and denominator fields so it continues to test the same missing-total failure.

Validation: 22 focused source-evidence/routing tests and all 10 existing
subscription-tracking tests pass. `git diff --check` passes. A combined
`PYTHONUTF8=1 uv run --frozen python -m unittest discover -s tests -q` run on the
shared working tree executed 1,231 tests with seven errors outside this collector:
two Windows filename/symlink constraints and five reviewed-evidence publication
errors while that independent workstream was being edited. The run log is retained
in `.cache/spectraa-evidence-20260918/full-suite-utf8.log`; this is not a claim of a
green combined release. The coordinator must rerun the combined gate after
integration. An earlier run without UTF-8 failed existing Unicode fixture reads
on Windows and is superseded by the UTF-8 run.

## Decision and next action

SpectraA remains blocked for accepted headline subscription publication: the
proper SME detail supplies bid counts without category multiples, the category
denominator table is unusable, and the available 18.43 value is separately
qualified graph output. Identity and graph-denominator investigation are now
complete; this is no longer merely a source-access failure. A comparable official
subscription observation with supported category scope and valid denominators
is still required. Do not clear the hold using this receipt, a collection-clock
refresh, a historical total or category ratios synthesized from these documents.

This increment changes only the collector guard, focused tests/fixtures and this
workstream evidence. Canonical records, proposals, historical review records and
holds remain unchanged. Actual P4 blockers removed: zero. P5/performance remains
gated, and official hosting does not establish commercial redistribution rights.
