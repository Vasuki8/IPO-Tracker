"""Acceptance at the correction -> policy -> public display -> publisher boundary."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import apply_corrections as corrections
import publish_transaction as publisher
from public_quality import project_record
from reviewed_corrections import prepare, validate_scope, validate_records
from reviewed_evidence import load_groups

FIELDS = ('issueComposition', 'issueSizeCr', 'freshIssueCr', 'ofsCr')


class ReviewedEvidencePublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / 'data/verified_corrections.json').read_text())
        cls.groups = [group for group in load_groups() if group['identity']['id'] == 'emmvee']
        cls.production = json.loads((ROOT / 'data/ipos.json').read_text())

    def setUp(self):
        # Retained legacy values/proofs in e59b9735's pre-refresh dataset.
        # These reproduce the defect even after production data is repaired.
        self.row = copy.deepcopy(next(r for r in self.production['ipos'] if r['id'] == 'emmvee'))
        legacy = {'freshShares':34845069, 'ofsShares':17422535,
                  'freshIssueCr':378.069, 'ofsCr':378.069, 'totalIssueSizeCr':756.138}
        self.row.update(issueComposition=legacy, issueSizeCr=756.138, freshIssueCr=378.069, ofsCr=378.069)
        for field in FIELDS:
            self.row.setdefault('staticFieldProvenance', {})[field] = {
                'source':'Final Prospectus',
                'sourceUrl':'https://nsearchives.nseindia.com/corporate/FP_INE1C6T01020_14NOV2025.pdf',
                'documentType':'PROSPECTUS', 'documentDate':'2025-11-14',
                'sha256':'85eb9319dc01027821813c71d3702164911442a14547ad72cc04270ea6612eda',
                'parserVersion':24, 'checkedAt':'2026-09-16T22:32:50+05:30',
                'issueOpenDate':'2025-11-11', 'field':field,
                'value':copy.deepcopy(self.row[field]),
                'evidence':{'basis':'validated Final Prospectus issue composition', **legacy},
            }
        self.payload = {'meta':{'generatedAt':'2026-09-18T01:01:18Z'},
                        'ipos':[self.row, {'id':'unrelated', 'company':'Unrelated Limited'}]}
        self.scoped = {**self.registry, 'changes':[c for c in self.registry['changes'] if c['id']=='emmvee'], 'fillMissing':[]}

    def candidate(self):
        return prepare(self.payload, self.registry, self.groups, ['emmvee'])

    def test_values_only_correction_is_not_a_verified_public_release(self):
        corrections.apply(self.payload, self.scoped)
        quality = project_record(self.row)['publicQuality']['fields']
        self.assertEqual(self.row['issueSizeCr'], 2900)
        self.assertTrue(all(quality[field]['state']=='under_review' for field in FIELDS))

    def test_source_proofs_restore_all_four_fields_without_changing_other_evidence(self):
        before = copy.deepcopy(self.row)
        result = self.candidate()
        row = result['ipos'][0]
        quality = project_record(row)['publicQuality']['fields']
        self.assertTrue(all(quality[field]['state']=='final_verified' for field in FIELDS))
        self.assertEqual(row['issueSizeCr'], 2900)
        self.assertEqual(row['freshIssueCr'], 2143.862)
        self.assertEqual(row['ofsCr'], 756.138)
        for field in ('objectsOfIssue', 'documentFieldProvenance', 'offerDocumentExtraction'):
            self.assertEqual(row.get(field), before.get(field))
        self.assertEqual(row['dataCorrections'][:len(before.get('dataCorrections', []))], before.get('dataCorrections', []))
        audit = row['dataCorrections'][-1]
        self.assertEqual(audit['before'], {field:before['staticFieldProvenance'][field] for field in FIELDS})
        self.assertEqual(audit['after'], self.groups[0]['proofs'])
        self.assertEqual(self.payload['ipos'][0], before, 'Preparation must not mutate its input')

    def test_already_changed_values_can_receive_proofs_and_reapplication_is_idempotent(self):
        corrections.apply(self.payload, self.scoped)
        corrections.apply(self.payload, self.scoped, evidence_groups=self.groups)
        once = copy.deepcopy(self.row)
        corrections.apply(self.payload, self.scoped, evidence_groups=self.groups)
        self.assertEqual(self.row, once)

    def test_concurrent_value_or_proof_blocks_the_whole_group(self):
        for kind in ('value', 'proof', 'missing_proof', 'identity'):
            with self.subTest(kind=kind):
                payload = copy.deepcopy(self.payload); row=payload['ipos'][0]
                if kind=='value': row['ofsCr']=123
                elif kind=='proof': row['staticFieldProvenance']['ofsCr']['checkedAt']='2026-09-18T02:00:00Z'
                elif kind=='missing_proof': row['staticFieldProvenance'].pop('ofsCr')
                else: row['symbol']='DIFFERENT'
                original=copy.deepcopy(row)
                _, conflicts=corrections.apply(payload,self.scoped,evidence_groups=self.groups)
                self.assertTrue(conflicts)
                self.assertEqual(row,original)

    def test_tampered_source_artifact_or_incomplete_group_fails_before_mutation(self):
        for kind in ('proof','fields','registry_identity','duplicate'):
            with self.subTest(kind=kind):
                groups=copy.deepcopy(self.groups); registry=copy.deepcopy(self.scoped); payload=copy.deepcopy(self.payload)
                if kind=='proof': groups[0]['proofs']['ofsCr']['evidence']['page']=4
                elif kind=='fields': groups[0]['proofs'].pop('ofsCr')
                elif kind=='registry_identity': registry['changes'][0]['identity']['symbol']='OTHER'
                else: groups.append(copy.deepcopy(groups[0]))
                with self.assertRaises(ValueError): corrections.apply(payload,registry,evidence_groups=groups)
                self.assertEqual(payload,self.payload)

    def test_proof_file_cannot_escape_registry_or_change_its_recorded_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory); registry=folder/'evidence.json'
            for name in ('../emmvee.json','/tmp/emmvee.json','emmvee.json'):
                with self.subTest(name=name):
                    registry.write_text(json.dumps({'schemaVersion':1,'groups':[{
                        'proofsFile':name,'sourceProofsSha256':'0'*64}]}))
                    (folder/'evidence').mkdir(exist_ok=True)
                    (folder/'evidence/emmvee.json').write_text('{}')
                    with self.assertRaises(ValueError): load_groups(registry)

    def test_ids_are_explicit_and_must_have_reviewed_evidence(self):
        for ids in ([],[''],['teamtech'],['emmvee','emmvee'],['all']):
            with self.subTest(ids=ids),self.assertRaises(ValueError):
                prepare(self.payload,self.registry,self.groups,ids)

    def test_current_full_dataset_preserves_unselected_records_and_pending_bytes(self):
        pending=(ROOT/'data/pending_updates.json').read_bytes()
        before=copy.deepcopy(self.production)
        candidate=prepare(before,self.registry,self.groups,['emmvee'])
        self.assertEqual([r for r in before['ipos'] if r['id']!='emmvee'],
                         [r for r in candidate['ipos'] if r['id']!='emmvee'])
        self.assertEqual(len(candidate['ipos']),len(before['ipos']))
        self.assertEqual((ROOT/'data/pending_updates.json').read_bytes(),pending)
        team=next(r for r in candidate['ipos'] if r['id']=='teamtech')
        self.assertEqual(project_record(team)['publicQuality']['fields']['objectsOfIssue']['state'],'under_review')

    def test_preparation_performs_no_source_requests(self):
        with patch('requests.sessions.Session.request',side_effect=AssertionError('No source collection')):
            self.candidate()

    def test_scope_rejects_unrelated_changes_and_history_loss(self):
        candidate=self.candidate()
        for kind in ('other_issuer','date','proof','history','order','duplicate'):
            with self.subTest(kind=kind):
                changed=copy.deepcopy(candidate)
                if kind=='other_issuer': changed['ipos'][1]['company']='Changed'
                elif kind=='date': changed['ipos'][0]['openDate']='2025-12-11'
                elif kind=='proof': changed['ipos'][0]['staticFieldProvenance']['registrar']={'sourceUrl':'changed'}
                elif kind=='history': changed['ipos'][0]['dataCorrections']=[]
                elif kind=='order': changed['ipos'].reverse()
                else: changed['ipos'].append(copy.deepcopy(changed['ipos'][0]))
                with self.assertRaises(ValueError): validate_scope(self.payload,changed,['emmvee'])

    def files(self,directory):
        folder=Path(directory); candidate=self.candidate()
        paths={key:folder/(key+'.json') for key in ('base','proposed','current','pending','manifest')}
        for name,payload in [('base',self.payload),('proposed',candidate),('current',self.payload)]:
            paths[name].write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
        paths['pending'].write_text('{ "updates" : [{"fingerprint":"preserved", "status":"pending_conflict_review"}] }\n')
        manifest={'schemaVersion':1,'ids':['emmvee'],**{key+'Sha256':hashlib.sha256(paths[key].read_bytes()).hexdigest() for key in ('base','proposed')}}
        paths['manifest'].write_text(json.dumps(manifest))
        paths['source']=folder/'source-commit.txt';paths['source'].write_text('a'*40+'\n')
        return paths

    def publish(self,paths,source=True):
        argv=['publish_transaction.py', '--base',str(paths['base']), '--proposed',str(paths['proposed']),
              '--current',str(paths['current']), '--pending',str(paths['pending']),
              '--reviewed-manifest',str(paths['manifest'])]
        if source: argv+=['--source-commit-file',str(paths['source'])]
        with patch.object(sys,'argv',argv),patch.object(publisher,'verify_source_commit') as guard,redirect_stdout(StringIO()):
            publisher.main()
        guard.assert_called_once_with('a'*40)

    def test_publisher_preserves_pending_bytes_and_independent_subscription_update(self):
        with tempfile.TemporaryDirectory() as directory:
            paths=self.files(directory); original=paths['pending'].read_bytes()
            current=json.loads(paths['current'].read_text()); current['ipos'][0]['subscription']={'total':2.0}
            paths['current'].write_text(json.dumps(current))
            self.publish(paths)
            output=json.loads(paths['current'].read_text())
            self.assertEqual(output['ipos'][0]['subscription'],{'total':2.0})
            self.assertEqual(output['ipos'][0]['issueSizeCr'],2900)
            self.assertEqual(paths['pending'].read_bytes(),original)

    def test_publisher_rejects_concurrent_documents_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            paths=self.files(directory); current=json.loads(paths['current'].read_text())
            current['ipos'][0]['documentRepair']={'newer':'accepted evidence'}
            paths['current'].write_text(json.dumps(current))
            before={key:p.read_bytes() for key,p in paths.items()}
            with self.assertRaisesRegex(ValueError,'concurrent conflicts'): self.publish(paths)
            self.assertEqual({key:p.read_bytes() for key,p in paths.items()},before)

    def test_publisher_rejects_missing_source_manifest_and_corrupt_snapshot(self):
        for kind in ('missing_source','changed_snapshot','unrelated_change'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as directory:
                paths=self.files(directory)
                if kind!='missing_source':
                    data=json.loads(paths['proposed'].read_text()); data['ipos'][1]['company']='Unexpected'
                    paths['proposed'].write_text(json.dumps(data))
                    if kind=='unrelated_change':
                        manifest=json.loads(paths['manifest'].read_text())
                        manifest['proposedSha256']=hashlib.sha256(paths['proposed'].read_bytes()).hexdigest()
                        paths['manifest'].write_text(json.dumps(manifest))
                before={key:p.read_bytes() for key,p in paths.items()}
                with self.assertRaises(ValueError): self.publish(paths,source=kind!='missing_source')
                self.assertEqual({key:p.read_bytes() for key,p in paths.items()},before)

    def test_old_proof_cannot_be_promoted_by_rehashing_the_manifest(self):
        candidate=self.candidate();candidate['ipos'][0]['staticFieldProvenance']['ofsCr']=self.row['staticFieldProvenance']['ofsCr']
        with self.assertRaises(ValueError): validate_records(candidate,self.registry,self.groups,['emmvee'])

    def test_publisher_rechecks_before_proofs_and_rejects_fabricated_audit(self):
        for kind in ('before_proof','extra_audit'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as directory:
                paths=self.files(directory)
                key='base' if kind=='before_proof' else 'proposed'
                data=json.loads(paths[key].read_text())
                if kind=='before_proof':
                    data['ipos'][0]['staticFieldProvenance']['ofsCr']['parserVersion']=999
                    paths['current'].write_text(json.dumps(data))
                else:
                    data['ipos'][0]['dataCorrections'].append({'field':'ofsCr','reason':'not reviewed'})
                paths[key].write_text(json.dumps(data))
                manifest=json.loads(paths['manifest'].read_text())
                manifest[key+'Sha256']=hashlib.sha256(paths[key].read_bytes()).hexdigest()
                paths['manifest'].write_text(json.dumps(manifest))
                before={name:p.read_bytes() for name,p in paths.items()}
                with self.assertRaises(ValueError): self.publish(paths)
                self.assertEqual({name:p.read_bytes() for name,p in paths.items()},before)


if __name__=='__main__':
    unittest.main()
