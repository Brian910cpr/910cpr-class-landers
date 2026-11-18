from datetime import datetime
import json
import unittest

from scripts.publish_scheduling_landscape import operational_lane_cells, quarter_hour_cells, public_scheduling_landscape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SchedulingLandscapeOperationalLanesTest(unittest.TestCase):
    def test_portrait_details_panel_and_delayed_hover_contract(self):
        html = (ROOT / "docs" / "admin" / "scheduling-landscape.html").read_text(encoding="utf-8")
        script = (ROOT / "docs" / "admin" / "scheduling-landscape-lanes.js").read_text(encoding="utf-8")
        self.assertIn(".site-theme-toggle{display:none!important}", html)
        self.assertIn(".drawer{position:static", html)
        self.assertIn("setTimeout(() => cell.click(), 650)", script)
        self.assertIn('matrix.addEventListener("pointerout"', script)
        self.assertIn('document.documentElement.dataset.theme = "light"', script)
        self.assertIn("let m=0;while(m<24*60)", html)
        self.assertIn("--slot-h:4px", html)
        self.assertIn(".matrix-wrap{height:auto;overflow:visible", html)
        self.assertIn("table-layout:fixed", html)
        self.assertIn('<div class="topbar">', html)
        self.assertIn('height:clamp(118px,15dvh,260px)', html)
        self.assertIn('grid-template-columns:62px minmax(0,1fr) 62px minmax(0,1fr)', html)
        self.assertIn('event.key === "ArrowLeft"', script)
        self.assertIn('event.key === "ArrowRight"', script)
        self.assertIn("fitFullDayToViewport", script)
        self.assertIn("window.visualViewport?.height", script)
        self.assertIn("viewportHeight - wrap.getBoundingClientRect().top", script)
        self.assertIn('window.addEventListener("resize"', script)
        self.assertIn("new ResizeObserver(fitSoon)", script)

    def test_feed_declares_a_complete_midnight_to_midnight_grid(self):
        publisher = (ROOT / "scripts" / "publish_scheduling_landscape.py").read_text(encoding="utf-8")
        self.assertIn('{"startTime": "00:00", "endTime": "24:00", "stepMinutes": 15}', publisher)

    def test_partial_intervals_fill_each_overlapping_quarter_hour(self):
        self.assertEqual(
            [("2026-08-25", "09:00"), ("2026-08-25", "09:15")],
            quarter_hour_cells(datetime.fromisoformat("2026-08-25T09:07:00-04:00"), datetime.fromisoformat("2026-08-25T09:22:00-04:00")),
        )

    def test_builds_enrollware_source_and_brian_unavailability_lanes(self):
        schedule = {"build": {"source_mode": "enrollware_ical_authoritative"}, "sessions": [{
            "session_id": "13946813", "course_name": "BLS Renewal",
            "start_at": "2026-08-25T09:15:00-04:00", "end_at": "2026-08-25T11:15:00-04:00",
        }]}
        availability = {"events": [{
            "instructor_key": "brian", "source_key": "brian_do_not_schedule", "title": "Unavailable",
            "start": "2026-08-25T13:00:00-04:00", "end": "2026-08-25T14:00:00-04:00",
        }]}
        cells = operational_lane_cells(schedule, availability)
        enrollware = [cell for cell in cells if cell["laneId"] == "enrollware"]
        brian = [cell for cell in cells if cell["laneId"] == "brian"]
        self.assertEqual(8, len(enrollware))
        self.assertTrue(all(cell["result"] == "enrollware-ical" for cell in enrollware))
        self.assertEqual(4, len(brian))
        self.assertTrue(all(cell["result"] == "unavailable" for cell in brian))
        self.assertNotIn("location", brian[0]["items"][0])
        self.assertEqual("Unavailable", brian[0]["items"][0]["title"])


    def test_public_landscape_removes_private_intake_and_travel_diagnostics(self):
        secret = "PRIVATE_PARTICIPANT_AND_RESOURCE_SENTINEL"
        when = "2026-11-25T09:30:00-05:00"
        end = "2026-11-25T11:30:00-05:00"
        payload = {
            "schemaVersion": "scheduling-landscape.v1",
            "generatedAt": "2026-11-18T15:01:00Z", "builtAt": "2026-11-18T15:01:30Z",
            "buildId": "test", "pageId": "scheduling-landscape", "timezone": "America/New_York",
            "window": {"startDate": "2026-11-25", "endDate": "2026-11-25"},
            "timeGrid": {"startTime": "00:00", "endTime": "24:00", "stepMinutes": 15},
            "courses": [{"courseId": "209806", "courseName": "Public BLS"}],
            "cells": [{
                "date": "2026-11-25", "startTime": "09:30", "courseId": "209806",
                "courseFamily": "BLS", "pageKey": "bls", "result": "suppressed",
                "instructor": secret, "location": secret, "registrationUrl": secret,
                "sessionId": secret, "edgeIds": [secret], "sourceSessionIds": [secret],
                "availabilityWindow": {"label": secret},
                "reasons": ["private booking " + secret, "RECONCILIATION_REQUIRED"],
            }],
            "laneCells": [
                {"date": "2026-11-25", "startTime": "09:30", "laneId": "enrollware",
                 "items": [{"sessionId": secret, "courseName": secret,
                            "start": when, "end": end}], "sourceLabel": secret},
                {"date": "2026-11-25", "startTime": "09:45", "laneId": "brian",
                 "items": [{"title": secret, "sourceKey": secret}], "sourceLabel": secret},
            ],
            "dailyTruth": {"2026-11-25": {
                "hardBlocks": [{"label": secret, "location": secret, "instructor": secret,
                                "source": secret, "start": when, "end": end}],
                "classes": [{"canonicalSessionId": secret, "externalClassId": secret,
                             "courseName": secret, "registeredCount": 1, "source": secret,
                             "start": when, "end": end}],
            }},
            "sourcePages": {"bls": {
                "generatedAt": "2026-11-18T15:01:00Z", "schedulingModel": "layered-publication.v2",
                "counts": {"failed_windows": 11, "publicSelectableOfferCount": 6},
                "rejectionReasonCounts": {"private " + secret: 2},
                "layeredLandscape": {"sources": [{
                    "sourceId": secret, "role": "blocking", "resource": secret,
                    "courseId": secret, "registeredCount": 1, "start": when, "end": end}],
                    "occupiedBlocks": [{"id": secret, "source_ids": [secret],
                                        "start": when, "end": end}]},
            }},
            "reconciliationIssues": [
                {"date": "2026-11-25", "code": "HARD_BLOCK_COLLISION",
                 "reason": "travel to " + secret, "resource": secret,
                 "instructor": secret, "start": when, "end": end},
                {"start": when, "reason": secret},
            ],
            "operationalLaneSources": {"enrollware": secret},
            "authority": "block_start_time_selector.build_block_schedule_page",
        }
        sanitized = public_scheduling_landscape(payload)
        wire = json.dumps(sanitized)
        self.assertNotIn(secret, wire)
        for forbidden_key in (
            "canonicalSessionId", "externalClassId", "sessionId", "sourceKey",
            "sourceSessionIds", "edgeIds", "operationalLaneSources",
            "registrationUrl", "registeredCount\": 1", "instructor", "resource", "location"
        ):
            self.assertNotIn('"' + forbidden_key + '"', wire)
        self.assertEqual("09:30", sanitized["cells"][0]["startTime"])
        self.assertEqual("suppressed", sanitized["cells"][0]["result"])
        self.assertEqual(["RECONCILIATION_REQUIRED"], sanitized["cells"][0]["reasons"])
        self.assertEqual(2, len(sanitized["reconciliationIssues"]))
        self.assertEqual("HARD_BLOCK_COLLISION", sanitized["reconciliationIssues"][0]["code"])
        self.assertEqual(when, sanitized["dailyTruth"]["2026-11-25"]["classes"][0]["start"])
        self.assertEqual(end, sanitized["dailyTruth"]["2026-11-25"]["hardBlocks"][0]["end"])
        self.assertEqual("Occupied interval", sanitized["laneCells"][0]["items"][0]["title"])
        self.assertEqual(11, sanitized["sourcePages"]["bls"]["counts"]["failed_windows"])
        self.assertEqual(when, sanitized["sourcePages"]["bls"]["layeredLandscape"]["sources"][0]["start"])
        self.assertNotIn("registeredCount", sanitized["sourcePages"]["bls"]["layeredLandscape"]["sources"][0])


if __name__ == "__main__":
    unittest.main()
