# Scheduled operation health monitor — 2026-09-28

The repository configures live and background workflows more frequently than GitHub has consistently started them in recent observations. This monitor distinguishes two failure classes that the existing operator snapshot could not reliably separate:

1. **scheduled start overdue / recent schedule gap exceeded** — the workflow did not start within the allowed freshness window;
2. **latest scheduled run failed** — the workflow started, but its execution failed.

The monitor is read-only. It does not change IPO data or operator state and does not add another direct-to-main writer.

## Monitored workflows

| Workflow | Configured cadence | Criticality | Overdue threshold |
|---|---:|---|---:|
| Sync live IPO data | hourly | critical | 180 min |
| Sync Pre-IPO draft sources | every 2h | critical | 360 min |
| Backfill historical BSE SME addition notices | every 2h | warning | 480 min |
| Backfill historical IPO offer dates | hourly | warning | 480 min |
| Backfill historical IPO PDF fields | hourly | warning | 480 min |

The larger thresholds deliberately distinguish operational freshness from normal GitHub scheduling jitter. Historical backfills remain warnings because they do not define live IPO freshness.

The monitor runs hourly and after completion of any monitored workflow. It retains the raw run-clock sample and evaluated report as 14-day artifacts and writes a readable Actions job summary.
