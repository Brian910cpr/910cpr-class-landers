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
                                                  ('209818','ACLS','skills')]]
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

    def test_oct10_actual_full_interval_and_edges(self):
        self.add('14:00','16:30','209809',active_registration_count=1)
        for cid in ['210549','209808']:
            self.assertEqual(self.starts(self.report(),cid),{'13:00','16:30'})
        self.assertFalse(self.starts(self.report(),'209818'))

    def test_empty_day_includes_midnight_and_tight_intervals(self):
        self.assertIn('00:00',self.starts(self.report()))
        self.assertIn('23:00',self.starts(self.report()))
        self.assertEqual(self.starts(self.report('03:30','04:30',10)),{'03:30'})

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


if __name__=='__main__':
    unittest.main()
