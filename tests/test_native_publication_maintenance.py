import copy
from datetime import timedelta
from pathlib import Path
import unittest
from scripts import run_native_publication as runner
from scripts.fetch_canonical_scheduling_demand import validate_payload
from scripts.layered_publication_adapter import publish
from tests.test_native_seated_publication import NativeSeatedContinuationTests

class NativePublicationMaintenanceTests(unittest.TestCase):
    def test_expired_empty_native_hold_remains_blocked_until_exact_release_then_next_publication_reopens(self):
        case,first,choice,source,demand,_=NativeSeatedContinuationTests().fixture()
        old=runner.retained_projection({'sessions':[]},demand)
        expired=copy.deepcopy(source);expired.update(active_registration_count=0,held_seat_count=0,native_booking_admission=None)
        still_active=runner.retained_projection(old,dict(demand,sessions=[expired]))
        self.assertFalse(still_active['sessions'][0]['public_direct_booking'])
        self.assertEqual(still_active['sessions'][0]['start_at'],source['start_at'])
        case.sources=[dict(source_event_id=source['canonical_session_id'],external_class_id=source['external_class_id'],
            start=source['start_at'],end=source['consumption_end_at'],instructor='Brian Ennis',course_id='359474',resource=case.room,
            location_resolution='location_resource_map',source_file='canonical_class_sessions',active_registration_count=0,count_available=True)]
        emit=lambda:publish(case.calculation(),case.page,case.courses,case.windows,case.now,
            lambda *a:(_ for _ in ()).throw(AssertionError('external fallback')),lambda *a:[],native_policy=case.policy['native_publication_scope'])
        self.assertFalse(any(o['date']==choice['date'] and o['startTime']==choice['startTime'] for o in emit()['offers']))
        paid=copy.deepcopy(old['sessions'][0]);paid.update(session_id='paid-retained',canonical_session_id='paid')
        staff=copy.deepcopy(old['sessions'][0]);staff.update(session_id='staff-retained',canonical_session_id='staff')
        snapshot={'sessions':still_active['sessions']+[paid,staff]}
        release={k:source[k] for k in ['canonical_session_id','external_class_id','start_at','end_at','consumption_start_at','consumption_end_at']}
        release.update(authority='native-generated-release.v1',release_reason='expired_unpaid_hold',released_at=case.now.isoformat())
        fresh=dict(demand,sessions=[],released_native_sessions=[release])
        updated=runner.retained_projection(snapshot,fresh)
        self.assertEqual([r['session_id'] for r in updated['sessions']],['paid-retained','staff-retained'])
        self.assertEqual(updated['build']['counts']['released_native_sessions'],1)
        self.assertEqual(snapshot['sessions'][0]['session_id'],source['external_class_id'],'input is not mutated')
        case.sources=[] # Only the exact source released above occupied this fixture day.
        self.assertTrue(any(o['date']==choice['date'] and o['startTime']==choice['startTime'] for o in emit()['offers']))
        self.assertEqual(len(runner.retained_projection(snapshot,dict(demand,sessions=[]))['sessions']),3,'absence never means released')
        for change in [{'start_at':(runner.scope.instant(source['start_at'])+timedelta(seconds=1)).isoformat()}, {'canonical_session_id':'other'}, {'authority':'untrusted'}]:
            with self.assertRaises(ValueError):runner.retained_projection(snapshot,dict(fresh,released_native_sessions=[dict(release,**change)]))

    def test_two_missing_reads_preserve_only_native_identity_then_exact_release_retires(self):
        case,_,_,source,demand,_=NativeSeatedContinuationTests().fixture()
        first=runner.retained_projection({'sessions':[]},demand)
        original=copy.deepcopy(first)
        identity=first['sessions'][0]['last_verified_native_identity']
        release={k:source[k] for k in runner.NATIVE_IDENTITY_FIELDS}
        release.update(authority='native-generated-release.v1',release_reason='expired_unpaid_hold',released_at=case.now.isoformat())
        missing=dict(demand,sessions=[])
        gap=first
        for _ in range(2):
            gap=runner.retained_projection(gap,missing)
            row=gap['sessions'][0]
            self.assertNotIn('canonical_session_id',row)
            self.assertEqual(row['last_verified_native_identity'],identity)
            self.assertEqual(row['demand_status'],'missing_canonical_session')
            self.assertEqual(row['demand_basis'],'unknown')
            self.assertIsNone(row['active_registration_count'])
            self.assertFalse(row['count_available'])
            self.assertFalse(row['public_direct_booking'])
            self.assertNotIn('registration_url',row)
            self.assertNotIn('native_booking_admission',row)
            for key in runner.NATIVE_INTERVAL_FIELDS:self.assertEqual(row[key],source[key])
        self.assertEqual(first,original,'preservation must not mutate the retained input')
        # Paid/staff rows without release proofs must stay conservative blockers.
        others=[]
        for label in ['paid','staff']:
            row=copy.deepcopy(gap['sessions'][0]);row.update(session_id=label,external_class_id=label)
            row.pop('last_verified_native_identity');others.append(row)
        gap['sessions'].extend(others)
        fresh=dict(missing,released_native_sessions=[release])
        result=runner.retained_projection(gap,fresh)
        self.assertEqual([r['session_id'] for r in result['sessions']],['paid','staff'])
        self.assertEqual(result['build']['counts']['released_native_sessions'],1)
        for key in runner.NATIVE_INTERVAL_FIELDS:
            changed=copy.deepcopy(gap)
            changed['sessions'][0][key]=(runner.scope.instant(source[key])+timedelta(seconds=1)).isoformat()
            with self.subTest(changed_interval=key),self.assertRaises(ValueError):runner.retained_projection(changed,fresh)
        for key,value in [('canonical_session_id','different-canonical'),('external_class_id','different-external')]:
            changed=copy.deepcopy(gap);changed['sessions'][0]['last_verified_native_identity'][key]=value
            with self.subTest(changed_provenance=key),self.assertRaises(ValueError):runner.retained_projection(changed,fresh)
        changed=copy.deepcopy(gap);changed['sessions'][0]['canonical_session_id']='conflicting-current-id'
        with self.assertRaises(ValueError):runner.retained_projection(changed,fresh)
        changed_release=dict(release,canonical_session_id='different-release-id')
        with self.assertRaises(ValueError):runner.retained_projection(gap,dict(missing,released_native_sessions=[changed_release]))
        # Stored provenance cannot re-admit a seat, even if an old DTO remains.
        stale=copy.deepcopy(gap);stale['sessions'][0].update(native_booking_admission=source['native_booking_admission'],public_direct_booking=True)
        self.assertFalse(runner.retained_projection(stale,missing)['sessions'][0]['public_direct_booking'])
        polluted=copy.deepcopy(gap)
        polluted['sessions'][0]['last_verified_native_identity']['notes']='must not enter public output'
        self.assertNotIn('notes',runner.retained_projection(polluted,missing)['sessions'][0]['last_verified_native_identity'])
        polluted['sessions'][0]['last_verified_native_identity']['canonical_session_id']={'secret':'not an identity'}
        self.assertNotIn('last_verified_native_identity',runner.retained_projection(polluted,missing)['sessions'][0])

    def test_pre_upgrade_current_row_preserves_identity_but_already_lost_identity_is_not_guessed(self):
        case,_,_,source,demand,_=NativeSeatedContinuationTests().fixture()
        prior=runner.retained_projection({'sessions':[]},demand)
        prior['sessions'][0].pop('last_verified_native_identity')
        gap=runner.retained_projection(prior,dict(demand,sessions=[]))
        self.assertEqual(gap['sessions'][0]['last_verified_native_identity']['canonical_session_id'],source['canonical_session_id'])
        release={k:source[k] for k in runner.NATIVE_IDENTITY_FIELDS}
        release.update(authority='native-generated-release.v1',release_reason='expired_unpaid_hold',released_at=case.now.isoformat())
        fresh=dict(demand,sessions=[],released_native_sessions=[release])
        self.assertEqual(runner.retained_projection(gap,fresh)['sessions'],[])
        gap['sessions'][0].pop('last_verified_native_identity')
        unknown=runner.retained_projection(gap,fresh)
        self.assertEqual(len(unknown['sessions']),1)
        self.assertEqual(unknown['build']['counts']['released_native_sessions'],0)
        self.assertFalse(unknown['sessions'][0]['public_direct_booking'])
        self.assertIsNone(unknown['sessions'][0]['active_registration_count'])
        self.assertNotIn('canonical_session_id',unknown['sessions'][0])
        # A legacy external identifier does not acquire native provenance.
        legacy=copy.deepcopy(prior);legacy['sessions'][0].update(session_id='12345',external_class_id='12345')
        self.assertNotIn('last_verified_native_identity',runner.retained_projection(legacy,dict(demand,sessions=[]))['sessions'][0])

    def test_release_payload_rejects_conflict_duplicate_legacy_or_future_proof(self):
        case,_,_,source,demand,_=NativeSeatedContinuationTests().fixture()
        release={k:source[k] for k in runner.NATIVE_IDENTITY_FIELDS}
        release.update(authority='native-generated-release.v1',release_reason='expired_unpaid_hold',released_at=case.now.isoformat())
        payload=dict(schema_version='910cpr-canonical-scheduling-demand.v1',generated_at=case.now.isoformat(),sessions=[],released_native_sessions=[release])
        self.assertEqual(len(validate_payload(payload,now=case.now)['released_native_sessions']),1)
        for changes in [dict(sessions=[source]),dict(released_native_sessions=[release,release]),dict(released_native_sessions=[dict(release,external_class_id='123')]),dict(released_native_sessions=[dict(release,released_at=(case.now+timedelta(seconds=1)).isoformat())])]:
            with self.assertRaises(ValueError):validate_payload(dict(payload,**changes),now=case.now)

    def test_only_production_workflow_calls_mutation_before_canonical_fetch(self):
        root=Path(__file__).resolve().parents[1]
        workflow=(root/'.github/workflows/publish-native-availability.yml').read_text()
        section=workflow.split('      - name: Release only proven abandoned native holds',1)[1].split('      - name:',1)[0]
        self.assertIn('if: inputs.publish',section)
        self.assertIn('scripts.maintain_native_publication',section)
        self.assertLess(workflow.index('scripts.maintain_native_publication'),workflow.index('scripts.fetch_canonical_scheduling_demand'))
        self.assertNotIn('maintain_native_publication',(root/'.github/workflows/verify-skills-native-claim.yml').read_text().split('  selector-preview:',1)[1])

if __name__=='__main__':unittest.main()
