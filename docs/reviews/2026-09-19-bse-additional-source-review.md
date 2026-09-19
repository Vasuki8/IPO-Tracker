# BSE upcoming-offer recovery: Elevate and Unitec

Source review on 19 September 2026 against accepted main `338af7fdfbf724f40cacabaf0ddd8d422580000f`. This is the next bounded source-family batch after the urgent restoration of the four previously accepted BSE receipts. Neither issuer belongs to the older 1,357-ID historical comparison cohort.

## Accepted scope

| Issuer | Provisional price, INR/share | Market lot, shares | Minimum bid quantity, shares | Offer window |
| --- | --- | --- | --- | --- |
| Elevate Campuses Limited | 343–362 | 41 | 41 | 23–25 September 2026 |
| Unitec Fibres Limited | 83–88 | 1,600 | 3,200 | 23–25 September 2026 |

Accept these six values only through the existing explicit-reviewed correction and publication request. They expire after 25 September IST. The canonical records are upcoming, have no listing date, and have no applicable display hold or data-review conflict. Both source pages identify Equity and Book Building – Forthcoming. Exact issuer names, source symbols ELEVATE/UNITEC, issue IDs 4838/4839, IPO numbers 7987/7988, form actions, detail links, index rows and offer dates agree. Current retained BSE price observations agree. Completed static terms still require matching Final Prospectus authority.

## Exact source evidence

The JSON companion records full URLs, all collection attempts, SHA256, byte counts, independent review, physical rows and blockers. The gzip files under `tests/fixtures/bse-additional-active-offer-terms/` retain exact unmodified response bytes. The first ordinary urllib requests returned HTTP 403; ordinary browser User-Agent retries returned HTTP 200. No source observation time is present: `observedAt` stays null. Collection times are 17:53:23.111330, 17:53:28.979278 and 17:53:35.987908 UTC for index, Elevate and Unitec respectively.

| Source | SHA256 | Bytes |
| --- | --- | ---: |
| Current BSE index | `695b2dd4b27112d60fb025d5f5d231ddae232f790edabc43c1fe98482fcb3667` | 32,242 |
| Elevate detail | `722d3fbade89f9bcaacfee35c5bf4013b980c9097f550afbe076344b67608bce` | 34,946 |
| Unitec detail | `a6a015452c24a064f44a3b901393d0b39e2fdd050367e2f4c1fccdac23d2bf35` | 34,798 |

Using the existing zero-based HTML table contract, Elevate fields are `/html/tables/2` rows 9, 13 and 14; Unitec fields are the same table rows 9, 15 and 16. Exact labels are Price Band, Market Lot and Minimum Bid Quantity. The index is table 3, rows 11 and 12. The price currency marker is the already retained and visually verified rupee image `rs_b.gif`, SHA256 `780cc4f5c88a8c41047804b4fa764872b6648ed1df2927225996c5d1bca6a4bc`.

Only two literal parser compatibilities are needed: accept the actual index query `Type=p` as well as `Type=P`, and normalize the literal board `MainBoard` to canonical `Mainboard`. Raw source URLs and index cells remain unchanged. Replaying with these changes leaves all four original receipts byte-for-byte identical. Unsupported query types, Debt, changed offer dates and an unreviewed currency marker remain rejected. Existing receipt validation still binds immutable source identity.

## Unresolved fields and next work

Market lot, bidding increment, minimum bid quantity and minimum application money remain separate. Do not multiply shares by the cap to invent a whole-offer amount. No canonical symbol, issue size, composition, lot size, application money or intermediary is changed by this transaction.

Elevate's linked price advertisement and RHP returned HTTP 502 on the recorded retries. Independent normal User-Agent retries of those links and Unitec's Windows-path advertisement and RHP/GID ZIP also returned HTTP 502 between 17:56:11 and 17:56:48 UTC. The exact URLs are retained in the source bytes and companion evidence. No unavailable document is treated as reviewed evidence.

The next exact task is to obtain matching official Final Prospectus authority for the six upcoming issuers when their offer stage permits it, starting with the accessible FX/Robokidz advertisement family for separately reviewed bidding increments while continuing to leave completed static amounts blocked. Vivekanand remains a separate issuer/date/price conflict review. The historical 1,357-ID cohort remains at 274 public bands and 154 public issue sizes; this batch must not be reported as repairing its evidence backlog. P5 remains blocked while P4 is blocked.
