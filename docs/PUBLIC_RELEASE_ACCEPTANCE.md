# Read-only public release acceptance

A successful Pages job does not prove that the browser is receiving the intended
summary, profiles or trust/freshness assets. `tests/verify_public_release.py` closes
that deployment gap; it is not a new source collector or a source-accuracy gate.

## Acceptance and scope

The verifier checks **every local generated profile** against the directory:
unique safe routes, inventory counts, issuer/path identity, shared displayed
fields, field/source decisions, subscription observation/check clocks and source
authority. It rejects populated held fields, unknown contract versions, invalid
source references, duplicate embedded payloads and malformed JSON. Source indexes
are resolved to their evidence before comparing compacted contracts.

When given a base URL, it compares complete served bytes with the immutable
checkout's public assets, full directory summary, route manifest and a bounded
sample of profiles. The sample includes available Emmvee, Teamtech, Shakti and
Kheria boundaries, a timestamped secondary subscription, unknown source time,
a final-verified field and the first directory record. The receipt names the
actual sample; this is not an all-profile live browser test. HTTP 200 alone is
not success. A stale or mixed release, missing response or oversized content
fails rather than being relabelled as fresh.

The check does not rebuild, scrape exchanges, download the canonical master from
the website, change source time, apply corrections, resolve proposals or alter
P4/P5. It proves output consistency and release-byte delivery, **not the accuracy
of every original prospectus figure or freshness of the underlying feed**. The
existing regression, browser, source-evidence and P4 gates remain required.

## Commands and deployment binding

Use an immutable checkout from the successful Pages run, not whichever `main`
happens to contain later. The SHA argument labels that expected snapshot; the
workflow binds it by checking out the Pages run's exact `head_sha` and comparing
it with `git rev-parse HEAD`. For a downloaded Pages archive, independently verify
the archive digest and workflow/commit binding before supplying its SHA.

```sh
uv run --no-project --python 3.12 python -m unittest discover -s tests -p 'test_public_release_verifier.py' -v
uv run --no-project --python 3.12 python tests/verify_public_release.py --expected-commit "$(git rev-parse HEAD)"
uv run --no-project --python 3.12 python tests/verify_public_release.py --expected-commit "$(git rev-parse HEAD)" --base-url https://vasuki8.github.io/IPO-Tracker/ > release-receipt.json
```

The verifier uses only Python's standard library and introduces no production
dependency. For local HTTP tests, only loopback hosts may use unencrypted HTTP.

## Operations and recovery

`Verify public release` runs read-only after successful main-branch Pages runs.
PR changes to the verifier also test against a local HTTP server. The existing
frontend workflow runs the same byte checks after its real browser journeys.
Only `contents: read` is granted; checkout credentials are not persisted. There
is no second data writer, scheduled source collection or external notification.

Each run has an eight-minute cap, at most three attempts with ten seconds between
attempts, bounded response reads and fifteen-second request timeouts. Receipts,
including failed attempts, are retained for fourteen days. This adds a small CI
job and bounded site requests per successful deployment; it does not activate
paid infrastructure, product analytics, accounts or billing.

On failure, inspect the expected commit, deployment run, failing path and hashes.
Check whether a newer deployment superseded the checked one before declaring an
incident. Do not compare against a moving branch, accept a newer scrape time as
source freshness, or force a rollback. For an actual mixed/stale deployment,
rebuild/redeploy through the existing authorized publisher and verify again.
Retain failed receipts and source/correction history. Source repairs still require
their own review and exact deployed-data acceptance.
