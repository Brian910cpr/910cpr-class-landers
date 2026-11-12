import unittest
from datetime import datetime, timezone
from scripts.audit_family_publication_coverage import summarize, continuity_incident, parse_arguments


class ObservationDateTests(unittest.TestCase):
    def day(self, instant, *args):
        return parse_arguments(['--output','fixture.json',*args],datetime.fromisoformat(instant)).day

    def test_omitted_date_uses_new_york_not_utc_date(self):
        self.assertEqual(self.day('2026-11-10T02:43:47+00:00'),'2026-11-09')
        self.assertEqual(self.day('2026-11-10T04:59:59+00:00'),'2026-11-09')
        self.assertEqual(self.day('2026-11-10T05:00:00+00:00'),'2026-11-10')

    def test_explicit_historical_date_is_preserved_exactly(self):
        self.assertEqual(self.day('2026-11-10T02:43:47+00:00','--day','2026-10-14'),'2026-10-14')

    def test_dst_changes_do_not_use_fixed_offset_or_change_date_at_clock_transition(self):
        cases={
            '2026-03-08T04:59:59+00:00':'2026-03-07',
            '2026-03-08T05:00:00+00:00':'2026-03-08',
            '2026-03-08T06:59:59+00:00':'2026-03-08',
            '2026-03-08T07:00:00+00:00':'2026-03-08',
            '2026-03-09T04:00:00+00:00':'2026-03-09',
            '2026-11-01T03:59:59+00:00':'2026-10-31',
            '2026-11-01T04:00:00+00:00':'2026-11-01',
            '2026-11-01T05:59:59+00:00':'2026-11-01',
            '2026-11-01T06:00:00+00:00':'2026-11-01',
            '2026-11-02T04:59:59+00:00':'2026-11-01',
            '2026-11-02T05:00:00+00:00':'2026-11-02',
        }
        for instant,day in cases.items():
            with self.subTest(instant=instant):self.assertEqual(self.day(instant),day)


class WindowDiagnosticTests(unittest.TestCase):
    def test_preserves_direction_and_bounds_but_not_source_or_instructor(self):
        issue={'start':'2026-11-10T02:00:00Z','end':'2026-11-10T03:00:00Z',
               'reason':'missing directional travel rule: MedNorth->Shipyard B',
               'instructor':'PRIVATE INSTRUCTOR','source_id':'PRIVATE SOURCE',
               'student':{'email':'private@example.invalid'},'raw':'PRIVATE RECORD'}
        result=summarize({'counts':{'failed_windows':7},'reconciliationIssues':[issue,issue]},'2026-11-09',family='bls')
        diag=result['reconciliationWindowDiagnostics']
        self.assertEqual(diag['uniqueIssueContexts'],1)
        self.assertEqual(diag['records'],[{'family':'bls','start':'2026-11-10T02:00:00+00:00',
            'end':'2026-11-10T03:00:00+00:00','date':'2026-11-09',
            'reason':'missing_directional_travel_rule','fromLocation':'MedNorth','toLocation':'Shipyard B'}])
        self.assertNotIn('PRIVATE',str(diag));self.assertNotIn('private@',str(diag))
        self.assertTrue(result['coverageAlert'])
        self.assertEqual(result['failedWindowReasons'][issue['reason']],2)
        self.assertEqual(result['dayFailedWindows'],0)  # Existing literal-prefix semantics retained.

    def test_bounded_deduplicated_context_does_not_change_aggregates(self):
        issues=[{'reason':f'missing directional travel rule: Venue {i}->Shipyard B'} for i in range(55)]
        result=summarize({'counts':{'failed_windows':55},'reconciliationIssues':issues+issues},'2026-11-09')
        diag=result['reconciliationWindowDiagnostics']
        self.assertEqual(len(diag['records']),50);self.assertEqual(diag['uniqueIssueContexts'],55)
        self.assertTrue(diag['truncated']);self.assertEqual(sum(result['failedWindowReasons'].values()),110)
        self.assertTrue(result['coverageAlert'])

    def test_missing_invalid_bounds_and_unknown_errors_are_not_invented_or_disclosed(self):
        for issue in [{}, {'start':'bad','end':'2026-11-10T02:00:00','reason':'private@example.invalid failure'},
                      {'reason':'missing directional travel rule: unsafe\nname->B'}]:
            diag=summarize({'reconciliationIssues':[issue]},'2026-11-09')['reconciliationWindowDiagnostics']
            self.assertEqual(diag['records'],[{'family':None,'reason':'unclassified_reconciliation_issue'}])
        self.assertEqual(summarize({},'2026-11-09')['reconciliationWindowDiagnostics']['records'],[])


class CoverageCheckpointTests(unittest.TestCase):
    def test_remaining_seated_classes_do_not_downgrade_missing_appointments(self):
        feeds={family:summarize({'dates':[{'date':'2026-11-03','startTimes':[
            {'startTime':'09:30','courses':[{'courseId':'existing','offerType':'seated_class'}]}]}]},'2026-11-03')
            for family in ('bls','heartsaver')}
        incident=continuity_incident(feeds)
        self.assertEqual(incident['priority'],'P0')
        self.assertEqual({f['family'] for f in incident['failures']},{'bls','heartsaver'})
        self.assertEqual(incident['recovery_owner'],'Codex')

    def test_expired_dynamic_inventory_is_p0_but_other_empty_families_are_not(self):
        now=datetime(2026,11,1,6,tzinfo=timezone.utc)
        payload={'validUntil':'2026-11-01T05:59:00Z','dates':[{'date':'2026-11-03',
            'startTimes':[{'startTime':'09:30','courses':[{'courseId':'skills','offerType':'dynamic_appointment'}]}]}]}
        incident=continuity_incident({'bls':summarize(payload,'2026-11-03',now)})
        self.assertEqual(incident['failures'][0]['reason'],'expired_dynamic_appointments')
        payload['validUntil']='2026-11-01T06:15:00Z'
        self.assertIsNone(continuity_incident({'bls':summarize(payload,'2026-11-03',now),
            'arc':summarize({},'2026-11-03',now)}))

    def test_expired_feed_is_detected_while_seated_counts_remain_separate(self):
        now=datetime(2026,10,12,3,tzinfo=timezone.utc)
        payload={'validUntil':'2026-10-12T02:59:59Z','dates':[{'date':'2026-10-14',
            'startTimes':[{'startTime':'17:30','courses':[{'courseId':'skills','offerType':'seated_class'},
                {'courseId':'other','offerType':'dynamic_appointment'}]}]}]}
        result=summarize(payload,'2026-10-14',now)
        self.assertTrue(result['publicationExpired'])
        self.assertEqual((result['dynamicOffers'],result['seatedOffers']),(1,1))
        payload['validUntil']='2026-10-12T03:15:00Z'
        self.assertFalse(summarize(payload,'2026-10-14',now)['publicationExpired'])
        for value in ('bad','2026-10-12T03:15:00',None):
            payload['validUntil']=value
            self.assertTrue(summarize(payload,'2026-10-14',now)['publicationExpired'])

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
