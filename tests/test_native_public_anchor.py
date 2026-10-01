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
