# BSE May 2026 official-universe source review

This is an identity/lifecycle review only. It continues the released official-universe snapshot without recrawling completed NSE/SEBI/BSE archive cohorts. Canonical `data/ipos.json` is not changed by this stage.

- Base snapshot: `docs/audits/official-universe/2026-09-19-bse-june`
- Baseline commit: `8309e9193d76c7fc0c071d439e9a1a51aa6edaaa`
- Candidate records: **10**
- Unambiguous identity-only admissions proposed: **10**
- Possible duplicates/collisions requiring review: **0**
- Source unavailable / not verified: **0**
- Review version: `official-universe-bse-cohort-v1`

| Official issuer | Board | BSE symbol | Decision |
|---|---|---|---|
| AUREATE TRADDE LIMITED | SME | AUREATE | accept_identity_only |
| SMR Jewels Limited | SME | SMR | accept_identity_only |
| RAJNANDINI FASHION INDIA LIMITED | SME | RFIL | accept_identity_only |
| YAASHVI JEWELLERS LIMITED | SME | YAASHVI | accept_identity_only |
| M R Maniveni Foods Limited | SME | MANIVENI | accept_identity_only |
| AUTOFURNISH LTD | SME | AFLTD | accept_identity_only |
| Harikanta overseas Limited | SME | HARIKANTA | accept_identity_only |
| Vegorama Punjabi Angithi Limited | SME | VPAL | accept_identity_only |
| Goldline Pharmaceutical Limited | SME | GOLDLINE | accept_identity_only |
| RECODE STUDIOS LIMITED | SME | RECODE | accept_identity_only |

Every accepted proposal has an independent retained BSE detail response with exact issuer header, Equity security type, symbol and issue period matching the retained historical archive row. Listing dates and all numerical/financial/offer fields remain unknown unless separately evidenced. No fuzzy merge is performed.

The inherited Dhanwel June/August collision remains unresolved and is not included in these admissions. See `collision-review.json`. The next stage may promote only `accept_identity_only` records after reviewing this evidence; all other decisions remain non-admissions.
