import unittest
from scripts.canonical_scheduling_demand import resolve_canonical_demand
from scripts.anchor_state import promote_seated_sessions

class NativeAnchorTests(unittest.TestCase):
    def row(self):
        return dict(canonical_session_id="b48b53c7-df11-409f-a8f0-61b72a7f17e9", external_class_id="lw-b48b53c7-df11-409f-a8f0-61b72a7f17e9", source="landerware_event", registration_backend="landerware", session_status="scheduled", visibility="public", registration_status="open", workspace_projection_status="current", count_available=True, active_registration_count=1, external_course_id="209809", course_name="Heartsaver", start_at="2026-10-10T14:00:00-04:00", end_at="2026-10-10T16:30:00-04:00", location_name=":: Wilmington; Shipyard Blvd", lead_instructor_name="Brian Ennis")
    def test_native_class_publishes_once_and_is_anchor(self):
        row=self.row()
        sessions,audit=resolve_canonical_demand([], [row])
        self.assertEqual(audit[0]["result"], "matched")
        self.assertEqual(len(promote_seated_sessions(sessions)), 1)
        self.assertEqual(sessions[0]["start_at"], row["start_at"])
        again,_=resolve_canonical_demand(sessions, [row])
        self.assertEqual(len(again), 1)
    def test_unproven_private_external_or_closed_rows_cannot_be_added(self):
        for key,value in [("count_available",False),("workspace_projection_status","missing"),("visibility","private"),("registration_status","closed"),("registration_backend","enrollware"),("source","enrollware_reconciled")]:
            row={**self.row(),key:value}
            sessions,_=resolve_canonical_demand([], [row])
            self.assertEqual(sessions, [], key)

    def test_native_projection_is_accepted_by_admin_and_lander_gates(self):
        from scripts.validate_public_refresh_output import validate_admin_reconciliation
        from scripts.build_landers import is_session_lander_candidate
        sessions,_=resolve_canonical_demand([], [self.row()])
        self.assertEqual(validate_admin_reconciliation({"sessions":[]}, {"sources":{"hot_sync":{"available":True}},"sessions":sessions}), {sessions[0]["session_id"]})
        self.assertTrue(is_session_lander_candidate(sessions[0]))
        self.assertFalse(is_session_lander_candidate({**sessions[0],"registration_url":"https://example.invalid/register"}))
        with self.assertRaises(ValueError):
            validate_admin_reconciliation({"sessions":[]}, {"sources":{"hot_sync":{"available":True}},"sessions":[{**sessions[0],"count_available":False}]})

    def test_explicit_compatible_skills_survive_same_family_group(self):
        from scripts.apply_anchor_policy import apply_selector_policy, production_anchor_policy
        sessions,_=resolve_canonical_demand([], [self.row()])
        base=dict(date="2026-10-10",courseId="329495",courseName="Heartsaver Blended",location=":: Wilmington; Shipyard Blvd",instructor="Brian Ennis",durationMinutes=120,schedulerConsumptionMinutes=120,appointmentUrl="https://example.test")
        offers=[{**base,"startTime":t,"schedulerConsumptionEnd":e} for t,e in [("12:00","14:00"),("16:30","18:30"),("09:00","11:00"),("14:30","16:30")]]
        payload={"dates":[{"date":"2026-10-10","startTimes":[{"startTime":o["startTime"],"courses":[o]} for o in offers]}],"counts":{}}
        result=apply_selector_policy(payload,promote_seated_sessions(sessions),production_anchor_policy())
        kept=[o for d in result["dates"] for slot in d["startTimes"] for o in slot["courses"]]
        self.assertEqual({o["startTime"] for o in kept}, {"12:00","16:30"})
        self.assertTrue(all(o["schedule_role"]=="barnacle" for o in kept))
