from datetime import datetime, timezone
import unittest

from scripts.block_start_time_selector import parse_dt, public_policy_reasons, selector_reference_datetime, seated_family_anchors, session_enrollment_count


class SelectorClockTests(unittest.TestCase):
    def test_candidate_consolidation_uses_canonical_demand_or_explicit_commitment(self):
        occurrence = {"session_id":"fixture", "course_id":"359474", "start_at":"2030-09-08T13:00:00-04:00", "registered_count":99}
        def anchors(row):
            return seated_family_anchors(schedule_future_payload={"sessions":[row]},selected_course_ids=set(),minimum_enrollment=0,location_resource_map={})
        self.assertIsNone(session_enrollment_count(occurrence))
        self.assertEqual(anchors(occurrence), [])
        self.assertEqual(anchors({**occurrence,"active_registration_count":0,"demand_basis":"canonical_active_registrations"}), [])
        self.assertEqual(len(anchors({**occurrence,"active_registration_count":1,"demand_basis":"canonical_active_registrations"})),1)
        for basis in ("manual_override","committed_public_session"):
            self.assertEqual(len(anchors({**occurrence,"anchor_basis":basis})),1)

    def test_reported_build_clock_is_eastern_even_on_utc_runner(self):
        reference = selector_reference_datetime(datetime(2026,9,26,18,2,15,tzinfo=timezone.utc))
        self.assertEqual(reference,datetime(2026,9,26,14,2,15))
        common = dict(course_id="210549",course_family="BLS",policy={"minimum_lead_hours":24},reference_now=reference)
        self.assertNotIn("inside_minimum_lead_time", public_policy_reasons(start=datetime(2026,9,27,15),**common))
        self.assertIn("inside_minimum_lead_time", public_policy_reasons(start=datetime(2026,9,27,14),**common))

    def test_v2_aware_start_matches_existing_eastern_policy(self):
        reference=datetime(2026,10,7,8)
        policy={"minimum_lead_hours":24,"dynamic_public_start_time_window":{"enabled":True,"earliest_start":"07:00","latest_start":"22:00"}}
        for instant in ("2026-10-08T12:00:00Z","2026-10-08T06:00:00Z","2026-10-07T15:00:00Z"):
            start=datetime.fromisoformat(instant.replace("Z","+00:00"))
            args=dict(course_id="210549",course_family="BLS",policy=policy,reference_now=reference)
            self.assertEqual(public_policy_reasons(start=start,**args),public_policy_reasons(start=parse_dt(instant),**args))

    def test_winter_summer_and_dst_inputs_normalize_to_business_time(self):
        for instant, expected in [
            ("2026-01-15T18:00:00Z","2026-01-15T13:00:00"),
            ("2026-07-15T18:00:00Z","2026-07-15T14:00:00"),
            ("2026-11-01T07:00:00Z","2026-11-01T02:00:00"),
            ("2027-03-14T07:00:00Z","2027-03-14T03:00:00"),
        ]:
            with self.subTest(instant=instant):
                self.assertEqual(parse_dt(instant).isoformat(),expected)
        self.assertEqual(parse_dt("2026-09-27T13:00:00-04:00"),datetime(2026,9,27,13))


if __name__ == "__main__":
    unittest.main()
