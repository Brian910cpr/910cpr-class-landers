import json
import unittest
from datetime import datetime

from scripts.audit_historical_source_recovery import exclusion, normalized, parse_date, registration_id, summarize


class SourceRecoveryTests(unittest.TestCase):
    cutoff = datetime.fromisoformat('2026-09-14T00:00:00-04:00')

    def row(self, **changes):
        result = {'session_id': 123, 'course': 'AHA BLS Provider', 'start': '2025-01-01 09:00:00',
                  'end': '2025-01-01 13:00:00', 'location': ':: Public Center',
                  'register_url': 'https://example.enrollware.com/enroll?id=456', 'students': 0}
        result.update(changes)
        return result

    def test_dates_refuse_unknown_and_dst_ambiguity(self):
        for value in ['unknown', None, '2026-03-08 02:30:00', '2026-11-01 01:30:00']:
            self.assertIsNone(parse_date(value))
        self.assertEqual(parse_date('2026-07-01T13:00:00Z').hour, 9)

    def test_elapsed_requires_valid_positive_duration_and_end_before_cutoff(self):
        for end in ['2025-01-01 09:00:00', '2025-01-01 08:00:00', None]:
            self.assertEqual(exclusion(normalized(self.row(end=end)), self.cutoff), 'invalid_or_ambiguous_timing')
        self.assertEqual(exclusion(normalized(self.row(end=self.cutoff)), self.cutoff), 'not_elapsed_at_cutoff')

    def test_registration_identity_validates_host_and_unique_id(self):
        self.assertEqual(registration_id(self.row()['register_url']), '456')
        for url in ['https://enrollware.com.evil.test/enroll?id=456',
                    'https://example.enrollware.com/enroll?id=4&id=5',
                    'https://example.enrollware.com/enroll?id=abc', 'javascript:alert(1)']:
            self.assertIsNone(registration_id(url))

    def test_private_client_from_workbook_overrides_stripped_json(self):
        row = self.row()
        source = normalized(self.row(client='PRIVATE CLIENT'))
        result, _ = summarize([row], {'123'}, set(), self.cutoff, {'123': [source]})
        self.assertEqual(result['exclusive_classification'], {'client_present_review': 1})
        self.assertNotIn('PRIVATE CLIENT', json.dumps(result))

    def test_missing_and_mismatched_workbook_never_approve(self):
        for workbook in [{}, {'123': [normalized(self.row(location='Different'))]}]:
            result, _ = summarize([self.row()], set(), set(), self.cutoff, workbook)
            self.assertEqual(result['exclusive_classification'], {'workbook_provenance_unresolved': 1})

    def test_duplicate_aliases_require_identity_review(self):
        result, _ = summarize([self.row(), self.row(session_id=124)], {'123','999'}, {'123'}, self.cutoff)
        self.assertEqual(result['exclusive_classification'], {'duplicate_or_conflicting_identity': 2})
        self.assertEqual(result['urls']['legacy_html_without_source_id'], 1)
        self.assertEqual(result['urls']['preservable_legacy_url_percent'], 50)

    def test_counts_preserve_zero_enrollment_without_claiming_completion(self):
        result, _ = summarize([self.row()], {'123'}, set(), self.cutoff)
        self.assertEqual(result['overlapping_flags']['zero_enrollment'], 1)
        self.assertEqual(result['exclusive_classification'], {'preliminary_public_candidate_requires_review': 1})
        self.assertEqual(sum(c['source_rows'] for c in result['by_course_label_sha256'].values()), 1)

    def test_location_prefix_and_output_privacy(self):
        result, _ = summarize([self.row(location='Private Office', course='PRIVATE PERSON COURSE',
                                       instructor='PRIVATE INSTRUCTOR')], {'123'}, set(), self.cutoff)
        self.assertEqual(result['exclusive_classification'], {'non_public_location_review': 1})
        for secret in ['Private Office', 'PRIVATE PERSON', 'PRIVATE INSTRUCTOR', 'enrollware.com']:
            self.assertNotIn(secret, json.dumps(result))


if __name__ == '__main__':
    unittest.main()
