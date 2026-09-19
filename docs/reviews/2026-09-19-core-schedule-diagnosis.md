# Bounded diagnosis of overdue core checks

Recovered main: `5e8642f34447ee56f9026ad23b61838b66204162`. This diagnosis
continues the existing operational checkpoint; it does not repeat its audit or
change source clocks, schedules, tolerances or canonical data.

The GitHub scheduled-run API's newest 50 of 84 runs covered 15 September
07:47:47Z through 19 September 04:51:55Z. In that bounded result, only two
scheduled runs occurred on 19 September:

| Run | Actual collection | Publication evidence |
|---|---|---|
| [35411915942](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35411915942) | Created 01:12:26Z; event cron `17 * * * *`; core job 105813062061 finished its source check at 01:14:46Z | Job 105814951814 rejected the artifact because collector code or reviewed-correction policy changed after collection. The stale artifact must be recollected, not rerun into publication. |
| [35422427845](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35422427845) | Created 04:51:55Z; event cron `31 */6 * * *`; filings job 105842425572 | Publisher 105843265052 succeeded, producing `1e86840856525db2ee2b436ed64f2b6e60374ee0`. A filings run does not refresh general core-source checks. |

Replacement push run
[35413219212](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35413219212)
started at 01:37:19Z. Core collector job 105816767523 recorded the retained check
at 01:39:43Z. These are actual collector-step observations, distinguished from
simulated errors printed by the preceding regression suite.

At 05:30Z the retained operational report had five failed sources, one partial
failure and 27 recorded successes. BSE, NSE live and SEBI checks were overdue,
as was one core stage. The later filings register stage timed out at its 300-second
budget; earlier source-attempt evidence was retained. No subsequent hourly core
execution appeared in the bounded API result. This cannot distinguish a missing
trigger from a delayed GitHub schedule, nor reconstruct its intended trigger time.

No mode-routing defect is demonstrated. A new existing `core` workflow dispatch
is the appropriate bounded recovery if no later core run has appeared. The
available GitHub capability supports reads and reruns but exposes no workflow
dispatch operation. The stale publisher must not be rerun. An operator with the
existing GitHub CLI capability can first inspect current runs, then use:

```bash
gh run list --repo Vasuki8/IPO-Tracker --workflow refresh.yml --limit 20
gh workflow run refresh.yml --repo Vasuki8/IPO-Tracker --ref main -f mode=core
```

After a new run, inspect actual source-step logs, retained failures and accepted
publication metadata before treating anything as refreshed. Successful Pages
delivery and a separately reviewed offer receipt do not refresh these clocks.

## Subsequent scheduled recovery verified

After the interruption, fresh GitHub evidence confirms scheduled core run
[35425291431](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35425291431)
completed. Its collector job 105850056326 ran 05:57:01–06:06:57Z; the actual core
source stage finished at **05:59:57.874451Z**. Publisher 105851229914 ran
06:07:00–06:07:36Z and accepted
`2d07c3b63a631a3560f75996180fe0fb7979f665`. Pages 35425762822 and public verifier
35425782777 passed; five direct public-file byte checks match that main.

BSE beta returned ten current rows while the primary page parsed zero and the
SME host timed out. The SEBI priority-register stage still timed out at 300 seconds.
These failures are retained alongside fresh attempt clocks. The update added
Elevate Campuses and Unitec Fibres, retaining all earlier issuers: 1,406 records,
P4 408 actionable + 69 higher priority, 1,553 blocking / 1,557 total reviews.
The four prepared BSE receipt identities and empty before-values are unchanged.
No manual dispatch is needed to repair the previously missing core attempt; the
earlier diagnosis remains an evidence window, not the current operational state.
