import copy
from datetime import timedelta
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from scripts import run_native_publication as runner
from scripts.block_start_time_selector import seated_class_selector_offers
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload
from scripts.layered_publication_adapter import publish
from tests.test_native_publication_wiring import NativeWiringTests


class NativeSeatedContinuationTests(unittest.TestCase):
    def fixture(self):
        case = NativeWiringTests().fixture()
        case.sources = []  # First publication has a truly unoccupied fixture day.
        forbidden = lambda *args: (_ for _ in ()).throw(AssertionError('external fallback forbidden'))
        def emit(seated=()):
            return publish(case.calculation(), case.page, case.courses, case.windows, case.now,
                           forbidden, lambda *args: [], seated,
                           native_policy=case.policy['native_publication_scope'])
        first = emit(); self.assertTrue(first['offers'])
        choice = first['offers'][0]
        start = runner.scope.instant(choice['date']+'T'+choice['startTime']+':00-04:00')
        sid = 'lw-11111111-1111-4111-8111-111111111111'
        source = dict(canonical_session_id='canonical-fixture', external_class_id=sid, external_course_id='359474',
            source='landerware_event', registration_backend='landerware', registration_authority='landerware-generated-session.v1',
            session_status='scheduled', registration_status='open', visibility='public', workspace_projection_status='current',
            count_available=True, active_registration_count=1, canonical_registered_count=0, held_seat_count=1, unreconciled_reserved_count=0,
            start_at=start.isoformat(), end_at=(start+timedelta(minutes=120)).isoformat(),
            consumption_start_at=start.isoformat(), consumption_end_at=(start+timedelta(minutes=150)).isoformat(),
            location_name=':: Wilmington; Shipyard Blvd - B', lead_instructor_name='Brian Ennis', course_name='BLS Renewal',
            native_booking_admission=dict(schemaVersion='native-session-booking.v1', publicCourseId='359474', profileVersion=2, capacity=6, remaining=5))
        demand = {'generated_at': case.now.isoformat(), 'sessions': [source]}
        return case, first, choice, source, demand, emit

    def test_empty_publication_to_held_class_retains_remaining_seats_without_duplicate(self):
        case, first, choice, source, demand, emit = self.fixture()
        schedule = runner.retained_projection({'sessions': []}, demand)
        row = schedule['sessions'][0]
        self.assertTrue(row['public_direct_booking'])
        self.assertEqual(row['active_registration_count'], 1)
        # The new canonical class blocks its full instruction + cleanup interval.
        case.sources.append(dict(source_event_id=source['canonical_session_id'], external_class_id=source['external_class_id'],
            start=source['start_at'], end=source['consumption_end_at'], instructor='Brian Ennis', course_id='359474',
            resource=case.room, location_resolution='location_resource_map', source_file='canonical_class_sessions',
            active_registration_count=1, count_available=True))
        seated = seated_class_selector_offers(schedule_future_payload=schedule, selected_courses=case.courses,
            selected_course_ids={'359474'}, course_rules={'359474': {'duration_minutes': 120, 'scheduler_consumption_minutes': 150, 'cleanup_buffer_minutes': 30}})
        self.assertEqual(len(seated), 1)
        result = runner.annotate_seated_offers(emit(seated), schedule)
        feed = public_selector_availability_payload(result)
        offers = [c for d in feed['dates'] for t in d['startTimes'] for c in t['courses']]
        same = [o for o in offers if o['date'] == choice['date'] and o['startTime'] == choice['startTime'] and o['courseId'] == choice['courseId']]
        self.assertEqual(len(same), 1, 'physical class must not become a second dynamic alternative')
        remaining = same[0]
        self.assertEqual(remaining['offerType'], 'seated_class')
        self.assertEqual(remaining['authority'], 'native-session-booking.v1')
        self.assertEqual(remaining['capacity'], 6)
        self.assertEqual(remaining['remainingSeats'], 5)
        self.assertEqual(remaining['registrationUrl'], '/register/?session='+source['external_class_id'])
        runner.validate_seated_offer(remaining, schedule, case.now, 300)
        with self.assertRaises(ValueError): runner.validate_seated_offer(remaining, schedule, case.now+timedelta(minutes=15), 0)
        # Actual browser reader retains a fresh admission then drops it at the
        # original proof deadline even if the global payload was restamped.
        code="const s=require('./docs/assets/resolved-selector-availability.js');let x='';process.stdin.on('data',b=>x+=b);process.stdin.on('end',()=>{const p=JSON.parse(x);console.log(JSON.stringify([s.datesForPublication(p.dates,p.validUntil,p.now),s.datesForPublication(p.dates,'2099-01-01T00:00:00Z',p.now+900000)]));});"
        visible=subprocess.run(['node','-e',code],input=json.dumps(dict(feed,now=int(case.now.timestamp()*1000))),text=True,capture_output=True,check=True,cwd=Path(__file__).resolve().parents[1])
        fresh,expired=json.loads(visible.stdout);self.assertTrue(fresh);self.assertEqual(expired,[])

    def test_legacy_profile_disabled_capacity_unknown_full_or_identity_drift_preserves_blocker_without_cta(self):
        case, _, _, source, demand, _ = self.fixture()
        schedule=runner.retained_projection({'sessions': []},demand)
        for change in [dict(registration_authority=None),dict(native_booking_admission=None),dict(visibility='private'),
                       dict(active_registration_count=6),dict(workspace_projection_status='missing'),
                       dict(native_booking_admission={**source['native_booking_admission'],'capacity':None}),
                       dict(native_booking_admission={**source['native_booking_admission'],'remaining':6})]:
            new=copy.deepcopy(demand);new['sessions'][0].update(change)
            result=runner.retained_projection(schedule,new)
            self.assertEqual(len(result['sessions']),1)
            self.assertFalse(result['sessions'][0]['public_direct_booking'])
            self.assertNotIn('registration_url',result['sessions'][0])
            self.assertNotIn('native_booking_admission',result['sessions'][0])
        changed=copy.deepcopy(schedule);changed['sessions'][0]['end_at']=source['consumption_end_at']
        self.assertFalse(runner.retained_projection(changed,demand)['sessions'][0]['public_direct_booking'])

    def test_adopted_exact_authority_is_admitted_but_a_prior_public_dto_is_not_authority(self):
        _,_,_,source,demand,_=self.fixture()
        source['registration_authority']='landerware-session-authority.v1'
        result=runner.retained_projection({'sessions':[]},demand)
        self.assertTrue(result['sessions'][0]['public_direct_booking'])
        self.assertFalse(runner.retained_projection(result,{'generated_at':demand['generated_at'],'sessions':[]})['sessions'][0]['public_direct_booking'])

if __name__=='__main__':unittest.main()
