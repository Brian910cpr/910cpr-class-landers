"""Incident regression: source interval evidence, not an invented cleanup override.

The source IDs/times are public evidence; counts below are synthetic scenarios.
Owner confirmed 2026-10-15: required turnaround is already unavailable space;
there must be no additional cleanup veto after its recorded occupied end.
"""
import copy
import unittest
from urllib.parse import parse_qs, urlparse

from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload
from scripts.build_seed_appointment_url_preview import build_registration_url
from scripts.layered_selector_adapter import aware
from scripts.layered_scheduling_engine import interval_conflict
from tests import test_layered_publication_adapter as fixtures


class October17ContractTests(unittest.TestCase):
    def setUp(self):
        self.case = fixtures.LayeredPublicationTests()
        self.case.setUp()
        self.case.windows = []
        self.case.coverage = []
        self.case.window(17)
        self.anchor = self.case.add(17, '10:00', '12:00', cid='359474', count=2)
        self.anchor['source_event_id'] = '3b2731a3-19bb-4d10-9757-08a8e81e336f'

    def test_noon_full_and_skills_preserve_source_boundary_and_candidate_cleanup(self):
        before = copy.deepcopy(self.case.sources)
        payload = self.case.payload()
        noon = {o['courseId']: o for o in payload['offers'] if o['startTime'] == '12:00'}
        for cid, instruction, consumption in [('209809', 120, 150), ('329495', 45, 60), ('210549', 45, 60)]:
            with self.subTest(cid=cid):
                self.assertEqual(noon[cid]['durationMinutes'], instruction)
                self.assertEqual(noon[cid]['schedulerConsumptionMinutes'], consumption)
                self.assertEqual(noon[cid]['sourceSessionIds'], [self.anchor['source_event_id']])
        self.assertEqual(self.case.sources, before)
        self.assertEqual(self.case.calculation()['reports'][0]['blocks'][0]['end'], aware(self.anchor['end']))

    def test_left_full_and_skills_consumption_finishes_before_anchor(self):
        self.assertEqual(self.case.starts('209809'), {'07:30', '12:00'})
        self.assertEqual(self.case.starts('329495'), {'09:00', '12:00'})

    def test_explicit_source_consumption_until_1230_is_preserved(self):
        self.anchor['end'] = self.case.at(17, '12:30').isoformat()
        self.assertEqual(self.case.starts('209809'), {'07:30', '12:30'})
        self.assertNotIn('12:00', self.case.starts('329495'))

    def test_same_instructor_overlap_in_room_c_still_blocks_noon(self):
        row = self.case.add(17, '12:00', '12:15', cid='other')
        row['resource'] = ':: Wilmington; Shipyard Blvd - C'
        self.assertNotIn('12:00', self.case.starts('209809'))

    def test_other_instructor_same_room_blocks_noon_without_automatic_relocation(self):
        self.case.add(17, '12:00', '13:00', cid='other', name='Other instructor')
        self.assertNotIn('12:00', self.case.starts('209809'))
        self.assertTrue(all(o['resource'] == self.case.room for o in self.case.payload()['offers']))

    def test_new_offer_cleanup_cannot_overlap_later_commitment(self):
        row = self.case.add(17, '14:00', '15:00', cid='other')
        row['source_file'] = 'live_availability_snapshot.blocked'
        self.assertNotIn('12:00', self.case.starts('209809'))
        self.assertIn('12:00', self.case.starts('329495'))

    def test_paid_anchor_is_retained_and_same_course_is_not_scattered(self):
        self.assertEqual(self.case.starts('359474'), set())
        seated = self.case.calculation()['reports'][0]['seated_offers']
        self.assertTrue(any(o['source_id'] == self.anchor['source_event_id'] for o in seated))

    def test_other_course_families_keep_adjacent_offers_but_brian_acls_is_ineligible(self):
        self.case.courses.extend([
            dict(course_id='arc-test', course_family='ARC', kind='skills'),
            dict(course_id='hsi-test', course_family='HSI', kind='skills'),
            dict(course_id='acls-test', course_family='ACLS', kind='skills'),
            dict(course_id='pals-test', course_family='PALS', kind='skills')])
        for cid in ['arc-test', 'hsi-test']:
            self.assertIn('12:00', self.case.starts(cid))
        for cid in ['acls-test', 'pals-test']:
            self.assertEqual(self.case.starts(cid), set())

    def test_feed_names_active_policy_and_does_not_claim_checkout_validation(self):
        feed = public_selector_availability_payload(self.case.payload())
        self.assertEqual(feed['sourceArtifacts']['activeSchedulingPolicy'], 'data/config/layered_scheduling_policy.json')
        self.assertIn('supplied occupied intervals', feed['authority']['description'])
        self.assertIn('does not prove its checkout-time validation', feed['authority']['description'])
        legacy = public_selector_availability_payload({'dates': []})
        self.assertNotIn('activeSchedulingPolicy', legacy['sourceArtifacts'])
        self.assertIn('Work Order 1B', legacy['authority']['description'])

    def test_exact_owned_day_and_url_parameters(self):
        import json
        from datetime import date, time
        from pathlib import Path
        from scripts.build_seed_appointment_url_preview import compute_appointment_day_id
        root = Path(__file__).resolve().parents[1]
        containers = json.loads((root/'data/inventory/appointment_containers.json').read_text())['containers']
        container = next(c for c in containers if c['container_id'] == 'shipyard_brian_continuous_20260621_20270430')
        self.assertEqual(compute_appointment_day_id(container, date(2026, 10, 17)), 260788)
        query = parse_qs(urlparse(build_registration_url(260788, time(12), '209809')).query)
        self.assertEqual(query, {'appointmentDayId': ['260788'], 'startTime': ['12:00 PM'], 'courseId': ['209809']})

    def visible_offers_and_conflicts(self):
        """Exercise the runtime's actual collision predicate on public intervals.

        This is local booking-time collision proof, not Enrollware checkout proof.
        Explicit source bounds already contain required reservations. No duration
        rule is inferred again from the previous class's teaching end.
        """
        payload = self.case.payload()
        feed = public_selector_availability_payload(payload)
        offers = [c for d in feed['dates'] for t in d['startTimes'] for c in t['courses']]
        occupied = [b for report in self.case.calculation()['reports'] for b in report['normalized_occupancy']]
        def conflicts(offer, sources=occupied):
            start = aware(offer['date']+'T'+offer['startTime']+':00-04:00')
            end = aware(offer['occupiedUntil'])
            return [b['id'] for b in sources
                    if (b['instructor'] == offer['instructor'] or b['location'] == offer['resource'])
                    and interval_conflict(start, end, b['start'], b['end'])]
        return offers, occupied, conflicts

    def test_visible_oct17_noon_revalidates_identical_canonical_interval(self):
        offers, occupied, conflicts = self.visible_offers_and_conflicts()
        noon = next(o for o in offers if o['courseId'] == '209809' and o['startTime'] == '12:00')
        self.assertEqual(noon['occupiedUntil'], '2026-10-17T14:30:00-04:00')
        self.assertEqual(conflicts(noon), [])
        # New facts invalidate the old displayed choice immediately. They do not
        # depend on whether a newly proposed edge now happens to be at 12:30.
        extended = [dict(b, end=self.case.at(17, '12:30')) for b in occupied]
        self.assertEqual(conflicts(noon, extended), [self.anchor['source_event_id']])
        self.anchor['end'] = self.case.at(17, '12:30').isoformat()
        self.assertNotIn('12:00', self.case.starts('209809'))
        self.assertIn('12:30', self.case.starts('209809'))

    def test_visible_skills_revalidates_and_fresh_instructor_overlap_rejects(self):
        offers, occupied, conflicts = self.visible_offers_and_conflicts()
        skills = next(o for o in offers if o['courseId'] == '329495' and o['startTime'] == '12:00')
        self.assertEqual(conflicts(skills), [])
        fresh = dict(occupied[0], id='fresh-instructor-commitment',
                     start=self.case.at(17, '12:15'), end=self.case.at(17, '12:30'),
                     location=':: Wilmington; Shipyard Blvd - C')
        self.assertEqual(conflicts(skills, occupied+[fresh]), ['fresh-instructor-commitment'])
        # The same physical teaching overlap still fails after changing rooms.
        self.case.add(17, '12:15', '12:30', cid='other', resource_override='C')
        self.case.sources[-1]['resource'] = fresh['location']
        self.assertNotIn('12:00', self.case.starts('329495'))

    def test_all_family_display_intervals_match_collision_validation(self):
        # A qualified fixture instructor is used for advanced courses rather than
        # weakening Brian's existing ACLS/PALS exclusion. No production mapping.
        self.case.windows[0]['instructor_name'] = 'Qualified fixture instructor'
        self.case.windows[0]['person_id'] = 'qualified-fixture'
        self.case.coverage[0]['instructor'] = 'Qualified fixture instructor'
        self.anchor['instructor'] = 'Qualified fixture instructor'
        self.case.courses = [dict(course_id=family+'-'+kind, course_family=family,
                                 kind=kind, blended_classroom_skills='blended' if kind=='skills' else 'classroom')
                             for family in ['BLS', 'Heartsaver', 'ARC', 'HSI', 'ACLS', 'PALS', 'USCG', 'Family CPR']
                             for kind in ['skills', 'full']]
        offers, occupied, conflicts = self.visible_offers_and_conflicts()
        self.assertEqual(len({o['courseId'] for o in offers}), 16)
        for offer in offers:
            with self.subTest(course=offer['courseId'], start=offer['startTime']):
                self.assertEqual(conflicts(offer), [])
                if offer['startTime'] == '12:00':
                    extended = [dict(b, end=self.case.at(17, '12:30')) for b in occupied]
                    self.assertTrue(conflicts(offer, extended))

    def test_owner_rule_is_durable_and_extra_reservation_not_added_twice(self):
        self.assertIn('Never append a separate cleanup veto', self.case.policy['occupied_interval_rule'])
        self.anchor['end'] = self.case.at(17, '12:30').isoformat()
        offers, occupied, conflicts = self.visible_offers_and_conflicts()
        next_full = next(o for o in offers if o['courseId'] == '209809' and o['startTime'] == '12:30')
        self.assertEqual(conflicts(next_full), [])
        self.assertEqual(next_full['occupiedUntil'], '2026-10-17T15:00:00-04:00')
        self.assertEqual(occupied[0]['end'], self.case.at(17, '12:30'))


if __name__ == '__main__':
    unittest.main()
