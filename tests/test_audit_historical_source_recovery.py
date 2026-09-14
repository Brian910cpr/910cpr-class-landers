import json
import unittest
from datetime import datetime

from scripts.audit_historical_source_recovery import (
    exclusion, normalized, parse_date, reconcile_identities, registration_id, summarize,
)


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


class IdentityReconciliationTests(unittest.TestCase):
    def old(self, **changes):
        row = {'session_id': 123, 'course': 'AHA BLS', 'start': '2025-01-01 09:00:00',
               'end': '2025-01-01 13:00:00', 'location': ':: Public Center',
               'register_url': 'https://example.enrollware.com/enroll?id=456'}
        row.update(changes)
        return row

    def current(self, **changes):
        row = {'session_id': 456, 'course_name': 'AHA BLS', 'start_at': '2025-01-01T14:00:00Z',
               'end_at': '2025-01-01T18:00:00Z', 'location_name': ':: Public Center',
               'registration_url': 'https://example.enrollware.com/enroll?id=456', 'session_status': 'past'}
        row.update(changes)
        return row

    def reason(self, old=None, current=None):
        result = reconcile_identities(old or [self.old()], current or [self.current()])
        return result['exclusive_historical_dispositions']

    def test_cross_namespace_identity_and_equivalent_instants_match(self):
        result = reconcile_identities([self.old()], [self.current()])
        self.assertEqual(result['exclusive_historical_dispositions'], {'shared_identity_facts_match': 1})
        self.assertEqual(result['current_source_status_labels'], {'past': 1})
        self.assertIsNone(result['publication_authorized_count'])

    def test_changed_facts_are_flagged_without_replacing_historical_facts(self):
        old = self.old()
        result = reconcile_identities([old], [self.current(course_name='AHA ACLS', location_name='Elsewhere')])
        self.assertEqual(result['exclusive_historical_dispositions'], {'shared_identity_facts_changed': 1})
        self.assertEqual(result['overlapping_changed_fields_in_unique_pairs'], {'course': 1, 'location': 1})
        self.assertEqual(result['unique_pair_difference_sets'], {'course+location': 1})
        self.assertEqual(old, self.old())

    def test_duplicate_links_or_session_ids_never_choose_first_match(self):
        self.assertEqual(self.reason([self.old(), self.old(session_id=124)]), {'ambiguous_historical_identity': 2})
        self.assertEqual(self.reason(current=[self.current(), self.current(session_id=457)]), {'ambiguous_current_identity': 1})
        self.assertEqual(self.reason(current=[self.current(), self.current(registration_url='https://example.enrollware.com/enroll?id=789')]),
                         {'ambiguous_current_identity': 1})

    def test_invalid_timing_is_not_treated_as_matching_complete_facts(self):
        self.assertEqual(self.reason([self.old(start=None)], [self.current(start_at=None)]),
                         {'shared_identity_invalid_timing': 1})

    def test_missing_identity_is_distinct_from_missing_current_record(self):
        result = reconcile_identities([self.old(), self.old(session_id=124, register_url='invalid')], [])
        self.assertEqual(result['exclusive_historical_dispositions'], {
            'invalid_historical_registration_identity': 1, 'registration_identity_absent_from_current': 1})

    def test_orphan_registration_match_requires_review(self):
        pages = {'docs/classes/999.html': '<a href="https://example.enrollware.com/enroll?id=456&amp;x=1">Book</a>'}
        result = reconcile_identities([], [self.current()], pages)
        self.assertEqual(result['orphan_dispositions'], {'current_source_link_match_requires_historical_facts_review': 1})
        self.assertIsNone(result['publication_authorized_count'])
        self.assertNotIn('999', result['orphans_by_path_sha256'])

    def test_orphan_multiple_missing_and_unmatched_links_are_separate(self):
        pages = {'one': '<a href="https://example.enrollware.com/enroll?id=111">a</a>',
                 'two': '<a href="https://example.enrollware.com/enroll?id=456">a</a><a href="https://example.enrollware.com/enroll?id=457">b</a>',
                 'three': '<a href="https://enrollware.com.evil.test/enroll?id=456">c</a>'}
        result = reconcile_identities([self.old()], [self.current()], pages)
        self.assertEqual(result['orphan_dispositions'], {'multiple_registration_identities': 1,
            'no_registration_link': 1, 'registration_identity_absent_from_both_sources': 1})
        self.assertEqual(sum(result['orphan_dispositions'].values()), 3)

    def test_private_fields_and_statuses_do_not_leak(self):
        private = 'PRIVATE PERSON AND CLIENT'
        old = self.old(course=private, location=private, instructor=private)
        current = self.current(client=private, session_status=private)
        result = reconcile_identities([old], [current], {'private-path': '<p>' + private + '</p>'})
        serialized = json.dumps(result)
        for value in (private, 'private-path', 'enrollware.com'):
            self.assertNotIn(value, serialized)
        self.assertEqual(result['current_source_status_labels'], {'unrecognized': 1})

    def test_source_status_is_only_evidence_and_never_authorizes_publication(self):
        for status in ('cancelled', 'completed', 'past', ''):
            result = reconcile_identities([self.old()], [self.current(session_status=status)])
            self.assertIsNone(result['publication_authorized_count'])
            self.assertEqual(sum(result['current_source_status_labels'].values()), 1)

    def test_invalid_current_id_is_an_explicit_exception(self):
        self.assertEqual(self.reason(current=[self.current(session_id='not-an-id')]), {'invalid_current_session_id': 1})

    def test_orphan_duplicate_source_id_is_ambiguous_even_when_link_is_unique(self):
        current = [self.current(), self.current(registration_url='https://example.enrollware.com/enroll?id=789')]
        pages = {'orphan': '<a href="https://example.enrollware.com/enroll?id=456">a</a>'}
        result = reconcile_identities([], current, pages)
        self.assertEqual(result['orphan_dispositions'], {'ambiguous_source_registration_identity': 1})


if __name__ == '__main__':
    unittest.main()
