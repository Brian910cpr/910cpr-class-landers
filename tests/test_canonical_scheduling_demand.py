import unittest
from pathlib import Path

from scripts.anchor_state import promote_seated_sessions
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
        # The endpoint may inspect confirmation provenance internally; forbid
        # participant contact fields, not the word "email" in internal names.
        for forbidden in ('"email"', "customer_email", "participant_email"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
