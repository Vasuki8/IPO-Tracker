# Browser gate stabilization — 2026-10-04

Separate batch from admission/identity PR #356. Scope: BUG-014 production-dependent
fixtures and a reproduced duplicate-route keyboard-focus race. No IPO data changes.

## Design and reproduced failure

The application subscribed the same route renderer to both popstate and hashchange.
A second notification for an already displayed URL rendered the detail again,
reset expanded evidence and focused the heading after a user used Skip to content.
An offline real-Chromium probe first observed focus on `main`, then `detailName`
after the duplicate; the regression assertion failed before and passed after repair.
The browser regression holds a native hashchange until after popstate and keyboard
interaction, then releases it. It also checks evidence-node preservation, Tab,
back/forward, query-only navigation and same-URL data reload at 320/390/1440px.
The route key is invalidated for each data load, so retries are not suppressed.

## Deterministic tests

Synthetic test-only datasets independently specify six offers open on September 30,
two closing that day, pricing conflicts, trading/bid quantities, unknown boards,
101-row pagination, and distinct draft/lifecycle/refresh clocks. They never enter
recovery or the public dataset. Scenario overrides still test errors and conflicts.
The general interface script also has a separate current-corpus smoke test without
fixed issuer/status/count assumptions. Abakkus's draft-to-progressed behavior is a
fixed example, not a permanent assertion that it must remain pre-IPO today.

All four browser scripts run even when one fails; any failure fails the gate.
The workflow repeats the suite three times and retains per-script logs/results.
There are no whole-test retries, disabled assertions, fixed sleeps, or bypasses.
The fixture and runner paths trigger interface validation. Existing Node 20 and
Playwright 1.56.1 pins and read-only interface permissions are unchanged.

## Verification boundary

Local fixture schema checks, syntax, builder consistency and 101 non-browser
entrypoints passed. Original production-dependent browser failures were retained
from the earlier baseline comparison. An offline focus assertion failed on the
original application and passed on the repair. Full HTTP browser execution in the
local runtime is administrator-blocked, so GitHub runner results must be checked
before merge. Those results are recorded in the PR/release receipt, not assumed.

## Release sequence

Merge this independently validated stabilization batch first. Then refresh PR #356
against current main, rebuild its derived JSON from current recovery evidence,
rerun all PR checks, and verify the actually served projection after merge.
Do not replay historical imports. SSEK #352 and other audit repairs remain separate.
