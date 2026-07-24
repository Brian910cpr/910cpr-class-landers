from __future__ import annotations

import json
import re
import unittest
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAXIM_PAGE = ROOT / "docs" / "corp" / "maxim.html"
SCHEDULE_FUTURE = ROOT / "docs" / "data" / "schedule_future.json"

EXPECTED_VARIANTS = {
    "Initial": "209806",
    "Renewal": "359474",
    "HeartCode": "210549",
    "In Person": "209809",
    "Online + Skills": "329495",
}


def read_page() -> str:
    return MAXIM_PAGE.read_text(encoding="utf-8")


def schedule_reference_now(payload: dict) -> datetime:
    generated_at = payload.get("build", {}).get("generated_at")
    if generated_at:
        return datetime.fromisoformat(generated_at)
    return datetime.now().astimezone()


def parse_start(row: dict) -> datetime | None:
    raw = row.get("start_at") or row.get("start") or row.get("start_datetime")
    if not raw:
        return None
    return datetime.fromisoformat(raw)


def is_public_valid_row(row: dict, course_id: str, now: datetime) -> bool:
    start = parse_start(row)
    if start is None:
        return False
    if start.tzinfo is None and now.tzinfo is not None:
        start = start.replace(tzinfo=now.tzinfo)
    return (
        str(row.get("course_id")) == course_id
        and start >= now
        and str(row.get("registration_status") or "open").lower() == "open"
        and row.get("public_direct_booking") is not False
        and bool(row.get("registration_url"))
    )


class MaximCorporatePortalTests(unittest.TestCase):
    def test_maxim_course_pills_map_to_exact_authoritative_variants(self) -> None:
        html = read_page()
        for label, course_id in EXPECTED_VARIANTS.items():
            self.assertIn(f"label:'{label}',courseId:'{course_id}'", html)
            self.assertIn("data-course-id=\"'+v.courseId+'\"", html)

        self.assertNotIn("const courses=", html)
        self.assertNotIn("available:[", html)
        self.assertNotIn("aug:[", html)
        self.assertNotIn("times:[", html)

    def test_maxim_uses_schedule_future_with_public_scheduler_rules(self) -> None:
        html = read_page()
        self.assertIn("const SCHEDULE_FUTURE_URL='/data/schedule_future.json'", html)
        self.assertIn("registration_status||'open'", html)
        self.assertIn("row.public_direct_booking!==false", html)
        self.assertIn("!!row.registration_url", html)
        self.assertIn("start>=now", html)

    def test_maxim_refreshes_availability_on_required_paths(self) -> None:
        html = read_page()
        required_refreshes = {
            "initial": r"refreshAvailability\('initial'\)",
            "course": r"refreshAvailability\('course'\)",
            "variant": r"refreshAvailability\('variant'\)",
            "date": r"refreshAvailability\('date'\)",
            "schedule-for": r"refreshAvailability\('schedule-for'\)",
            "confirm": r"refreshAvailability\('confirm'\)",
        }
        for reason, pattern in required_refreshes.items():
            self.assertRegex(html, pattern, reason)

        self.assertIn("cache:'no-store'", html)
        self.assertIn("Date.now()", html)
        self.assertIn("that class time is no longer available", html)

    def test_maxim_has_gantt_filters_and_selection_aware_registration(self) -> None:
        html = read_page()
        self.assertIn('id="trainingGantt"', html)
        self.assertIn('id="flowSearch"', html)
        self.assertIn('id="flowStage"', html)
        self.assertIn('id="flowAccount"', html)
        self.assertIn("registerBox.classList.remove('open')", html)
        self.assertIn("Register for ${activeVariant().label} at ${selectedTime}", html)

    def test_google_voice_chat_is_an_explicit_nonfunctional_shell(self) -> None:
        html = read_page()
        self.assertIn("Google Voice not connected", html)
        self.assertIn("no supported SMS API is available", html)
        self.assertIn('placeholder="Message the Maxim group" disabled', html)

    def test_employee_names_open_edit_and_safe_deactivation_drawer(self) -> None:
        html = read_page()
        self.assertIn('id="employeeBackdrop"', html)
        self.assertIn("openEmployee('${personIdFromName(p.name)}')", html)
        self.assertIn("method:'PATCH'", html)
        self.assertIn("method:'DELETE'", html)
        self.assertIn("Remove from active list", html)
        self.assertIn("history will be preserved", html)
        self.assertIn("scheduleEmployee", html)

    def test_each_maxim_variant_resolves_independent_authoritative_rows(self) -> None:
        payload = json.loads(SCHEDULE_FUTURE.read_text(encoding="utf-8"))
        now = schedule_reference_now(payload)
        sessions = payload.get("sessions", [])
        counts = {
            label: sum(1 for row in sessions if is_public_valid_row(row, course_id, now))
            for label, course_id in EXPECTED_VARIANTS.items()
        }

        self.assertEqual(set(counts), set(EXPECTED_VARIANTS))
        for label, count in counts.items():
            self.assertGreater(count, 0, f"{label} resolved no authoritative valid rows")

        self.assertNotEqual(EXPECTED_VARIANTS["Initial"], EXPECTED_VARIANTS["Renewal"])
        self.assertNotEqual(EXPECTED_VARIANTS["In Person"], EXPECTED_VARIANTS["Online + Skills"])


if __name__ == "__main__":
    unittest.main()
