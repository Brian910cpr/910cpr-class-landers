from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
from zoneinfo import ZoneInfo

from scripts.static_public_inventory_projection import render_from_schedule, select_stable_sessions
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload


TZ = ZoneInfo("America/New_York")


def session(now, days, sid, course_id="209806", **changes):
    row = {
        "session_id": sid,
        "course_id": course_id,
        "course_name": "AHA BLS Provider",
        "start_at": (now + timedelta(days=days)).isoformat(),
        "location_display": ":: Wilmington; Shipyard Blvd - B",
        "registration_url": f"https://coastalcprtraining.enrollware.com/enroll?id={sid}",
        "session_status": "active",
        "registration_status": "open",
        "schedule_role": "anchor",
        "external_publication_eligible": True,
        "public_direct_booking": True,
    }
    row.update(changes)
    return row


class StaticPublicInventoryProjectionTests(unittest.TestCase):
    def test_public_selector_payload_drops_internal_repeated_source_objects(self):
        payload = {
            "dates": [{
                "date": "2026-09-28",
                "displayDate": "Monday, September 28",
                "startTimes": [{
                    "startTime": "14:00",
                    "displayStartTime": "2:00 PM",
                    "courses": [{
                        "courseId": "209806",
                        "courseName": "AHA BLS Provider",
                        "durationMinutes": 120,
                        "appointmentUrl": "https://coastalcprtraining.enrollware.com/enroll?id=123",
                        "location": "Wilmington",
                        "sourceAvailabilityBlock": {"large": "internal object"},
                        "publicSelectable": True,
                    }],
                }],
            }],
        }
        compact = public_selector_availability_payload(payload)
        encoded = json.dumps(compact)
        self.assertNotIn("sourceAvailabilityBlock", encoded)
        self.assertNotIn("publicSelectable", encoded)
        self.assertIn("courseId", encoded)
        self.assertIn("appointmentUrl", encoded)
        self.assertIn("durationMinutes", encoded)

    def test_selects_only_verified_public_anchors_in_14_to_21_day_window(self):
        now = datetime(2026, 9, 14, 10, 0, tzinfo=TZ)
        rows = [
            session(now, 1, "near"),
            session(now, 14, "start"),
            session(now, 18, "middle"),
            session(now, 21, "end"),
            session(now, 22, "far"),
            session(now, 18, "draft", session_status="draft"),
            session(now, 18, "private", external_publication_eligible=False),
            session(now, 18, "request", registration_url="/request_group_session.html"),
        ]
        selected = select_stable_sessions(rows, ["209806"], now=now)
        self.assertEqual(["start", "middle", "end"], [row["session_id"] for row in selected])

    def test_rendered_projection_contains_class_links_not_registration_links(self):
        now = datetime(2026, 9, 14, 10, 0, tzinfo=TZ)
        with TemporaryDirectory() as temp:
            path = Path(temp) / "schedule.json"
            path.write_text(json.dumps({"sessions": [session(now, 18, "123")]}), encoding="utf-8")
            rendered = render_from_schedule(path, course_ids=["209806"], family="BLS", now=now)
        self.assertIn('/classes/123.html', rendered)
        self.assertNotIn('enrollware.com', rendered)
        self.assertIn('Planning two to three weeks ahead', rendered)


if __name__ == "__main__":
    unittest.main()
