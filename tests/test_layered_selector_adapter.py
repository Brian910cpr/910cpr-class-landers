import json
import unittest
from datetime import datetime
from pathlib import Path
from scripts.layered_selector_adapter import build_shadow

ROOT = Path(__file__).resolve().parents[1]


class LayeredAdapterTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT/'data/config/layered_scheduling_policy.json').read_text())
        self.resources = json.loads((ROOT/'data/config/location_resource_map.json').read_text())
        self.window = dict(instructor_name='Brian Ennis', person_id=self.policy['brian_person_id'],
                           location_name=':: Wilmington; Shipyard Blvd',
                           source_availability_window='real-declared-instructor-window')
        self.courses = [dict(course_id=cid, course_family=family, kind=kind)
                        for cid, family, kind in [('210549','BLS','skills'),('209808','Heartsaver','skills'),
                                                  ('209806','BLS','full'),('209809','Heartsaver','full'),
                                                  ('fixture-acls-skills','ACLS','skills')]]
        self.busy = []

    def at(self, clock, day=10):
        return datetime.fromisoformat(f'2026-10-{day:02d}T{clock}:00-04:00')

    def add(self, start, end, cid='210549', **extra):
        self.busy.append(dict(start=self.at(start), end=self.at(end), instructor='Brian',
            course_id=cid, resource=self.policy['primary_resource'],
            location_resolution='location_resource_map', source_file='canonical_class_sessions',
            source_event_id='real-'+start, **extra))

    def report(self, start='00:00', end='00:00', end_day=11):
        return build_shadow([self.window], self.busy, self.courses, self.policy, self.resources,
            self.at('00:00',1), lambda w:(self.at(start),self.at(end,end_day)),
            lambda w,c:False)  # Brian's owner rule applies across skills/full.

    def starts(self, report, cid='210549'):
        return {c['start'].astimezone(self.at('00:00').tzinfo).strftime('%H:%M')
                for c in report['accepted'] if c['course']==cid}

    def test_actual_source_identity_and_growth_both_skills_at_each_edge(self):
        self.add('12:00','13:00')
        for cid in ['210549','209808']:
            self.assertEqual(self.starts(self.report(),cid),{'11:00','13:00'})
        self.add('13:00','14:00','209808')
        self.assertEqual(self.starts(self.report()),{'11:00','14:00'})
        self.add('11:00','12:00')
        self.assertEqual(self.starts(self.report()),{'10:00','14:00'})
        self.add('14:00','16:30','209809')
        self.assertEqual(self.starts(self.report()),{'10:00','16:30'})

    def test_equivalent_utc_and_local_booking_has_one_anchor_and_real_edges(self):
        from scripts.generate_dynamic_offers import parse_dt
        self.add('12:00', '13:00', active_registration_count=1, count_available=True)
        mirrored = dict(self.busy[0], source_event_id='enrollware:real-12:00',
                        source_file='docs/data/schedule_future.json',
                        linked_canonical_session_id='real-12:00',
                        start=parse_dt('2026-10-10T16:00:00Z'),
                        end=parse_dt('2026-10-10T17:00:00Z'))
        self.busy.append(mirrored)
        report = self.report()
        self.assertEqual(len(report['normalized_occupancy']), 1)
        self.assertEqual(len(report['seated_offers']), 1)
        self.assertEqual(report['normalized_occupancy'][0]['canonical_source_ids'], ['real-12:00'])
        self.assertEqual(self.starts(report), {'11:00', '13:00'})
        for offer in report['accepted']:
            self.assertEqual(offer['source_ids'], ['real-12:00'])

    def test_contradictory_attested_courses_hold_geometry_without_arbitrary_gravity(self):
        self.add('12:00', '13:00', '209806', active_registration_count=1, count_available=True)
        self.add('12:00', '13:00', '209809', active_registration_count=2, count_available=True)
        self.busy[-1]['source_event_id'] = 'distinct-canonical-session'
        for order in (list(self.busy), list(reversed(self.busy))):
            self.busy = order
            report = self.report()
            self.assertEqual(len(report['normalized_occupancy']), 1)
            occupied = report['normalized_occupancy'][0]
            self.assertEqual(occupied['kind'], 'hold')
            self.assertEqual(occupied['uncertainty_reason'], 'conflicting_attested_course_identity')
            self.assertIsNone(occupied['course'])
            self.assertIsNone(occupied['headcount'])
            self.assertEqual(report['seated_offers'], [])
            for cid in ('209806', '209809', '210549'):
                self.assertNotIn('12:00', self.starts(report, cid))

    def test_independent_same_course_claims_preserve_both_ids_as_block_not_joinable(self):
        self.add('12:00', '13:00', '209806', active_registration_count=1, count_available=True)
        self.add('12:00', '13:00', '209806', active_registration_count=2, count_available=True)
        self.busy[-1]['source_event_id'] = 'second-canonical'
        for order in (list(self.busy), list(reversed(self.busy))):
            self.busy = order
            report = self.report()
            occupied, = report['normalized_occupancy']
            self.assertEqual(occupied["canonical_source_ids"], ["real-12:00", "second-canonical"])
            self.assertEqual(occupied["kind"], "hold")
            self.assertEqual(report['seated_offers'], [])
            self.assertNotIn('12:00', self.starts(report))

    def test_unknown_conflicting_legacy_mirror_does_not_veto_attributed_seat(self):
        self.add('12:00', '13:00', '209806', active_registration_count=1, count_available=True)
        self.add('12:00', '13:00', '209809', active_registration_count=None, count_available=False)
        self.busy[-1].update(source_file='docs/data/schedule_future.json', source_event_id='mirror')
        self.busy.reverse()
        report = self.report()
        self.assertEqual(len(report['normalized_occupancy']), 1)
        self.assertEqual(report['normalized_occupancy'][0]['course'], '209806')
        self.assertEqual(report['normalized_occupancy'][0]['headcount'], 1)
        self.assertEqual(len(report['seated_offers']), 1)

    def test_other_instructor_and_room_same_instant_are_not_course_ambiguity(self):
        self.add('12:00', '13:00', '209806', active_registration_count=1, count_available=True)
        self.add('12:00', '13:00', '209809', active_registration_count=2, count_available=True)
        self.busy[-1].update(source_event_id='other-canonical-session', instructor='Other instructor',
                             resource=':: Wilmington; Shipyard Blvd - C')
        report = self.report()
        self.assertEqual(len(report['normalized_occupancy']), 2)
        self.assertEqual({row['course'] for row in report['normalized_occupancy']}, {'209806','209809'})
        self.assertNotIn('12:00', self.starts(report, '210549'))

    def test_utc_conversion_preserves_eastern_winter_and_dst_clock(self):
        from scripts.generate_dynamic_offers import parse_dt
        for utc, local in [('2026-01-10T17:00:00Z', '2026-01-10T12:00:00'),
                           ('2026-07-10T16:00:00Z', '2026-07-10T12:00:00')]:
            self.assertEqual(parse_dt(utc), datetime.fromisoformat(local))
        self.assertEqual(parse_dt('2026-10-10T12:00:00'), self.at('12:00').replace(tzinfo=None))

    def test_oct10_actual_full_interval_and_edges(self):
        self.add('14:00','16:30','209809',active_registration_count=1)
        for cid in ['210549','209808']:
            self.assertEqual(self.starts(self.report(),cid),{'13:00','16:30'})
        self.assertEqual(self.starts(self.report(),'fixture-acls-skills'),{'13:00','16:30'})

    def test_brian_all_skills_keeps_advanced_full_courses_excluded(self):
        self.courses.extend([dict(course_id='advanced-full',course_family='PALS',kind='full'),
                             dict(course_id='pals-skills',course_family='PALS',kind='skills')])
        self.add('12:00','13:00',active_registration_count=1)
        self.assertEqual(self.starts(self.report(),'pals-skills'),{'11:00','13:00'})
        self.assertFalse(self.starts(self.report(),'advanced-full'))

    def test_empty_day_includes_midnight_and_tight_intervals(self):
        self.assertIn('00:00',self.starts(self.report()))
        self.assertIn('23:00',self.starts(self.report()))
        self.assertEqual(self.starts(self.report('03:30','04:30',10)),{'03:30'})

    def test_heartsaver_cpr_aed_uses_90_plus_15_at_real_edges(self):
        self.courses.append(dict(course_id='344085', course_family='Heartsaver', kind='full'))
        self.add('12:00','13:00')
        offers=[c for c in self.report()['accepted'] if c['course']=='344085']
        self.assertEqual(self.starts(self.report(),'344085'), {'10:15','13:00'})
        self.assertTrue(all(c['duration_minutes']==105 for c in offers))
        self.assertEqual(self.starts(self.report(),'209806'), {'09:30','13:00'})

    def test_real_room_reservation_blocks_and_no_automatic_room_c(self):
        self.add('12:00','13:00')
        self.add('13:00','14:00',source_file_override='calendar')
        self.busy[-1]['source_file']='live_availability_snapshot.blocked[1]'
        self.busy[-1]['instructor']='another instructor'
        self.assertEqual(self.starts(self.report()),{'11:00'})
        self.assertTrue(all(c['location']==self.policy['primary_resource'] for c in self.report()['accepted']))

    def test_missing_travel_fails_closed_not_no_travel_assumption(self):
        self.busy=[dict(start=self.at('09:00'),end=self.at('11:00'),instructor='Brian',
                        location='offsite',source_file='canonical_class_sessions')]
        with self.assertRaisesRegex(ValueError,'missing directional travel'):
            self.report()

    def test_proven_native_venue_label_reserves_primary_without_claiming_room(self):
        from scripts.generate_dynamic_offers import normalize_location_resource
        label = '4018 Shipyard Blvd, Room B, 910CPR Office'
        location, resource, resolved = normalize_location_resource(label, label, self.resources)
        self.assertTrue(resolved)
        self.assertEqual(location, ':: Wilmington; Shipyard Blvd')
        # Authenticated session FK proves the venue, but resource_id is null.
        # Keep this a venue alias, never an invented explicit Room B assignment.
        self.assertEqual(resource, label)
        self.busy = [dict(start=self.at('12:00'), end=self.at('13:00'),
            instructor='another instructor', location=location, resource=resource,
            location_resolution='location_resource_map', source_file='canonical_class_sessions')]
        report = self.report()
        self.assertEqual(len(report['normalized_occupancy']), 1)
        self.assertNotIn('12:00', self.starts(report))
        self.assertTrue(all(c['location'] == self.policy['primary_resource']
                            for c in report['accepted']))
        # The same physical reservation must still block Brian himself.
        self.busy[0]['instructor'] = 'Brian'
        self.assertNotIn('12:00', self.starts(self.report()))

    def test_room_worded_shipyard_venue_is_occupied_without_offsite_travel_guess(self):
        from scripts.generate_dynamic_offers import normalize_location_resource
        label = '910CPR Office - Shipyard Blvd, Room B'
        venue, resource, verified_venue = normalize_location_resource(label, label, self.resources)
        self.assertTrue(verified_venue)
        self.assertEqual(resource, label)  # No room FK: don't manufacture a Room B allocation.
        self.busy = [dict(start=self.at('12:00'), end=self.at('13:00'),
            instructor='Brian Ennis', location=venue, resource=resource,
            location_resolution='location_resource_map',
            source_file='canonical_class_sessions')]
        report = self.report()
        self.assertEqual(len(report['normalized_occupancy']), 1)
        self.assertNotIn('12:00', self.starts(report))
        self.assertEqual(self.starts(report), {'11:00', '13:00'})

    def test_room_hours_do_not_resolve_unknown_occupied_duration(self):
        self.add('12:00','12:00')
        with self.assertRaisesRegex(ValueError,'zero-duration'):
            self.report()

    def test_unassigned_instructor_does_not_become_free_at_another_room(self):
        self.add('12:00','13:00',instructor_unassigned=True)
        self.busy[-1]['instructor']=''
        self.busy[-1]['resource']=':: Wilmington; Shipyard Blvd - A'
        self.assertNotIn('12:00',self.starts(self.report()))

    def test_two_blocks_have_both_edges_and_no_interior_space_scan(self):
        self.add('09:00','10:00')
        self.add('17:00','18:00','209808')
        self.assertEqual(self.starts(self.report()),{'08:00','10:00','16:00','18:00'})
        self.assertNotIn('13:00',self.starts(self.report()))

    def test_source_backed_fixture_both_heartsaver_variants_at_oct10_edges(self):
        data=json.loads((ROOT/'tests/fixtures/layered_native_oct10.json').read_text())
        report=build_shadow(data['windows'],data['occupancy'],data['courses'],self.policy,self.resources,
            datetime.fromisoformat(data['now'].replace('Z','+00:00')),
            lambda w:(datetime.fromisoformat(w['start']),datetime.fromisoformat(w['end'])),
            lambda w,c:False)
        for cid in ['210549','209808','329495']:
            self.assertEqual(self.starts(report,cid),{'13:00','16:30'})

    def test_unknown_instructor_venue_is_not_assigned_to_shipyard(self):
        self.window['location_name']='unknown venue'
        with self.assertRaisesRegex(ValueError,'known Shipyard venue'):
            self.report()


B='Brian Ennis'; A='Amy Arnold'; P='instructor_24057895173'; ROOM='Room B'
POLICY=dict(room_hours='24/7',simultaneous_classes_per_room=1,primary_resource=ROOM,
 automatic_relocation=False,slot_minutes=30,edge_grid_policy='exact_existing_boundary',
 full_family_paid_positions_per_day=1,skills_instruction_minutes=45,skills_cleanup_minutes=15,
 full_instruction_minutes=120,full_cleanup_minutes=30,owner_room_hours_evidence='fixture',
 brian_person_id=P,brian_excluded_families=['ACLS','PALS'])
RES={'locations':[dict(canonical_public_location='Shipyard',internal_resources=[{'resource_name':ROOM}])]}
COURSES=[dict(course_id='1',course_family='BLS',kind='skills')]
def at(clock): return '2026-12-10T'+clock+':00-05:00'
def src(person,unassigned=False,venue='Offsite'):
 return dict(instructor=person,instructor_unassigned=unassigned,start=at('10:00'),end=at('12:00'),location=venue)
def calc(name,persons,extend=False,person_id=None,travel=None):
 p=dict(POLICY,owner_travel_in_calendar_only=True) if extend else POLICY
 out=build_shadow([dict(instructor_name=name,person_id=person_id or (P if name==B else 'other'),location_name='Shipyard',
 start=at('08:00'),end=at('16:00'))],persons,COURSES,p,RES,datetime.fromisoformat('2026-12-01T13:00:00Z'),
 lambda w:(w['start'],w['end']),lambda w,c:True,lead_minutes=0,
 travel_minutes=travel)
 return [(i[0].isoformat(),i[1].isoformat()) for i in out['resource_availability'][0]['free']]

class OwnerTravelExactIntervalTests(unittest.TestCase):
 def test_named_owner_uses_exact_intervals(self):
  self.assertEqual(calc(B,[src(B)],True),[('2026-12-10T13:00:00+00:00','2026-12-10T15:00:00+00:00'),('2026-12-10T17:00:00+00:00','2026-12-10T21:00:00+00:00')])
 def test_amy_unchanged(self):
  with self.assertRaisesRegex(ValueError,'missing directional travel'):
   calc(A,[src(A)],True)
 def test_unassigned_even_if_shares_route(self):
  with self.assertRaisesRegex(ValueError,'missing directional travel'):
   calc(B,[src(B),dict(src('unassigned',True),start=at('11:00'))],True)
 def test_display_name_alone_is_not_authority(self):
  with self.assertRaisesRegex(ValueError,'missing directional travel'):
   calc(B,[src(B)],True,person_id='unrelated-id')
 def test_separate_owner_calendar_block_not_doubled(self):
  travel=dict(src(B),start=at('09:30'),end=at('10:00'),availability_location_mode='instructor_time_only')
  self.assertEqual(calc(B,[src(B),travel],True),[('2026-12-10T13:00:00+00:00','2026-12-10T14:30:00+00:00'),('2026-12-10T17:00:00+00:00','2026-12-10T21:00:00+00:00')])
 def test_explicit_asymmetric_routes_win_over_owner_fallback(self):
  self.assertEqual(calc(B,[src(B)],True,travel={
      'Room B->Offsite': 30, 'Offsite->Room B': 45}),
      [('2026-12-10T13:00:00+00:00','2026-12-10T14:30:00+00:00'),
       ('2026-12-10T17:45:00+00:00','2026-12-10T21:00:00+00:00')])
 def test_invalid_explicit_route_does_not_fall_back(self):
  for invalid in (None, -10, True, float('nan'), float('inf')):
   with self.subTest(invalid=invalid):
    with self.assertRaisesRegex(ValueError,'invalid directional travel'):
     calc(B,[src(B)],True,travel={'Room B->Offsite':invalid})
 def test_no_opt_in_unchanged(self):
  with self.assertRaisesRegex(ValueError,'missing directional travel'):
   calc(B,[src(B)])


 def test_opt_in_invalidates_cache_and_preserves_direct_candidate_decisions(self):
  from tempfile import TemporaryDirectory
  from scripts.layered_day_cache import cached_calculate
  from scripts.layered_publication_adapter import calculate

  window = dict(instructor_name=B, person_id=P, location_name='Shipyard',
                start=at('08:00'), end=at('16:00'))
  now = datetime.fromisoformat('2026-12-01T13:00:00Z')
  proof = dict(instructor=B, location=ROOM, status='known_complete',
               start=window['start'], end=window['end'],
               observed_at=now.isoformat(), valid_until='2026-12-01T14:00:00Z')
  def args(opt_in):
   return ([window], [src(B)], COURSES,
           dict(POLICY, mode='active_local_v2', owner_travel_in_calendar_only=opt_in, lead_minutes=0),
           RES, now, lambda w:(w['start'],w['end']), lambda *_:True, [proof])

  with TemporaryDirectory() as temp:
   def cached(opt_in):
    return cached_calculate(*args(opt_in), cache_dir=Path(temp))
   self.assertEqual(cached(False)['counts']['failed_windows'], 1)
   cold, warm = cached(True), cached(True)
   direct = calculate(*args(True))
   self.assertEqual(cold['incremental_cache']['hits'], 0)
   self.assertEqual(warm['incremental_cache']['hits'], 1)
   self.assertTrue(direct['reports'][0]['accepted'])
   for key in ('accepted', 'rejected'):
    self.assertEqual(cold['reports'][0][key], direct['reports'][0][key])
    self.assertEqual(warm['reports'][0][key], direct['reports'][0][key])
   self.assertEqual(cached(False)['counts']['failed_windows'], 1)



 def test_attested_same_interval_mirror_preserves_unassigned_hold_in_both_orders(self):
  assigned = dict(src(B), source_event_id='paid', kind='paid',
                  operational_has_active_seat=True)
  unassigned = dict(src(B, unassigned=True), source_event_id='unknown')
  windows = [
      dict(instructor_name=B, person_id=P, location_name='Shipyard',
           start=at('08:00'), end=at('16:00')),
      dict(instructor_name=A, person_id='other', location_name='Shipyard',
           start=at('08:00'), end=at('16:00')),
  ]
  for rows in ([assigned, unassigned], [unassigned, assigned]):
   with self.subTest(order=rows[0]['source_event_id']):
    out = build_shadow(windows, rows, COURSES, POLICY, RES,
                       datetime.fromisoformat('2026-12-01T13:00:00Z'),
                       lambda w:(w['start'],w['end']),lambda *_:True,
                       lead_minutes=0,travel_minutes={
                         'Room B->Offsite':30,'Offsite->Room B':45})
    hold = [r for r in out['source_truth'] if r['instructor']==A and r['kind']=='hold']
    self.assertEqual(len(hold),1)
    self.assertFalse(hold[0]['operational_has_active_seat'])
    amy = next(r for r in out['resource_availability'] if r['instructor']==A)
    self.assertEqual([(a.isoformat(),b.isoformat()) for a,b in amy['free']],
                     [('2026-12-10T13:00:00+00:00','2026-12-10T14:30:00+00:00'),
                      ('2026-12-10T17:45:00+00:00','2026-12-10T21:00:00+00:00')])


if __name__=='__main__':
    unittest.main()
