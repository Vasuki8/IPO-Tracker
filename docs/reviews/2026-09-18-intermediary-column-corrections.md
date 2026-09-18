# Source acceptance for the bounded intermediary-column repair

Reviewed on 18 September 2026 against main `64697fe1d837e422a6678c51959e647fb7ad6e0b`.
This note accepts only the four intermediary facts below from the exact Final
Prospectuses. It does not claim their publication, release, or acceptance of any
financial, subscription, allocation or issue-composition figures.

| Issuer / offer opening | Field | Source-supported current value | Physical PDF page |
| --- | --- | --- | ---: |
| Snehaa Organics Limited / 2025-08-29 | `leadManagers` | `FAST TRACK FINSEC PRIVATE LIMITED` | 1 |
| Snehaa Organics Limited / 2025-08-29 | `registrar` | `SKYLINE FINANCIAL SERVICES PRIVATE LIMITED` | 1 |
| Sacheerome Limited / 2025-06-09 | `leadManagers` | `GYR CAPITAL ADVISORS PRIVATE LIMITED` | 3 |
| Sacheerome Limited / 2025-06-09 | `registrar` | `MUFG INTIME INDIA PRIVATE LIMITED` | 3 |

The lead-manager fields are one-element lists. The registrar fields are strings.
Snehaa's missing registrar is a supported fill, not a zero, estimate or inferred
identity. Existing incorrect values and their original proofs must remain in the
correction history. The original hold registry and historical review remain intact.

## Exact sources and inspection

The complete official HTTPS PDFs were downloaded with successful HTTP responses,
without redirects. Byte lengths, SHA-256 hashes and complete page counts match
the earlier hold review. They remain local inspection inputs; no full PDF is
added to the repository.

| Source | Document date | Bytes / pages | SHA-256 |
| --- | --- | --- | --- |
| [Snehaa Final Prospectus](https://nsearchives.nseindia.com/emerge/corporates/content/SnehaaOrganicsLimited_PROSP.pdf) | 2025-09-03 | 18,126,150 / 467 | `05326ed87f0869904f25d9be04e93a59f9a6491e45446bd0f098c10150daee73` |
| [Sacheerome Final Prospectus](https://nsearchives.nseindia.com/emerge/corporates/content/SacheeromeLimited_PROSP.pdf) | 2025-06-12 | 7,589,875 / 293 | `f5abf7b4258fd52c88aadcac66bcd65c96ded9c952c1e7fe364a0a4fc4c3c07e` |

Snehaa physical pages 1 and 83 and Sacheerome physical pages 1, 3 and 52 were
rendered with bundled Poppler and visually inspected, including the issuer and
document-date identities on the covers. Snehaa page 1 places the registrar's
name one physical row above the lead-manager name, in its own right-hand column.
Page 83's key-intermediaries table independently identifies Fast Track as lead
manager/underwriter and Skyline as registrar. Extracted physical pages 3 and 17
corroborate both roles and the full registrar name; page 85 calls Fast Track the
sole book-running lead manager.

Sacheerome page 3 and its key-intermediaries table on physical page 52 identify
GYR and MUFG in separate role columns. The MUFG cell explicitly identifies Link
Intime India Private Limited as the former name. Page 1 retains `LINK INTIME` in
the registrar heading, but the entity immediately below it is explicitly MUFG
with the same former-name explanation; this is not evidence for a second
registrar. Pages 3 and 52 repeat registration `INR000004058`. Page 54 describes
GYR as the sole book-running lead manager. The acceptance uses the expressly
identified current entity and excludes its former-name annotation.

All 467 and 293 pages were passed through pypdf 6.18.1 in layout mode to locate
same-issuer role references and inspect relevant context. pypdf warned about
rotated text elsewhere in each PDF. This is not a claim that every disclosure
or rotated table was visually audited. The five rendered pages above and the
listed corroborating role passages establish these bounded facts. No unresolved
competing current role identity was found in that inspection.

The source receipt records collection and review times separately. The complete
source PDFs' accessibility does not establish commercial redistribution rights.

## Reusable helper and retained evidence

`scripts/review_intermediary_columns.py`, version
`reviewed-intermediary-columns-v1`, is a separate review helper. It is not imported
by a production collector and does not alter global parser versions, scheduling,
dependencies or broad source extraction. The main parser and residual parser
remain unchanged by this workstream.

The helper supports one current legal entity in each of two explicit cover-role
columns. It retains the exact full-width physical source lines, role heading,
heading span, column bounds and each name's line/character span. Offsets are
zero-based with excluded ends within the retained `rawLines`; `page` is the
one-based physical PDF page. A wide heading separator and an empty name-row
divider prevent cross-column joins. Wrapped names require bounded spans within
one column. Incomplete names, multiple legal entities in one cell, unknown role
headings, divider-crossing text, former-name-only cells and conflicting paired
tables are rejected.

The Sacheerome layout extraction emits an isolated `N` between the role headings;
the rendered page has no additional role there. The exact glyph is retained in
the fixture and heading line. An isolated single glyph with wide whitespace on
both sides can be ignored as non-role decoration; text or an additional heading
cannot supply a role or change the fixed divider.

`validate_evidence(field, value, detail)` replays the retained source lines and
requires the exact value and all evidence fields to match. That establishes
internal consistency; source-hash/issuer/date checks and visual source review
remain required separately. The two real-PDF excerpts are retained in
`tests/fixtures/intermediary_columns_reviewed.json` with source hashes, physical
pages, extraction engine and expected values. Their byte identity is checked in
the tests. The source engine here is explicitly pypdf layout, not a claim of
production Poppler extraction equivalence.

## Verification and integration boundary

Frozen uv Python 3.12.14 / pypdf 6.18.1 passed 15 new helper regressions, four
existing intermediary-layout tests, three existing public-hold tests, ten current
offer-parser tests, eight residual-parser tests and eight financial-layout tests
(48 tests). Existing UTF-8 fixture readers require `python -X utf8` on Windows;
the initial default-cp1252 fixture failures were rerun with that explicit mode.
No complete combined publication or live acceptance pass is claimed here.

The integration coordinator must preserve both issuer records outside the two
role fields and matching proof/history groups, preserve all 441 proposals, keep
the original public holds, and complete existing reviewed publication and live
acceptance. The source-supported Fast Track legal name includes `FINSEC`, which
the existing generic manager-name allowlist does not recognize. Publication must
handle this exact source-backed case without weakening source authority or
silently changing unrelated parser behavior.

If all four fields are safely published, the baseline has three fewer active
held review items and one fewer missing registrar: total source reviews
1,601 to 1,598, blocking reviews 1,597 to 1,594. These are expected bounded
deltas, not deployment results. Both issuers retain other work, so the baseline
388 P4 actionable plus 55 higher-priority record counts need not fall. P5 and
performance remain blocked. Full financial-layout triage still dominates the
backlog: 1,299 review items (702 source-table conflicts, 570 missing revalidated
period evidence, 27 possible percentage/currency contamination).
