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
        "registered_count": 1,
    }
    value.update(overrides)
    return value


class AnchorStateTests(unittest.TestCase):
    def test_existing_public_class_promotes_to_anchor(self):
        anchors = promote_seated_sessions([session()])
        self.assertEqual(len(anchors), 1)
        anchor = anchors[0]
        self.assertEqual(anchor["schedule_role"], "anchor")
        self.assertEqual(anchor["schedule_symbol"], ANCHOR_SYMBOL)
        self.assertEqual(anchor["promotion_reason"], "existing_public_class")
        self.assertIs(anchor["landing_page_required"], True)
        self.assertIs(anchor["external_publication_eligible"], True)

    def test_enrollware_class_without_a_reported_count_is_still_seated(self):
        anchors = promote_seated_sessions([session(registered_count=0)])
        self.assertEqual(1, len(anchors))
        self.assertEqual(0, anchors[0]["registered_count"])

    def test_closed_or_nonpublic_class_is_not_promoted(self):
        self.assertEqual(promote_seated_sessions([session(registration_status="closed")]), [])
        self.assertEqual(promote_seated_sessions([session(public_direct_booking=False)]), [])

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
            registered_count=1,
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
        self.assertEqual(policy["mode"], "anchor_repeat_bubble_v2")
        self.assertFalse(policy["one_course_type_per_calendar_day"])
        self.assertEqual(0, policy["default_repeat_delay_minutes"])
        self.assertTrue(policy["retain_barnacle_offers"])
        self.assertEqual(policy["open_day_excluded_families"], ["ACLS", "PALS"])\n        self.assertTrue(\n            all(family["retain_barnacle_offers"] for family in policy["families"].values()),\n            "Every customer-facing course family must retain barnacle offers",\n        )\n        self.assertTrue(\n            all(course["retain_barnacle_offers"] for course in policy["exact_courses"].values()),\n            "Every exact-course repeat rule must retain barnacle offers",\n        )


if __name__ == "__main__":
    unittest.main()
