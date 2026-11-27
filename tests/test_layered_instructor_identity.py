import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.block_start_time_selector import build_occupancy, find_url
from scripts.layered_day_cache import cached_calculate
from scripts.layered_instructor_identity import explicit_external_crosswalk
from scripts.layered_publication_adapter import apply_default_owner_occupancy, publish
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload
from tests import test_layered_publication_adapter as fixtures


class VerifiedInstructorIdentityTests(unittest.TestCase):
    def setUp(self):
        self.f = f = fixtures.LayeredPublicationTests()
        f.setUp()
        f.policy.update(verified_instructor_identity=True, require_verified_day_gravity=True)
        f.windows[:] = []
        f.coverage[:] = []
        f.window(11, '08:00', '18:00', next_day=False)
        self.owner = f.windows[0]['person_id']
        self.other = 'synthetic-second-instructor-id'
        f.coverage[0]['instructor_person_id'] = self.owner

    def test_crosswalk_requires_unique_explicit_ids(self):
        people = [{"person_id": self.owner}, {"person_id": self.other}]
        self.assertEqual(explicit_external_crosswalk(people, {}), {})
        self.assertEqual(explicit_external_crosswalk(people, {self.owner: '8765'}), {'8765': self.owner})
        for extra in (self.other, 'inactive-person'):
            self.assertEqual(explicit_external_crosswalk(people, {self.owner: '8765', extra: '8765'}), {})
        self.assertEqual(explicit_external_crosswalk(people, {self.owner: '08765'}), {})
        self.assertEqual(explicit_external_crosswalk(people + people[:1], {self.owner: '8765'}), {})

    def test_normalization_accepts_five_verified_and_five_unassigned_keeps_others_busy(self):
        f = self.f
        sessions = []
        for i in range(11):
            known = i < 5
            unassigned = 5 <= i < 10
            sessions.append(dict(canonical_session_id=f'synthetic-{i}', session_status='scheduled',
                start_at=f.at(11, '10:00').isoformat(), end_at=f.at(11, '12:30').isoformat(),
                external_course_id=None if i == 10 else '359474',
                location_name=f.windows[0]['location_name'], operational_has_active_seat=True,
                lead_instructor_id=None if unassigned else f'fake-fk-{i}',
                lead_instructor_name=None if unassigned else 'Not identity evidence',
                lead_instructor_identity={'status': 'verified' if known or not unassigned else 'unassigned',
                                          'catalog_external_id': '8765' if known else None}))
        before = copy.deepcopy(sessions)
        rows = build_occupancy({'canonical_demand': {'sessions': sessions},
                               'location_resource_map': f.resources},
                              {'359474': {}}, True, known_catalog_ids={'359474'},
                              strict_instructor_crosswalk={'8765': self.owner})
        self.assertEqual(sessions, before)
        self.assertEqual([r['stored_instructor_identity_state'] for r in rows],
                         ['verified']*5 + ['unassigned']*5 + ['unresolved'])
        self.assertEqual([r['effective_instructor_person_id'] for r in rows],
                         [self.owner]*5 + [None]*6)
        self.assertEqual(rows[-1]['kind'], 'hold')
        self.assertTrue(rows[-1]['instructor_unassigned'])
        self.assertEqual(len({(r['start'], r['end']) for r in rows}), 1)
        self.assertNotIn('fake-fk-', str(rows))

    def test_default_owner_requires_compatible_fresh_proof_and_does_not_set_stored_id(self):
        f = self.f
        row = f.add_intake(11, stored_instructor_identity_state='unassigned',
                           stored_instructor_person_id=None)
        def run():
            return apply_default_owner_occupancy(f.sources, 'Brian Ennis', f.room,
                f.now, f.coverage, lambda _: True, strict_identity=True, owner_person_id=self.owner)[0]
        attributed = run()
        self.assertEqual(attributed['effective_instructor_person_id'], self.owner)
        self.assertIsNone(attributed['stored_instructor_person_id'])
        self.assertNotIn('effective_instructor_person_id', row)
        f.coverage[0]['instructor_person_id'] = self.other
        self.assertIs(run(), row)
        f.coverage[0]['instructor_person_id'] = self.owner
        row['stored_instructor_identity_state'] = 'unresolved'
        self.assertIs(run(), row)

    def test_shared_name_different_id_holds_room_but_does_not_create_selected_instructor_anchor(self):
        f = self.f
        row = f.add(11,'12:00','14:30',cid='359474', count=1,
            stored_instructor_person_id=self.other, effective_instructor_person_id=self.other)
        baseline = f.calculation()
        r = baseline['reports'][0]
        self.assertTrue(r['accepted'])
        self.assertEqual(r['normalized_occupancy'][0]['instructor'], 'unmatched instructor 1')
        self.assertTrue(all(o['end'] <= f.at(11,'12:00') or o['start'] >= f.at(11,'14:30')
                            for o in r['accepted']))
        self.assertTrue(any(o['mode']=='free' for o in r['accepted']))
        with tempfile.TemporaryDirectory() as work:
            def compute():
                return cached_calculate(f.windows,f.sources,f.courses,f.policy,f.resources,f.now,
                    lambda w:(w['start'],w['end']),lambda *_:True,f.coverage,cache_dir=Path(work))
            cold, warm = compute(), compute()
            self.assertEqual(warm['incremental_cache']['hits'], 1)
            self.assertEqual(cold['reports'][0]['accepted'], r['accepted'])
            self.assertEqual(warm['reports'][0]['accepted'], r['accepted'])
            row['stored_instructor_person_id'] = row['effective_instructor_person_id'] = self.owner
            changed = compute()
            self.assertEqual(changed['incremental_cache']['hits'], 0)
            self.assertEqual(changed['reports'][0]['normalized_occupancy'][0]['instructor'], 'Brian Ennis')
            f.coverage[0]['instructor_person_id'] = self.other
            self.assertFalse(compute()['reports'][0]['accepted'])

    def test_public_serializer_never_exports_new_instructor_id_fields(self):
        f = self.f
        f.add(11,'12:00','14:30',cid='359474', count=1,
            stored_instructor_person_id=self.other, effective_instructor_person_id=self.other)
        result = publish(f.calculation(), f.page, f.courses, f.windows, f.now,
            lambda *_:('fixture-day','fixture-container','https://fixture.invalid/register',None),
            lambda *_:[], require_verified_day_gravity=True, strict_instructor_identity=True)
        self.assertTrue(result['offers'])
        for payload in (result, public_selector_availability_payload(result)):
            self.assertNotIn(self.other, json.dumps(payload))
            self.assertNotIn(self.owner, json.dumps(payload))

    def test_same_name_container_without_identity_is_not_a_route(self):
        f = self.f
        window = f.windows[0]
        candidates = [{'container_id': 'wrong', 'instructor_name': 'Brian Ennis'},
                      {'container_id': 'proved', 'instructor_name': 'Brian Ennis'}]
        rejected = find_url(window, f.at(11, '09:00'), '359474', candidates, f.resources,
                            strict_container_owners={'wrong': self.other})
        self.assertEqual(rejected, (None, None, None, 'unverified_appointment_container_owner'))
        with patch('scripts.block_start_time_selector.matching_container',
                   return_value=(candidates[1], 1234, None)) as match:
            approved = find_url(window, f.at(11, '09:00'), '359474', candidates, f.resources,
                                strict_container_owners={'wrong': self.other, 'proved': self.owner})
            self.assertEqual(approved[1], 'proved')
            self.assertEqual(match.call_args.args[1], [candidates[1]])

    def test_owner_role_is_separate_from_numeric_namespace(self):
        from scripts.layered_instructor_identity import canonical_instructor_projection
        proof = {'status':'verified','catalog_external_id':'50001'}
        row = {'lead_instructor_id':'synthetic-owner-fk','lead_instructor_identity':proof}
        self.assertEqual(canonical_instructor_projection(row, {'50001':self.owner},
                         owner_person_id=self.owner), ('unresolved',None))
        proof['verified_role']='configured_910cpr_owner'
        self.assertEqual(canonical_instructor_projection(row, {},owner_person_id=self.owner),
                         ('verified',self.owner))
        proof['status']='conflicting'
        self.assertEqual(canonical_instructor_projection(row, {},owner_person_id=self.owner),
                         ('unresolved',None))

    def test_exact_historical_course_keeps_private_shape_and_mirror_nonbookable(self):
        f=self.f
        date=f.at(11,'12:00').isoformat()
        end=f.at(11,'14:30').isoformat()
        historic=dict(canonical_session_id='synthetic-private-session',external_class_id='808888',
            lead_instructor_id=None,lead_instructor_identity={'status':'unassigned','catalog_external_id':None},
            start_at=date,end_at=end,location_name=f.windows[0]['location_name'],
            course_key='hist-course:7107a1c4f42ee0b1',course_name='Same title',
            verified_occupancy_course_id='252737', visibility='private',source='confirmed_booking_intake',
            registration_backend='landerware',session_status='scheduled',operational_has_active_seat=True)
        legacy=dict(session_id='808888', course_id='252737',start_at=date,end_at=end,
            location=f.windows[0]['location_name'], instructor='Brian Ennis')
        rows=build_occupancy({'canonical_demand':{'sessions':[historic]},'location_resource_map':f.resources,
            'schedule_future':{'sessions':[legacy]}},{'252737':{}},True,
            known_catalog_ids={'252737'},strict_instructor_crosswalk={})
        mirror, canonical=rows
        self.assertEqual(canonical['course_id'],'252737')
        self.assertTrue(canonical['instructor_unassigned'])
        self.assertFalse(canonical['public_direct_booking'])
        self.assertFalse(mirror['public_direct_booking'])
        self.assertEqual(mirror['kind'],'hold')
        f.sources=rows
        seated=dict(session_id='808888',date='2026-10-11',startTime='12:00',courseId='252737',
            offerType='seated_class',visibility='public',instructor='Brian Ennis')
        result=publish(f.calculation(), f.page, f.courses, f.windows, f.now,
            lambda *_:('fixture-day','fixture-container','https://fixture.invalid/register',None),
            lambda *_:[], [seated], strict_instructor_identity=True)
        self.assertFalse(any(o.get('offerType')=='seated_class' for o in result['offers']))
        public=public_selector_availability_payload(result)
        for private in ('synthetic-private-session','808888'):
            self.assertNotIn(private,json.dumps(public))
        for corrupt in [{'course_key':'wrong'},{'external_course_id':'unknown'},{'visibility':'public'}]:
            row=build_occupancy({'canonical_demand':{'sessions':[{**historic,**corrupt}]},
                'location_resource_map':f.resources},{'252737':{}},True,known_catalog_ids={'252737'},
                strict_instructor_crosswalk={})[0]
            self.assertIsNone(row['course_id'])
            self.assertEqual(row['kind'],'hold')
