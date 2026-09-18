# Bounded reviewed publication

A corrected value without matching field evidence must remain withheld. This path
pairs a reviewed field group with its exact retained proofs and uses
the existing serialized publisher. It is not permission to roll out an unreviewed
parser or clear unrelated review items. Teamtech remains held.

Supported groups are the original complete four-field composition and an explicit
`intermediaries` pair (`leadManagers`, `registrar`). The latter requires exact
issuer/offer identity on each proof, one PDF hash/date, the same physical table,
replayable role/name column spans, and separate collection/review clocks. It does
not change the production parser version or schedule broader extraction.

Intermediary corrections carry `publicationScope: explicit-reviewed`. Ordinary
registry application skips the whole group, including proof attachment; merging
its support files is not numerical/data acceptance. A support-only release uses
the existing source-free `review` path. It must then be followed by a separate
reviewed request for the exact accepted IDs. Mixed source-collector changes
retain ordinary repair routing. The reviewed source manifest remains mandatory.

Once accepted, exact current reviewed-role evidence survives generic extraction
of the same PDF bytes, including mirrors, and legacy name-token quarantine.
Different authoritative documents remain eligible under the normal policy.
Historical field holds and correction snapshots are preserved. Source acceptance
does not establish commercial redistribution permission.

## Prepare a review

Use a current checkout and `uv sync --frozen`. Run:

```sh
uv run --frozen python -m unittest discover -s tests -q
uv run --frozen python scripts/reviewed_corrections.py --ids emmvee --bundle /tmp/ipo-reviewed
```

The bundle contains exact base/proposed snapshots and a hash manifest. It does not
write canonical data. Keep its real source commit; never relabel an old manifest.
The publisher replays the accepted transition, checks complete source proofs and
public decisions, and fails before writing on document conflicts. Independent
subscription changes survive. Pending proposals are never rewritten by this mode.

## Publish through the existing workflow

After code, evidence, tests and source acceptance are reviewed, use **Collect and
publish IPO data → Run workflow → mode: reviewed → reviewed_ids: emmvee** on main.
This path skips all source/residual collection. Inspect the publish job and actual
canonical diff, then verify Pages and the affected live profile/directory/export.

The current GitHub connection cannot dispatch a manual workflow. An equivalent
reviewable route is a PR that changes **only** `data/reviewed_publication_request.json`:

```json
{"schemaVersion":1,"requestId":"emmvee-proof-repair-1","ids":["emmvee"]}
```

Use a new request ID for another attempt. Merge only after reviewing the selected
IDs and passing checks. The request-only main push selects the same `reviewed`
mode and mandatory guards. A mixed request/code/data/docs push fails closed rather
than triggering broad collection. Missing files, malformed requests, unknown IDs
or incomplete evidence fail; there is no implicit all-record batch. Keep release
status documentation in a separate PR, not mixed with the request. The request
is protected source policy, so a newer request invalidates an older pending run.
No new writer, token, permissions, paid service or account is introduced.

## Acceptance and recovery

Confirm the proposed and published issuer scope, matching proof hashes, unchanged
unselected records and pending-proposal bytes, retained source clocks and history,
strict validation, public hold decisions and actual served bytes. Green unit tests
are not a new full-document source audit. Retain release receipts in docs/releases.
On failure, retain the bundle and request. Rebuild from the newer accepted baseline
and review the conflict; do not drop pending work, mutate hashes or force an old
proposal through. An ordinary collector-code push still follows its existing
repair mode; its outcome must not be reported as the bounded reviewed release.


## Verify delivery, not only page consistency

The automatic read-only public-release workflow now checks the latest explicit
reviewed publication against its locally retained value/proof group. Run the same
check on an immutable deployed checkout:

```sh
uv run --no-project --python 3.12 python tests/verify_public_release.py \
  --expected-commit "$(git rev-parse HEAD)" \
  --base-url https://vasuki8.github.io/IPO-Tracker/ \
  --check-reviewed-publication
```

`reviewedPublication.status=passed` means the reviewed group's accepted values,
original proof artifact, public fields and evidence were delivered together. The
master dataset and proof artifacts are read locally only. All reviewed profiles
join the bounded complete-byte HTTPS comparison, not only the ordinary sample.
A still-withheld repair, wrong public amount/source clock/document, missing issuer,
malformed scope or changed proof artifact fails. A normal source publication reports
`not_requested`; that is not a reviewed-repair pass. The overall receipt still
measures delivery of retained evidence, **not new source-value correctness**.

The completed Emmvee request is #116, published as `3834c732`; do not repeat it on
recovery. Its original bundle and proof/audit preservation are recorded in
[the recovery receipt](releases/2026-09-18-reviewed-publication-recovery.json).
