import unittest
from datetime import datetime, timedelta, timezone
from scripts.build_live_availability_snapshot import layered_calendar_coverage

class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,10,7,tzinfo=timezone.utc)
        self.config={"calendar_sources":[dict(calendar_source_key="busy",calendar_mode="inverse_blocking",owner_instructor_key="brian")]}
        self.people={"people":[dict(person_id="brian",display_name="Brian Ennis")]}
        self.blocks=[dict(person_id="brian",availability_status="available",location_name="Shipyard")]
        self.evidence=dict(generated_at=self.now.isoformat(),date_range=dict(start=self.now.isoformat(),end=(self.now+timedelta(days=90)).isoformat()),export_status="ok",warnings=[],skipped={})
        self.snapshot=dict(source_evidence={"busy":self.evidence},events_by_source={"busy":[]})
    def rows(self):
        return layered_calendar_coverage(self.config,self.people,self.snapshot,self.blocks,now=self.now)
    def test_successful_empty_calendar_has_bounded_proof(self):
        rows=self.rows();self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["valid_until"],(self.now+timedelta(minutes=15)).isoformat())
        self.assertNotIn("events",rows[0])
    def test_failed_stale_partial_and_missing_exports_never_open_time(self):
        for field,value in [("export_status","failed"),("generated_at",(self.now-timedelta(minutes=16)).isoformat()),("warnings",["partial"]),("skipped",{"unparseable":1})]:
            original=self.evidence[field];self.evidence[field]=value
            self.assertEqual(self.rows(),[],field);self.evidence[field]=original
        self.snapshot["source_evidence"]={};self.assertEqual(self.rows(),[])
    def test_all_configured_owner_calendars_required(self):
        self.config["calendar_sources"].append(dict(calendar_source_key="other",calendar_mode="blocking",owner_instructor_key="brian"))
        self.assertEqual(self.rows(),[])
    def test_invalid_event_never_opens_time(self):
        self.snapshot["events_by_source"]["busy"]=[dict(start="invalid",end="invalid")]
        self.assertEqual(self.rows(),[])

    def test_expected_exclusions_do_not_invalidate_complete_export(self):
        self.evidence["skipped"]={"outside_export_window":138,"excluded_by_exdate":2}
        self.assertEqual(len(self.rows()),1)
