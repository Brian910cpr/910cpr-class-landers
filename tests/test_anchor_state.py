import unittest

from datetime import datetime

from scripts.anchor_state import ANCHOR_SYMBOL, annotate_offer, in_repeat_bubble, promote_seated_sessions, repeat_scope_key, same_course_anchor


def session(**overrides):
    value = {
        "session_id": "13833211",
        "course_id": "359474",
        "start_at": "2026-08-05T09:30:00-04:00",
        "end_at": "2026-08-05T11:30:00-04:00",
        "location_name": ":: Wilmington; Shipyard Blvd - B",
        "lead_instructor_name": "Brian Ennis",
        "active_registration_count": 1,
        "demand_basis": "canonical_active_registrations",
    }
    value.update(overrides)
    return value


class AnchorStateTests(unittest.TestCase):
    def test_canonical_active_registration_promotes_to_anchor(self):
        anchors = promote_seated_sessions([session()])
        self.assertEqual(len(anchors), 1)
        anchor = anchors[0]
        self.assertEqual(anchor["schedule_role"], "anchor")
        self.assertEqual(anchor["schedule_symbol"], ANCHOR_SYMBOL)
        self.assertEqual(anchor["promotion_reason"], "canonical_active_registration")
        self.assertIs(anchor["landing_page_required"], True)
        self.assertIs(anchor["external_publication_eligible"], True)

    def test_zero_demand_appointment_inventory_is_not_anchor(self):
        self.assertEqual([], promote_seated_sessions([session(active_registration_count=0)]))

    def test_legacy_counts_and_snapshots_cannot_promote(self):
        candidate = session(active_registration_count=None, registered_count=4, source_seats=4,
                            historical_student_count=4, confirmed_seated=True)
        self.assertEqual([], promote_seated_sessions([candidate]))

    def test_explicit_committed_public_session_can_promote_without_registration(self):
        anchors = promote_seated_sessions([session(active_registration_count=0, anchor_basis="committed_public_session")])
        self.assertEqual("committed_public_session", anchors[0]["promotion_reason"])

    def test_cancelled_or_nonpublic_class_is_not_promoted(self):
        self.assertEqual(promote_seated_sessions([session(session_status="cancelled")]), [])
        self.assertEqual(promote_seated_sessions([session(public_direct_booking=False)]), [])

    def test_full_public_class_with_active_demand_remains_anchor(self):
        self.assertEqual(1, len(promote_seated_sessions([session(registration_status="full")])))

    def test_barnacle_with_first_seat_promotes_on_next_refresh(self):
        prior_offer = annotate_offer(
            {
                "course_id": "210549",
                "start_at": "2026-08-05T11:30:00-04:00",
            },
            attached_to=promote_seated_sessions([session()])[0],
        )
        self.assertEqual(prior_offer["schedule_role"], "barnacle")
        self.assertEqual(prior_offer["schedule_symbol"], "")

        newly_seated = session(
            session_id="13818252",
            course_id="210549",
            start_at="2026-08-05T11:30:00-04:00",
            end_at="2026-08-05T12:30:00-04:00",
            active_registration_count=1,
        )
        promoted = promote_seated_sessions([newly_seated])[0]
        self.assertEqual(promoted["schedule_role"], "anchor")
        self.assertEqual(promoted["schedule_symbol"], ANCHOR_SYMBOL)

    def test_existing_same_course_anchor_wins_before_new_time(self):
        anchors = promote_seated_sessions([
            session(),
            session(
                session_id="later",
                start_at="2026-08-05T14:00:00-04:00",
                end_at="2026-08-05T16:00:00-04:00",
            ),
        ])
        selected = same_course_anchor(
            course_id="359474",
            date="2026-08-05",
            location=":: Wilmington; Shipyard Blvd - B",
            anchors=anchors,
        )
        self.assertIsNotNone(selected)
        self.assertEqual(selected["session_id"], "13833211")
        self.assertTrue(selected["start_at"].startswith("2026-08-05T09:30:00"))

    def test_wrong_course_does_not_reuse_anchor(self):
        anchors = promote_seated_sessions([session()])
        selected = same_course_anchor(
            course_id="210549",
            date="2026-08-05",
            location=":: Wilmington; Shipyard Blvd - B",
            anchors=anchors,
        )
        self.assertIsNone(selected)

    def test_repeat_bubble_projects_backward_and_forward_start_to_start(self):
        anchor = datetime.fromisoformat("2026-08-05T12:00:00-04:00")
        self.assertTrue(in_repeat_bubble(datetime.fromisoformat("2026-08-05T08:00:00-04:00"), anchor, 240))
        self.assertTrue(in_repeat_bubble(datetime.fromisoformat("2026-08-05T16:00:00-04:00"), anchor, 240))
        self.assertFalse(in_repeat_bubble(datetime.fromisoformat("2026-08-05T16:30:00-04:00"), anchor, 240))

    def test_shared_bls_family_and_exact_low_demand_scopes(self):
        policy = {
            "families": {"bls": {"course_ids": ["209806", "359474"], "repeat_delay_minutes": 240}},
            "exact_courses": {"463743": {"repeat_delay_minutes": 4320}},
        }
        self.assertEqual(repeat_scope_key("209806", policy), repeat_scope_key("359474", policy))
        self.assertEqual(repeat_scope_key("463743", policy), ("course:463743", 4320))

    def test_production_policy_uses_calendar_day_identity_mode(self):
        import json
        from pathlib import Path

        policy_path = Path(__file__).resolve().parents[1] / "data/config/anchor_schedule_policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        self.assertEqual(policy["mode"], "daily_anchor_stack_v1")
        self.assertFalse(policy["one_course_type_per_calendar_day"])
        self.assertTrue(
            policy["compact_paid_days"],
            "Once a real seated/committed class exists on a day, public choices must compact into nearest barnacles around planted seats instead of exposing scattered gaps",
        )
        self.assertEqual(0, policy["default_repeat_delay_minutes"])
        self.assertEqual(policy["open_day_excluded_families"], ["ACLS", "PALS"])
        self.assertNotIn("retain_barnacle_offers", policy)
        self.assertTrue(all("retain_barnacle_offers" not in family for family in policy["families"].values()))
        pairs = {tuple(pair) for pair in policy.get("barnacle_course_pairs", [])}
        self.assertNotIn(("209806", "359474"), pairs, "BLS Initial and Renewal are explicit alternatives, not mutual barnacles")
        self.assertNotIn(("359474", "209806"), pairs, "BLS Initial and Renewal are explicit alternatives, not mutual barnacles")
        self.assertTrue(
            all("retain_barnacle_offers" not in course for course in policy["exact_courses"].values()),
            "Barnacle retention is an invariant, not an exact-course configuration switch",
        )

    def test_real_open_public_class_is_anchor_when_roster_freshness_is_unknown(self):
        session = {
            "session_id": "14501248",
            "course_id": "209806",
            "start_at": "2026-10-02T12:45:00-04:00",
            "end_at": "2026-10-02T14:45:00-04:00",
            "location_name": "NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office",
            "lead_instructor_name": "Brian Ennis",
            "active_registration_count": None,
            "demand_basis": "unknown",
            "demand_status": "stale_reconciliation",
            "public_direct_booking": True,
            "registration_status": "open",
            "session_status": "active",
            "registration_url": "https://coastalcprtraining.enrollware.com/enroll?id=14501248",
        }
        anchors = promote_seated_sessions([session])
        self.assertEqual(len(anchors), 1)
        self.assertEqual(anchors[0]["promotion_reason"], "committed_public_session")

    def test_ambiguous_public_class_does_not_promote(self):
        session = {
            "session_id": "ambiguous",
            "course_id": "209806",
            "start_at": "2026-10-02T12:45:00-04:00",
            "end_at": "2026-10-02T14:45:00-04:00",
            "location_name": "Room B",
            "lead_instructor_name": "Brian Ennis",
            "demand_status": "ambiguous",
            "public_direct_booking": True,
            "registration_status": "open",
            "session_status": "active",
            "registration_url": "https://coastalcprtraining.enrollware.com/enroll?id=14501248",
        }
        self.assertEqual(promote_seated_sessions([session]), [])



if __name__ == "__main__":
    unittest.main()
