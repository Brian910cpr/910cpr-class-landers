from datetime import datetime
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.anchor_state import promote_seated_sessions
from scripts.layered_day_cache import cached_calculate, pack
from scripts.layered_publication_adapter import calculate, publish
from scripts.layered_selector_adapter import aware
from scripts.block_start_time_selector import build_occupancy
from scripts.canonical_scheduling_demand import resolve_canonical_demand, summarize_positive_v1_attribution


def occurrence(**overrides):
    row = {
        "session_id": "enrollware-row",
        "course_id": "359474",
        "course_key": "aha_bls_renewal",
        "start_at": "2026-09-14T11:15:00-04:00",
        "end_at": "2026-09-14T13:15:00-04:00",
        "location_name": ":: Wilmington; Shipyard Blvd - B",
        "lead_instructor_name": "Brian Ennis",
        "public_direct_booking": True,
    }
    row.update(overrides)
    return row


def demand(**overrides):
    row = {
        "canonical_session_id": "durable-sep-14-bls-renewal",
        "external_class_id": None,
        "external_course_id": "359474",
        "course_key": "aha_bls_renewal",
        "start_at": "2026-09-14T11:15:00-04:00",
        "end_at": "2026-09-14T13:15:00-04:00",
        "location_name": "Wilmington Shipyard Blvd B",
        "lead_instructor_name": "Brian Ennis",
        "active_registration_count": 1,
        "demand_basis": "canonical_active_registrations",
    }
    row.update(overrides)
    return row


class CanonicalSchedulingDemandTests(unittest.TestCase):
    def test_sep_14_regression_matches_without_inventing_class_id(self):
        sessions, audit = resolve_canonical_demand([occurrence()], [demand()])
        self.assertEqual("durable-sep-14-bls-renewal", sessions[0]["canonical_session_id"])
        self.assertEqual(1, sessions[0]["active_registration_count"])
        self.assertNotIn("external_class_id", sessions[0])
        self.assertEqual("strict_occurrence_identity", audit[0]["match_basis"])
        self.assertEqual(1, len(promote_seated_sessions(sessions)))

    def test_exact_external_class_id_wins(self):
        rows = [occurrence(session_id="13800001"), occurrence(session_id="13800002")]
        sessions, audit = resolve_canonical_demand(rows, [demand(external_class_id="13800002")])
        self.assertNotIn("canonical_session_id", sessions[0])
        self.assertEqual("durable-sep-14-bls-renewal", sessions[1]["canonical_session_id"])
        self.assertEqual("external_class_id", audit[0]["match_basis"])

    def test_ambiguous_fallback_fails_closed(self):
        sessions, audit = resolve_canonical_demand([occurrence(session_id="a"), occurrence(session_id="b")], [demand()])
        self.assertFalse(any("canonical_session_id" in row for row in sessions))
        self.assertEqual("ambiguous", audit[0]["result"])
        self.assertEqual(2, audit[0]["candidate_count"])

    def test_add_increment_cancel_and_move_recompute_both_occurrences(self):
        old = occurrence(session_id="old", start_at="2026-09-14T11:15:00-04:00")
        new = occurrence(session_id="new", start_at="2026-09-15T11:15:00-04:00")
        first, _ = resolve_canonical_demand([old], [demand(active_registration_count=1)])
        second, _ = resolve_canonical_demand([old], [demand(active_registration_count=2)])
        cancelled, _ = resolve_canonical_demand([old], [demand(active_registration_count=0)])
        moved, _ = resolve_canonical_demand(
            [old, new],
            [demand(active_registration_count=0), demand(canonical_session_id="new-durable", start_at="2026-09-15T11:15:00-04:00")],
        )
        self.assertEqual(1, promote_seated_sessions(first)[0]["registered_count"])
        self.assertEqual(2, promote_seated_sessions(second)[0]["registered_count"])
        self.assertEqual([], promote_seated_sessions(cancelled))
        self.assertEqual(["new"], [row["session_id"] for row in promote_seated_sessions(moved)])

    def test_multiple_rows_in_same_window_do_not_all_promote(self):
        rows = [occurrence(session_id="bls"), occurrence(session_id="heartcode", course_id="210549", course_key="aha_bls_heartcode")]
        sessions, _ = resolve_canonical_demand(rows, [demand(external_class_id="bls")])
        self.assertEqual(["bls"], [row["session_id"] for row in promote_seated_sessions(sessions)])

    def test_private_and_unlisted_canonical_identity_overrides_legacy_public_route(self):
        for visibility in ("private", "unlisted", "internal"):
            with self.subTest(visibility=visibility):
                rows, audit = resolve_canonical_demand(
                    [occurrence(public_direct_booking=True, visibility="public")],
                    [demand(visibility=visibility, registration_status="open")],
                )
                row = rows[0]
                self.assertEqual(visibility, row["visibility"])
                self.assertFalse(row["public_direct_booking"])
                self.assertEqual("closed", row["registration_status"])
                self.assertEqual("canonical_class_sessions", row["registration_status_source"])
                # Privacy cannot erase the registered operational commitment.
                self.assertEqual(1, row["active_registration_count"])
                self.assertEqual("current", row["demand_status"])
                self.assertEqual("matched", audit[0]["result"])

    def test_unlisted_visibility_survives_stale_start_identity(self):
        rows, _ = resolve_canonical_demand(
            [occurrence(session_id="13800001", public_direct_booking=True)],
            [demand(external_class_id="13800001", visibility="unlisted",
                    registration_status="open", start_at="2026-09-15T11:15:00-04:00")],
        )
        row = rows[0]
        self.assertEqual("unlisted", row["visibility"])
        self.assertFalse(row["public_direct_booking"])
        self.assertEqual("closed", row["registration_status"])
        self.assertEqual("stale_anchor", row["demand_status"])

    def test_public_canonical_visibility_does_not_suppress_existing_open_route(self):
        rows, _ = resolve_canonical_demand(
            [occurrence(visibility="private", public_direct_booking=True)],
            [demand(visibility="public", registration_status="open")],
        )
        self.assertEqual("public", rows[0]["visibility"])
        self.assertTrue(rows[0]["public_direct_booking"])
        self.assertEqual(1, rows[0]["active_registration_count"])

    def test_audit_contains_no_participant_pii(self):
        _, audit = resolve_canonical_demand([occurrence()], [demand()])
        serialized = str(audit).lower()
        self.assertNotIn("email", serialized)
        self.assertNotIn("customer", serialized)
        self.assertNotIn("participant", serialized)

    def test_positive_private_with_no_legacy_row_is_v1_gap_not_public_anchor(self):
        private = demand(visibility="private", session_status="scheduled",
                         count_available=True, active_registration_count=1,
                         external_class_id=None)
        resolved, audit = resolve_canonical_demand([], [private])
        self.assertEqual([], resolved)
        self.assertEqual([], promote_seated_sessions(resolved))
        summary = summarize_positive_v1_attribution([private], audit)
        self.assertEqual(1, summary["positive_active_sessions"])
        self.assertEqual(1, summary["unmatched_positive"])
        self.assertEqual(1, summary["v1_identity_gap_positive"])
        self.assertEqual("v1_occurrence_identity_only_not_v2_occupancy", summary["scope"])
        self.assertNotIn(private["canonical_session_id"], str(summary))

    def test_positive_v1_audit_separates_matched_from_ambiguous(self):
        positive = demand(session_status="active", count_available=True)
        resolved, audit = resolve_canonical_demand([occurrence()], [positive])
        summary = summarize_positive_v1_attribution([positive], audit)
        self.assertEqual(1, len(promote_seated_sessions(resolved)))
        self.assertEqual(1, summary["matched_positive"])
        self.assertEqual(0, summary["v1_identity_gap_positive"])
        _, ambiguous_audit = resolve_canonical_demand(
            [occurrence(session_id="a"), occurrence(session_id="b")], [positive])
        ambiguous = summarize_positive_v1_attribution([positive], ambiguous_audit)
        self.assertEqual(1, ambiguous["ambiguous_positive"])
        self.assertEqual(1, ambiguous["v1_identity_gap_positive"])

    def test_private_recorded_seat_counts_without_external_roster_authority(self):
        private = demand(
            session_status="active", visibility="private",
            canonical_recorded_registration_count=1,
            active_registration_count=None, count_available=False,
            demand_basis="unknown",
        )
        _, audit = resolve_canonical_demand([], [private])
        summary = summarize_positive_v1_attribution([private], audit)
        self.assertEqual(1, summary["positive_active_sessions"])
        self.assertEqual(1, summary["positive_recorded_without_external_roster_proof"])
        self.assertEqual(1, summary["unmatched_positive"])
        self.assertNotIn(private["canonical_session_id"], str(summary))
        self.assertEqual(0, summarize_positive_v1_attribution(
            [dict(private, session_status="canceled")], audit)["positive_active_sessions"])
        self.assertEqual(0, summarize_positive_v1_attribution(
            [dict(private, canonical_recorded_registration_count=True)], audit)["positive_active_sessions"])

    def test_v1_audit_excludes_provisional_and_canceled_or_unproven_seats(self):
        rows = [
            demand(session_status="active", count_available=True,
                   active_registration_count=0),
            demand(session_status="canceled", count_available=True,
                   active_registration_count=1),
            demand(session_status="scheduled", count_available=False,
                   active_registration_count=1),
            demand(session_status="scheduled", count_available=True,
                   active_registration_count=True),
        ]
        summary = summarize_positive_v1_attribution(
            rows, [{"result": "unmatched"}] * len(rows))
        self.assertEqual(0, summary["positive_active_sessions"])
        self.assertEqual(0, summary["v1_identity_gap_positive"])

    def test_numeric_external_native_seat_reaches_internal_hard_occupancy_without_opening_public_join(self):
        # A counted native lifecycle seat can be operational even while a
        # numeric legacy external roster is unproven; do not synthesize public
        # availability or silently drop the longer occupied consumption end.
        session = dict(canonical_session_id="numeric-native-fixture",
            external_class_id="80001", session_status="scheduled",
            start_at="2030-11-23T10:00:00-05:00",
            end_at="2030-11-23T12:00:00-05:00",
            consumption_end_at="2030-11-23T12:30:00-05:00",
            visibility="private", registration_status="closed",
            location_name="Private venue", lead_instructor_name=None,
            active_registration_count=None, count_available=False,
            operational_has_active_seat=True)
        loaded = dict(location_resource_map={}, sessions_current={"sessions": []},
                      schedule_future={"sessions": []}, live_availability_snapshot={},
                      canonical_demand={"sessions": [session]})
        with (patch("scripts.block_start_time_selector.generate_dynamic_offers.normalize_occupancy", return_value=[]),
              patch("scripts.block_start_time_selector.generate_dynamic_offers.availability_windows", return_value=[]),
              patch("scripts.block_start_time_selector.generate_dynamic_offers.normalize_location_resource",
                    return_value=("Private venue", None, False))):
            blocks = build_occupancy(loaded, {}, allow_unresolved=True)
        self.assertEqual(len(blocks), 1)
        self.assertTrue(blocks[0]["operational_has_active_seat"])
        self.assertFalse(blocks[0]["count_available"])
        self.assertIsNone(blocks[0]["active_registration_count"])
        self.assertTrue(blocks[0]["instructor_unassigned"])
        self.assertEqual(aware(blocks[0]["end"]).isoformat(), "2030-11-23T12:30:00-05:00")
        self.assertNotIn("public_direct_booking", blocks[0])
        self.assertEqual(blocks[0]["visibility"], "private")

    def test_v2_consumes_only_consistent_explicit_catalog_course_identity(self):
        from scripts.block_start_time_selector import parse_dt
        start, end = "2030-11-23T10:00:00-05:00", "2030-11-23T12:30:00-05:00"
        base = dict(
            canonical_session_id="synthetic-class", external_class_id="80123",
            external_course_id=None, course_key="historical-title-is-not-proof",
            session_status="scheduled", start_at=start, end_at=end,
            location_name="Shipyard", lead_instructor_name="Brian Ennis",
            visibility="private", operational_has_active_seat=True,
            count_available=False, active_registration_count=None,
        )
        catalog = {"209806", "359474", "329495", "987654"}
        rules = {cid: {} for cid in ("209806", "359474", "329495")}
        scenarios = [
            ({"catalog_course_id": "209806"}, "209806"),
            ({"catalog_course_id": 359474}, "359474"),
            ({"catalog_course_id": "329495"}, "329495"),
            ({"external_course_id": "359474"}, "359474"),
            ({"catalog_course_id": "359474", "external_course_id": 359474}, "359474"),
            ({"catalog_course_id": "359474", "external_course_id": "209806"}, None),
            ({"catalog_course_id": "987654"}, None),
            ({"catalog_course_id": "NOT-A-CATALOG-COURSE"}, None),
            ({}, None),
        ]
        for extra, expected in scenarios:
            with self.subTest(extra=extra):
                mirror = dict(start=parse_dt(start), end=parse_dt(end), location="Shipyard",
                              instructor="Brian Ennis", source_file="docs/data/schedule_future.json")
                distinct = dict(mirror, instructor="Amy Arnold")
                loaded = dict(location_resource_map={}, sessions_current={"sessions": []},
                    schedule_future={"sessions": [
                        {"session_id": "80123", "course_id": "209806",
                         "count_available": True, "active_registration_count": 1},
                        {"session_id": "80124", "course_id": "209806",
                         "count_available": True, "active_registration_count": 1},
                    ]}, live_availability_snapshot={},
                    canonical_demand={"sessions": [{**base, **extra}]})
                with (patch("scripts.block_start_time_selector.generate_dynamic_offers.normalize_occupancy",
                            side_effect=[[], [mirror, distinct]]),
                      patch("scripts.block_start_time_selector.generate_dynamic_offers.availability_windows",
                            return_value=[]),
                      patch("scripts.block_start_time_selector.generate_dynamic_offers.normalize_location_resource",
                            return_value=("Shipyard", "Room B", True))):
                    legacy, other, canonical = build_occupancy(
                        loaded, rules, allow_unresolved=True, known_catalog_ids=catalog)
                self.assertEqual(canonical["course_id"], expected)
                self.assertEqual(canonical.get("kind"), "hold" if expected is None else None)
                self.assertEqual((canonical["start"], canonical["end"]), tuple(
                    datetime.fromisoformat(value.replace("Z", "+00:00")) for value in (start, end)))
                self.assertEqual(canonical["external_class_id"], "80123")
                self.assertEqual(canonical["visibility"], "private")
                self.assertIsNone(canonical["active_registration_count"])
                self.assertEqual(legacy.get("kind"), None if expected == "209806" else "hold")
                self.assertIsNone(other.get("kind"))
                self.assertEqual(other["instructor"], "Amy Arnold")

    def test_protected_projection_source_has_required_contract_and_no_customer_fields(self):
        source = (Path(__file__).resolve().parents[1] / "supabase/functions/canonical-scheduling-demand/index.ts").read_text(encoding="utf-8")
        for field in (
            "canonical_session_id", "external_class_id", "external_course_id", "course_key",
            "start_at", "end_at", "location_id", "location_name", "lead_instructor_id",
            "lead_instructor_name", "source", "session_status", "active_registration_count", "demand_basis",
        ):
            self.assertIn(field, source)
        self.assertIn('req.headers.get("x-hot-sync-admin-key")', source)
        self.assertNotIn("customers", source)
        self.assertNotIn("first_name", source)
        self.assertNotIn("last_name", source)
        self.assertNotIn('"email"', source)
        self.assertNotIn("customer_email", source)


    def test_private_stale_carry_in_blocks_cleanup_without_becoming_an_offer(self):
        config = Path(__file__).resolve().parents[1] / 'data/config'
        policy = json.loads((config/'layered_scheduling_policy.json').read_text())
        policy.update(lead_minutes=0, require_verified_day_gravity=True)
        resource = json.loads((config/'location_resource_map.json').read_text())
        page = json.loads((config/'block_schedule_pages.json').read_text())['pages']['heartsaver']
        now = aware('2026-10-10T12:00:00-04:00')
        course = dict(course_id='329495', course_family='Heartsaver', kind='skills',
                      clean_course_name='Heartsaver Blended Skills',blended_classroom_skills='blended')
        name, location = 'Brian Ennis', ':: Wilmington; Shipyard Blvd'
        row = dict(canonical_session_id='synthetic-private-night', external_class_id='123123',
            catalog_course_id='329495', external_course_id='329495', course_name='Heartsaver Blended Skills',
            visibility='private', registration_status='closed', demand_status='stale_reconciliation',
            count_available=False, active_registration_count=None, operational_has_active_seat=False,
            session_status='completed', start_at='2026-10-10T23:00:00-04:00',
            end_at='2026-10-11T00:00:00-04:00', consumption_end_at='2026-10-11T00:30:00-04:00',
            lead_instructor_name=name, location_name=policy['primary_resource'])
        payload = dict(location_resource_map=resource, sessions_current={'sessions': []},
            schedule_future={'sessions': []}, live_availability_snapshot={},
            canonical_demand={'sessions': [row]})
        occupancy = build_occupancy(payload, {'329495': {}}, allow_unresolved=True, known_catalog_ids={'329495'})
        self.assertEqual(len(occupancy), 1)
        self.assertEqual(occupancy[0]["end"], aware(row["consumption_end_at"]))
        self.assertIsNone(occupancy[0]['active_registration_count'])
        self.assertFalse(occupancy[0]['operational_has_active_seat'])
        start, end = '2026-10-11T00:00:00-04:00','2026-10-11T03:00:00-04:00'
        window = dict(instructor_name=name, person_id=policy['brian_person_id'], location_name=location,
                      start=start, end=end, source_availability_window='synthetic-window')
        proof = dict(status='known_complete', instructor=name, location=policy['primary_resource'],
            start=start, end=end, observed_at=now.isoformat(), valid_until='2026-10-10T13:00:00-04:00')
        args = ([window],occupancy,[course],policy,resource,now,
            lambda w:(w['start'],w['end']),lambda *_:True,[proof])
        direct=calculate(*args)
        with TemporaryDirectory() as directory:
            cold=cached_calculate(*args,cache_dir=directory)
            warm=cached_calculate(*args,cache_dir=directory)
        for calculation in (direct,cold,warm):
            self.assertFalse(calculation['issues'])
            report=calculation['reports'][0]
            self.assertEqual(len(report['normalized_occupancy']),1)
            self.assertFalse(report['normalized_occupancy'][0]['operational_has_active_seat'])
            self.assertEqual(min(x['start'] for x in report['accepted']), aware(row['consumption_end_at']))
            published=publish(calculation,page,[course],[window],now,
                lambda w,s,c:('day','container',f'https://fixture.test/enroll?appointmentDayId=day&courseId={c}&startTime={s:%H:%M}',None),
                lambda s,c:[],[],require_verified_day_gravity=True)
            offers=published['offers']
            self.assertTrue(offers)
            self.assertEqual(min(x['startTime'] for x in offers),'00:30')
            self.assertTrue(all(x['date']=='2026-10-11' and x.get('offerType')!='seated_class' for x in offers))
            self.assertNotIn('synthetic-private-night',json.dumps(offers))
        self.assertEqual(warm['incremental_cache']['hits'],1)
        self.assertEqual(pack(cold["reports"]), pack(warm["reports"]))

    def test_explicit_fall_back_instants_do_not_collapse_in_occupancy(self):
        config = Path(__file__).resolve().parents[1] / 'data/config'
        policy = json.loads((config/'layered_scheduling_policy.json').read_text())
        policy.update(lead_minutes=0)
        resource = json.loads((config/'location_resource_map.json').read_text())
        now = aware('2026-10-30T12:00:00-04:00')
        course = dict(course_id='329495', course_family='Heartsaver', kind='skills')
        name, location = 'Brian Ennis', ':: Wilmington; Shipyard Blvd'
        row = dict(canonical_session_id='synthetic-fall-back', catalog_course_id='329495',
            course_name='Heartsaver', session_status='completed', visibility='private',
            count_available=False, active_registration_count=None, operational_has_active_seat=False,
            start_at='2026-11-01T05:30:00Z', end_at='2026-11-01T06:30:00Z',
            lead_instructor_name=name, location_name=policy['primary_resource'])
        payload = dict(location_resource_map=resource, sessions_current={'sessions': []},
            schedule_future={'sessions': []}, live_availability_snapshot={},
            canonical_demand={'sessions': [row]})
        occupancy = build_occupancy(payload, {'329495': {}}, allow_unresolved=True, known_catalog_ids={'329495'})
        start, end = '2026-11-01T00:00:00-04:00','2026-11-01T04:00:00-05:00'
        window = dict(instructor_name=name, person_id=policy['brian_person_id'], location_name=location,
                      start=start, end=end, source_availability_window='synthetic-window')
        proof = dict(status='known_complete', instructor=name, location=policy['primary_resource'],
            start=start, end=end, observed_at=now.isoformat(), valid_until='2026-10-30T13:00:00-04:00')
        args = ([window],occupancy,[course],policy,resource,now,
            lambda w:(w['start'],w['end']),lambda *_:True,[proof])
        direct=calculate(*args)
        with TemporaryDirectory() as directory:
            cold=cached_calculate(*args,cache_dir=directory)
            warm=cached_calculate(*args,cache_dir=directory)
        for calculation in (direct,cold,warm):
            self.assertFalse(calculation['issues'])
            report=calculation['reports'][0]
            busy=report['normalized_occupancy'][0]
            self.assertEqual(busy['start'].isoformat(),'2026-11-01T05:30:00+00:00')
            self.assertEqual(busy['end'].isoformat(),'2026-11-01T06:30:00+00:00')
            self.assertFalse(busy['operational_has_active_seat'])
            self.assertTrue(report['accepted'])
            self.assertTrue(all(slot['end'] <= busy['start'] or slot['start'] >= busy['end']
                                for slot in report['accepted']))
        self.assertEqual(warm['incremental_cache']['hits'],1)
        self.assertEqual(pack(cold["reports"]), pack(warm["reports"]))


    def test_fall_back_availability_scope_proof_and_public_clock(self):
        from scripts.block_start_time_selector import layered_window_instants

        config = Path(__file__).resolve().parents[1] / 'data/config'
        policy = json.loads((config/'layered_scheduling_policy.json').read_text())
        policy.update(lead_minutes=0)
        resource = json.loads((config/'location_resource_map.json').read_text())
        page = json.loads((config/'block_schedule_pages.json').read_text())['pages']['heartsaver']
        now = aware('2026-10-30T12:00:00-04:00')
        cid, name = '329495', 'Brian Ennis'
        course = dict(course_id=cid, course_family='Heartsaver', kind='skills')
        first, second = '2026-11-01T01:30:00-04:00', '2026-11-01T01:30:00-05:00'
        after = '2026-11-01T03:00:00-05:00'
        window = dict(instructor_name=name, person_id=policy['brian_person_id'],
                      location_name=':: Wilmington; Shipyard Blvd', start_datetime=first, end_datetime=second,
                      source_availability_window='cross-fold')
        proof = dict(status='known_complete', instructor=name, location=policy['primary_resource'],
                     start=first, end=after, observed_at=now.isoformat(),
                     valid_until='2026-10-30T13:00:00-04:00')
        next_window = dict(window,start_datetime=second,end_datetime=after,source_availability_window='after-scope')
        bad = dict(instructor=name, resource=policy['primary_resource'],
                   location_resolution='location_resource_map',
                   source_event_id='synthetic-unclear-source', start='unresolved', end='unresolved',
                   uncertainty_scope=dict(start=first,end=second))
        later_proof = dict(proof, start=second)
        for selected, sources, proofs, expected_open in (
                (window, [], [proof], True),
                (window, [], [later_proof], False),
                (window, [bad], [proof], False),
                (next_window, [bad], [later_proof], True)):
            args = ([selected],sources,[course],policy,resource,now,
                    layered_window_instants,lambda *_:True,proofs)
            direct=calculate(*args)
            with TemporaryDirectory() as directory:
                cold=cached_calculate(*args,cache_dir=directory)
                warm=cached_calculate(*args,cache_dir=directory)
            self.assertEqual(warm['incremental_cache']['hits'],1)
            self.assertEqual(pack(direct['reports']),pack(cold['reports']))
            self.assertEqual(pack(cold['reports']),pack(warm['reports']))
            self.assertTrue(direct['reports'],direct['issues'])
            report=direct['reports'][0]
            self.assertEqual(bool(report['accepted']),expected_open)
            self.assertEqual(bool(direct['issues']),bool(sources and selected is window))
            if selected is window and proofs == [later_proof]:
                self.assertEqual(report['valid_until'],now)
            visited = []
            def url_for(w, start, c):
                visited.append(start.strftime('%H:%M'))
                return 'day','container',f'/register/?startTime={start:%H:%M}',None
            published=publish(direct,page,[course],[selected],now,url_for,lambda *_:[])
            self.assertFalse(any(t.startswith('01:') for t in visited))
            self.assertEqual([x['startTime'] for x in published['offers']],
                             ['02:00'] if selected is next_window else [])

        ambiguous = dict(window, start_datetime='2026-11-01T01:30:00')
        args = ([ambiguous],[],[course],policy,resource,now,
                layered_window_instants,lambda *_:True,[proof])
        with TemporaryDirectory() as directory:
            result=cached_calculate(*args,cache_dir=directory)
        self.assertFalse(result['reports'])
        self.assertEqual(result['issues'],calculate(*args)['issues'])
        self.assertIn('ambiguous',result['issues'][0]['reason'])


if __name__ == "__main__":
    unittest.main()
