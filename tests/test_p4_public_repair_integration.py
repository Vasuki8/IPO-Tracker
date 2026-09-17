"""Integration of the preserved repair stack with the deployed display boundary.

Reuses the existing repair fixtures and exact physical source excerpts.
These deterministic checks do not replace complete-PDF release acceptance.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import apply_corrections as corrections
import build_company_pages as pages
import final_prospectus_parser as parser
import final_prospectus_policy as policy
import public_quality
import publish_transaction as publication
import test_final_mixed_ofs_policy as composition_fixtures
import test_reviewed_objects_quarantine as objects_fixtures

REGISTRY = json.loads((ROOT / 'data/verified_corrections.json').read_text())
ENTRIES = {entry['identity']['id']: entry for entry in REGISTRY['reviewedObjects']}
CI_ROWS = {row['id']: row for row in json.loads((ROOT / 'tests/fixtures/objects-source-review/new-document-ci-records.json').read_text())['records']}


def apply_excerpt(row, identifier, field):
    if identifier == 'emmvee':
        text = (ROOT / 'tests/fixtures/issue_composition/emmvee-final-offer.txt').read_text()
        proof = row['staticFieldProvenance']['issueComposition']
        doc = {'type': 'PROSPECTUS', 'url': proof['sourceUrl'], 'source': 'NSE', 'filedDate': '2025-11-14'}
        sha = proof['sha256']
    else:
        text = (ROOT / f'tests/fixtures/objects-source-acceptance/{identifier}.txt').read_text()
        entry = ENTRIES[identifier]
        doc, sha = entry['source'], entry['evidence']['sha256']
    parsed = parser.parse_document_text(text)
    # Test only the reviewed field; unrelated parsed fields are not approved here.
    parsed = {field: parsed[field], 'fieldEvidence': {field: parsed['fieldEvidence'][field]}}
    changes = policy.apply_final_prospectus_static_fields(
        row, parsed, doc, sha256=sha, parser_version=parser.PARSER_VERSION,
        checked_at='2026-09-17T22:00:00Z',
    )
    row.setdefault('dataCorrections', []).extend(changes)
    return changes


class P4PublicRepairIntegrationTests(unittest.TestCase):
    def test_repaired_emmvee_composition_reaches_summary_and_profile_with_matching_proof(self):
        row = composition_fixtures.FinalMixedOfsPolicyTests().record()
        before = copy.deepcopy(row)
        apply_excerpt(row, 'emmvee', 'issueComposition')
        self.assertEqual(row['issueSizeCr'], 2900.0)
        self.assertEqual(row['freshIssueCr'], 2143.862)
        self.assertEqual(row['ofsCr'], 756.138)
        for projection in (pages.public_summary_record, pages.public_profile_record):
            view = projection(row)
            self.assertEqual(view['issueSizeCr'], 2900.0)
            decision = view['publicQuality']['fields']['issueSizeCr']
            self.assertEqual(decision['state'], 'final_verified')
            source = view['publicQuality']['sources'][decision['source']]
            self.assertEqual(source['sha256'], row['staticFieldProvenance']['issueSizeCr']['sha256'])
            self.assertEqual(source['sourceUrl'], row['staticFieldProvenance']['issueSizeCr']['sourceUrl'])
        for field in ('objectsOfIssue', 'financials', 'documents'):
            self.assertEqual(row[field], before[field])
        self.assertEqual(row['staticFieldProvenance']['objectsOfIssue'], before['staticFieldProvenance']['objectsOfIssue'])
        self.assertEqual(row['dataCorrections'][:len(before['dataCorrections'])], before['dataCorrections'])

    def test_corrected_teamtech_value_resolves_hold_without_erasing_its_review(self):
        row = objects_fixtures.record(ENTRIES['teamtech'])
        self.assertEqual(corrections.quarantine_reviewed_objects({'teamtech': row}, [ENTRIES['teamtech']]), (1, []))
        snapshot = copy.deepcopy(row['objectsOfIssueReview']['snapshot'])
        apply_excerpt(row, 'teamtech', 'objectsOfIssue')
        self.assertEqual(row['objectsOfIssueReview']['status'], 'resolved')
        self.assertEqual(row['objectsOfIssueReview']['snapshot'], snapshot)
        view = pages.public_profile_record(row)
        self.assertEqual(len(view['objectsOfIssue']), 4)
        self.assertAlmostEqual(sum(item['amountCr'] for item in view['objectsOfIssue']), 45.4859)
        self.assertEqual(view['publicQuality']['fields']['objectsOfIssue']['state'], 'final_verified')
        self.assertNotIn('Cost of Land', [item['purpose'] for item in view['objectsOfIssue']])
        # Public projection never mutates the canonical correction snapshot.
        self.assertEqual(row['objectsOfIssueReview']['snapshot'], snapshot)

    def test_canonical_holds_keep_five_reviewed_lists_hidden_without_temporary_display_registry(self):
        for identifier in ('unimech', 'blackbuck', 'mbel', 'shriahimsa', 'genxai'):
            with self.subTest(id=identifier):
                row = objects_fixtures.record(ENTRIES[identifier])
                previous = copy.deepcopy(row['objectsOfIssue'])
                self.assertEqual(corrections.quarantine_reviewed_objects({identifier: row}, [ENTRIES[identifier]]), (1, []))
                saved = copy.deepcopy(row)
                view = public_quality.project_record(row, holds=[])
                self.assertIsNone(view['objectsOfIssue'])
                self.assertEqual(view['publicQuality']['fields']['objectsOfIssue']['state'], 'under_review')
                self.assertEqual(row['objectsOfIssueReview']['snapshot']['before'], previous)
                self.assertEqual(row, saved)

    def test_new_source_holds_survive_publication_with_independent_subscription_update(self):
        for identifier, source_record in CI_ROWS.items():
            with self.subTest(id=identifier):
                proposed = copy.deepcopy(source_record)
                baseline = copy.deepcopy(source_record)
                baseline['objectsOfIssue'] = None
                baseline['staticFieldProvenance'].pop('objectsOfIssue', None)
                current = copy.deepcopy(baseline)
                current.update(subscription={'total': 2.5}, subscriptionSource='NSE',
                               subscriptionSourceUrl='https://www.nseindia.com/market-data/issue-information',
                               subscriptionObservedAt='2026-09-17T16:00:00+05:30',
                               subscriptionCollectedAt='2026-09-17T16:10:00+05:30',
                               subscriptionTimeBasis='source_reported')
                merged, conflicts = publication.merge_payload(
                    {'ipos': [baseline]}, {'ipos': [proposed]}, {'ipos': [current]},
                )
                self.assertEqual(conflicts, [])
                row = merged['ipos'][0]
                self.assertEqual(corrections.quarantine_reviewed_objects({identifier: row}, [ENTRIES[identifier]]), (1, []))
                saved = copy.deepcopy(row)
                view = public_quality.project_record(row, holds=[])
                self.assertIsNone(view['objectsOfIssue'])
                self.assertEqual(view['publicQuality']['fields']['objectsOfIssue']['state'], 'under_review')
                for field in ('subscription', 'subscriptionObservedAt', 'subscriptionCollectedAt', 'subscriptionSourceUrl'):
                    self.assertEqual(view[field], current[field])
                self.assertEqual(row, saved)
                self.assertEqual(row['objectsOfIssueReview']['snapshot']['sourceEvidence'], proposed['staticFieldProvenance']['objectsOfIssue'])


if __name__ == '__main__':
    unittest.main()
