# BSE reviewed-receipt preservation regression

Read-only diagnosis on 19 September 2026, discovered during the qualified amount
source-family release. This report does not apply a restoration or claim recovery.

## Repository evidence overrides the previous release checkpoint

The four receipts accepted in [reviewed release 599798ff](https://github.com/Vasuki8/IPO-Tracker/commit/599798ff18e92e8ad9fc0da0f99a98f6fb5ce1ad)
were removed by [scheduled core publication 20068a87](https://github.com/Vasuki8/IPO-Tracker/commit/20068a8798108d96f7ca9e728cebcecf2aedcc15)
at 11:13:45 UTC on 19 September. [Core run 35439077621](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35439077621)
used collector `8c1e851da8ec8c15f81a27a36d2104285aeed548`. Subsequent filings
publication `0a393cd40ec910958c9d685d586076d3b0e6f8f6` retained the loss.

| Issuer ID | Accepted band, INR/share | Market lot, shares | Minimum quantity, shares |
|---|---:|---:|---:|
| fx-multitech-limited | 110–116 | 1,200 | 2,400 |
| robokidz-eduventures-limited | 100–106 | 1,200 | 2,400 |
| himalaya-nutravedics-india-limited | 100–106 | 1,200 | 2,400 |
| s-k-offset-limited | 119–125 | 1,000 | 2,000 |

All four lost `activeOfferTerms`, their one original `dataCorrections` event,
and the BSE active-detail source entry. IDs, names, null canonical symbols,
boards and offer dates remained identical. This was not identity conflict or
expiry. Across the full payload these were the only four records that lost
receipts or correction history. `exchange.priceBand` gaps increased **50 → 54**;
eight separately labelled quantities disappeared. Higher-priority record and
source-review counts were unchanged because other gaps already kept the four
issuers queued. The qualified Axiom/Varmora repair does not recover these values.

## Reproduced cause

`scripts/run_update.py::clean_existing_record()` removes BSE source entries
except cumulative-demand evidence and a source explicitly bound to
`universeAdmission`. When no non-BSE source remains, it returns `None`, treating
the record as disposable validation data. A successful core collection then
reconstructs it from the current index without reviewed receipts/history.
The cleaner drops all seven BSE-only upcoming records in `20068a87^`; four carry
the accepted evidence at risk.

Reproduce offline without writing files:

```bash
uv run --frozen python - <<'PY'
import copy, json, subprocess, sys
sys.path.insert(0, 'scripts')
from run_update import clean_existing_record
ids = {'fx-multitech-limited', 'robokidz-eduventures-limited',
       'himalaya-nutravedics-india-limited', 's-k-offset-limited'}
for ref in ('20068a87^', '20068a87', '0a393cd4'):
    payload = json.loads(subprocess.check_output(['git', 'show', f'{ref}:data/ipos.json']))
    print(ref)
    for row in payload['ipos']:
        if row['id'] in ids:
            print(row['id'], 'receipt=', bool(row.get('activeOfferTerms')),
                  'corrections=', len(row.get('dataCorrections', [])),
                  'cleaner_drops=', clean_existing_record(copy.deepcopy(row)) is None)
PY
```

The qualified Axiom/Varmora candidate was separately passed through this cleaner:
its exact supplemented receipts, complete history, publicly eligible amount pairs
and zero dynamic exchange gaps survived. NSE-backed records do not enter the
identified BSE-only deletion path.

## Exact next coherent P4 task

Preserve durable reviewed evidence through existing-record cleanup and a
successful core refresh, including invalid, held or expired receipts that must
remain available even when public values are withheld. Test the complete cleanup
and refresh path using all four real BSE receipts; merge-helper-only coverage
misses this failure. Include Axiom/Varmora supplemented receipts as controls.

Replay the four prior accepted receipts against current identity, official
observations, holds and lifecycle. Recover only their exact receipts and original
correction/detail-source history from `599798ff`, preserving current index rows,
clocks, inventory and unrelated fields. Do not roll back whole records. Publish
through the bounded reviewed path and verify current live output and a subsequent
successful refresh. Preserve every pending proposal, hold and unrelated review.

Expected recovery, conditional on current eligibility, is four price-band gaps
and eight quantities. It is recovery of a prior accepted release, not a new
source-review resolution. Afterward reassess Elevate Campuses/Unitec Fibres detail
sources and Vivekanand's empty/conflicting detail evidence. SpectraA remains held:
three category gaps and one snapshot review; the prior inspection found counts
without acceptable category multiples. Do not repeat that inspection or synthesize
multiples from counts. P5/performance expansion remain gated.
