from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAXIM_PAGE = ROOT / "docs" / "corp" / "maxim.html"
SHARED_AVAILABILITY = ROOT / "docs" / "assets" / "resolved-selector-availability.js"
PUBLIC_SELECTOR_PAGES = [ROOT / "docs" / "bls.html", ROOT / "docs" / "heartsaver.html"]
SELECTOR_GENERATOR = ROOT / "scripts" / "build_bls_block_schedule_pilot.py"
MAXIM_EDGE_FUNCTION = ROOT / "supabase" / "functions" / "maxim-portal" / "index.ts"

EXPECTED_VARIANTS = {
    "Initial": "209806",
    "Renewal": "359474",
    "HeartCode": "210549",
    "In Person": "209809",
    "Online + Skills": "329495",
}


def read_page() -> str:
    return MAXIM_PAGE.read_text(encoding="utf-8")


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

    def test_maxim_consumes_exact_public_resolved_selector_artifacts(self) -> None:
        html = read_page()
        self.assertIn("bls:'/data/block-selector-availability/bls.json'", html)
        self.assertIn("hs:'/data/block-selector-availability/heartsaver.json'", html)
        self.assertIn('src="/assets/resolved-selector-availability.js?v=20260723.1"', html)
        self.assertIn("ResolvedSelectorAvailability.filterDatesByCourse", html)
        self.assertIn("ResolvedSelectorAvailability.selectableStartTimes", html)
        self.assertIn("ResolvedSelectorAvailability.isSelectableDate", html)
        self.assertIn("payload.schemaVersion!==ResolvedSelectorAvailability.schemaVersion", html)
        self.assertNotIn("/data/schedule_future.json", html)
        self.assertNotIn("function isValidPublicRow", html)
        self.assertNotIn("public_direct_booking", html)
        self.assertNotIn("registration_status", html)

    def test_public_pages_and_generator_use_the_same_shared_projection(self) -> None:
        self.assertTrue(SHARED_AVAILABILITY.exists())
        for path in [*PUBLIC_SELECTOR_PAGES, SELECTOR_GENERATOR]:
            source = path.read_text(encoding="utf-8")
            self.assertIn("ResolvedSelectorAvailability.filterDatesByCourse", source, path)
            self.assertIn("ResolvedSelectorAvailability.selectableStartTimes", source, path)
            self.assertIn("ResolvedSelectorAvailability.isSelectableDate", source, path)

    def test_registration_revalidation_uses_canonical_selector_artifact(self) -> None:
        source = MAXIM_EDGE_FUNCTION.read_text(encoding="utf-8")
        self.assertIn("/data/block-selector-availability/${selector}.json", source)
        self.assertIn('payload.schemaVersion !== "selector-resolved-availability.v1"', source)
        self.assertIn("canonicalSlotKey(course)", source)
        self.assertNotIn("schedule_future.json", source)

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
        self.assertIn("openEmployee('${p.id||personIdFromName(p.name)}')", html)
        self.assertIn("method:'PATCH'", html)
        self.assertIn("method:'DELETE'", html)
        self.assertIn("Remove from active list", html)
        self.assertIn("history will be preserved", html)
        self.assertIn("scheduleEmployee", html)

    def test_training_flow_uses_connected_stage_values_with_quiet_fallbacks(self) -> None:
        html = read_page()
        self.assertIn("function flowStageContent", html)
        self.assertIn('Connected data not available yet', html)
        self.assertIn("person.expirationDate", html)
        self.assertIn("person.lastClassUrl", html)
        self.assertIn("person.classDate||person.detail", html)
        self.assertIn("person.eCardCode", html)
        self.assertIn("person.eCardUrl", html)
        self.assertIn("person.invoiceUrl", html)
        self.assertIn("function lastNameOf", html)
        self.assertIn(".sort((a,b)=>lastNameOf(a).localeCompare(lastNameOf(b)", html)

    def test_maxim_portal_uses_supabase_access_gate_and_persistent_employee_api(self) -> None:
        html = read_page()
        self.assertIn('id="accessGate"', html)
        self.assertIn("functions/v1/maxim-portal", html)
        self.assertIn("MAXIM_API_BASE+'/login'", html)
        self.assertIn("MAXIM_API_BASE+'/employees'", html)
        self.assertIn("sessionStorage.setItem('maximPortalSession'", html)
        self.assertNotIn("2106", html)
        self.assertNotIn("/api/corp/maxim", html)

    def test_empty_canonical_course_projection_is_shown_without_fallback(self) -> None:
        self.assertIn(
            '<div class="empty">No current valid dates returned for ',
            read_page(),
        )


if __name__ == "__main__":
    unittest.main()
