import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
from scripts.enrollware_roster_reconciliation import prepare_snapshot, reconcile_snapshot
from scripts.audit_enrollware_reconciliation import audit


class CompleteRosterContract(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2030,9,27,12,tzinfo=timezone.utc)
        self.row={'external_class_id':'100','source_observed_at':self.now.isoformat(),
                  'committed':True,'complete_roster':True,'roster_count':0,'registrations':[]}
    def prepare(self,row):
        return prepare_snapshot({'schema_version':'enrollware-complete-roster.v1','sessions':[row]},self.now)
    def test_zero_requires_current_complete_roster(self):
        self.assertEqual(self.prepare(self.row)['p_rows'][0]['roster_count'],0)
        for field,value in [('complete_roster',False),('roster_count',None),('roster_count',True),('registrations',None)]:
            with self.subTest(field=field),self.assertRaises(ValueError):self.prepare({**self.row,field:value})
    def test_stale_unknown_naive_and_future_times_rejected(self):
        for value in ['2020-01-01T00:00:00Z','2030-09-27T12:00:00',(self.now+timedelta(hours=1)).isoformat()]:
            with self.subTest(value=value),self.assertRaises(ValueError):self.prepare({**self.row,'source_observed_at':value})
    def test_registration_ids_are_exact_and_unique(self):
        row=copy.deepcopy(self.row);row.update(roster_count=2,registrations=[{'external_registration_id':'9'},{'external_registration_id':'9'}])
        with self.assertRaises(ValueError):self.prepare(row)
    def test_fingerprint_includes_source_watermark(self):
        first=self.prepare(self.row)
        self.assertEqual(first,self.prepare(self.row))
        second=self.prepare({**self.row,'source_observed_at':(self.now-timedelta(seconds=1)).isoformat()})
        self.assertNotEqual(first['p_source_sha256'],second['p_source_sha256'])
    def test_masked_contact_batch_is_rejected_before_rpc_payload(self):
        good={'external_registration_id':'9','first_name':'Alex','last_name':'Example',
              'email':'alex@example.test','phone':'910-555-0100'}
        for field,value in [('email','<redacted>'),('email','[MASKED]'),
                            ('phone','***-***-0100'),('first_name','<masked>'),
                            ('email','not-an-email'),('email',42)]:
            with self.subTest(field=field,value=value):
                row={**self.row,'roster_count':1,'registrations':[{**good,field:value}]}
                with self.assertRaises(ValueError):self.prepare(row)
        row={**self.row,'roster_count':2,'registrations':[good,{**good,'external_registration_id':'10','email':'<redacted>'}]}
        with self.assertRaises(ValueError):self.prepare(row)
    def test_actual_contacts_preserved_and_existing_id_can_omit_contacts(self):
        good={'external_registration_id':'9','first_name':'Alex','last_name':'Example',
              'email':'alex@example.test','phone':'910-555-0100'}
        row={**self.row,'roster_count':1,'registrations':[good]}
        self.assertEqual(self.prepare(row)['p_rows'][0]['registrations'][0],good)
        row['registrations']=[{'external_registration_id':'9'}]
        self.assertEqual(self.prepare(row)['p_rows'][0]['registrations'][0],{'external_registration_id':'9'})
    def test_masked_snapshot_never_reaches_apply_transport(self):
        row={**self.row,'source_observed_at':datetime.now(timezone.utc).isoformat(),
             'roster_count':1,'registrations':[{'external_registration_id':'9','email':'<redacted>'}]}
        with tempfile.TemporaryDirectory() as directory, patch('scripts.enrollware_roster_reconciliation.urlopen') as transport:
            path=Path(directory)/'snapshot.json'
            path.write_text(json.dumps({'schema_version':'enrollware-complete-roster.v1','sessions':[row]}),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'masked'):
                reconcile_snapshot(path,apply=True)
            transport.assert_not_called()
    def test_new_projected_class_alarms_without_becoming_zero(self):
        health={'sessions':[{'external_class_id':'100','canonical_session_id':'s','status':'stale_reconciliation'}]}
        result=audit(health,{'sessions':[{'session_id':'100'},{'session_id':'200'}]})
        self.assertFalse(result['healthy'])
        self.assertEqual(result['gap_breakdown'],{'stale_reconciliation':1,'committed_projection_without_canonical_session':1})
        self.assertEqual(result['stale_source_checks'],1)
        self.assertEqual(result['record_integrity_gaps'],1)
        self.assertEqual([g['status'] for g in result['gaps']],['stale_reconciliation','committed_projection_without_canonical_session'])
        self.assertNotIn('participant_count',str(result))
    def test_reviewed_deadline_is_explicit_not_an_unknown_class_or_zero_count(self):
        deadline={'external_class_id':'900','canonical_session_id':None,'status':'classified_non_session',
                  'non_session_classification':'renewal_deadline','approved_location_key':'fixture-room'}
        result=audit({'sessions':[deadline]},{'sessions':[{'session_id':'900'}]})
        self.assertTrue(result['healthy'])
        self.assertEqual(result['canonical_external_sessions'],0)
        self.assertEqual(result['non_session_sources'][0]['external_class_id'],'900')
        self.assertNotIn('participant_count',str(result))
        conflict={**deadline,'canonical_session_id':'unexpected-session','status':'non_session_conflicting_canonical_session'}
        self.assertFalse(audit({'sessions':[conflict]},{})['healthy'])

if __name__=='__main__':unittest.main()
