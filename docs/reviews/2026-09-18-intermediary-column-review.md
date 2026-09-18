# Intermediary column review - 18 September 2026

At canonical commit `3bdbdc5cdfb6ad44c230d2977512a2e8fa69fee4`, automated extraction had restored three unsupported intermediary values which the public projection labelled `final_verified`. The values combine separate role columns or retain only a former-name qualifier. The affected users are people researching the lead managers and registrars on IPO profiles and quick views.

The immediate correction is a value-bound public hold for Snehaa's `leadManagers` and Sacheerome's `leadManagers` and `registrar`. This does not replace canonical names or resolve a P4 item. Canonical values, source proofs, collection dates, review metadata and correction history remain intact. An accepted correction must provide the role-specific source evidence before publication.

## Source inspection

Both official HTTPS downloads returned HTTP 200 on 18 September 2026. Their SHA-256 digests exactly match the affected canonical field proofs. The full PDFs were opened to check page counts. The affected physical pages were extracted in layout mode with pypdf and rendered with Poppler for visual inspection; the findings below come from the visible column boundaries and role headings, not from linear text order alone.

| Issue | Final Prospectus | Identity | Inspected physical page |
| --- | --- | --- | --- |
| Snehaa Organics Limited (`SNEHAA`, opened 2025-08-29) | [NSE Final Prospectus](https://nsearchives.nseindia.com/emerge/corporates/content/SnehaaOrganicsLimited_PROSP.pdf), dated 2025-09-03 | 467 pages; 18,126,150 bytes; SHA-256 `05326ed87f0869904f25d9be04e93a59f9a6491e45446bd0f098c10150daee73` | 1 |
| Sacheerome Limited (`SACHEEROME`, opened 2025-06-09) | [NSE Final Prospectus](https://nsearchives.nseindia.com/emerge/corporates/content/SacheeromeLimited_PROSP.pdf), dated 2025-06-12 | 293 pages; 7,589,875 bytes; SHA-256 `f5abf7b4258fd52c88aadcac66bcd65c96ded9c952c1e7fe364a0a4fc4c3c07e` | 3 |

Snehaa's inspected page places Fast Track Finsec in the lead-manager column and Skyline Financial Services in the registrar column. The retained `leadManagers` entry concatenates both legal entities into one string. Snehaa's canonical registrar is missing and remains missing in this improvement.

Sacheerome's inspected page places GYR Capital Advisors in the lead-manager column and MUFG Intime India in the registrar column. The retained `leadManagers` entry concatenates both entities. The retained `registrar` value consists only of the parenthetical former-name line beneath the current registrar. This is an extraction defect; the hold does not assert that the prospectus contradicts itself.

The immutable regression fixture retains the two complete production records, including the three bad values and their source evidence, at the baseline commit. Source URLs, document dates, physical page numbers and exact document/value digests are also recorded in `data/public_display_holds.json`. The PDFs were used for source inspection only; public access does not establish commercial redistribution rights.

## Acceptance and release boundary

- All three affected fields are withheld with `under_review` and a retained source link across the shared public projection, profile and quick-view consumers. The directory and its exports must not introduce a fallback for these fields.
- Each active hold produces an actionable source-review item which preserves its registry identity and evidence. It is routed to manual source review rather than repeatedly submitting an unchanged parser result.
- The original canonical records, all retained proposals and correction history are preserved; no missing value is filled and no corrected entity is guessed.
- A new collection timestamp, parser number or mirror of the same PDF cannot release the same held value. These extraction holds remain value-scoped: they do not label the whole PDF contradictory or block every future source-checked correction from that document.

Next source-repair task: extract the two role columns independently, review field-specific evidence against these exact Final Prospectuses, and publish any accepted replacement through a bounded correction with history. The immediate hold and queue routing are not numerical source acceptance or P4 completion.

## Local verification before integration

The three new retained-record regressions passed when combined with the shared hold-to-review routing implementation, together with 26 existing public-quality tests, nine company-route tests and eight Node public-quality tests. The new tests cover all three withheld fields, retained source links and complete correction history, unchanged missing registrar data, a repeated extraction through a PDF mirror, and one manual repair task for each held field. The generic public explanation now requires matching source evidence without implying that a replacement has already been accepted.

Chromium 153.0.8010.0 checked both actual generated profiles and their directory quick views at widths of 1,440 and 390 pixels. All three affected fields displayed Under review, none of the malformed names appeared, there was no horizontal overflow, no uncaught browser error, and no request for the unsanitized canonical dataset. Source-review screenshots were visually checked separately from the website checks.

The public build regenerated only the two affected profiles and their route digests: 1,366 routes, two written and 1,364 unchanged, with no canonical or public-summary rewrite. Both full regression records exactly matched the baseline canonical records. `data/ipos.json` remained SHA-256 `fe8a78b6149d1e8f25b0f81fc16b4ba1e3e00aa59a436d5ae1566d0080d27bcd`; retained proposals remained SHA-256 `ed4b1ae67dfc0b9a9a92090749e24c631933a884a92e6fe9576a6af1f8ba68a3`.

The existing checked-in source-review-count assertion correctly requires regenerated phase and queue reports after active holds become operational reviews. Integration must regenerate those reports and run the complete required checks; the focused results above do not claim a release or source-value correction.
