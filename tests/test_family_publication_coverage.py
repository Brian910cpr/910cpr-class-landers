import unittest
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from datetime import datetime, timezone
from scripts.audit_family_publication_coverage import summarize, continuity_incident, parse_arguments, public_landscape_diagnostics_safe
from scripts import audit_family_publication_coverage as audit


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
        payload['dates'][0]['startTimes'][0]['courses'][0]['validUntil'] = payload['validUntil']
        self.assertIsNone(continuity_incident({'bls':summarize(payload,'2026-11-03',now),
            'arc':summarize({},'2026-11-03',now)}))

    def test_individual_expired_or_missing_leases_not_masked_by_global_maximum(self):
        now = datetime(2026, 11, 1, 6, tzinfo=timezone.utc)
        live = '2026-11-01T06:15:00Z'
        courses = [
            {'courseId': 'live', 'offerType': 'dynamic_appointment', 'validUntil': live},
            {'courseId': 'expired', 'offerType': 'dynamic_appointment', 'validUntil': '2026-11-01T06:00:00Z'},
            {'courseId': 'missing', 'offerType': 'dynamic_appointment'},
            {'courseId': 'naive', 'offerType': 'dynamic_appointment', 'validUntil': '2026-11-01T06:15:00'},
            {'courseId': 'seated', 'offerType': 'seated_class'},
        ]
        payload = {'validUntil': live, 'dates': [{'date': '2026-11-03',
            'startTimes': [{'startTime': '09:30', 'courses': courses}]}]}
        summary = summarize(payload, '2026-11-03', now)
        self.assertEqual((summary['dynamicOffers'], summary['liveDynamicOffers'],
                          summary['expiredOrMalformedDynamicOffers'], summary['seatedOffers']), (4, 1, 3, 1))
        self.assertEqual(summary['nextThreeDays']['2026-11-03']['liveDynamicOffers'], 1)
        self.assertEqual(summary['nextThreeDays']['2026-11-03']['expiredOrMalformedDynamicOffers'], 3)
        self.assertEqual(continuity_incident({'arc': summary})['failures'][0]['reason'],
                         'invalid_individual_appointment_leases')
        courses.pop(0)
        self.assertEqual(summarize(payload, '2026-11-03', now)['liveDynamicOffers'], 0)
        self.assertIsNotNone(continuity_incident({'bls': summarize(payload, '2026-11-03', now)}))
        courses[:] = [courses[-1]]
        self.assertIsNone(continuity_incident({'arc': summarize(payload, '2026-11-03', now)}))

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
        self.assertEqual(result['failedWindowReasons'], {'restricted': 1})

    def test_counts_actual_nested_courses_and_does_not_invent_offers(self):
        result = summarize({'counts': {'failed_windows': 0}, 'dates': [
            {'date': '2026-10-14', 'startTimes': [{'startTime': '17:30',
                'courses': [{'courseId': 'a'}, {'courseId': 'b'}]}]}]}, '2026-10-14')
        self.assertFalse(result['coverageAlert'])
        self.assertEqual(result['actualOffers'], 2)
        self.assertEqual(result['dayTimes'], ['17:30'])
        self.assertEqual(result['dayPerCourse'], {'a': 1, 'b': 1})

    def test_three_day_observer_counts_public_candidates_and_scoped_failures_only(self):
        # DST day rollover is a calendar-date operation, never a fixed UTC offset.
        payload = {'counts': {'failed_windows': 2}, 'dates': [
            {'date': '2026-11-01', 'startTimes': [{'startTime': '08:30',
                'courses': [{'courseId': 'bls'}, {'courseId': 'bls'}]}]},
            {'date': '2026-11-02', 'startTimes': [{'startTime': '12:00',
                'courses': [{'courseId': 'heartsaver'}]}]},
            {'date': '2026-11-03', 'startTimes': []},
            {'date': '2026-11-04', 'startTimes': [{'startTime': '15:00',
                'courses': [{'courseId': 'later'}]}]}],
            'reconciliationIssues': [
                {'start': '2026-11-02T11:00:00-05:00',
                 'reason': 'missing directional travel rule'},
                {'start': '2026-11-04T15:00:00-05:00',
                 'reason': 'missing directional travel rule'}]}
        summary = summarize(payload, '2026-11-01')
        days = summary['nextThreeDays']
        self.assertEqual(list(days), ['2026-11-01', '2026-11-02', '2026-11-03'])
        self.assertEqual([days[d]['publishedOffers'] for d in days], [2, 1, 0])
        self.assertEqual([days[d]['failedWindows'] for d in days], [0, 1, 0])
        self.assertEqual(days['2026-11-01']['failedWindowReasons'], {})
        self.assertEqual(days['2026-11-02']['failedWindowReasons'], {'restricted': 1})
        self.assertEqual(days['2026-11-03']['failedWindowReasons'], {})
        self.assertEqual(summary['failedWindowReasons'], {'restricted': 2})
        self.assertEqual(days['2026-11-01']['perCourse'], {'bls': 2})
        self.assertEqual(days['2026-11-02']['publishedTimes'], ['12:00'])
        self.assertTrue(summary['coverageAlert'],
                        'partial coverage must remain a failing health signal')
        self.assertEqual(summary['actualOffers'], 4)
        self.assertNotIn('2026-11-04', days)

    def test_24_hour_lead_explains_cutoff_without_declaring_booking_healthy(self):
        # 18:09 Eastern on Nov 18, policy lead=24h. Nov 19 has potential
        # after-18:09 starts; zero observed offers alone cannot prove a fault.
        now = datetime(2026, 11, 18, 23, 9, tzinfo=timezone.utc)
        payload = {'minimumLeadHours': 24, 'counts': {'failed_windows': 11},
                   'reconciliationIssues': [
                       {'reason': 'missing_directional_travel_rule',
                        'start': '2026-12-07'}]}
        result = summarize(payload, '2026-11-18', now)
        self.assertEqual(result['leadCutoffAtEastern'], '2026-11-19T18:09:00-05:00')
        self.assertEqual(result['dayLeadWindowStatus'], 'entire_day_inside_lead_window')
        self.assertEqual(
            [value['leadWindowStatus'] for value in result['nextThreeDays'].values()],
            ['entire_day_inside_lead_window', 'partly_inside_lead_window',
             'outside_lead_window'])
        self.assertEqual(result['dayOffers'], 0)
        self.assertTrue(result['coverageAlert'], 'known travel uncertainty remains RED')

    def test_global_travel_failures_are_not_mislabeled_as_same_day_lead_outage(self):
        # A past/current day can be fully inside the 24h lead rule while real
        # future travel uncertainty still requires a failing global monitor.
        now = datetime(2026, 11, 18, 23, 9, tzinfo=timezone.utc)
        feed = {'minimumLeadHours': 24, 'counts': {'failed_windows': 1},
                'reconciliationIssues': [
                    {'reason': 'missing_directional_travel_rule', 'start': '2026-12-07'}]}
        current = summarize(feed, '2026-11-18', now)
        self.assertEqual(current['dayLeadWindowStatus'], 'entire_day_inside_lead_window')
        self.assertEqual(current['dayOffers'], 0)
        self.assertEqual(current['dayFailedWindows'], 0)
        self.assertFalse(current['dayCoverageAlert'])
        self.assertTrue(current['coverageAlert'])
        self.assertEqual(current['coverageAlertScope'], 'other_or_unscoped_windows')
        on_failure_day = summarize(feed, '2026-12-07', now)
        self.assertTrue(on_failure_day['dayCoverageAlert'])
        self.assertEqual(on_failure_day['dayFailedWindows'], 1)
        self.assertEqual(on_failure_day['coverageAlertScope'], 'includes_observed_day')
        clear = summarize({'counts': {'failed_windows': 0}}, '2026-11-18', now)
        self.assertFalse(clear['coverageAlert'])
        self.assertEqual(clear['coverageAlertScope'], 'none')

    def test_lead_window_exact_midnight_and_unknown_policy(self):
        # At the exact cutoff, midnight Nov 19 is a legal lead-time boundary.
        now = datetime(2026, 11, 18, 5, tzinfo=timezone.utc)
        result = summarize({'minimumLeadHours': 24}, '2026-11-18', now)
        self.assertEqual(result['nextThreeDays']['2026-11-19']['leadWindowStatus'],
                         'outside_lead_window')
        for bad in (None, '24', -1, True):
            result = summarize({'minimumLeadHours': bad}, '2026-11-18', now)
            self.assertEqual(result['dayLeadWindowStatus'], 'unknown')
            self.assertIsNone(result['leadCutoffAtEastern'])

    def test_live_shipyard_offer_location_is_public_alias_not_internal_room(self):
        # Verify only browser-visible offer fields. No source ID or attendee
        # information is copied to monitoring artifacts.
        payload = {'dates': [{'date': '2026-11-24', 'startTimes': [{
            'startTime': '14:00', 'courses': [
                {'courseId': 'acls', 'offerType': 'seated_class',
                 'location': 'Wilmington; Shipyard Blvd'},
                {'courseId': 'other', 'location': 'Other Approved Venue'}]}]}]}
        result = summarize(payload, '2026-11-24')
        self.assertTrue(result['publicShipyardAliasSafe'])
        self.assertEqual(result['shipyardOffersChecked'], 1)
        for internal in (':: Wilmington; Shipyard Blvd - B',
                         '4018 Shipyard Blvd, Room B, 910CPR Office',
                         ':: Wilmington; Shipyard Blvd'):
            with self.subTest(internal=internal):
                payload['dates'][0]['startTimes'][0]['courses'][0]['location'] = internal
                result = summarize(payload, '2026-11-24')
                self.assertFalse(result['publicShipyardAliasSafe'])
                self.assertEqual(result['shipyardOffersChecked'], 1)
        empty = summarize({'dates': []}, '2026-11-24')
        self.assertTrue(empty['publicShipyardAliasSafe'])
        self.assertEqual(empty['shipyardOffersChecked'], 0,
                         'empty inventory is no proof of a public offer')

    def test_hosted_public_diagnostic_metadata_is_strictly_redacted(self):
        # The host observer must not echo private staff names, room labels,
        # client venues or operational time bounds into public error reports.
        safe = {'counts': {'failed_windows': 1}, 'reconciliationIssues': [
            {'reason': 'missing_directional_travel_rule', 'start': '2026-12-06'}]}
        result = summarize(safe, '2026-12-06')
        self.assertTrue(result['publicDiagnosticsSafe'])
        self.assertTrue(result['coverageAlert'])
        self.assertEqual(result['dayFailedWindows'], 1)
        self.assertEqual(result['failedWindowReasons'],
                         {'missing_directional_travel_rule': 1})
        for bad in [
            {'reason': 'missing directional travel rule: Client->Room B',
             'start': '2026-12-06T00:00:00-05:00',
             'instructor': 'Sensitive Instructor', 'resource': 'Sensitive Room'},
            {'reason': 'missing_directional_travel_rule',
             'start': '2026-12-06T00:00:00-05:00'},
            {'reason': 'unapproved_free_text_reason', 'start': '2026-12-06'},
            {'reason': 'missing_directional_travel_rule',
             'start': '2026-12-06', 'end': '2026-12-06T07:30:00-05:00'},
        ]:
            with self.subTest(bad=tuple(bad)):
                reported = summarize({'reconciliationIssues': [bad]}, '2026-12-06')
                self.assertFalse(reported['publicDiagnosticsSafe'])
        self.assertTrue(summarize({'reconciliationIssues': []}, '2026-12-06')['publicDiagnosticsSafe'])


    def test_unsafe_diagnostic_text_never_reaches_saved_summary(self):
        secret = 'fixture internal venue and instructor identifier'
        summary = summarize({'counts': {'failed_windows': 2}, 'reconciliationIssues': [
            {'reason': secret, 'start': '2026-11-25'},
            {'reason': {'private': secret}, 'start': '2026-11-25'}]}, '2026-11-25')
        self.assertFalse(summary['publicDiagnosticsSafe'])
        self.assertTrue(summary['coverageAlert'])
        self.assertEqual(summary['failedWindowReasons'], {'restricted': 2})
        self.assertEqual(summary['nextThreeDays']['2026-11-25']['failedWindowReasons'],
                         {'restricted': 2})
        self.assertNotIn(secret, json.dumps(summary))
        for malformed in (None, {'reason': secret}, [None, secret]):
            result = summarize({'reconciliationIssues': malformed}, '2026-11-25')
            self.assertFalse(result['publicDiagnosticsSafe'])
            self.assertNotIn(secret, json.dumps(result))

    def test_host_observer_rejects_public_landscape_private_diagnostics(self):
        safe = {
            "cells": [{"date": "2026-11-25", "startTime": "09:30",
                       "courseId": "209806", "result": "suppressed",
                       "reasons": ["availability_restricted"]}],
            "laneCells": [{"date": "2026-11-25", "startTime": "09:30",
                           "laneId": "enrollware", "sourceLabel": "Committed class",
                           "items": [{"title": "Occupied interval"}]}],
            "dailyTruth": {"2026-11-25": {"classes": [{
                "courseName": "Committed class", "registeredCount": "Restricted",
                "start": "2026-11-25T09:30:00-05:00",
                "end": "2026-11-25T11:30:00-05:00"}],
                "hardBlocks": [{"label": "Unavailable time",
                                "start": "2026-11-25T09:30:00-05:00",
                                "end": "2026-11-25T11:30:00-05:00"}]}},
            "reconciliationIssues": [{
                "date": "2026-11-25", "code": "AVAILABILITY_COVERAGE_UNKNOWN",
                "reason": "Availability requires operational review",
                "blocksSynthesis": True}],
            "sourcePages": {"bls": {
                "generatedAt": "2026-11-18T15:00:00Z",
                "rejectionReasonCounts": {"restricted": 2},
                "layeredLandscape": {
                    "sources": [{"role": "blocking", "start": "2026-11-25T09:30:00",
                                 "end": "2026-11-25T11:30:00"}],
                    "occupiedBlocks": []}}},
        }
        self.assertTrue(public_landscape_diagnostics_safe(safe))
        for category, changes in [
            ("external source paths", {"operationalLaneSources": {"private": "/private/path"}}),
            ("raw issue", {"reconciliationIssues": [{
                "reason": "private instructor private trip", "resource": "Internal room"}]}),
            ("raw intake lane", {"laneCells": [{
                "date": "2026-11-25", "startTime": "09:30",
                "laneId": "enrollware", "items": [{
                    "title": "Occupied interval", "sessionId": "restricted"}]}]}),
            ("raw canonical names", {"dailyTruth": {"2026-11-25": {
                "hardBlocks": [], "classes": [{
                    "courseName": "Named private session",
                    "start": "2026-11-25T09:30:00-05:00", "end": "2026-11-25T11:30:00-05:00",
                    "registeredCount": 1, "canonicalSessionId": "restricted"}]}}}),
            ("internal offer trace", {"cells": [{
                "date": "2026-11-25", "startTime": "09:30",
                "courseId": "209806", "result": "seated",
                "sessionId": "private", "edgeIds": ["private"]}]}),
            ("nonanonymous source page", {"sourcePages": {"bls": {
                "rejectionReasonCounts": {"private_name": 1},
                "layeredLandscape": {"sources": [{
                    "sourceId": "private", "role": "blocking",
                    "start": "2026-11-25T09:30:00",
                    "end": "2026-11-25T11:30:00"}]}}}}),
        ]:
            with self.subTest(category=category):
                self.assertFalse(public_landscape_diagnostics_safe({**safe, **changes}))

    def test_empty_day_is_unknown_coverage_not_inferred_occupancy(self):
        result = summarize({'counts': {'failed_windows': 0}}, '2026-10-14')
        self.assertEqual(result['dayOffers'], 0)
        self.assertFalse(result['coverageAlert'])


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

class ScheduledObservationDateTests(unittest.TestCase):
    def test_scheduled_command_uses_operational_day_preserves_override_and_keeps_alerts(self):
        observed = datetime(2026, 11, 13, 2, 0, tzinfo=timezone.utc)

        class FixedClock(datetime):
            @classmethod
            def now(cls, tz=None):
                return observed.astimezone(tz) if tz is not None else observed.replace(tzinfo=None)

        feed = {'generatedAt': observed.isoformat(), 'validUntil': '2026-11-13T02:10:00Z',
                'counts': {'failed_windows': 1}, 'dates': [
                    {'date': '2026-11-12', 'startTimes': [{'startTime': '22:00', 'courses': [
                        {'courseId': 'fixture', 'offerType': 'dynamic_appointment', 'validUntil': '2026-11-13T02:10:00Z'},
                        {'courseId': 'second-fixture', 'offerType': 'dynamic_appointment', 'validUntil': '2026-11-13T02:10:00Z'}]}]},
                    {'date': '2026-10-14', 'startTimes': [{'startTime': '09:00', 'courses': [
                        {'courseId': 'historical-fixture', 'offerType': 'dynamic_appointment', 'validUntil': '2026-11-13T02:10:00Z'}]}]}]}
        landscape = {'cells': [{'date': '2026-11-12', 'result': 'fixture-current'},
                               {'date': '2026-10-14', 'result': 'fixture-historical'}], 'sourcePages': {}}

        def read_fixture(url, timeout):
            self.assertEqual(timeout, 30)
            self.assertIn('coverage=' + observed.isoformat(), url)
            return io.BytesIO(json.dumps(landscape if 'scheduling_landscape.json' in url else feed).encode())

        with TemporaryDirectory() as folder:
            for override, expected_day, offers, cell in [
                    ([], '2026-11-12', 2, 'fixture-current'),
                    (['--day', '2026-10-14'], '2026-10-14', 1, 'fixture-historical')]:
                with self.subTest(override=override):
                    output = Path(folder) / 'observation.json'
                    argv = ['audit', '--live', '--continuity', '--output', str(output), *override]
                    with patch('sys.argv', argv), patch.object(audit, 'datetime', FixedClock), \
                            patch.object(audit, 'urlopen', side_effect=read_fixture) as mocked, \
                            patch('sys.stdout', new_callable=io.StringIO):
                        self.assertEqual(audit.main(), 1, 'real coverage alerts must remain failures')
                    result = json.loads(output.read_text(encoding='utf-8'))
                    self.assertEqual(result['observedAt'], observed.isoformat())
                    self.assertEqual(result['mode'], 'live-read-only')
                    self.assertEqual(mocked.call_count, len(audit.FAMILIES) + 1)
                    for family in result['families'].values():
                        self.assertEqual((family['day'], family['dayOffers']), (expected_day, offers))
                        self.assertTrue(family['coverageAlert'])
                    self.assertEqual(result['landscape']['dayCellResults'], {cell: 1})
                    self.assertIsNone(result['incident'])


if __name__ == '__main__':
    unittest.main()
