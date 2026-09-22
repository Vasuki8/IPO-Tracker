# IPO Tracker Development Process

This document is the operating contract for all future IPO Tracker development runs.

A new chat or agent should read this file before making changes.

---

## 1. Core principle

Every development run must complete **one coherent unit of work**, verify it, document it, and leave a clean handoff for the next run.

Do not optimize for the largest possible change. Optimize for the smallest complete change that materially advances the earliest unfinished priority.

---

## 2. Mandatory recovery sequence

Before changing code or data:

1. Fetch the latest `main`.
2. Read:
   - `README.md`
   - `docs/PROJECT_STATUS.md`
   - `docs/DEVELOPMENT_PROCESS.md`
3. Inspect recent commits and deployment state.
4. Inspect the code/data relevant to the next task.
5. Determine:
   - completed work
   - partially completed work
   - blockers
   - earliest unfinished priority
6. Do not repeat work already completed unless verification shows it is broken or incomplete.

Repository/deployment evidence overrides stale summaries.

---

## 3. Priority ladder

Work in this order unless a documented blocker requires another dependency first.

### P1 — Data correctness

- IPO universe coverage
- issuer identity
- dates
- price band / issue price
- issue size
- lot size
- minimum bid quantity
- minimum application amount
- IPO status

### P2 — Source evidence

- official source URL
- document identity/type
- publication date
- page/evidence when available
- source precedence
- conflict handling
- correction history

### P3 — Freshness and automation

- new IPO discovery
- scheduled collection
- observation vs collection vs publication timestamps
- stale-data detection
- collection failures
- repair/recovery workflows

### P4 — Core product UX

- homepage
- filters
- IPO detail
- timeline
- documents
- mobile UX

### P5 — Research depth

- financials
- subscription
- valuation
- peers
- promoter/company information

### P6 — User features

- watchlist
- alerts
- compare
- calendar
- saved IPOs

### P7 — Commercial readiness

- SEO
- performance
- reliability
- source/licensing review
- maintainability
- analytics/monetization only with explicit approval

Do not expand downstream features while upstream correctness is materially blocked.

---

## 4. One run = one coherent batch

Each run should have a bounded objective.

Good examples:

- Recover price-band evidence for up to 15 IPOs.
- Add source-evidence UI to the IPO detail page.
- Fix one reusable source family and test it across several IPOs.
- Build the IPO calendar screen and verify mobile behavior.

Bad examples:

- Improve everything.
- Redesign the full product and rebuild the data system in one run.
- Touch unrelated areas just because they are nearby.

If a task is too large, split it automatically into smaller coherent batches and complete the first batch now.

---

## 5. Batch definition

Before implementation, determine internally:

### Problem
What exactly is missing, broken, or unreliable?

### User impact
Why does it matter?

### Scope
What will change in this run?

### Out of scope
What must not change?

### Acceptance criteria
What evidence will prove the batch is complete?

Do not ask the user to restate information already present in the repo or handoff.

---

## 6. Implementation rules

- Prefer extending existing architecture over creating parallel systems.
- Reuse existing parsers, data models, components, utilities, and workflows where reasonable.
- Avoid speculative abstractions.
- Prefer small correct implementations over large unfinished redesigns.
- Preserve backwards compatibility unless a deliberate migration is part of the batch.
- Do not delete historical evidence or correction history without explicit justification.
- Do not introduce paid services, billing, accounts, ads, analytics, contracts, or infrastructure migration without explicit approval.

---

## 7. IPO data rules

For every important field, preserve the concept of:

- value
- source
- source/document identity
- publication date
- observation date when applicable
- collection date
- source status
- conflict/correction history where relevant

### Missing data

If a value cannot be verified, preserve it as null/missing.

Never:

- guess
- estimate
- silently infer
- replace missing with zero
- copy unsupported values from aggregators

The UI should explicitly communicate missing/provisional/conflicting states.

### Distinct concepts

Keep these separate:

- market lot
- minimum bid quantity
- minimum application amount

Do not collapse them into one field.

### Final Prospectus

A Final Prospectus is **not required** for an IPO to appear in the tracker.

Use the best available official source for the field, including as appropriate:

- DRHP
- RHP
- price-band advertisement
- exchange notice
- prospectus / final prospectus
- registrar disclosure
- issuer disclosure
- other official filing

### Conflicts

If two official sources disagree:

1. Preserve both pieces of evidence.
2. Mark the field as conflicting until resolved.
3. Apply documented source precedence or later authoritative correction.
4. Retain the correction history.

Do not silently overwrite one value with another.

---

## 8. Testing requirements

Testing must match the type of work.

### Data changes

Check as relevant:

- schema validity
- source availability
- parser behavior
- null preservation
- duplicate issuer detection
- cross-document consistency
- correction/conflict handling
- multiple examples from the same source family

### UI changes

Check as relevant:

- desktop
- mobile
- long company names
- missing values
- provisional/conflict states
- empty states
- filters
- navigation
- source links
- responsive layout

### Automation changes

Check as relevant:

- fresh run
- rerun/idempotency
- source unavailable
- document missing
- changed source format
- publication output
- failure visibility

---

## 9. Diff review

Before publishing, explicitly verify:

- What changed?
- What should not have changed?
- Was any data unexpectedly deleted?
- Were source fields or timestamps lost?
- Did any null become a guessed value?
- Did unrelated UI or pipeline behavior regress?

Data trust is a product requirement, not only an implementation detail.

---

## 10. Publication workflow

Default path:

```
main
  ↓
GitHub Actions
  ↓
GitHub Pages
  ↓
live verification
```

Use a feature branch / pull request when the change is materially risky, broad, destructive, or benefits from isolated review.

Do not force PR overhead for every tiny safe repair.

---

## 11. Completion states

Use these states conceptually:

- TODO
- IN_PROGRESS
- BLOCKED
- READY_FOR_REVIEW
- DEPLOYED
- VERIFIED

A task is not fully complete merely because code was committed.

A batch reaches **VERIFIED** only after checking the deployed/operational result when deployment is relevant.

---

## 12. End-of-run handoff

Every substantial run must update:

- `docs/PROJECT_STATUS.md`
- the handoff section in `README.md` when materially needed

Record:

- what changed
- files/components touched
- tests performed
- commits/PRs merged
- deployment status
- live verification result
- remaining blockers
- failed approaches and why they failed
- recommended next task

The next run should be able to continue without rediscovering the previous run.

---

## 13. Workstream separation

Treat these as separate workstreams even when they share the same repository:

```
IPO Tracker
├── Data Pipeline
│   ├── IPO discovery
│   ├── document discovery
│   ├── extraction
│   ├── validation
│   └── publication
├── Product
│   ├── homepage
│   ├── IPO detail
│   ├── calendar
│   ├── compare
│   └── watchlist
└── Operations
    ├── scheduled jobs
    ├── freshness
    ├── error reporting
    ├── deployment
    └── recovery
```

A UI change should not casually rewrite source recovery. A parser repair should not casually redesign the product.

---

## 14. Default continuation behavior

When the user says **"continue"**:

1. Re-read the latest repository state if it may have changed.
2. Read the current handoff/status.
3. Select the earliest unfinished priority.
4. Complete the next coherent batch.
5. Test it.
6. Publish when appropriate.
7. Verify the result.
8. Update handoff/status.
9. Stop after one coherent batch unless the current batch naturally requires a few tightly related steps.

Do not ask the user to resend the master prompt.

---

## 15. When to stop and report a blocker

Stop the batch and clearly document the blocker when continuing would require:

- inventing data
- destructive action without approval
- new spending
- external contracts
- material access/permission changes
- unsupported assumptions that could corrupt production data

Where possible, complete all safe work before reporting the blocker.
