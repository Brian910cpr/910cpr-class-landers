from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
import subprocess
import unittest
from unittest.mock import patch

from scripts import validate_public_refresh_output as output
from scripts.block_start_time_selector import (
    contextual_course, course_rules_by_id, load_block_schedule_page_configs,
)
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload
from scripts.layered_publication_adapter import publish
import test_layered_publication_adapter as source


class FrozenClock(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls.fromisoformat("2026-10-05T16:00:00+00:00").astimezone(tz)


class LayeredRequestReleaseTests(unittest.TestCase):
    def compact(self, occupied=False, key="heartsaver"):
        fixture = source.LayeredPublicationTests()
        fixture.setUp()
        fixture.windows, fixture.coverage = [], []
        window = fixture.window(11, "08:00", "19:00", next_day=False,
                                name="Amy Arnold" if key in {"acls", "pals"} else "Brian Ennis")
        window.update(public_location_allowed=True, visibility="public", public_selectable=True,
                      source_live_availability_block={"private": "SENSITIVE-CALENDAR-ID"})
        fixture.coverage[0]["instructor_person_id"] = window["person_id"]
        fixture.policy.update(verified_instructor_identity=True, require_verified_day_gravity=True)
        page = load_block_schedule_page_configs()[key]
        cid = "209809" if key in {"heartsaver", "uscg_first_aid_cpr_aed"} else next(
            o["course_id"] for o in page["course_options"] if o["delivery_mode"] == "in-person"
        )
        if key in {"acls", "pals"}:
            rules = course_rules_by_id(json.loads(
                (source.ROOT / "data/inventory/course_consumption_rules.json").read_text()))
            course = contextual_course(cid, {}, {cid: dict(course_id=cid, blended_classroom_skills="classroom")}, rules)
            course["blended_classroom_skills"] = "classroom"
            fixture.courses.append(course)
        elif cid not in {course["course_id"] for course in fixture.courses}:
            fixture.courses.append(dict(course_id=cid, course_family=page["family"], kind="full",
                                        clean_course_name="Exact classroom", blended_classroom_skills="classroom",
                                        duration_minutes=120, minimum_reservation_block_minutes=150))
        if occupied:
            fixture.add(11, "12:00", "14:30", "359474", count=1, visibility="private",
                        effective_instructor_person_id=window["person_id"],
                        stored_instructor_person_id=window["person_id"])
        p = publish(fixture.calculation(), page, fixture.courses, fixture.windows, fixture.now,
                    lambda *_: ("SENSITIVE-DAY-ID", "SENSITIVE-SESSION-ID", None,
                                "unverified_appointment_container_owner"),
                    lambda *_: [], (), require_verified_day_gravity=True, strict_instructor_identity=True,
                    request_course_ids=[cid], request_qualification=lambda *_: True)
        return public_selector_availability_payload(p)

    def validate(self, payload, key="heartsaver"):
        with patch.object(output, "datetime", FrozenClock), patch.object(output, "load_json", return_value=payload):
            return output.validate_selector(key, set())

    def test_actual_compact_requests_are_accepted_without_a_checkout_or_private_ids(self):
        for occupied in (False, True):
            with self.subTest(occupied=occupied):
                payload = self.compact(occupied=occupied)
                rows = [c for d in payload["dates"] for s in d["startTimes"] for c in s["courses"]]
                self.assertTrue(rows)
                self.assertEqual({c["scheduleRole"] for c in rows}, {"barnacle" if occupied else "open_day"})
                self.assertNotIn("SENSITIVE", json.dumps(payload))
                self.assertNotIn("fixture-11-12", json.dumps(payload))
                if occupied:
                    self.assertTrue(all(c["startTime"] < "12:00" or c["startTime"] >= "14:30" for c in rows))
                self.assertEqual(self.validate(payload)["offers"], len(rows))
                script = "const a=require('./docs/assets/resolved-selector-availability.js'); console.log(JSON.stringify(a.registrationAction(JSON.parse(process.argv[1]))));"
                action = json.loads(subprocess.check_output(["node","-e",script,json.dumps(rows[0])], cwd=source.ROOT, text=True))
                self.assertEqual(action["mode"], "request")
                self.assertTrue(action["href"].startswith("mailto:brian@910cpr.com?"))
                self.assertIn("No seat is reserved", action["notice"])

    def test_route_and_authority_tampering_fail(self):
        base = self.compact(occupied=True)
        for key, value in (("registrationUrl", "/register/?session=123"),
                           ("appointmentUrl", "https://legacy.example/enroll"),
                           ("appointmentDayId", "secret"), ("attached_to_session_id", "secret"),
                           ("availabilityBlockId", "secret"), ("sourceAvailabilityBlock", {}),
                           ("courseId", "509474"), ("courseId", "359474"), ("date", "2026-10-12"),
                           ("startTime", "10:30"), ("scheduleRole", "weird"),
                           ("schedulerConsumptionMinutes", 0), ("deliveryMode", "blended"),
                           ("occupiedUntil", "2026-10-11T10:30:00-04:00"),
                           ("validUntil", "2026-10-05T15:59:59Z"),
                           ("validUntil", "2026-10-05T18:00:00Z")):
            p = deepcopy(base)
            p["dates"][0]["startTimes"][0]["courses"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.validate(p)
        for attr, value in (("pageKey", "bls"), ("schedulingModel", "legacy"), ("anchor_policy", {"finalized": True, "mode": "legacy"}),
                            ("synthesisBlockedDates", ["2026-10-11"])):
            p = deepcopy(base)
            p[attr] = value
            with self.subTest(attr=attr), self.assertRaises(ValueError):
                self.validate(p)

    def test_all_generated_family_feeds_are_in_release_validator_scope(self):
        configured = set(load_block_schedule_page_configs())
        self.assertEqual(set(output.REQUIRED_SELECTORS), configured)
        for key in sorted(configured):
            with self.subTest(key=key):
                self.assertGreater(self.validate(self.compact(key=key), key)["offers"], 0)


if __name__ == "__main__":
    unittest.main()
