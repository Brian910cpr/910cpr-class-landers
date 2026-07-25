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
        self.assertIn('id="flowSort"', html)
        self.assertIn('<option value="gantt" selected>Gantt order</option>', html)
        self.assertIn('id="flowReset"', html)
        self.assertIn("return (Number(a.stage)-Number(b.stage))||nameOrder()", html)
        self.assertIn("flowSort.value='gantt'", html)
        self.assertIn("flowSearch.value=''", html)
        self.assertIn("flowStage.value='all'", html)
        self.assertIn("flowAccount.value='all'", html)
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

    def test_training_flow_uses_compact_connected_workflow_cells(self) -> None:
        html = read_page()
        self.assertIn("function flowStageContent", html)
        self.assertIn("<div>eCard #</div><div>Invoice #</div>", html)
        self.assertIn("grid-template-columns:24% 14% 18% 18% 13% 13%", html)
        self.assertIn(".layout{grid-template-columns:minmax(360px,40fr) minmax(0,60fr)", html)
        self.assertIn(".gantt{min-width:0;width:100%}", html)
        self.assertIn(".gantt-pill{display:none!important}", html)
        self.assertIn("person.expirationDate", html)
        self.assertIn("person.classDate||stage===2", html)
        self.assertIn("person.eCardCode", html)
        self.assertIn("person.invoiceUrl", html)
        self.assertIn("No eCard found yet", html)
        self.assertIn("Schedule for them", html)
        self.assertIn("returnToComingDue", html)
        self.assertIn("Wilmingtonoffice%40maxim.com", html)
        self.assertIn("https://www.910cpr.com/go/myecards", html)
        self.assertIn("function lastNameOf", html)
        self.assertIn("function compareTrainingFlow", html)
        self.assertIn(".sort(compareTrainingFlow)", html)

    def test_workflow_columns_have_the_requested_meaning_and_actions(self) -> None:
        html = read_page()
        self.assertIn("<div>Participant</div><div>Coming Due</div><div>Link Sent</div>", html)
        self.assertIn("<div>Registered</div><div>eCard #</div><div>Invoice #</div>", html)
        self.assertIn("else cell.push('<span class=\"flow-value\">Unknown</span>')", html)
        self.assertIn(">Send link</button>", html)
        self.assertIn(">Schedule</button>", html)
        self.assertIn(">Skip</button>", html)
        self.assertIn(">Reschedule</button>", html)
        self.assertIn(">Delete</button>", html)
        self.assertIn("No eCard found yet", html)
        self.assertNotIn("person.invoiceLabel||'Not yet available'", html)

    def test_desktop_workflow_scrolls_inside_a_fixed_viewport_box(self) -> None:
        html = read_page()
        self.assertIn(".flow{position:sticky;top:12px;height:calc(100vh - 24px)", html)
        self.assertIn(".gantt-wrap{flex:1 1 auto;min-height:0;overflow:auto", html)
        self.assertIn(".gantt-head{position:sticky;top:0", html)
        self.assertIn(".flow{position:static;height:auto;max-height:none}", html)

    def test_link_sent_date_is_persisted_before_opening_email(self) -> None:
        html = read_page()
        source = MAXIM_EDGE_FUNCTION.read_text(encoding="utf-8")
        self.assertIn("/link-sent", html)
        self.assertIn("markScheduleLinkSent", source)
        self.assertIn("link_sent_at: sentAt", source)
        self.assertIn("linkSentDate: row.link_sent_at", source)
        self.assertIn('route[2] === "link-sent"', source)

    def test_return_to_due_is_a_persistent_authenticated_workflow_action(self) -> None:
        html = read_page()
        source = MAXIM_EDGE_FUNCTION.read_text(encoding="utf-8")
        self.assertIn("/return-to-due", html)
        self.assertIn("returnEmployeeToComingDue", source)
        self.assertIn('workflow_stage: 0', source)
        self.assertIn('status: "superseded"', source)
        self.assertIn("current_external_registration_id: null", source)
        self.assertIn('route[2] === "return-to-due"', source)

    def test_employee_api_returns_real_registration_date_and_url(self) -> None:
        source = MAXIM_EDGE_FUNCTION.read_text(encoding="utf-8")
        self.assertIn("maxim_registration_requests?select=", source)
        self.assertIn("starts_at", source)
        self.assertIn("registration_url", source)
        self.assertIn("classDate: registration?.starts_at", source)
        self.assertIn("registrationUrl: registration?.registration_url", source)

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
