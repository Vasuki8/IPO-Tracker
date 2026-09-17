# Collector source freshness

Retained collector artifacts can be merged only when their recorded source commit is an ancestor of the publisher's current checkout and all publication dependencies are unchanged. `scripts/publication_source_policy.py` defines the guard used by `scripts/publish_transaction.py`.

The protected paths are `scripts/`, `uv.lock`, `pyproject.toml`, and `data/verified_corrections.json`. The corrections registry is policy: adding, editing, or deleting it invalidates a run collected under the previous policy. Reapplying current corrections at the end is not a substitute for recollecting under the current source and review rules.

A change to IPO output data, pending proposals, source-review reports, or documentation alone does not invalidate collection. The existing three-way merge still decides which independent data updates can be accepted and retains competing proposals for review. This guard does not change that merge or promote source-preview data automatically.

On a source/policy mismatch, recollect from the latest accepted code and registry, then rerun validation and publication. Do not remove `--source-commit-file`, substitute a new SHA for old artifacts, or disable the guard to reuse a stale run. Git failures and non-ancestor commits fail closed. Path checks are repository-root-relative, including when invoked from a subdirectory.

Run the focused regression suite with:

```sh
uv run --frozen python -m unittest discover -s tests -p 'test_publication_source_policy.py' -v
```

The tests use disposable local Git repositories and do not contact external sources. They cover unchanged source, permitted data/documentation advances, each protected dependency, registry addition/deletion, recollection, subdirectory invocation, invalid SHAs, divergent history, and Git errors.
