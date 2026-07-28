from __future__ import annotations

import unittest
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAXIM_PAGE = ROOT / "docs" / "corp" / "maxim.html"
SHARED_AVAILABILITY = ROOT / "docs" / "assets" / "resolved-selector-availability.js"
PUBLIC_SELECTOR_PAGES = [ROOT / "docs" / "bls.html", ROOT / "docs" / "heartsaver.html"]
SELECTOR_GENERATOR = ROOT / "scripts" / "build_bls_block_schedule_pilot.py"
MAXIM_EDGE_FUNCTION = ROOT / "supabase" / "functions" / "maxim-portal" / "index.ts"
MAXIM_MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "20260725031000_maxim_atomic_registration_replacement.sql"
)

EXPECTED_VARIANTS = {
    "Initial": "209806",
    "Renewal": "359474",
    "HeartCode": "210549",
    "In Person": "209809",
    "Online + Skills": "329495",
}


def read_page() -> str:
    return MAXIM_PAGE.read_text(encoding="utf-8")

def run_dashboard_eligibility(cases: list[dict[str, object]]) -> list[bool]:
    script = r"""
const fs=require('fs');
const html=fs.readFileSync(process.argv[1],'utf8');
const start=html.indexOf('function easternDateParts');
const end=html.indexOf('async function loadEmployees',start);
if(start<0||end<0)throw new Error('eligibility functions not found');
eval(html.slice(start,end));
const cases=JSON.parse(process.argv[2]);
process.stdout.write(JSON.stringify(cases.map(item=>isDashboardEligible(item.person,new Date(item.viewedAt)))));
"""
    completed = subprocess.run(
        ["node", "-e", script, str(MAXIM_PAGE), json.dumps(cases)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


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
        self.assertIn(".gantt-row{height:44px;min-height:44px}", html)
        self.assertIn('class="participant-icon"', html)
        self.assertIn('class="participant-meta"', html)
        self.assertIn(".gantt-head>div:first-child,.gantt-person{position:sticky", html)
        self.assertIn("const stageOrder=aStage-bStage", html)
        self.assertIn("return milestoneOrder||nameOrder()", html)
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
        self.assertIn("<div>eCard / expiration</div><div>Invoice</div>", html)
        self.assertIn("grid-template-columns:24% 14% 18% 18% 13% 13%", html)
        self.assertIn(".layout{grid-template-columns:minmax(360px,40fr) minmax(0,60fr)", html)
        self.assertIn(".gantt{min-width:0;width:100%}", html)
        self.assertIn(".gantt-pill{display:none!important}", html)
        self.assertIn("person.expirationDate", html)
        self.assertIn("if(index===2){if(person.classDate)", html)
        self.assertIn("person.eCardCode", html)
        self.assertIn("person.invoiceUrl", html)
        self.assertIn("No eCard found yet", html)
        self.assertIn("Schedule for them", html)
        self.assertIn("returnToComingDue", html)
        self.assertIn("Wilmingtonoffice%40maxim.com", html)
        self.assertIn("https://ecards.heart.org/Student/MyeCards", html)
        self.assertIn("function lastNameOf", html)
        self.assertIn("function compareTrainingFlow", html)
        self.assertIn(".sort(compareTrainingFlow)", html)

    def test_workflow_columns_have_the_requested_meaning_and_actions(self) -> None:
        html = read_page()
        self.assertIn("<div>Participant</div><div>Coming Due / Link</div><div>Status</div>", html)
        self.assertIn("<div>Class date / time</div><div>eCard / expiration</div>", html)
        self.assertIn("completed=Boolean(person.eCardCode)", html)
        self.assertIn(">Send link</button>", html)
        self.assertIn(">Schedule</button>", html)
        self.assertIn(">Skip</button>", html)
        self.assertIn(">Reschedule</button>", html)
        self.assertIn("returnToComingDue", html)
        self.assertIn("No eCard found yet", html)
        self.assertNotIn("person.invoiceLabel||'Not yet available'", html)

    def test_desktop_workflow_scrolls_inside_a_fixed_viewport_box(self) -> None:
        html = read_page()
        self.assertIn(".flow{position:sticky;top:12px;height:calc(100vh - 24px)", html)
        self.assertIn(".gantt-wrap{flex:1 1 auto;min-height:0;overflow:auto", html)
        self.assertIn(".gantt-head{position:sticky;top:0", html)
        self.assertIn(".flow{position:static;height:auto;max-height:none}", html)

    def test_participant_column_shows_searchable_clickable_email_state(self) -> None:
        html = read_page()
        self.assertIn("${p.name} ${p.email} ${p.course}", html)
        self.assertIn('class="gantt-email" href="mailto:', html)
        self.assertIn("Email unavailable", html)

    def test_link_sent_date_is_persisted_before_opening_email(self) -> None:
        html = read_page()
        source = MAXIM_EDGE_FUNCTION.read_text(encoding="utf-8")
        self.assertIn("/link-sent", html)
        self.assertIn("markScheduleLinkSent", source)
        self.assertIn("link_sent_at: sentAt", source)
        self.assertIn("linkSentDate: row.link_sent_at", source)
        self.assertIn('route[2] === "link-sent"', source)
        self.assertIn("person.stage=result.workflowStage", html)
        self.assertIn("profiles[0].current_external_registration_id ? 2 : 1", source)
        self.assertIn("Scheduling is closed because this employee has an eCard.", source)

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
        self.assertIn("const currentClassDate = registration?.starts_at || row.scheduled_class_date", source)
        self.assertIn("registrationUrl: registration?.registration_url", source)

    def test_employee_api_returns_imported_certification_baseline(self) -> None:
        html = read_page()
        source = MAXIM_EDGE_FUNCTION.read_text(encoding="utf-8")
        self.assertIn("prior_class_date", source)
        self.assertIn("expiration_date", source)
        self.assertIn("prior_ecard_code", source)
        self.assertIn("scheduled_class_date", source)
        self.assertIn("expirationDate: row.expiration_date", source)
        self.assertIn("classDate: currentClassDate", source)
        self.assertIn("ganttMilestone(a,aStage)", html)

    def test_employee_api_limits_due_and_retains_searchable_history(self) -> None:
        html = read_page()
        source = MAXIM_EDGE_FUNCTION.read_text(encoding="utf-8")
        self.assertIn("function easternMonthBoundary", source)
        self.assertIn("const afterNextMonth = easternMonthBoundary(2)", source)
        self.assertIn("expirationDate >= currentMonth", source)
        self.assertIn("expirationDate < afterNextMonth", source)
        self.assertIn('history: mapped.filter((row: any) => row.bucket === "history")', source)
        self.assertIn('invoiceLabel: workflowStage === 5 && currentClassDate ? "INVOICED"', source)
        self.assertIn("function ecardCodeFromStatus", source)
        self.assertIn("const priorECardCode = row.prior_ecard_code || null", source)
        self.assertIn("workflowStage >= 4", source)
        self.assertIn("${p.eCardCode||''}", html)
        self.assertIn("invoicedOrder=(aStage===5?1:0)", html)

    def test_gantt_order_uses_the_displayed_progression_not_stale_workflow_stage(self) -> None:
        html = read_page()
        self.assertIn("function ganttStage(person,viewedAt=new Date())", html)
        self.assertIn("if(person.eCardCode)return 4", html)
        self.assertIn("if(person.classDate&&new Date(person.classDate)<viewedAt)return 3", html)
        self.assertIn("if(person.registrationId||person.classDate)return 2", html)
        self.assertIn("if(person.linkSentDate)return 1", html)
        self.assertIn("const stageOrder=aStage-bStage", html)
        self.assertIn("String(ganttStage(p))===stage", html)
        self.assertIn("const current=Math.min(ganttStage(p),4)", html)

    def test_historical_certification_facts_do_not_advance_current_cycle(self) -> None:
        html = read_page()
        source = MAXIM_EDGE_FUNCTION.read_text(encoding="utf-8")
        self.assertIn("classDate:employee.classDate||null", html)
        self.assertNotIn("classDate:employee.classDate||employee.priorClassDate", html)
        self.assertIn("priorECardCode:employee.priorECardCode||null", html)
        self.assertIn("const priorWorkflowClassDate = (workflowStage >= 3 || importedCompletion)", source)
        self.assertIn("priorWorkflowClassAgeDays >= 0", source)
        self.assertIn("priorWorkflowClassAgeDays <= 14", source)
        self.assertIn("const eCardCode = workflowStage >= 4 && currentClassDate", source)
        self.assertIn("Due ${safeText(displayDateOnly(person.expirationDate))}", html)

    def test_old_stage_three_class_ecard_and_invoice_are_context_only(self) -> None:
        source = MAXIM_EDGE_FUNCTION.read_text(encoding="utf-8")
        self.assertIn("recentPriorWorkflowClassDate", source)
        self.assertIn("registration?.starts_at || row.scheduled_class_date", source)
        self.assertIn("invoiceLabel: workflowStage === 5 && currentClassDate", source)
        self.assertIn("invoiceDate: workflowStage === 5 && currentClassDate", source)

    def test_current_class_location_reschedule_and_invoice_window_are_explicit(self) -> None:
        html = read_page()
        self.assertIn("function classWithinLastMonths(person,months,viewedAt=new Date())", html)
        self.assertIn("recentInvoiceClass=classWithinLastMonths(person,12)", html)
        self.assertIn("if(person.locationKey)cell.push", html)
        self.assertIn("scheduleFlowPerson('${person.id}',true)", html)
        self.assertIn("if(index===4&&recentInvoiceClass)", html)

    def test_scheduled_people_hide_due_date_and_move_actions_to_class_date(self) -> None:
        html = read_page()
        self.assertIn("if(index===0&&!person.classDate)", html)
        self.assertIn("if(index===2){if(person.classDate)", html)
        self.assertIn("emailScheduleLink('${person.id}')", html)
        self.assertIn(">Reschedule</button>", html)
        self.assertIn("month:'2-digit',day:'2-digit',year:'numeric'", html)
        self.assertIn("`${match[2]}/${match[3]}/${match[1]}`", html)

    def test_participant_skip_remove_prevents_resurfacing_but_preserves_searchable_history(self) -> None:
        html = read_page()
        source = MAXIM_EDGE_FUNCTION.read_text(encoding="utf-8")
        self.assertIn('title="Skip / Remove"', html)
        self.assertIn("They will not resurface for future recertification", html)
        self.assertIn("method:'DELETE'", html)
        self.assertIn("active: false", source)
        self.assertIn('history: mapped.filter((row: any) => row.bucket === "history")', source)
        self.assertIn("p.bucket==='history'&&q", html)

    def test_visible_ecards_copy_as_aha_batches_of_twenty(self) -> None:
        html = read_page()
        self.assertIn("function normalizeEcardCode(code)", html)
        self.assertIn("replace(/[^A-Za-z0-9]/g,'')", html)
        self.assertIn("visibleEcardCodes=[...new Set(rows.map", html)
        self.assertIn("function copyVisibleEcardsAndOpen(clickedCode)", html)
        self.assertIn("batchSize=20", html)
        self.assertIn("batch.join('\\n')", html)
        self.assertIn("Math.floor(clickedIndex/batchSize)", html)
        self.assertIn("https://ecards.heart.org/Student/MyeCards", html)
        self.assertIn("navigator.clipboard.writeText(text)", html)
        self.assertIn("Copied batch ${batchIndex+1} of ${batchCount}", html)
        self.assertNotIn("copyEcardAndOpen(", html)

    def test_completed_people_archive_after_fourteen_days_until_renewal_window(self) -> None:
        html = read_page()
        source = MAXIM_EDGE_FUNCTION.read_text(encoding="utf-8")
        self.assertIn("expirationDate >= currentMonth", source)
        self.assertIn("expirationDate < afterNextMonth", source)
        self.assertIn("registration?.starts_at || row.scheduled_class_date", source)
        self.assertIn("currentClassAgeDays <= 14", source)
        self.assertIn("renewalDueNow", source)
        self.assertIn("isDashboardEligible(p)", html)
        self.assertIn("if(index===4&&recentInvoiceClass)", html)
        self.assertIn("Invoice unresolved", html)

    def test_due_window_month_rollover_leap_year_and_completion_grace_boundaries(self) -> None:
        active = {"bucket": "active"}
        results = run_dashboard_eligibility(
            [
                {"viewedAt": "2026-07-31T16:00:00Z", "person": {**active, "expirationDate": "2026-07-01"}},
                {"viewedAt": "2026-07-31T16:00:00Z", "person": {**active, "expirationDate": "2026-08-31"}},
                {"viewedAt": "2026-07-31T16:00:00Z", "person": {**active, "expirationDate": "2026-09-01"}},
                {"viewedAt": "2026-12-15T17:00:00Z", "person": {**active, "expirationDate": "2027-01-31"}},
                {"viewedAt": "2024-02-29T17:00:00Z", "person": {**active, "expirationDate": "2024-03-31"}},
                {"viewedAt": "2026-07-24T16:00:00Z", "person": {**active, "expirationDate": "2028-07-31", "classDate": "2026-07-10"}},
                {"viewedAt": "2026-07-25T16:00:00Z", "person": {**active, "expirationDate": "2028-07-31", "classDate": "2026-07-10"}},
                {"viewedAt": "2026-07-25T16:00:00Z", "person": {**active, "expirationDate": "2026-08-31", "classDate": "2026-07-10"}},
            ]
        )
        self.assertEqual(results, [True, True, False, True, True, True, False, True])

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
            "No current valid dates are available at the approved location",
            read_page(),
        )

    def test_atomic_reschedule_preserves_history_and_releases_after_insert(self) -> None:
        sql = MAXIM_MIGRATION.read_text(encoding="utf-8")
        insert_at = sql.index("insert into public.maxim_registration_requests")
        release_at = sql.index("commitment_released_at = now()")
        self.assertLess(insert_at, release_at)
        self.assertIn("status = 'superseded'", sql)
        self.assertIn("supersedes_request_id", sql)
        self.assertIn("maxim_one_active_requirement", sql)
        self.assertIn("pg_advisory_xact_lock", sql)

    def test_reschedule_api_uses_atomic_database_rule(self) -> None:
        source = MAXIM_EDGE_FUNCTION.read_text(encoding="utf-8")
        self.assertIn("rpc/maxim_replace_registration", source)
        self.assertNotIn(
            'body: JSON.stringify({ status: "superseded", updated_at:',
            source[source.index("async function registerEmployee"):],
        )

    def test_actions_continue_until_ecard_and_passed_date_stays_visible(self) -> None:
        html = read_page()
        self.assertIn("if(!completed)cell.push", html)
        self.assertIn(">Send link</button>", html)
        self.assertIn(">Reschedule</button>", html)
        self.assertIn("Class date passed / Awaiting eCard", html)
        self.assertIn("if(index===2){if(person.classDate)", html)
        self.assertIn("completed=Boolean(person.eCardCode)", html)

    def test_recent_completed_class_without_ecard_remains_visible_for_fourteen_days(self) -> None:
        html = read_page()
        source = MAXIM_EDGE_FUNCTION.read_text(encoding="utf-8")
        self.assertIn("const importedCompletion = /^Completed", source)
        self.assertIn("workflowStage >= 3 || importedCompletion", source)
        self.assertIn("const hasCurrentClassActivity = Boolean(", source)
        self.assertIn("currentClassAgeDays <= 14", source)
        self.assertIn("if(person.classDate){const age=calendarDayDifference", html)
        self.assertNotIn("if(person.eCardCode&&person.completionDate)", html)

    def test_recent_completion_and_history_windows_are_explicit(self) -> None:
        source = MAXIM_EDGE_FUNCTION.read_text(encoding="utf-8")
        html = read_page()
        self.assertIn("calendarDayDifference", source)
        self.assertIn("currentClassAgeDays <= 14", source)
        self.assertNotIn('.slice(0, 15)', source)
        self.assertIn('"recently_completed"', source)
        self.assertIn('"history"', source)
        self.assertIn("p.bucket==='history'&&q", html)

    def test_location_and_expiration_policies_are_enforced(self) -> None:
        source = MAXIM_EDGE_FUNCTION.read_text(encoding="utf-8")
        html = read_page()
        self.assertIn('id="locationChoice"', html)
        self.assertIn("locationKeyForCourse", html)
        self.assertIn("canUseDateForPerson", html)
        self.assertIn("adminOverrideExpiration:true", html)
        self.assertIn("MAXIM_APPROVED_LOCATIONS", source)
        self.assertIn("!body.adminOverrideExpiration && body.expirationDate", source)
        self.assertIn("canonicalLocationKey !== String(body.locationKey", source)

    def test_maxim_registration_never_requests_payment(self) -> None:
        html = read_page()
        self.assertIn("No payment or promo code is needed.", html)

    def test_internal_landerware_explanation_is_not_shown_to_maxim(self) -> None:
        html = read_page()
        self.assertNotIn("Dates load from the authoritative public LanderWare schedule", html)
        self.assertNotIn("eCard and invoice cells remain blank or awaiting", html)
        self.assertNotIn("PaymentIntent", html)
        self.assertNotIn("checkout.session", html)


if __name__ == "__main__":
    unittest.main()
