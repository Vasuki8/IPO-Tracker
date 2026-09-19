# Recorded operational health

Assessed at **2026-09-19T04:30:00+00:00**. Frozen evidence, not live monitoring.

Source observation, collection attempts, publisher execution and exact acceptance are separate clocks. Missing clocks stay unknown.

## Counts

| Signal | Count / state |
| --- | --- |
| canonicalRecords | 1404 |
| lifecycleScopes | {"after_close": 91, "before_open": 7, "not_live_status": 1288, "open_by_recorded_dates": 5, "unknown_dates": 13} |
| openSubscriptions | 5 |
| retainedOfferReceipts | 3 |
| offerReceiptStates | {"provisional": 3} |
| offerReceiptUnknownObservations | 3 |
| observationStates | {"outside_monitoring_deadline": 2, "source_time_unknown": 3} |
| collectionStates | {"missing": 1, "outside_monitoring_deadline": 4} |
| sourceOutcomes | {"failed": 5, "partial_failure": 1, "successful": 27} |
| stageOutcomes | {"source_blocked": 3, "successful": 10, "unknown": 1} |
| overdueSourceChecks | 3 |
| overdueStages | 1 |
| observationsOlderThanTolerance | 2 |
| unresolvedProposals | 441 |
| stagesNeedingInvestigation | 4 |
| sourcesNeedingInvestigation | 8 |

## Publication

Recorded dataset publisher: {"collectorCommit": "9c404bea6e7edbeccee4680e7cce7d0984d6c57e", "mode": "reviewed", "pendingConflictCount": 441, "reviewedIds": ["axiomgas", "varmora", "poojalogis"], "runId": "35417782070", "status": "published"}.

Exact accepted publication time: **unknown**. Publisher execution does not establish per-source acceptance or deployment.

Delivery evidence: {"collectionToPublisherCompletion": {"from": "2026-09-19T03:11:01Z", "minutes": 0.533, "state": "recorded_interval", "to": "2026-09-19T03:11:33Z"}, "collectorCommit": "9c404bea6e7edbeccee4680e7cce7d0984d6c57e", "jobs": {"collect": {"completed_at": "2026-09-19T03:11:01Z", "conclusion": "success", "started_at": "2026-09-19T03:10:14Z", "status": "completed"}, "publish": {"completed_at": "2026-09-19T03:11:33Z", "conclusion": "success", "started_at": "2026-09-19T03:11:03Z", "status": "completed"}}, "publisherWindow": {"acceptedAt": null, "completedAt": "2026-09-19T03:11:33Z", "meaning": "Publisher execution window; exact accepted commit time is not recorded in canonical publication metadata.", "startedAt": "2026-09-19T03:11:03Z", "state": "bound_successful_publisher"}, "recordedRunConclusion": "success", "recordedRunStatus": "completed", "recordedRunUpdatedAt": "2026-09-19T03:11:34Z", "runAttempt": 1, "runId": "35417782070", "scope": "supplied-workflow-snapshot-not-live-polling-or-source-acceptance", "state": "accepted_run_matches"}.

## Sources

Check clocks describe collection attempts. Source roles do not establish field-level authority. Retained older entries remain visible without an invented cadence.

| Source / authority | Observation | Last check / freshness | Outcome | Latest retained successful stage | Failure / deferral evidence | Next action |
| --- | --- | --- | --- | --- | --- | --- |
| BSE / official_exchange | unknown (missing) | 2026-09-19T07:09:41+05:30 (overdue) | partial_failure | {"checkedAt": "2026-09-19T01:39:43.590593+00:00", "status": "updated"} | {"errors": ["https://www.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=1&Type=p: No IPO rows parsed; disclosure absence not established", "https://www.bsesme.com/PublicIssues/PublicIssues.aspx?id=2: HTTPSConnectionPool(host='www.bsesme.com', port=443): Max retries exceeded with url: /PublicIssues/PublicIssues.aspx?id=2 (Caused by ConnectTimeoutError(<HTTPSConnection(host='www.bsesme.com', port=443) at 0x7f7e6dc436e0>, 'Connection to www.bsesme.com timed out. (connect timeout=30)'))"]} | Review failed items individually; successful items do not clear the failures. |
| BSE-P4-issue-terms / not_assessed | unknown (missing) | 2026-09-14T03:41:10+05:30 (recorded_only) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| BSE-detail / not_assessed | unknown (missing) | unknown (missing) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| BSE-history-detail / not_assessed | unknown (missing) | unknown (missing) | failed | unknown | {"error": "BSE historical archive unavailable on official hosts: https://www.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=2&Type=P: historical page did not contain its ASP.NET form; https://beta.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=2&Type=P: historical issue-type selector was not found"} | Inspect the recorded failure and original run; preserve accepted values before an authorized retry. |
| Critical-backfill / not_assessed | unknown (missing) | 2026-09-14T11:57:31+05:30 (recorded_only) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| IPO-subscription / per_snapshot_official_secondary_or_unknown | unknown (missing) | 2026-09-19T01:52:15+05:30 (outside_monitoring_deadline) | failed | unknown | {"errors": ["SpectraA Technology Solutions Limited: official and secondary subscription feeds unavailable (NSE: 403 Client Error: Forbidden for url: https://www.nseindia.com/; BSE: no matching BSE public-issue link; secondary: IPO Premium subscription (secondary): IPO Premium subscription (secondary) row not found for SpectraA Technology Solutions Limited; Groww IPO subscription (secondary): Groww IPO subscription (secondary) page contained no parseable table rows; IPO Dhamaka subscription (secondary): IPO Dhamaka subscription (secondary) row not found for SpectraA Technology Solu)"]} | Inspect the recorded failure and original run; preserve accepted values before an authorized retry. |
| Issuer-offer-docs / document_specific | unknown (missing) | 2026-09-19T07:17:40+05:30 (within_tolerance) | successful | {"checkedAt": "2026-09-19T01:47:41.783104+00:00", "status": "updated"} | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| NSE-history / official_exchange | unknown (missing) | 2026-09-19T07:09:01+05:30 (recorded_only) | successful | {"checkedAt": "2026-09-19T01:39:43.590593+00:00", "status": "updated"} | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| NSE-history-IPO-filter / not_assessed | unknown (missing) | 2026-09-13T23:20:21+05:30 (recorded_only) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| NSE-issue-info / not_assessed | unknown (missing) | unknown (missing) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| NSE-issue-info-terms / not_assessed | unknown (missing) | unknown (missing) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| NSE-live / official_exchange | unknown (missing) | 2026-09-19T07:08:40+05:30 (overdue) | successful | {"checkedAt": "2026-09-19T01:39:43.590593+00:00", "status": "updated"} | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| NSE-lot-size-backfill / not_assessed | unknown (missing) | 2026-09-16T10:11:00+05:30 (recorded_only) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| NSE-primary-market-reports / not_assessed | unknown (missing) | 2026-09-13T23:20:35+05:30 (recorded_only) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| Offer-docs / not_assessed | unknown (missing) | unknown (missing) | failed | unknown | {} | Inspect the recorded failure and original run; preserve accepted values before an authorized retry. |
| P4-legacy-debt-symbol-cleanup / not_assessed | unknown (missing) | unknown (missing) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| P4-verified-non-IPO-cleanup / not_assessed | unknown (missing) | unknown (missing) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| P4-verified-record-repairs / not_assessed | unknown (missing) | 2026-09-14T03:33:10+05:30 (recorded_only) | failed | unknown | {} | Inspect the recorded failure and original run; preserve accepted values before an authorized retry. |
| SEBI / official_regulator | unknown (missing) | 2026-09-19T07:09:08+05:30 (overdue) | successful | {"checkedAt": "2026-09-19T01:39:43.590593+00:00", "status": "updated"} | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| SEBI-document-links / document_specific | unknown (missing) | 2026-09-19T07:10:24+05:30 (within_tolerance) | successful | {"checkedAt": "2026-09-19T01:40:25.443906+00:00", "status": "no_change"} | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| SEBI-offer-issue-terms / not_assessed | unknown (missing) | 2026-09-14T03:39:42+05:30 (recorded_only) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| SEBI-offer-terms / not_assessed | unknown (missing) | 2026-09-16T05:55:34+05:30 (recorded_only) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| SEBI-other-doc-lot-backfill / not_assessed | unknown (missing) | 2026-09-15T23:19:16+05:30 (recorded_only) | failed | unknown | {"errors": ["Jayesh Logistics Limited Jayesh Logistics Limited: ('Connection broken: IncompleteRead(7759815 bytes read, 2263951 more expected)', IncompleteRead(7759815 bytes read, 2263951 more expected))"]} | Inspect the recorded failure and original run; preserve accepted values before an authorized retry. |
| SEBI-priority-registers / official_regulator | unknown (missing) | 2026-09-19T07:10:20+05:30 (within_tolerance) | successful | {"checkedAt": "2026-09-19T01:40:21.347551+00:00", "status": "no_change"} | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| verified-filing-offer-fields / not_assessed | unknown (missing) | 2026-09-16T05:55:34+05:30 (recorded_only) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| verified-lot-sizes / not_assessed | unknown (missing) | 2026-09-14T03:33:10+05:30 (recorded_only) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| verified-p4-final-composition / not_assessed | unknown (missing) | 2026-09-14T04:48:01+05:30 (recorded_only) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| verified-p4-final-issue-terms / not_assessed | unknown (missing) | 2026-09-14T04:29:55+05:30 (recorded_only) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| verified-p4-nse-issue-terms / not_assessed | unknown (missing) | 2026-09-14T04:26:04+05:30 (recorded_only) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| verified-p4-official-issue-terms / not_assessed | unknown (missing) | 2026-09-14T03:51:33+05:30 (recorded_only) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| verified-recent-issue-terms / not_assessed | unknown (missing) | 2026-09-16T10:34:24+05:30 (recorded_only) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| verified-recent-offer-fields / not_assessed | unknown (missing) | 2026-09-14T03:33:11+05:30 (recorded_only) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |
| verified-upcoming-lot-sizes / not_assessed | unknown (missing) | 2026-09-13T08:37:57+05:30 (recorded_only) | successful | unknown | {} | A recorded success is not source freshness or field verification; inspect independent clocks and reviews. |

## Stage outcomes

| Stage | Last check / freshness | Outcome | Failure / deferral evidence |
| --- | --- | --- | --- |
| apply_corrections.py | 2026-09-19T01:38:14.066140+00:00 (recorded_only) | successful | {} |
| backfill_p4_lot_sizes.py | 2026-09-14T05:20:21.946187+00:00 (recorded_only) | source_blocked | {"diagnostics": "BSE historical detail unavailable: BSE historical archive unavailable on official hosts: https://www.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=2&Type=P: 403 Client Error: Forbidden for url: https://www.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=2&Type=P; https://beta.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=2&Type=P: 403 Client Error: Forbidden for url: https://beta.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=2&Type=P\n"} |
| backfill_recent_nse_lot_sizes.py | 2026-09-14T05:20:10.342798+00:00 (recorded_only) | successful | {} |
| backfill_recent_sebi_other_docs_lot_sizes.py | 2026-09-14T05:18:02.329039+00:00 (recorded_only) | source_blocked | {"diagnostics": "{\n  \"targets\": 113,\n  \"selected\": 113,\n  \"matchedPages\": 3,\n  \"discoveredDocuments\": 3,\n  \"attemptedDocuments\": 3,\n  \"updated\": 0,\n  \"failed\": 2,\n  \"updatedIds\": [],\n  \"errors\": [\n    \"Dhara Rail Projects Limited DHARA RAIL PROJECTS LIMITED: ('Connection broken: IncompleteRead(6974255 bytes read, 4066020 more expected)', IncompleteRead(6974255 bytes read, 4066020 more expected))\",\n    \"Jayesh Logistics Limited Jayesh Logistics Limited: ('Connection broken: IncompleteRead(5439423 bytes read, 4584343 more expected)', IncompleteRead(5439423 bytes read, 4584343 more expected))\"\n  ],\n  \"asOf\": \"2026-09-14T10:48:02+05:30\"\n}\n"} |
| collect_nse_offer_filings_final_policy.py | 2026-09-19T01:41:35.569212+00:00 (within_tolerance) | source_blocked | {"diagnostics": "{\"registerRows\": 2546, \"candidates\": 2, \"attempted\": 2, \"updated\": 0, \"documentsDiscovered\": 0, \"failed\": 1, \"errors\": [{\"sourceUrl\": \"https://nsearchives.nseindia.com/emerge/corporates/content/IPO_LISTING_11736_1724688_16092026054144_WEB.xml\", \"error\": \"HTTPSConnectionPool(host='nsearchives.nseindia.com', port=443): Read timed out. (read timeout=25)\"}], \"outcomes\": [{\"id\": \"vivekanand-cotspin-limited\", \"status\": \"no_match\", \"changedFields\": [], \"documentsAdded\": 0}, {\"id\": \"vinod\", \"status\": \"source_blocked\", \"changedFields\": [], \"documentsAdded\": 0}], \"checkedAt\": \"2026-09-19T01:41:34+00:00\", \"finalProspectusDiscovery\": {\"registerRows\": 2546, \"matchedRecords\": 48, \"candidates\": 1, \"selected\": 1, \"attempted\": 1, \"recordsWithFinalProspectus\": 0, \"documentsDiscovered\": 0, \"noFinalProspectusInRegister\": 1, \"skippedRecentFingerprint\": 47, \"deferredByDocumentLimit\": 0, \"historyDays\": 730, \"checkedAt\": \"2026-09-19T01:41:34+00:00\", \"outcomes\": [{\"id\": \"vivekanand-cotspin-limited\", \"company\": \"Vivekanand Cotspin Limited\", \"openDate\": \"2026-09-21\", \"status\": \"no_final_prospectus\", \"documentUrl\": null}], \"failed\": 0, \"errors\": []}}\n"} |
| enforce_final_prospectus_policy.py | 2026-09-19T01:47:49.292132+00:00 (recorded_only) | successful | {} |
| enrich_sebi_document_links.py | 2026-09-19T01:40:25.443906+00:00 (within_tolerance) | successful | {} |
| enrich_sebi_priority_registers_v2.py | 2026-09-19T01:40:21.347551+00:00 (within_tolerance) | successful | {} |
| normalize_source_health.py | 2026-09-19T01:39:47.212726+00:00 (recorded_only) | successful | {} |
| record_integrity.py | 2026-09-19T01:47:47.871517+00:00 (recorded_only) | successful | {} |
| run_issuer_offer_docs.py | 2026-09-19T01:47:41.783104+00:00 (within_tolerance) | successful | {} |
| run_offer_documents.py | 2026-09-19T01:47:08.920301+00:00 (within_tolerance) | successful | {} |
| run_priority_subscriptions_v3.py | unknown (missing) | unknown | {} |
| run_update_final_policy.py | 2026-09-19T01:39:43.590593+00:00 (overdue) | successful | {} |

## Active subscriptions

Scope follows recorded offer dates in Asia/Kolkata. Outside monitoring hours does not make an old observation current. Provisional snapshots do not become final.

| Issuer | Source / authority | Observation | Collection | Public state / finality | Next action |
| --- | --- | --- | --- | --- | --- |
| sona | {"authority": "official_exchange", "binding": "snapshot_fields_only_no_current_history_fallback", "label": "BSE cumulative demand", "url": "https://beta.bseindia.com/markets/publicIssues/CummDemandSchedule.aspx?ID=7973&status=L"} | unknown (source_time_unknown) | 2026-09-18T20:22:13+00:00 (outside_monitoring_deadline) | {"finality": "not_established_by_snapshot", "publicState": "reported"} | Check issue-bound source evidence; collection time cannot supply an observation or final subscription. |
| nse | {"authority": "official_exchange", "binding": "snapshot_fields_only_no_current_history_fallback", "label": "BSE cumulative demand", "url": "https://beta.bseindia.com/markets/publicIssues/CummDemandSchedule.aspx?ID=7977&status=L"} | unknown (source_time_unknown) | 2026-09-18T20:22:12+00:00 (outside_monitoring_deadline) | {"finality": "not_established_by_snapshot", "publicState": "reported"} | Check issue-bound source evidence; collection time cannot supply an observation or final subscription. |
| kheriaauto | {"authority": "secondary", "binding": "snapshot_fields_only_no_current_history_fallback", "label": "IPO Premium subscription (secondary)", "url": "https://www.ipopremium.in/view/subscription"} | 2026-09-18T14:23:17+00:00 (outside_monitoring_deadline) | 2026-09-18T20:22:10+00:00 (outside_monitoring_deadline) | {"finality": "not_established_by_snapshot", "publicState": "reported"} | Check issue-bound source evidence; collection time cannot supply an observation or final subscription. |
| spectraa | {"authority": "unknown", "binding": "snapshot_fields_only_no_current_history_fallback", "label": null, "url": null} | unknown (source_time_unknown) | unknown (missing) | {"finality": "not_established_by_snapshot", "publicState": "under_review"} | Check issue-bound source evidence; collection time cannot supply an observation or final subscription. |
| axiomgas | {"authority": "secondary", "binding": "snapshot_fields_only_no_current_history_fallback", "label": "IPO Premium subscription (secondary)", "url": "https://www.ipopremium.in/view/subscription"} | 2026-09-18T15:11:14+00:00 (outside_monitoring_deadline) | 2026-09-18T20:22:15+00:00 (outside_monitoring_deadline) | {"finality": "not_established_by_snapshot", "publicState": "reported"} | Check issue-bound source evidence; collection time cannot supply an observation or final subscription. |

## Retained provisional offer receipts

Every stored receipt remains listed after expiry or a failed review. Replay uses the existing source and public-display policies; it is not a new source check. Review time is not accepted publication time.

No scheduled collection deadline applies to these bounded reviews. Unknown observation times remain unknown; the general NSE collector clock does not refresh these receipts.

| Issuer / state | Source | Observation | Collection | Review | Provisional through (IST) | Fields / unresolved / issues | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| axiomgas / provisional | {"authority": "official_exchange", "name": "NSE", "sha256": "9a2a3901052e7d9354c252820212ec5d9b39ad76fc79f3f5e102a5ea7088a8ce", "url": "https://www.nseindia.com/api/ipo-detail?symbol=AXIOMGAS&series=SME"} | unknown (missing) | 2026-09-19T02:30:05.462927+00:00 (recorded_only) | 2026-09-19T02:44:41+00:00 (recorded_only) | 2026-09-22 | {"issues": {}, "publicFields": {"issueComposition": {"row": 4, "state": "provisional", "table": "/issueInfo/dataList", "until": "2026-09-22", "usesThisReceipt": true}, "lotSize": {"row": 7, "state": "provisional", "table": "/issueInfo/dataList", "until": "2026-09-22", "usesThisReceipt": true}, "minimumBidQuantity": {"state": "awaiting_disclosure", "usesThisReceipt": false}, "priceBand": {"row": 6, "state": "provisional", "table": "/issueInfo/dataList", "until": "2026-09-22", "usesThisReceipt": true}}, "unresolved": {"issueSizeCr": "disclosure-absent: no explicit total INR amount in the supported source table", "minimumBidQuantity": "disclosure-absent"}} | Keep terms explicitly provisional; review official changes and expiry without inferring source freshness. |
| varmora / provisional | {"authority": "official_exchange", "name": "NSE", "sha256": "998c9afe8b5a6a7216dd675f85b4120efe4c24e703815f96e7a668c14a8263dd", "url": "https://www.nseindia.com/api/ipo-detail?symbol=VARMORA&series=EQ"} | unknown (missing) | 2026-09-19T02:30:05.723182+00:00 (recorded_only) | 2026-09-19T02:44:41+00:00 (recorded_only) | 2026-09-24 | {"issues": {}, "publicFields": {"issueComposition": {"row": 5, "state": "provisional", "table": "/issueInfo/dataList", "until": "2026-09-24", "usesThisReceipt": true}, "lotSize": {"row": 11, "state": "provisional", "table": "/issueInfo/dataList", "until": "2026-09-24", "usesThisReceipt": true}, "minimumBidQuantity": {"row": 12, "state": "provisional", "table": "/issueInfo/dataList", "until": "2026-09-24", "usesThisReceipt": true}, "priceBand": {"row": 7, "state": "provisional", "table": "/issueInfo/dataList", "until": "2026-09-24", "usesThisReceipt": true}}, "unresolved": {"issueSizeCr": "disclosure-absent: no explicit total INR amount in the supported source table"}} | Keep terms explicitly provisional; review official changes and expiry without inferring source freshness. |
| poojalogis / provisional | {"authority": "official_exchange", "name": "NSE", "sha256": "1662fe9ba50928c9715fcd0bb2c367270371bef54810ea6c456a05521289505e", "url": "https://www.nseindia.com/api/ipo-detail?symbol=POOJALOGIS&series=SME"} | unknown (missing) | 2026-09-19T02:30:26.012131+00:00 (recorded_only) | 2026-09-19T02:44:41+00:00 (recorded_only) | 2026-09-25 | {"issues": {}, "publicFields": {"issueComposition": {"row": 4, "state": "provisional", "table": "/issueInfo/dataList", "until": "2026-09-25", "usesThisReceipt": true}, "lotSize": {"row": 7, "state": "provisional", "table": "/issueInfo/dataList", "until": "2026-09-25", "usesThisReceipt": true}, "minimumBidQuantity": {"state": "awaiting_disclosure", "usesThisReceipt": false}, "priceBand": {"row": 6, "state": "provisional", "table": "/issueInfo/dataList", "until": "2026-09-25", "usesThisReceipt": true}}, "unresolved": {"issueSizeCr": "disclosure-absent: no explicit total INR amount in the supported source table", "minimumBidQuantity": "disclosure-absent"}} | Keep terms explicitly provisional; review official changes and expiry without inferring source freshness. |

## Retained proposals and reviews

Unresolved envelopes: **441**. Exact creation age unknown: **441**. Resolutions applied: **0**.

Comparison summary: {"byComparisonState": {"not_assessed": 260, "still_conflicting": 181}, "documentFieldProposals": 159, "documentWithEvidenceOrReviewDifferences": 159, "documentWithValueDifferences": 32, "duplicateFingerprintOccurrences": 0, "retainedProposals": 441, "subscriptionByComparisonState": {"still_conflicting": 22}, "subscriptionObservationRelations": {"not_comparable": 14, "proposed_older": 8}, "subscriptionSnapshotProposals": 22}.

Source-review queue: {"generatedAt": "2026-09-19T09:18:25+05:30", "meaning": "Retained review counts, not resolution or freshness.", "queuedRecords": 1389, "sourceReviewItems": 1557, "state": "recorded"}.

Each envelope, comparison, review decision and next action is retained in the JSON report. Originating publisher windows are supporting workflow evidence, not exact proposal creation times.

| Origin run | Publisher start | Publisher end | Window state |
| --- | --- | --- | --- |
| 35056273505 | 2026-09-16T04:44:00Z | 2026-09-16T04:44:24Z | bound_successful_publisher |
| 35204652736 | 2026-09-17T09:23:10Z | 2026-09-17T09:23:35Z | bound_successful_publisher |
| 35254384128 | 2026-09-17T18:18:36Z | 2026-09-17T18:19:04Z | bound_successful_publisher |
| 35257821039 | 2026-09-17T18:22:10Z | 2026-09-17T18:22:44Z | bound_successful_publisher |

## Limitations

- No source collection, accepted correction, proposal resolution or phase advancement.
- Recorded stage outcomes can outlive the run that produced them; unpublished failures need separate run/job evidence.
- No historical success clock is invented when the latest retained outcome failed or was deferred.
- Proposal creation and exact accepted-commit timestamps are absent; workflow execution windows remain separately labelled.
- Within tolerance describes clock age only, never source success or accurate financial values.
- Unknown/invalid lifecycle dates remain counted; no live deadline is guessed for those records.
- Offer receipt replay verifies retained evidence only; it does not recollect sources, resolve reviews or prove present source freshness.
- Successful no-change runs need not create a publication; an old snapshot alone does not prove publication delay.

Reproduce the JSON report with the original input files and assessment instant. A successful replay does not declare it fresh now.
