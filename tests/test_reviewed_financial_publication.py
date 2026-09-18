import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from apply_corrections import apply, fingerprint
from reviewed_corrections import prepare, validate_scope
from reviewed_evidence import digest, index_groups
from review_financial_tables import PARSER_VERSION
from public_quality import project_record
from validate_data import validate_payload
from test_reviewed_financial_tables import fixture, financial_value


class ReviewedFinancialPublicationTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads((ROOT/'tests/reviewed_financial_before.json').read_text(encoding='utf-8'))
        self.registry={'changes':[], 'fillMissing':[]}; self.groups=[]
        for row in self.payload['ipos']:
            identifier=row['id']; identity={k:row[k] for k in ('id','company','symbol','openDate')}
            extraction=row['offerDocumentExtraction']; evidence=fixture(identifier); value=financial_value(evidence)
            proof={'identity':identity,'source':'Final Prospectus','sourceUrl':extraction['documentUrl'],
                   'documentType':'PROSPECTUS','documentDate':'2026-08-27' if identifier=='htel' else '2026-05-05',
                   'sha256':extraction['sha256'],'parserVersion':PARSER_VERSION,'checkedAt':'2026-09-18T20:57:03Z',
                   'issueOpenDate':identity['openDate'],'field':'financials','value':value,'evidence':evidence}
            proofs={'financials':proof}
            self.registry['changes'].append({'id':identifier,'identity':identity,'field':'financials',
                'beforeHash':fingerprint(row['financials']),'after':value,'publicationScope':'explicit-reviewed',
                'reviewedAt':proof['checkedAt'],'source':{'name':'Final Prospectus','type':'PROSPECTUS','url':proof['sourceUrl']},
                'evidence':{'sha256':proof['sha256'],'documentDate':proof['documentDate']}})
            self.groups.append({'kind':'financials','identity':identity,'proofs':proofs,
                'beforeProofHashes':{'financials':digest(row.get('staticFieldProvenance',{}).get('financials'))},
                'sourceProofsSha256':hashlib.sha256((json.dumps(proofs,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest(),
                'sourceReviewUrl':'https://github.com/Vasuki8/IPO-Tracker/blob/'+'a'*40+'/docs/review.md',
                'reviewedAt':proof['checkedAt']})
        self.ids=[g['identity']['id'] for g in self.groups]

    def candidate(self): return prepare(self.payload,self.registry,self.groups,self.ids)

    def test_ordinary_apply_is_inert_and_reviewed_preparation_is_offline(self):
        original=copy.deepcopy(self.payload)
        self.assertEqual(apply(self.payload,self.registry,evidence_groups=self.groups),(0,[]))
        self.assertEqual(self.payload['ipos'],original['ipos'])
        self.payload=original
        with patch('requests.sessions.Session.request',side_effect=AssertionError('Offline review')):
            candidate=self.candidate()
        validate_scope(original,candidate,self.ids,groups=self.groups)
        for before,after in zip(original['ipos'],candidate['ipos']):
            for key in ('documentFieldProvenance','offerDocumentExtraction','subscription','objectsOfIssueReview'):
                self.assertEqual(before.get(key),after.get(key))
            self.assertEqual(project_record(after)['publicQuality']['fields']['financials']['state'],'final_verified')
            self.assertEqual(after['dataCorrections'][:len(before['dataCorrections'])],before['dataCorrections'])

    def test_exact_42_reviews_resolved_without_dropping_any_metric(self):
        candidate=self.candidate()
        self.assertEqual(validate_payload(self.payload)['reviewCount']-validate_payload(candidate)['reviewCount'],42)
        self.assertEqual(validate_payload(candidate)['errorCount'],0)
        for row in candidate['ipos']:
            self.assertEqual(len(row['financials']['periods']),3)
            self.assertTrue(all(len(p)==7 for p in row['financials']['periods']))

    def test_concurrent_value_proof_identity_and_conflict_fail_closed(self):
        for mutation in ('value','proof','identity','conflict'):
            payload=copy.deepcopy(self.payload); row=payload['ipos'][0]
            if mutation=='value': row['financials']['periods'][0]['eps']=9
            elif mutation=='proof': row.setdefault('staticFieldProvenance',{})['financials']={'newer':True}
            elif mutation=='identity': row['openDate']='2026-08-23'
            else: row['offerDocumentExtraction']['conflicts']=['FY2026.eps']
            original=copy.deepcopy(payload)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): prepare(payload,self.registry,self.groups,self.ids)
            self.assertEqual(payload,original)

    def test_financial_scope_cannot_drop_periods_metrics_or_change_other_fields(self):
        for mutation in ('period','metric','unrelated'):
            candidate=self.candidate(); row=candidate['ipos'][0]
            if mutation=='period': row['financials']['periods'].pop()
            elif mutation=='metric': del row['financials']['periods'][0]['eps']
            else: row['subscription']={'total':999}
            with self.subTest(mutation=mutation),self.assertRaises(ValueError): validate_scope(self.payload,candidate,self.ids,groups=self.groups)

    def test_accepted_proof_survives_old_same_pdf_reextract_and_policy(self):
        from final_prospectus_policy import apply_final_prospectus_static_fields
        from enforce_final_prospectus_policy import apply_policy
        candidate=self.candidate()
        for row,before in zip(candidate['ipos'],self.payload['ipos']):
            proof=copy.deepcopy(row['staticFieldProvenance']['financials'])
            parsed={'financials':before['financials'],'fieldEvidence':{'financials':{
                p['period']+'.'+k:{'page':1,'normalizedValue':v} for p in before['financials']['periods'] for k,v in p.items() if k!='period'}}}
            apply_final_prospectus_static_fields(row,parsed,{'type':'PROSPECTUS','url':proof['sourceUrl']},
                parser_version=31,sha256=proof['sha256'],checked_at='2026-09-18T21:00:00Z')
            apply_policy({'ipos':[row]})
            self.assertEqual(row['staticFieldProvenance']['financials'],proof)
            self.assertEqual(row['financials'],proof['value'])
            self.assertEqual(project_record(row)['publicQuality']['fields']['financials']['state'],'final_verified')

    def test_forged_cell_identity_or_nonexplicit_group_is_rejected_after_rehash(self):
        for mutation in ('cell','identity','scope'):
            groups=copy.deepcopy(self.groups);registry=copy.deepcopy(self.registry);proof=groups[0]['proofs']['financials']
            if mutation=='cell': proof['evidence']['cells']['FY2026.eps']['normalizedValue']=99
            elif mutation=='identity': proof['identity']['symbol']='OTHER'
            else: registry['changes'][0].pop('publicationScope')
            groups[0]['sourceProofsSha256']=hashlib.sha256((json.dumps(groups[0]['proofs'],ensure_ascii=False,indent=2)+'\n').encode()).hexdigest()
            with self.subTest(mutation=mutation),self.assertRaises(ValueError): index_groups(groups,registry)


if __name__=='__main__': unittest.main()
