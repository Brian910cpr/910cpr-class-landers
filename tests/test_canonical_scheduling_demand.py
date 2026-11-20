import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.anchor_state import promote_seated_sessions
from scripts.block_start_time_selector import build_occupancy, public_direct_bookable_session
from scripts.layered_selector_adapter import aware
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

    def test_native_seated_source_does_not_publish_inherited_legacy_enrollment_url(self):
        # A real native BLS seat may share the numerical Enrollware class ID
        # with its legacy schedule mirror. Keep its identity, but never turn
        # the mirror's old URL into an authorized native checkout route.
        legacy = occurrence(session_id="15000001", course_id="209806",
            registration_url="https://coastalcprtraining.enrollware.com/enroll?id=15000001",
            registration_status="open", session_status="scheduled")
        native = demand(external_class_id="15000001", source="landerware_public_offer",
            registration_backend="landerware", visibility="public",
            session_status="scheduled", registration_status="open",
            operational_has_active_seat=True, count_available=False,
            active_registration_count=None)
        resolved, audit = resolve_canonical_demand([legacy], [native])
        self.assertEqual("external_class_id", audit[0]["match_basis"])
        self.assertEqual(native["canonical_session_id"], resolved[0]["canonical_session_id"])
        self.assertFalse(resolved[0]["public_direct_booking"])
        self.assertFalse(public_direct_bookable_session(resolved[0]))
        self.assertEqual("native_canonical_legacy_url_unverified", resolved[0]["public_route_guard"])
        # This does not cancel the occupied canonical appointment or erase
        # a legitimate legacy-backed enrollment route absent native ownership.
        self.assertEqual(1, native["operational_has_active_seat"])
        old_owner, _ = resolve_canonical_demand([legacy], [dict(native, registration_backend="enrollware")])
        self.assertTrue(public_direct_bookable_session(old_owner[0]))

    def test_unlisted_canonical_seat_never_inherits_public_legacy_booking_route(self):
        # An accepted unlisted class still reserves a real seat, but the public
        # legacy mirror must not make it joinable, even with an "open" or
        # externally managed registration status. Preserve its source identity.
        legacy = occurrence(
            session_id="15000007",
            registration_url="https://coastalcprtraining.enrollware.com/enroll?id=15000007",
            registration_status="open",
            public_direct_booking=True,
        )
        for status in ("external", "open"):
            with self.subTest(status=status):
                unlisted = demand(
                    external_class_id="15000007",
                    visibility="unlisted",
                    source="enrollware_reconciled",
                    registration_backend="enrollware",
                    session_status="scheduled",
                    registration_status=status,
                    active_registration_count=1,
                    count_available=True,
                    operational_has_active_seat=True,
                )
                rows, audit = resolve_canonical_demand([legacy], [unlisted])
                self.assertEqual("external_class_id", audit[0]["match_basis"])
                self.assertEqual(unlisted["canonical_session_id"], rows[0]["canonical_session_id"])
                self.assertEqual(1, rows[0]["active_registration_count"])
                self.assertTrue(rows[0]["count_available"])
                self.assertFalse(rows[0]["public_direct_booking"])
                self.assertEqual("closed", rows[0]["registration_status"])
                self.assertFalse(public_direct_bookable_session(rows[0]))
        # Do not globally disable independently public, correctly owned seats.
        public = dict(unlisted, visibility="public", registration_status="open")
        rows, _ = resolve_canonical_demand([legacy], [public])
        self.assertTrue(public_direct_bookable_session(rows[0]))

    def test_explicit_private_unlisted_legacy_visibility_is_not_publicly_bookable(self):
        # Independent of canonical matching, a legacy source's explicit
        # private/unlisted visibility must never create a public join route.
        for visibility in ("private", "unlisted", "PRIVATE", "Unlisted"):
            with self.subTest(visibility=visibility):
                row = occurrence(visibility=visibility, registration_status="open",
                                 public_direct_booking=True)
                self.assertFalse(public_direct_bookable_session(row))
        # Missing legacy visibility is not proof of private status by itself;
        # existing legacy route and source-ownership checks still apply.
        self.assertTrue(public_direct_bookable_session(occurrence()))
        self.assertTrue(public_direct_bookable_session(occurrence(visibility="public")))

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

    def test_known_canonical_blended_skills_hold_cleanup_without_public_promotion(self):
        import json
        from scripts.block_start_time_selector import course_rules_by_id

        root = Path(__file__).resolve().parents[1]
        rules = course_rules_by_id(json.loads(
            (root / "data/inventory/course_consumption_rules.json").read_text(encoding="utf-8")))
        policy = json.loads(
            (root / "data/config/layered_scheduling_policy.json").read_text(encoding="utf-8"))
        self.assertEqual(policy["skills_instruction_minutes"], rules["329495"]["duration_minutes"])
        self.assertEqual(policy["skills_cleanup_minutes"], rules["329495"]["cleanup_buffer_minutes"])
        self.assertEqual(60, rules["329495"]["scheduler_consumption_minutes"])
        self.assertEqual(2, rules["329495"]["default_capacity"])

        def seat(identity, course, end, consumption_end=None, conflict=False, status="scheduled"):
            return dict(
                canonical_session_id=identity, session_status=status,
                start_at="2030-11-24T18:00:00-05:00",
                end_at=end, consumption_end_at=consumption_end,
                scheduler_course_id=course, course_identity_conflict=conflict,
                visibility="private", registration_status="closed",
                location_name="Private venue", lead_instructor_name=None,
                operational_has_active_seat=True, count_available=False,
                active_registration_count=None,
            )

        sessions = [
            # A real 45-minute canonical skills class missing cleanup must
            # protect the next 15 minutes, without inventing a second room.
            seat("incomplete-cleanup", "329495", "2030-11-24T18:45:00-05:00"),
            # Longer explicit holds are authoritative, never shortened.
            seat("longer-hold", "329495", "2030-11-24T18:45:00-05:00",
                 "2030-11-24T19:30:00-05:00"),
            # A 509474 skills record already carries exactly 15 cleanup minutes.
            seat("already-buffered", "509474", "2030-11-24T18:45:00-05:00",
                 "2030-11-24T19:00:00-05:00"),
            # Disputed or absent identities retain physical holds only.
            seat("conflicted", "329495", "2030-11-24T18:45:00-05:00",
                 conflict=True),
            seat("unmapped", None, "2030-11-24T18:45:00-05:00"),
            seat("canceled", "329495", "2030-11-24T18:45:00-05:00",
                 status="canceled"),
        ]
        loaded = dict(location_resource_map={}, sessions_current={"sessions": []},
                      schedule_future={"sessions": []}, live_availability_snapshot={},
                      canonical_demand={"sessions": sessions})
        with (patch("scripts.block_start_time_selector.generate_dynamic_offers.normalize_occupancy", return_value=[]),
              patch("scripts.block_start_time_selector.generate_dynamic_offers.availability_windows", return_value=[]),
              patch("scripts.block_start_time_selector.generate_dynamic_offers.normalize_location_resource",
                    return_value=("Private venue", None, False))):
            occupied = build_occupancy(loaded, rules, allow_unresolved=True)
        by_id = {row["source_event_id"]: row for row in occupied}
        self.assertEqual(set(by_id), {
            "incomplete-cleanup", "longer-hold", "already-buffered", "conflicted", "unmapped"})
        self.assertEqual({
            identity: aware(row["end"]).strftime("%H:%M")
            for identity, row in by_id.items()
        }, {
            "incomplete-cleanup": "19:00", "longer-hold": "19:30",
            "already-buffered": "19:00", "conflicted": "18:45", "unmapped": "18:45"})
        self.assertTrue(all(row["instructor_unassigned"] for row in occupied))
        self.assertTrue(all(row["operational_has_active_seat"] for row in occupied))
        self.assertTrue(all("public_direct_booking" not in row for row in occupied))

    def test_protected_projection_source_has_required_contract_and_no_customer_fields(self):
        source = (Path(__file__).resolve().parents[1] / "supabase/functions/canonical-scheduling-demand/index.ts").read_text(encoding="utf-8")
        for field in (
            "canonical_session_id", "external_class_id", "external_course_id", "course_key",
            "start_at", "end_at", "location_id", "location_name", "lead_instructor_id",
            "lead_instructor_name", "source", "session_status", "active_registration_count", "demand_basis",
            "operational_has_active_seat",
        ):
            self.assertIn(field, source)
        self.assertIn('req.headers.get("x-hot-sync-admin-key")', source)
        self.assertNotIn("customers", source)
        self.assertNotIn("first_name", source)
        self.assertNotIn("last_name", source)
        # A registration_source enum may contain the word email without
        # exporting an address; guard actual identity fields instead.
        self.assertNotIn('"email"', source)
        self.assertNotIn("customer_email", source)


if __name__ == "__main__":
    unittest.main()
