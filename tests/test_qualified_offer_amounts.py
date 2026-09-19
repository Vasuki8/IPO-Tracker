import copy
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from qualified_offer_amount_helpers import cohort, FIXTURES
from qualified_offer_amounts import FIELD, digest, extract, validate
from active_offer_terms import accepted_terms, validate_receipt
from apply_corrections import apply
from audit_data_completeness import expected_exchange_rules
from public_quality import project_record
from reviewed_corrections import prepare, validate_scope
from reviewed_evidence import index_groups
from publish_transaction import merge_payload
from validate_data import validate_payload, validate_record
from source_review_queue import review_task
from build_company_pages import public_summary_record, public_profile_record
from verify_public_release import verify_active_offer_delivery
from source_review_holds import active_hold_reviews, display_hold_matches


class QualifiedOfferAmountTests(unittest.TestCase):
    def setUp(self):
        self.before, self.registry, self.groups = cohort()
        self.ids = ['axiomgas', 'varmora']
        for module in ('active_offer_terms', 'public_quality', 'verify_public_release'):
            clock = self.enterContext(patch(module + '.datetime', wraps=datetime))
            clock.now.return_value = datetime(2026, 9, 19, 14, tzinfo=timezone.utc)

    def candidate(self):
        return prepare(self.before, self.registry, self.groups, self.ids)

    def missing(self, row, day=date(2026, 9, 19)):
        return [name for name, predicate in expected_exchange_rules(row, day) if not predicate(row)]

    def test_two_real_documents_preserve_printed_amounts_and_different_qualifications(self):
        expected = [(47.9298, 50.7492, 51, 54, 'subject_to_basis_of_allotment'),
                    (687.047, 708.021, 140, 148, 'up_to')]
        for row, want in zip(self.candidate()['ipos'], expected):
            pair = project_record(row)[FIELD]
            self.assertEqual(tuple(pair[k] for k in ('atFloorCr','atCapCr','floorPrice','capPrice','qualifier')), want)
            self.assertNotIn('issueSizeCr', row)
            self.assertIsNone(project_record(row)['issueSizeCr'])
        self.assertIn('Basis of Allotment', self.candidate()['ipos'][0]['activeOfferTerms']['fields'][FIELD]['value']['qualification'])

    def test_table_rejects_ambiguous_columns_units_leg_conflicts_and_wrong_total_row(self):
        original = self.groups[1]['proofs']['activeOfferTerms']['value']['amountEvidence']
        changes = [lambda t: t['columns'].reverse(),
                   lambda t: t['columns'][1].update(amountHeader='Amount'),
                   lambda t: t['columns'][0].update(amountHeader='Up to amount (USD million)'),
                   lambda t: t['rows'][2]['cells'].pop(),
                   lambda t: t['rows'][2]['cells'].__setitem__(1, '6,890.47'),
                   lambda t: t['rows'].__setitem__(2, t['rows'][3]),
                   lambda t: t['rows'][2]['cells'].__setitem__(3, '[●]'),
                   lambda t: t['rows'][1]['cells'].__setitem__(1, '3,67,0.47')]
        for mutate in changes:
            evidence = copy.deepcopy(original); mutate(evidence['transcription'])
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                extract(evidence['transcription'], evidence['identity'])

    def test_paragraph_rejects_stale_band_missing_qualification_tranche_and_unknown_unit(self):
        original = self.groups[0]['proofs']['activeOfferTerms']['value']['amountEvidence']
        changes = [lambda t: t.update(amountSentence=t['amountSentence'].replace('₹ 54', '₹ 53')),
                   lambda t: t.update(qualificationText='Up to 93,98,000 shares'),
                   lambda t: t.update(amountSentence=t['amountSentence'].replace('Issue size', 'Net Issue size')),
                   lambda t: t.update(amountSentence=t['amountSentence'].replace('lakhs', 'million')),
                   lambda t: t.update(supersessionText='The latest band is 51–54.')]
        for mutate in changes:
            evidence = copy.deepcopy(original); mutate(evidence['transcription'])
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                extract(evidence['transcription'], evidence['identity'])

    def test_review_binding_rejects_rehashed_wrapper_after_transcription_or_source_tampering(self):
        for target in ('transcription', 'pdfHash', 'sourceUrl', 'documentDate', 'reviewStatus'):
            registry, groups = copy.deepcopy(self.registry), copy.deepcopy(self.groups)
            receipt = groups[0]['proofs']['activeOfferTerms']['value']
            amount = receipt['amountEvidence']
            if target == 'transcription': amount['transcription']['amountSentence'] = amount['transcription']['amountSentence'].replace('5,074.92', '5,100.00')
            elif target == 'pdfHash': amount['source']['sha256'] = 'a'*64
            elif target == 'sourceUrl': amount['source']['url'] = 'https://example.com/unreviewed.pdf'
            elif target == 'documentDate': amount['source']['documentDate'] = '2026-09-15'
            else: amount['review']['status'] = 'parsed'
            registry['changes'][0]['after'] = copy.deepcopy(receipt)
            blob = (json.dumps(groups[0]['proofs'],ensure_ascii=False,indent=2)+'\n').encode()
            groups[0]['sourceProofsSha256'] = hashlib.sha256(blob).hexdigest()
            groups[0]['sourceProofsGitBlob'] = hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest()
            with self.subTest(target=target), self.assertRaises(ValueError): index_groups(groups, registry)

    def test_invalid_supplement_keeps_prior_nse_terms_but_creates_amount_review(self):
        row = self.candidate()['ipos'][0]
        row['activeOfferTerms']['amountEvidence']['transcription']['issuer'] = 'Other Issuer Limited'
        out = project_record(row)
        self.assertIsNone(out[FIELD]); self.assertEqual(out['lotSize'],2000)
        self.assertEqual(out['priceBand'],{'min':51,'max':54})
        self.assertIn('issueSizeCr', self.missing(row))
        issues = [i for i in validate_record(row) if i['field']==FIELD]
        self.assertEqual(len(issues),1)
        self.assertEqual(review_task(row,issues[0])['route'],'manual-source-review')
        self.assertIn('/activeOfferTerms',review_task(row,issues[0])['evidencePaths'])

    def test_rehashed_nested_review_cannot_relabel_changed_source_under_old_acceptance(self):
        registry,groups=copy.deepcopy(self.registry),copy.deepcopy(self.groups)
        receipt=groups[0]['proofs']['activeOfferTerms']['value'];amount=receipt['amountEvidence']
        amount['transcription']['amountSentence']=amount['transcription']['amountSentence'].replace('5,074.92','5,100.00')
        amount['review']['transcriptionSha256']=digest(amount['transcription'])
        receipt['fields'][FIELD]=extract(amount['transcription'],amount['identity'])
        registry['changes'][0]['after']=copy.deepcopy(receipt)
        blob=(json.dumps(groups[0]['proofs'],ensure_ascii=False,indent=2)+'\n').encode()
        groups[0]['sourceProofsSha256']=hashlib.sha256(blob).hexdigest()
        groups[0]['sourceProofsGitBlob']=hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest()
        with self.assertRaises(ValueError):prepare(self.before,registry,groups,self.ids)

    def test_pair_uses_issuer_pdf_source_with_date_page_unit_and_separate_nse_source(self):
        for row in self.candidate()['ipos']:
            out=project_record(row); quality=out['publicQuality']; d=quality['fields'][FIELD]
            source=quality['sources'][d['source']]
            amount=row['activeOfferTerms']['amountEvidence']
            self.assertEqual(source['sourceUrl'],amount['source']['url'])
            self.assertEqual(source['sha256'],amount['source']['sha256'])
            self.assertEqual(source['documentDate'],amount['source']['documentDate'])
            self.assertEqual(source['authority'],'issuer_disclosure')
            self.assertIsNone(source['observedAt']); self.assertEqual(d['page'],1)
            self.assertEqual(d['unit'],'INR crore')
            self.assertNotEqual(d['source'],quality['fields']['priceBand']['source'])

    def test_two_active_gaps_close_without_scalar_values_or_source_review_removal(self):
        after=self.candidate()
        self.assertEqual([self.missing(r) for r in self.before['ipos']],[['issueSizeCr'],['issueSizeCr']])
        self.assertEqual([self.missing(r) for r in after['ipos']],[[],[]])
        self.assertEqual(validate_payload(self.before)['issues'],validate_payload(after)['issues'])
        for old,new in zip(self.before['ipos'],after['ipos']):
            for key in (set(old)|set(new))-{'activeOfferTerms','dataCorrections','sources'}:
                self.assertEqual(old.get(key),new.get(key),key)
            self.assertEqual(new['dataCorrections'][-1]['before'],old['activeOfferTerms'])

    def test_expiry_restores_amount_gap_and_preserves_receipts_and_history(self):
        for row in self.candidate()['ipos']:
            close=date.fromisoformat(row['closeDate'])
            self.assertIn(FIELD,accepted_terms(row,close))
            after=date.fromordinal(close.toordinal()+1)
            out=project_record(row,today=after)
            self.assertIsNone(out[FIELD]); self.assertIn('issueSizeCr',self.missing(row,after))
            self.assertEqual(out['activeOfferTerms'],row['activeOfferTerms'])
        row=self.candidate()['ipos'][0]
        for status in ('listed','closed','cancelled','withdrawn'):
            self.assertNotIn(FIELD,accepted_terms({**row,'status':status}))

    def test_future_supplement_collection_does_not_backdate_amount_eligibility(self):
        row=self.candidate()['ipos'][0]
        self.assertNotIn(FIELD,accepted_terms(row,date(2026,9,18)))
        self.assertIn('lotSize',accepted_terms(row,date(2026,9,19)))

    def test_total_composition_and_band_holds_withhold_pair(self):
        for field in ('issueSizeCr','issueComposition','freshIssueCr','ofsCr','priceBand',FIELD):
            row=self.candidate()['ipos'][1];row['dataReview']={field:'Unresolved source conflict'}
            out=project_record(row)
            self.assertIsNone(out[FIELD]);self.assertIn('issueSizeCr',self.missing(row))
            self.assertEqual(out['lotSize'],101)

    def test_registry_document_and_value_holds_bind_the_actual_amount_document(self):
        for scope in ('document','value'):
            row=self.candidate()['ipos'][0];receipt=row['activeOfferTerms']
            hold={'id':row['id'],'scope':scope,'identity':receipt['identity'],
                  'fields':{FIELD:{'sha256':receipt['amountEvidence']['source']['sha256'],
                                  'valueDigest':digest(receipt['fields'][FIELD]['value'])}},
                  'reason':'Retain contradictory advertisement evidence'}
            self.assertTrue(display_hold_matches(row,FIELD,hold))
            reviews=active_hold_reviews(row,[hold]);self.assertEqual(len(reviews),1)
            self.assertEqual(reviews[0]['displayHold']['source']['sha256'],receipt['amountEvidence']['source']['sha256'])
            self.assertEqual(review_task(row,reviews[0])['route'],'manual-source-review')
            out=project_record(row,holds=[hold]);self.assertIsNone(out[FIELD]);self.assertEqual(out['lotSize'],2000)
            with patch('public_quality.display_holds',return_value=[hold]):
                self.assertIn('issueSizeCr',self.missing(row))
            self.assertNotIn(FIELD,row['staticFieldProvenance'])
            receipt['amountEvidence']['transcription']['amountSentence']='unsupported source layout'
            self.assertTrue(display_hold_matches(row,FIELD,hold))

    def test_new_canonical_terms_requiring_authority_withhold_dependent_pair(self):
        for field, value in [('priceBand', {'min': 140, 'max': 150}),
                             ('issueSizeCr', 710), ('freshIssueCr', 321), ('ofsCr', 390)]:
            with self.subTest(field=field):
                row = self.candidate()['ipos'][1]
                row[field] = value
                out = project_record(row)
                self.assertEqual(out['publicQuality']['fields'][field]['state'], 'under_review')
                self.assertIsNone(out[FIELD])
                self.assertEqual(out['publicQuality']['fields'][FIELD]['state'], 'under_review')
                self.assertEqual(out['lotSize'], 101)

    def test_official_band_or_explicit_pair_conflict_keeps_amount_unresolved(self):
        for field,value in [('priceBand',{'min':140,'max':150}),(FIELD,{'atCapCr':710}),('issueSizeCr',710)]:
            row=self.candidate()['ipos'][1]
            row['observations']['BSE']={'openDate':row['openDate'],'closeDate':row['closeDate'],field:value}
            self.assertIsNone(project_record(row)[FIELD]);self.assertIn('issueSizeCr',self.missing(row))
        # The known NSE observation is a derived scalar, never an explicit pair.
        row=self.candidate()['ipos'][1]
        self.assertEqual(row['observations']['NSE']['issueSizeCr'],726.31)
        self.assertEqual(project_record(row)[FIELD]['atCapCr'],708.021)
        row['observations']['NSE']['subscriptionSummary']['collectedAt']='2026-09-19T15:00:00+00:00'
        self.assertEqual(project_record(row)[FIELD]['atCapCr'],708.021)
        row['observations']['NSE']['issueSizeCr']=710
        self.assertIsNone(project_record(row)[FIELD])

    def test_ordinary_apply_is_inert_and_concurrent_receipt_remains_pending(self):
        original=copy.deepcopy(self.before)
        self.assertEqual(apply(self.before,self.registry,evidence_groups=self.groups),(0,[]))
        self.assertEqual(self.before['ipos'],original['ipos'])
        candidate=self.candidate(); current=copy.deepcopy(self.before)
        current['ipos'][0]['activeOfferTerms']['review']['url']='https://example.com/new-review'
        merged,conflicts=merge_payload(self.before,candidate,current)
        self.assertEqual(merged['ipos'][0]['activeOfferTerms'],current['ipos'][0]['activeOfferTerms'])
        self.assertTrue(any(c['path'][-1]=='activeOfferTerms' for c in conflicts))

    def test_summary_profile_and_delivery_verifier_keep_qualified_pair_and_source(self):
        for row,group in zip(self.candidate()['ipos'],self.groups):
            summary,profile=public_summary_record(row),public_profile_record(row)
            self.assertEqual(summary[FIELD],profile[FIELD]);self.assertNotIn('issueSizeCr',summary)
            verify_active_offer_delivery(row,profile,summary,group,group['proofs'])
            summary[FIELD]['atCapCr']+=1
            with self.assertRaises(ValueError):verify_active_offer_delivery(row,profile,summary,group,group['proofs'])

    def test_unreviewed_canonical_pair_never_appears_in_public_output(self):
        row=copy.deepcopy(self.before['ipos'][0]);row[FIELD]={'atCapCr':50.7}
        self.assertIsNone(project_record(row)[FIELD])
        self.assertIn('issueSizeCr',self.missing(row))

    def test_delivery_rejects_identical_wrong_scalar_promotion_on_both_surfaces(self):
        for row, group in zip(self.candidate()['ipos'], self.groups):
            for state in ('provisional', 'final_verified'):
                summary, profile = public_summary_record(row), public_profile_record(row)
                for surface in (summary, profile):
                    surface['issueSizeCr'] = surface[FIELD]['atCapCr']
                    surface['publicQuality']['fields']['issueSizeCr']['state'] = state
                with self.subTest(id=row['id'], state=state), self.assertRaisesRegex(ValueError, 'unknown scalar'):
                    verify_active_offer_delivery(row, profile, summary, group, group['proofs'])

    def test_health_reports_surviving_base_terms_when_amount_supplement_is_invalid(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
        from report_update_health import offer_receipt_health
        row = self.candidate()['ipos'][0]
        now = datetime(2026, 9, 19, 14, tzinfo=timezone.utc)
        entry = offer_receipt_health(row, [], now)
        self.assertIn(FIELD, entry['provisionalFields'])
        self.assertEqual(entry['publicFields'][FIELD]['documentSource']['authority'], 'issuer_disclosure')
        row['activeOfferTerms']['amountEvidence']['transcription']['issuer'] = 'Other Issuer'
        entry = offer_receipt_health(row, [], now)
        self.assertEqual(entry['state'], 'invalid_receipt')
        self.assertEqual(entry['receiptValidation'], 'rejected')
        self.assertNotIn(FIELD, entry['provisionalFields'])
        self.assertEqual(set(entry['provisionalFields']), {'priceBand', 'lotSize', 'issueComposition'})
        self.assertTrue(entry['publicFields']['priceBand']['usesThisReceipt'])


if __name__=='__main__': unittest.main()
