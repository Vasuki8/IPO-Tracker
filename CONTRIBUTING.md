# Contributing to IPO Tracker

IPO Tracker is a source-first Indian IPO research product. Correctness, provenance, and conservative publication are higher priority than filling every field.

## Before changing data

Use authoritative source evidence and preserve:

- the exact value and unit;
- source URL and document identity;
- publication and collection/observation clocks when applicable;
- page or locator evidence where available;
- nulls when a value is not verified;
- conflicts and correction history instead of silently overwriting them.

Do not infer minimum application amounts, collapse market lot into minimum bid quantity, or promote discovery-only evidence into publication authority.

## Scope changes

Keep one pull request focused on one coherent batch. Avoid mixing data-pipeline changes, UI redesign, unrelated source recovery, and operational refactors.

Do not add paid services, billing, accounts, analytics, ads, contracts, new spending, or material access-policy changes without explicit owner approval.

## Tests

Run the tests relevant to the change. Data changes should cover schema, identity, source/evidence guards, idempotency and preservation. Automation changes should cover retries, reruns, source failure and publication safety. UI changes should cover desktop/mobile and missing/conflicting states.

The repository's existing CI is part of the contract; do not remove checks merely to make a change pass.

## Pull requests

A pull request should state:

1. the problem and bounded scope;
2. what changed and what intentionally did not change;
3. source/evidence assumptions;
4. tests run and their result;
5. publication/live verification when relevant;
6. remaining blockers or limitations.

Never merge stale history wholesale when a branch is far behind `main`; compare semantically and port only validated unique deltas.

## Security

For sensitive security reports, follow [SECURITY.md](SECURITY.md). Do not put secrets or exploit details in public issues.
