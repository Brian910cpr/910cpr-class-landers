import unittest
from scripts.generate_dynamic_offers import selected_availability_windows
from scripts.block_start_time_selector import selected_public_page_live_windows


class GoogleOnlyAvailabilityTests(unittest.TestCase):
    def block(self, source):
        return dict(availability_status='available', source_type=source,
                    start_datetime='2026-10-16T09:00:00-04:00',
                    end_datetime='2026-10-16T12:00:00-04:00',
                    instructor_name='Fixture Instructor', location_name='Fixture Room')

    def test_only_google_explicit_and_inverse_windows_are_selected(self):
        blocks=[self.block(source) for source in
                ['google_calendar', 'inverse_google_calendar', 'manual', 'UNKNOWN']]
        payload={'availability_blocks': blocks}
        selected, stats=selected_availability_windows({'live_availability_snapshot':payload})
        self.assertEqual(len(selected),2)
        public, diagnostics=selected_public_page_live_windows(payload,{})
        self.assertEqual(len(public),2)
        self.assertFalse(stats['availability_fallback_used'])

    def test_missing_failed_or_empty_google_never_uses_legacy_windows(self):
        legacy={'availability_blocks':[self.block('manual')]}
        for payload in [None, [], {'availability_blocks':[]},
                        {'availability_blocks':[self.block('manual')]}]:
            with self.subTest(payload=payload):
                selected,stats=selected_availability_windows(dict(
                    live_availability_snapshot=payload, instructor_availability=legacy))
                self.assertEqual(selected,[])
                self.assertFalse(stats['availability_fallback_used'])
                self.assertEqual(stats['legacy_available_blocks_read'],0)
