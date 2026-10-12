import unittest
from scripts.audit_family_publication_coverage import summarize


class CoverageCheckpointTests(unittest.TestCase):
    def test_failed_window_alerts_even_when_thousands_of_offers_exist(self):
        result = summarize({'counts': {'failed_windows': 1},
            'reconciliationIssues': [{'start': '2026-10-14T07:45:00-04:00',
                'reason': 'missing directional travel rule'}]}, '2026-10-14')
        self.assertTrue(result['coverageAlert'])
        self.assertEqual(result['dayFailedWindows'], 1)
        self.assertEqual(result['failedWindowReasons'], {'missing directional travel rule': 1})

    def test_counts_actual_nested_courses_and_does_not_invent_offers(self):
        result = summarize({'counts': {'failed_windows': 0}, 'dates': [
            {'date': '2026-10-14', 'startTimes': [{'startTime': '17:30',
                'courses': [{'courseId': 'a'}, {'courseId': 'b'}]}]}]}, '2026-10-14')
        self.assertFalse(result['coverageAlert'])
        self.assertEqual(result['actualOffers'], 2)
        self.assertEqual(result['dayTimes'], ['17:30'])
        self.assertEqual(result['dayPerCourse'], {'a': 1, 'b': 1})

    def test_empty_day_is_unknown_coverage_not_inferred_occupancy(self):
        result = summarize({'counts': {'failed_windows': 0}}, '2026-10-14')
        self.assertEqual(result['dayOffers'], 0)
        self.assertFalse(result['coverageAlert'])


if __name__ == '__main__':
    unittest.main()
