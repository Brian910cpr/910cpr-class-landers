"""Canonical office labels must retain occupancy without inventing offsite travel."""
import copy
import unittest
from scripts.block_start_time_selector import build_occupancy
from scripts.layered_selector_adapter import aware
from tests.test_layered_publication_adapter import LayeredPublicationTests


class CanonicalOfficeAliasTests(unittest.TestCase):
    def fixture(self, location):
        case = LayeredPublicationTests()
        case.setUp()
        loaded = {'location_resource_map': case.resources, 'canonical_demand': {'sessions': [{
            'session_status': 'scheduled', 'canonical_session_id': 'fixture-canonical',
            'start_at': case.at(11, '12:00').isoformat(),
            'end_at': case.at(11, '13:00').isoformat(),
            'location_name': location, 'lead_instructor_name': 'Brian Ennis',
            'course_id': '210549', 'count_available': True, 'active_registration_count': 1,
        }]}}
        case.sources = build_occupancy(loaded, {}, allow_unresolved=True)
        return case

    def test_canonical_office_alias_preserves_occupied_interval_and_edges(self):
        case = self.fixture('910CPR Office - Shipyard Blvd')
        calculation = case.calculation()
        self.assertEqual(calculation['counts']['failed_windows'], 0)
        self.assertEqual(case.starts('329495'), {'11:00', '13:00'})
        self.assertEqual(case.starts('209809'), {'09:30', '13:00'})
        source = calculation['projected_sources'][0]
        self.assertEqual(source['source_event_id'], 'fixture-canonical')
        self.assertEqual(source['active_registration_count'], 1)
        self.assertEqual(aware(source['start']), case.at(11, '12:00'))
        self.assertEqual(aware(source['end']), case.at(11, '13:00'))

    def test_unmapped_offsite_still_fails_closed(self):
        case = self.fixture('Unknown offsite classroom')
        self.assertEqual(case.calculation()['counts']['failed_windows'], 1)
        self.assertFalse(case.starts('329495'))

    def test_old_map_reproduces_missing_travel_failure(self):
        case = self.fixture('910CPR Office - Shipyard Blvd')
        resources = copy.deepcopy(case.resources)
        resources['locations'][0]['aliases'].remove('910CPR Office - Shipyard Blvd')
        # Normalize the exact same canonical source with the previous map.
        case.resources = resources
        case.sources[0].pop('location_resolution')
        case.sources[0]['location'] = '910CPR Office - Shipyard Blvd'
        case.sources[0]['resource'] = '910CPR Office - Shipyard Blvd'
        result = case.calculation()
        self.assertEqual(result['counts']['failed_windows'], 1)
        self.assertIn('missing directional travel rule', result['issues'][0]['reason'])


if __name__ == '__main__':
    unittest.main()
