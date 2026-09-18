# Bounded source reconstruction — 17 September 2026

The missing seven-record proposal was reconstructed as a **new, unaccepted diagnostic lineage**. Emmvee's four composition fields pass the source check. Teamtech's proposed four allocations remain blocked by a contradiction within the Final Prospectus. No canonical data, repository code, remote resource or deployment was changed by this investigation.

The historical execution used actual combined commit `d8eed0555ff1480476a6d48347eec8e3e39b3f28`, tree `8a6375f1df9f336f1b09716928d28693bd6c3bd4`, and canonical base `2e0e8541f92608ca71ab76a14232f6626ca43050`. The base payload SHA-256 is `29e2c170165e9dad215f786b1805fb8e18680dd43b219a59c29a5954a4160e5c`. Later code commits must receive their own receipts; an equal tree does not authorize changing the historical commit identity.

The original proposal `5516b3ad6ba4345abc25d7a9b2771eb5c3b32f00e9163f30167da9d6b80cf6f6` and its publication transport remain unavailable. This reconstruction neither recovers that artifact nor invalidates its original review.

| Historical output | SHA-256 | Verified scope |
| --- | --- | --- |
| `UNACCEPTED-seven-record-ipos.json` | `9486eb77906508b7224e596e9efa6de7942794d5b3f4e6264675e6415d59d687` | Seven records changed; 1,359 others and all payload metadata preserved |
| `SOURCE_CHECK_PASSED-emmvee-only-ipos.json` | `00b6c5c6a2ed427127cd39dbde4c7f2cc766bb41eb3597752fdb1146631dfce6` | Only Emmvee changed; 1,365 others and all payload metadata preserved |
| `source-acceptance-receipt.json` | `134bf7a14d30bc6da8269aaa4ae60046c772e586bb6c150612d25a68a471470c` | 72 technical checks passed; both payloads have zero strict validation errors |

The independent replay reproduced both payloads, exact diffs, full source texts, parser diagnostics, field proofs and the full receipt byte-for-byte. Validation reports differed only in their actual `generatedAt` timestamps. Independent diff review found no unrelated business-value changes or source-proof mismatch. These checks do not establish source acceptance for Teamtech.

The historical seven-record payload demonstrates the **old value-scoped policy**, which marks its Teamtech replacement resolved. Its unaccepted status is carried by its filename and receipt, not by a document hold within that payload. **Never publish that historical diagnostic.** A fresh execution under the corrected policy must retain Teamtech's document hold and keep its four-row extraction solely as an unaccepted diagnostic.

| Source | Exact PDF SHA-256 | Complete extraction and reviewed context |
| --- | --- | --- |
| [Emmvee Final Prospectus, 14 November 2025](https://nsearchives.nseindia.com/corporate/FP_INE1C6T01020_14NOV2025.pdf) | `85eb9319dc01027821813c71d3702164911442a14547ad72cc04270ea6612eda` | All 511 pages extracted; physical pages 3, 11, 21 and 117 visually reviewed; deployment text on 118 checked |
| [Teamtech Final Prospectus, 22 May 2026](https://nsearchives.nseindia.com/emerge/corporates/content/TeamtechFormworkSolutionsLimited_PROSP.pdf) | `985909fbad119ffa02604f6fbb2895387a98d817a1fa8b486a7806ac18b537e8` | All 372 pages extracted; summary and Objects section 87–100 read with relevant cross-references; pages 87–92 visually reviewed |

Emmvee's cover contains both named selling-shareholder clauses. Physical page 11 corroborates the aggregate OFS, and page 21 gives the complete offer-size table: fresh issue ₹2,143.862 crore, OFS ₹756.138 crore, total ₹2,900 crore. The separate Emmvee candidate changes the four composition fields and matching source-bound field proofs, appending four correction events. Its two allocation amounts, ₹1,621.294 crore and ₹438.711 crore, and their **entire prior field proof** remain unchanged. Older whole-document metadata remains unchanged; the new parser-33 provenance applies only to the four repaired fields. The prospectus's Basis of Allotment qualification remains in the source evidence; no later allotment outcome is asserted.

Teamtech's pages 22–23 and 87 disclose four allocations totaling ₹4,548.59 lakh, or ₹45.4859 crore. Physical/printed page 89 places the same number under the numeric-column heading **“Amount in Crores”** for both net proceeds and total. That is a source contradiction, even though the repeated lakh tables and share-price arithmetic corroborate one interpretation. No typo is inferred as an accepted correction. A separate quotation discrepancy appears on pages 90–92. The source receipt records the exact distinctions and page mapping.

The five continuing holds are Unimech, Blackbuck, M&B Engineering, Shri Ahimsa and GenXAI. Exact recovered PDF bytes for the first three matched their existing registry hashes. Full Shri Ahimsa and GenXAI PDFs were unavailable in this execution; their existing holds were preserved without claiming fresh full-source review.

The [machine-readable receipt](2026-09-17-source-reconstruction.json) records the evidence and limits. The parameterized [reconstruction helper](../../scripts/reconstruct_source_review.py) requires explicit full code/base commits and a registry SHA-256. It pins the reviewed parser files, records all current policy/source scripts and the public display-hold registry, uses the real production extraction and policy functions, forbids network calls, and writes only to a new directory outside the checkout. It respects a current Teamtech document hold and never writes a replacement into that held record merely because structural checks pass.

For a **new execution**, first freeze the actual combined code on a reachable immutable commit and review its exact registry hash. Stage the exact PDFs in a separate input directory, with the names below. If the bytes cannot be recovered and hash-verified, retain the source blocker. Set the following paths and full digests to the reviewed values, then run:

```bash
RECON_CODE=/path/to/exact-frozen-checkout
RECON_SCRIPT="$RECON_CODE/scripts/reconstruct_source_review.py"
RECON_PDFS=/path/to/verified-source-pdfs
RECON_OUT=/path/to/new-outside-checkout-directory
RECON_CODE_COMMIT=FULL_REVIEWED_40_HEX_COMMIT
RECON_BASE_COMMIT=FULL_REVIEWED_40_HEX_BASE_COMMIT
RECON_REGISTRY_SHA256=FULL_REVIEWED_64_HEX_REGISTRY_DIGEST

PYTHONDONTWRITEBYTECODE=1 uv run --frozen --project "$RECON_CODE" python "$RECON_SCRIPT" \
  --code "$RECON_CODE" \
  --expected-code-commit "$RECON_CODE_COMMIT" \
  --expected-base-commit "$RECON_BASE_COMMIT" \
  --expected-registry-sha256 "$RECON_REGISTRY_SHA256" \
  --emmvee-pdf "$RECON_PDFS/emmvee.pdf" \
  --teamtech-pdf "$RECON_PDFS/teamtech.pdf" \
  --retained-pdf-dir "$RECON_PDFS" \
  --out "$RECON_OUT"
```

Use `unimech.pdf`, `blackbuck.pdf` and `mbel.pdf` for the recovered retained-hold inputs. The helper records missing full PDFs honestly. To reproduce candidate bytes from a completed execution, reuse its exact inputs and append `--reviewed-at` with that receipt's timestamp; validation report generation timestamps remain current.

A fresh reconstruction remains **unaccepted for publication**. The next technical requirement is a current-base, exact-code targeted transport with a reviewable diff and source acceptance for its precise scope. Teamtech requires authoritative reconciliation or explicit supersession and remains held. An Emmvee-only release can be evaluated as a separate scope; it cannot be presented as completion of the seven-record acceptance. The broad automatic repair preview is outside this scope. P4 remains blocked, so neither P5 nor performance expansion is enabled.
