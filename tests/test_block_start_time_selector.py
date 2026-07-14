from __future__ import annotations

import json
import unittest
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from scripts import build_bls_block_schedule_pilot
from scripts import build_deployed_selector_pages
from scripts import block_start_time_selector

ROOT = Path(__file__).resolve().parents[1]
PILOT_REPORT_PATH = ROOT / "data" / "audit" / "bls_block_schedule_pilot.json"


def artifact_offers(artifact):
    out = []
    for day in artifact.get("dates", []):
        for slot in day.get("startTimes", []):
            out.extend(slot.get("courses", []))
    return out


class BlockStartTimeSelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(PILOT_REPORT_PATH.read_text(encoding="utf-8"))

    def test_uses_live_availability_when_present(self):
        self.assertEqual(self.payload["availability_source_used"], "live_availability_snapshot")
        self.assertFalse(self.payload["availability_fallback_used"])

    def test_bls_offers_are_current_live_traced_when_present(self):
        course_ids = {offer["courseId"] for offer in self.payload["offers"]}
        self.assertLessEqual(course_ids, set(block_start_time_selector.BLS_PILOT_COURSE_IDS))
        self.assertEqual(
            self.payload["counts"]["publicSelectableOfferCount"],
            len(self.payload["offers"]),
        )
        for offer in self.payload["offers"]:
            self.assertTrue(offer.get("availabilityBlockId"))
            self.assertTrue(offer.get("sourceAvailabilityBlock"))

    def test_public_starts_are_inside_business_hours(self):
        for offer in self.payload["offers"]:
            hour, minute = [int(part) for part in offer["startTime"].split(":")]
            self.assertGreaterEqual((hour, minute), (8, 0))
            self.assertLessEqual((hour, minute), (19, 0))
            self.assertNotEqual(offer["startTime"], "00:00")

    def test_appointment_urls_include_required_query_params(self):
        for offer in self.payload["offers"][:25]:
            parsed = urlparse(offer["appointmentUrl"])
            query = parse_qs(parsed.query)
            self.assertEqual(parsed.scheme, "https")
            self.assertEqual(parsed.netloc, "coastalcprtraining.enrollware.com")
            self.assertIn("appointmentDayId", query)
            self.assertIn("startTime", query)
            self.assertEqual(query.get("courseId"), [offer["courseId"]])

    def test_whole_block_is_not_presented_as_class(self):
        self.assertFalse(self.payload["whole_block_presented_as_class"])
        self.assertFalse(self.payload["counts"]["wholeBlockPresentedAsClass"])
        visible_labels = set(self.payload["proof"]["visibleStartLabels"])
        for window in self.payload["proof"]["availabilityWindowsThatGeneratedOffers"]:
            self.assertNotIn(window, visible_labels)

    def test_rendered_html_loads_shell_without_actionable_static_times(self):
        html = build_bls_block_schedule_pilot.render_html(self.payload)
        self.assertIn("BLS Schedule Pilot", html)
        self.assertIn("Register", html)
        self.assertIn("Checking current class times…", html)
        self.assertIn("const embeddedScheduleDates = []", html)
        self.assertIn("let scheduleDates = embeddedScheduleDates", html)
        self.assertIn("fetch(availabilityUrl, { cache: 'no-store' })", html)
        self.assertIn("selector-resolved-availability.v1", html)
        self.assertNotIn("coastalcprtraining.enrollware.com/enroll?appointmentDayId", html)
        self.assertIn("Need BLS ASAP? Show all AHA BLS options", html)
        self.assertIn("const courseOptions =", html)
        self.assertIn("const optionGroups =", html)
        self.assertIn("let compareMode = false", html)
        self.assertIn("function courseIdFromDeepLink()", html)
        self.assertIn("new URLSearchParams(window.location.search)", html)
        self.assertIn("function showAllFromDeepLink()", html)
        self.assertIn("function publicDeliveryBucket", html)
        self.assertIn("deliveryLabel(course.deliveryMode)", html)
        self.assertNotIn('name="delivery-filter"', html)
        self.assertNotIn("Delivery type", html)
        self.assertNotIn('data-delivery-option="all"', html)
        self.assertNotIn('value="online-skills"> Online + Skills', html)
        self.assertNotIn('value="blended"> Blended', html)
        self.assertNotIn('value="skills-session"> HeartCode/Skills', html)
        self.assertIn("showAllOptions", html)
        self.assertIn("Show all certification options", html)
        self.assertIn("function activeCourseIds()", html)
        self.assertNotIn("12:00 AM-6:00 PM", html)
        self.assertNotIn("12:00 AM\u20136:00 PM", html)
        self.assertNotIn("Calendy", html)
        self.assertNotIn("shotgun", html.lower())

    def test_compare_mode_data_model_groups_bls_family_generically(self):
        html = build_bls_block_schedule_pilot.render_html(self.payload)
        self.assertIn('"family": "BLS"', html)
        self.assertIn('"209806"', html)
        self.assertIn('"359474"', html)
        self.assertIn('"210549"', html)
        self.assertIn("Object.values(optionGroups).find", html)
        self.assertIn("optionGroups[selected.family]?.courseIds", html)

    def test_rendered_register_cards_hide_debug_details(self):
        html = build_bls_block_schedule_pilot.render_html(self.payload)
        self.assertIn("Times shown are start times.", html)
        self.assertIn("course.location", html)
        self.assertNotIn("appointmentDayId $", html)
        self.assertNotIn("courseId $", html)
        self.assertNotIn("durationMinutes} min", html)
        self.assertIn("className = 'course-card'", html)
        self.assertIn("className = 'selected-summary'", html)
        self.assertIn("className = 'start-group'", html)
        self.assertIn("className = 'month-nav'", html)
        self.assertIn('id="date-list" class="month-stack"', html)
        self.assertIn('class="selector-shell"', html)
        self.assertIn('class="panel course-selector-panel"', html)
        self.assertIn('class="selector-grid"', html)
        self.assertNotIn('class="pilot-grid"', html)

    def test_schedule_ui_greys_past_dates_and_times_without_removing_data(self):
        html = build_bls_block_schedule_pilot.render_html(self.payload)
        self.assertIn("const scheduleTimezone = 'America/New_York'", html)
        self.assertIn("timeZone: scheduleTimezone", html)
        self.assertIn("function isPastStart(day, slot, now = businessNow())", html)
        self.assertIn("function isSelectableDate(day, now = businessNow())", html)
        self.assertIn("button.classList.add('is-past')", html)
        self.assertIn("button.disabled = disabled", html)
        self.assertIn("button.setAttribute('aria-disabled', String(disabled))", html)
        self.assertIn("not bookable; past date or no future ' + scheduleTimezone + ' start times", html)
        self.assertIn("not bookable; past ' + scheduleTimezone + ' start time", html)
        self.assertIn("selectedStart = selectableStartTimes(available)[0]?.startTime || ''", html)
        self.assertIn("if (!slot || isPastStart(day, slot) || !slot.courses.length)", html)
        self.assertIn("let scheduleDates = embeddedScheduleDates", html)
        self.assertIn("availabilityReady()", html)
        self.assertIn("renderAvailabilityPlaceholder", html)
        self.assertIn("Current class times are temporarily unavailable.", html)
        self.assertIn("course.appointmentUrl", html)

    def test_availability_artifact_keeps_future_enrollware_urls_unchanged(self):
        payload = {
            **self.payload,
            "pageKey": "test-page",
            "publicPage": "docs/test-page.html",
            "dates": [{
                "date": "2099-08-01",
                "displayDate": "Saturday, August 1, 2099",
                "startTimes": [{
                    "startTime": "14:30",
                    "displayStartTime": "2:30 PM",
                    "courses": [{
                        "courseId": "209806",
                        "courseName": "AHA BLS Provider",
                        "family": "BLS",
                        "deliveryMode": "in-person",
                        "displayStartTime": "2:30 PM",
                        "durationMinutes": 120,
                        "appointmentDayId": 260683,
                        "appointmentUrl": "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A30%20PM&courseId=209806",
                        "location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
                    }],
                }],
            }],
            "offers": [{
                "date": "2099-08-01",
                "displayDate": "Saturday, August 1, 2099",
                "startTime": "14:30",
                "displayStartTime": "2:30 PM",
                "courseId": "209806",
                "courseName": "AHA BLS Provider",
                "courseFamily": "BLS",
                "deliveryMode": "in-person",
                "durationMinutes": 120,
                "appointmentDayId": 260683,
                "appointmentUrl": "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A30%20PM&courseId=209806",
                "location": ":: Wilmington; Shipyard Blvd",
                "availabilityBlockId": "test-block",
                "sourceAvailabilityBlock": {"sourceAvailabilityBlockId": "test-block"},
                "schedulerConsumptionEnd": "16:30",
                "publicSelectable": True,
            }],
        }
        html = build_bls_block_schedule_pilot.render_html(payload)
        artifact = build_bls_block_schedule_pilot.public_selector_availability_payload(payload)
        self.assertNotIn(
            "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A30%20PM&courseId=209806",
            html,
        )
        self.assertIn(
            "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A30%20PM&courseId=209806",
            json.dumps(artifact, ensure_ascii=False),
        )
        self.assertNotIn("offers", artifact)

    def test_config_driven_heartsaver_page_generates_valid_schedule(self):
        configs = block_start_time_selector.load_block_schedule_page_configs()
        payload = block_start_time_selector.build_block_schedule_page(configs["heartsaver"])
        self.assertEqual(payload["publicPage"], "docs/heartsaver.html")
        course_ids = {offer["courseId"] for offer in payload["offers"]}
        self.assertLessEqual(course_ids, {"344085", "209808", "209809", "329495", "351632", "251545"})
        html = build_bls_block_schedule_pilot.render_html(payload)
        self.assertIn("Heartsaver Schedule", html)
        self.assertNotIn("Need First Aid or CPR ASAP? Show all AHA Heartsaver options", html)
        self.assertNotIn('id="compare-toggle"', html)
        self.assertIn('"variant": "cpr-aed"', html)
        self.assertIn('"first-aid-cpr-aed"', html)
        self.assertIn('"pediatric-first-aid-cpr-aed"', html)
        self.assertIn("courseIdFromDeepLink() || selectedCourseId", html)
        self.assertIn("showAllOptions = showAllFromDeepLink()", html)
        self.assertIn("No matching times are currently available.", html)
        self.assertNotIn("Try All delivery types.", html)
        self.assertIn("delivery-badge", html)
        self.assertIn("course-delivery", html)
        self.assertNotIn("Delivery type", html)
        self.assertNotIn('name="delivery-filter"', html)
        self.assertNotIn('data-delivery-option="all"', html)
        self.assertNotIn('value="online-skills"> Online + Skills', html)
        self.assertNotIn('value="blended"> Blended', html)
        self.assertNotIn('value="skills-session"> HeartCode/Skills', html)
        self.assertIn("Course details", html)
        self.assertIn("topics_covered", html)
        self.assertNotIn("Full course page", html)
        self.assertIn("selected-summary", html)
        self.assertIn("start-grid", html)
        self.assertIn("Show all course options", html)
        self.assertIn('"deliveryMode": "in-person"', html)
        self.assertIn('"deliveryMode": "blended"', html)
        self.assertIn('"recommended": false', html)
        self.assertIn('"209808"', html)
        self.assertIn('"329495"', html)
        self.assertIn('"351632"', html)
        self.assertNotIn("coastalcprtraining.enrollware.com/enroll?appointmentDayId", html)
        self.assertNotIn("appointmentDayId $", html)
        self.assertNotIn("courseId $", html)

    def test_heartsaver_cpr_aed_public_ids_exclude_fire_department_partner_course(self):
        configs = block_start_time_selector.load_block_schedule_page_configs()
        heartsaver = configs["heartsaver"]
        options_by_variant = {option.get("variant"): option for option in heartsaver["course_options"]}
        self.assertEqual(options_by_variant["cpr-aed"]["course_id"], "344085")
        self.assertEqual(options_by_variant["cpr-aed-online"]["course_id"], "209808")
        configured_ids = {option["course_id"] for option in heartsaver["course_options"]}
        self.assertNotIn("460465", configured_ids)
        self.assertIn("Fire Department/public-safety partner", heartsaver["course_id_notes"]["460465"])

        payload = block_start_time_selector.build_block_schedule_page(heartsaver)
        public_ids = {offer["courseId"] for offer in payload["offers"]}
        self.assertIn("344085", public_ids)
        self.assertIn("209808", public_ids)
        self.assertNotIn("460465", public_ids)
        html = build_bls_block_schedule_pilot.render_html(payload)
        artifact = build_bls_block_schedule_pilot.public_selector_availability_payload(payload)
        artifact_json = json.dumps(artifact, ensure_ascii=False)
        self.assertIn("courseId=344085", artifact_json)
        self.assertIn("courseId=209808", artifact_json)
        self.assertNotIn("coastalcprtraining.enrollware.com/enroll?appointmentDayId", html)
        self.assertNotIn("courseId=460465", html)

    def test_heartsaver_artifact_excludes_newly_conflicting_pediatric_offer(self):
        configs = block_start_time_selector.load_block_schedule_page_configs()
        payload = block_start_time_selector.build_block_schedule_page(configs["heartsaver"])
        artifact = build_bls_block_schedule_pilot.public_selector_availability_payload(payload)
        conflicting = [
            offer for offer in artifact_offers(artifact)
            if offer.get("date") == "2026-07-13"
            and offer.get("startTime") == "15:30"
            and str(offer.get("courseId")) == "251545"
        ]
        self.assertEqual([], conflicting)

    def test_public_artifact_uses_only_public_double_colon_locations(self):
        configs = block_start_time_selector.load_block_schedule_page_configs()
        for page_key in ("bls", "heartsaver", "acls", "pals", "uscg_first_aid_cpr_aed", "hsi"):
            with self.subTest(page_key=page_key):
                payload = block_start_time_selector.build_block_schedule_page(configs[page_key])
                artifact = build_bls_block_schedule_pilot.public_selector_availability_payload(payload)
                self.assertEqual("selector-resolved-availability.v1", artifact["schemaVersion"])
                for offer in artifact_offers(artifact):
                    self.assertTrue(
                        str(offer.get("location") or "").strip().startswith("::"),
                        f"{page_key} exposed non-public location: {offer.get('location')}",
                    )

    def test_acls_and_pals_are_deployed_selector_pages(self):
        self.assertIn("acls", build_deployed_selector_pages.DEPLOYED_SELECTOR_PAGE_KEYS)
        self.assertIn("pals", build_deployed_selector_pages.DEPLOYED_SELECTOR_PAGE_KEYS)
        self.assertIn("hsi", build_deployed_selector_pages.DEPLOYED_SELECTOR_PAGE_KEYS)
        configs = block_start_time_selector.load_block_schedule_page_configs()
        self.assertEqual(configs["acls"]["output_path"], "docs/acls.html")
        self.assertEqual(configs["pals"]["output_path"], "docs/pals.html")
        self.assertEqual(configs["hsi"]["output_path"], "docs/hsi.html")
        self.assertEqual(configs["acls"]["legacy_schedule_path"], "docs/acls-schedule.html")
        self.assertEqual(configs["pals"]["legacy_schedule_path"], "docs/pals-schedule.html")
        self.assertEqual(configs["hsi"]["legacy_schedule_path"], "docs/hsi-schedule.html")

    def test_acls_selector_shell_and_artifact_support_all_variants_without_static_times(self):
        configs = block_start_time_selector.load_block_schedule_page_configs()
        payload = block_start_time_selector.build_block_schedule_page(configs["acls"])
        guarded = block_start_time_selector.apply_final_live_availability_guard(payload)
        artifact = build_bls_block_schedule_pilot.public_selector_availability_payload(guarded)
        html = build_bls_block_schedule_pilot.render_html(guarded)
        course_ids = {option["course_id"] for option in configs["acls"]["course_options"]}
        self.assertEqual(course_ids, {"241108", "209818", "209811"})
        self.assertIn("AHA ACLS Provider (Initial)", html)
        self.assertIn("AHA ACLS Provider (Renewal)", html)
        self.assertIn("AHA ACLS HeartCode", html)
        self.assertIn("Checking current class times…", html)
        self.assertIn("const embeddedScheduleDates = []", html)
        self.assertIn("fetch(availabilityUrl, { cache: 'no-store' })", html)
        self.assertIn("Current class times are temporarily unavailable.", html)
        self.assertNotIn("coastalcprtraining.enrollware.com/enroll?appointmentDayId", html)
        offers = artifact_offers(artifact)
        self.assertEqual("selector-resolved-availability.v1", artifact["schemaVersion"])
        self.assertEqual(7, sum(1 for offer in offers if offer.get("courseId") == "241108"))
        self.assertEqual(7, sum(1 for offer in offers if offer.get("courseId") == "209818"))
        self.assertEqual(0, sum(1 for offer in offers if offer.get("courseId") == "209811"))
        self.assertEqual({"seated_class"}, {offer.get("offerType") for offer in offers})
        self.assertNotIn("12774086", json.dumps(artifact, ensure_ascii=False))
        self.assertNotIn("12774096", json.dumps(artifact, ensure_ascii=False))

    def test_pals_selector_shell_and_artifact_support_all_variants_without_static_times(self):
        configs = block_start_time_selector.load_block_schedule_page_configs()
        payload = block_start_time_selector.build_block_schedule_page(configs["pals"])
        guarded = block_start_time_selector.apply_final_live_availability_guard(payload)
        artifact = build_bls_block_schedule_pilot.public_selector_availability_payload(guarded)
        html = build_bls_block_schedule_pilot.render_html(guarded)
        course_ids = {option["course_id"] for option in configs["pals"]["course_options"]}
        self.assertEqual(course_ids, {"209805", "251496", "209812"})
        self.assertIn("AHA PALS Provider", html)
        self.assertIn("AHA PALS Renewal", html)
        self.assertIn("AHA PALS HeartCode", html)
        self.assertIn("Checking current class times…", html)
        self.assertIn("const embeddedScheduleDates = []", html)
        self.assertNotIn("coastalcprtraining.enrollware.com/enroll?appointmentDayId", html)
        offers = artifact_offers(artifact)
        self.assertEqual(7, sum(1 for offer in offers if offer.get("courseId") == "209805"))
        self.assertEqual(7, sum(1 for offer in offers if offer.get("courseId") == "251496"))
        self.assertEqual(0, sum(1 for offer in offers if offer.get("courseId") == "209812"))
        self.assertEqual({"seated_class"}, {offer.get("offerType") for offer in offers})

    def test_hsi_selector_shell_uses_resolved_authority_without_static_times(self):
        configs = block_start_time_selector.load_block_schedule_page_configs()
        payload = block_start_time_selector.build_block_schedule_page(configs["hsi"])
        guarded = block_start_time_selector.apply_final_live_availability_guard(payload)
        artifact = build_bls_block_schedule_pilot.public_selector_availability_payload(guarded)
        html = build_bls_block_schedule_pilot.render_html(guarded)
        self.assertEqual("selector-resolved-availability.v1", artifact["schemaVersion"])
        self.assertEqual("hsi", artifact["pageKey"])
        self.assertIn("HSI BLS Challenge", html)
        self.assertIn("HSI BLS + Adult First Aid", html)
        self.assertIn("HSI First Aid / CPR / AED", html)
        self.assertIn("HSI CPR / AED", html)
        self.assertIn('data-request-fragment="first-aid-cpr-aed"', html)
        self.assertIn('data-request-fragment="cpr-aed"', html)
        self.assertIn("function focusDeepLinkedElement()", html)
        self.assertIn("window.addEventListener('hashchange'", html)
        self.assertIn("Checking current class times…", html)
        self.assertIn("fetch(availabilityUrl, { cache: 'no-store' })", html)
        self.assertNotIn("coastalcprtraining.enrollware.com/enroll?appointmentDayId", html)
        offers = artifact_offers(artifact)
        self.assertGreater(len(offers), 0)
        self.assertLessEqual({offer["courseId"] for offer in offers}, {"463743", "445670"})
        self.assertFalse([offer for offer in offers if not str(offer.get("location", "")).startswith("::")])

    def test_hsi_hub_no_longer_embeds_static_dynamic_appointment_times(self):
        html = (ROOT / "docs" / "hsi.html").read_text(encoding="utf-8")
        self.assertIn("HSI BLS Challenge", html)
        self.assertIn("HSI BLS + Adult First Aid", html)
        self.assertNotIn("slug-appointment-option", html)
        self.assertNotIn("appointmentDayId=", html)
        self.assertIn("Checking current class times…", html)

    def test_blocked_calendar_interval_occupancy_rejects_hsi_overlap_boundaries(self):
        live_payload = {
            "availability_blocks": [{
                "availability_status": "blocked",
                "instructor_name": "Brian Ennis",
                "person_id": "instructor_24057895173",
                "date": "2026-07-04",
                "end_date": "2026-07-04",
                "start_datetime": "2026-07-04T15:00:00-04:00",
                "end_datetime": "2026-07-04T21:00:00-04:00",
                "start_time": "15:00",
                "end_time": "21:00",
                "location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
                "source_calendar_id": "brian_do_not_schedule",
                "source_event_id": "blocked-3-to-9",
                "source_type": "google_calendar_block",
            }]
        }
        occupancy = block_start_time_selector.build_occupancy(
            {
                "sessions_current": {"sessions": []},
                "schedule_future": {"sessions": []},
                "live_availability_snapshot": live_payload,
                "location_resource_map": block_start_time_selector.read_required_json(block_start_time_selector.LOCATION_RESOURCE_MAP_PATH),
            },
            {},
        )
        person = {"display_name": "Brian Ennis"}
        location = ":: Wilmington; Shipyard Blvd"

        def conflict(start_hour: int, start_minute: int, end_hour: int, end_minute: int) -> bool:
            start = datetime(2026, 7, 4, start_hour, start_minute)
            end = datetime(2026, 7, 4, end_hour, end_minute)
            return block_start_time_selector.generate_dynamic_offers.has_conflict(start, end, occupancy, location, person)[0]

        self.assertFalse(conflict(13, 30, 15, 0))
        self.assertTrue(conflict(14, 30, 15, 15))
        self.assertTrue(conflict(14, 0, 22, 0))
        self.assertTrue(conflict(17, 45, 19, 15))
        self.assertTrue(conflict(18, 0, 19, 30))
        self.assertTrue(conflict(18, 15, 19, 45))
        self.assertTrue(conflict(20, 45, 21, 15))
        self.assertFalse(conflict(21, 0, 22, 30))

    def test_closed_full_classes_remain_occupancy_but_not_direct_selector_offers(self):
        configs = block_start_time_selector.load_block_schedule_page_configs()
        payload = block_start_time_selector.build_block_schedule_page(configs["acls"])
        artifact = build_bls_block_schedule_pilot.public_selector_availability_payload(
            block_start_time_selector.apply_final_live_availability_guard(payload)
        )
        artifact_json = json.dumps(artifact, ensure_ascii=False)
        self.assertNotIn("12774086", artifact_json)
        self.assertNotIn("12774096", artifact_json)
        occupancy = block_start_time_selector.build_occupancy(
            {
                "sessions_current": block_start_time_selector.read_required_json(block_start_time_selector.SESSIONS_CURRENT_PATH),
                "schedule_future": block_start_time_selector.read_required_json(block_start_time_selector.SCHEDULE_FUTURE_PATH),
                "location_resource_map": block_start_time_selector.read_required_json(block_start_time_selector.LOCATION_RESOURCE_MAP_PATH),
            },
            block_start_time_selector.course_rules_by_id(
                block_start_time_selector.read_required_json(block_start_time_selector.COURSE_RULES_PATH)
            ),
        )
        occupancy_text = json.dumps(occupancy, default=str, ensure_ascii=False)
        self.assertIn("AHA ACLS HeartCode", occupancy_text)

    def test_acls_and_pals_hub_schedule_links_target_real_selector_pages(self):
        slug_hubs = json.loads((ROOT / "data" / "config" / "slug_hubs.json").read_text(encoding="utf-8"))
        configs = block_start_time_selector.load_block_schedule_page_configs()
        expected_targets = {
            "acls": "/acls.html",
            "pals": "/pals.html",
        }
        for slug, expected in expected_targets.items():
            with self.subTest(slug=slug):
                page = next(item for item in slug_hubs["pages"] if item["slug"] == slug)
                urls = {
                    tab.get("full_schedule_url")
                    for tab in page.get("tabs", [])
                    if tab.get("full_schedule_url")
                }
                self.assertEqual({expected}, urls)
                self.assertEqual(configs[slug]["output_path"], f"docs/{expected.lstrip('/')}")

    def test_promoted_family_pages_and_legacy_schedule_redirects(self):
        redirects = {
            "bls": "/bls.html",
            "acls": "/acls.html",
            "pals": "/pals.html",
            "hsi": "/hsi.html",
            "heartsaver": "/heartsaver.html",
            "arc": "/arc.html",
        }
        for slug, target in redirects.items():
            with self.subTest(slug=slug):
                canonical = (ROOT / "docs" / f"{slug}.html").read_text(encoding="utf-8")
                redirect = (ROOT / "docs" / f"{slug}-schedule.html").read_text(encoding="utf-8")
                if slug == "arc":
                    self.assertNotIn("selector-shell", canonical)
                    self.assertIn("Scheduling assistance available", canonical)
                else:
                    self.assertIn("selector-shell", canonical)
                    self.assertIn("const embeddedScheduleDates = []", canonical)
                    self.assertIn("Checking current class times…", canonical)
                    self.assertNotIn("Browse upcoming class times here", canonical)
                    self.assertNotIn("appointmentDayId=", canonical)
                self.assertIn(f'var target = "{target}";', redirect)
                self.assertIn("window.location.replace(target + query + hash)", redirect)
                self.assertIn('name="robots" content="noindex"', redirect)

    def test_uscg_cover_page_uses_only_aha_heartsaver_first_aid_cpr_aed_inventory(self):
        configs = block_start_time_selector.load_block_schedule_page_configs()
        uscg = configs["uscg_first_aid_cpr_aed"]
        configured_ids = {option["course_id"] for option in uscg["course_options"]}
        self.assertEqual(configured_ids, {"209809", "329495"})
        excluded_ids = {"344085", "209808", "351632", "251545", "460465", "248288", "248287", "445670", "463743"}
        self.assertTrue(configured_ids.isdisjoint(excluded_ids))
        self.assertFalse(uscg["compare_mode"]["enabled"])
        self.assertIn("Fire Department/public-safety partner", uscg["course_id_notes"]["460465"])

        payload = block_start_time_selector.build_block_schedule_page(uscg)
        self.assertEqual(payload["publicPage"], "docs/courses/uscg-first-aid-cpr-aed.html")
        public_ids = {offer["courseId"] for offer in payload["offers"]}
        self.assertLessEqual(public_ids, configured_ids)
        html = build_bls_block_schedule_pilot.render_html(payload)
        self.assertIn("USCG-Approved First Aid / CPR / AED", html)
        self.assertIn("AHA Heartsaver First Aid CPR AED Total", html)
        self.assertIn("AMERHA-216", html)
        self.assertIn("captain", html)
        self.assertIn("OUPV", html)
        self.assertIn("Master", html)
        self.assertIn("Merchant Mariner Credential", html)
        self.assertIn("online learning plus an in-person skills session", html)
        self.assertNotIn("fully online", html.lower())
        self.assertNotIn("Need First Aid or CPR ASAP", html)
        self.assertNotIn('id="compare-toggle"', html)
        self.assertNotIn('id="show-all-toggle"', html)
        self.assertNotIn("courseId=344085", html)
        self.assertNotIn("courseId=209808", html)
        self.assertNotIn("courseId=351632", html)
        self.assertNotIn("courseId=251545", html)
        self.assertNotIn("courseId=460465", html)
        self.assertNotIn("coastalcprtraining.enrollware.com/enroll?appointmentDayId", html)
        artifact_json = json.dumps(build_bls_block_schedule_pilot.public_selector_availability_payload(payload), ensure_ascii=False)
        if payload["offers"]:
            self.assertIn("courseId=209809", artifact_json)
            self.assertIn("courseId=329495", artifact_json)

    def test_final_live_guard_suppresses_july_4_stale_offer_without_live_block(self):
        stale_payload = {
            "pageConfig": {"allowed_course_ids": ["209806"]},
            "counts": {
                "publicSelectableOfferCount": 1,
                "publicSelectableDateCount": 1,
                "publicSelectableStartTimeCount": 1,
                "rejectedOfferCount": 0,
                "wholeBlockPresentedAsClass": False,
            },
            "proof": {"visibleStartLabels": ["8:00 AM"], "availabilityWindowsThatGeneratedOffers": ["08:00-12:00"]},
            "offers": [{
                "date": "2026-07-04",
                "displayDate": "Saturday, July 4, 2026",
                "startTime": "08:00",
                "displayStartTime": "8:00 AM",
                "courseId": "209806",
                "courseName": "AHA BLS Provider",
                "availabilityBlockId": "stale-july-4-block",
                "availabilityWindow": "08:00-12:00",
                "schedulerConsumptionEnd": "10:30",
            }],
            "dates": [{
                "date": "2026-07-04",
                "displayDate": "Saturday, July 4, 2026",
                "startTimes": [{
                    "startTime": "08:00",
                    "displayStartTime": "8:00 AM",
                    "courses": [],
                }],
            }],
        }
        original = block_start_time_selector.current_public_live_block_index
        block_start_time_selector.current_public_live_block_index = lambda: {
            "current-july-5-block": {
                "start": datetime(2026, 7, 5, 8, 0),
                "end": datetime(2026, 7, 5, 12, 0),
                "block": {},
            }
        }
        try:
            guarded = block_start_time_selector.apply_final_live_availability_guard(stale_payload)
        finally:
            block_start_time_selector.current_public_live_block_index = original
        self.assertEqual(guarded["offers"], [])
        self.assertEqual(guarded["dates"], [])
        self.assertEqual(guarded["counts"]["publicSelectableOfferCount"], 0)
        self.assertEqual(guarded["liveAvailabilityGuard"]["suppressedDates"], ["2026-07-04"])
        self.assertEqual(
            guarded["liveAvailabilityGuard"]["suppressedStaleOrOrphanedOffers"][0]["reason"],
            "source_availability_block_missing_from_current_live_snapshot",
        )

    def test_public_live_windows_allow_approved_inverse_sources_only(self):
        live_payload = {
            "generated_at": "2026-07-02T12:00:00-04:00",
            "availability_blocks": [
                {
                    "availability_status": "available",
                    "inverse_generated": True,
                    "source_calendar_id": "brian_do_not_schedule",
                    "source_event_id": "approved-gap",
                    "instructor_name": "Brian Ennis",
                    "person_id": "instructor_24057895173",
                    "date": "2026-07-04",
                    "end_date": "2026-07-04",
                    "start_datetime": "2026-07-04T08:00:00",
                    "end_datetime": "2026-07-04T12:00:00",
                    "start_time": "08:00",
                    "end_time": "12:00",
                    "location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
                    "allowed_course_families": ["BLS"],
                    "source_type": "inverse_google_calendar",
                },
                {
                    "availability_status": "available",
                    "inverse_generated": True,
                    "source_calendar_id": "unapproved_calendar",
                    "source_event_id": "unapproved-gap",
                    "instructor_name": "Brian Ennis",
                    "person_id": "instructor_24057895173",
                    "date": "2026-07-05",
                    "end_date": "2026-07-05",
                    "start_datetime": "2026-07-05T08:00:00",
                    "end_datetime": "2026-07-05T12:00:00",
                    "start_time": "08:00",
                    "end_time": "12:00",
                    "location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
                    "allowed_course_families": ["BLS"],
                    "source_type": "inverse_google_calendar",
                },
            ],
        }
        windows, stats = block_start_time_selector.selected_public_page_live_windows(live_payload, {})
        self.assertEqual([window["source_availability_window"] for window in windows], ["approved-gap"])
        self.assertEqual(stats["approved_inverse_blocks_used_count"], 1)
        self.assertEqual(stats["unapproved_inverse_blocks_suppressed_count"], 1)
        self.assertEqual(
            stats["suppressed_available_blocks"][0]["reason"],
            "inverse_generated_availability_source_not_approved_for_public_page",
        )

    def test_missing_live_calendar_snapshot_fails_closed(self):
        original_path = block_start_time_selector.LIVE_AVAILABILITY_PATH
        block_start_time_selector.LIVE_AVAILABILITY_PATH = ROOT / "data" / "audit" / "missing_live_snapshot_for_test.json"
        try:
            with self.assertRaises(block_start_time_selector.BlockSelectorInputError):
                block_start_time_selector.require_current_live_availability_snapshot()
        finally:
            block_start_time_selector.LIVE_AVAILABILITY_PATH = original_path

    def test_stale_live_calendar_snapshot_fails_closed(self):
        with self.assertRaises(block_start_time_selector.BlockSelectorInputError):
            original_read = block_start_time_selector.read_required_json
            block_start_time_selector.read_required_json = lambda _path: {
                "generated_at": "2026-07-01T23:59:00-04:00",
                "availability_blocks": [],
            }
            try:
                block_start_time_selector.require_current_live_availability_snapshot()
            finally:
                block_start_time_selector.read_required_json = original_read

    def test_malformed_blocked_calendar_occupancy_fails_closed(self):
        malformed = {
            "availability_blocks": [{
                "availability_status": "blocked",
                "source_event_id": "malformed-block",
                "instructor_name": "Brian Ennis",
                "location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
                "date": "2026-07-04",
                "start_time": "not-a-time",
                "end_time": "21:00",
            }]
        }
        with self.assertRaises(block_start_time_selector.BlockSelectorInputError):
            block_start_time_selector.normalize_live_calendar_block_occupancy(malformed)

    def test_blocked_calendar_occupancy_without_instructor_or_location_fails_closed(self):
        unsafe = {
            "availability_blocks": [{
                "availability_status": "blocked",
                "source_event_id": "unknown-resource-block",
                "start_datetime": "2026-07-04T15:00:00-04:00",
                "end_datetime": "2026-07-04T21:00:00-04:00",
            }]
        }
        with self.assertRaises(block_start_time_selector.BlockSelectorInputError):
            block_start_time_selector.normalize_live_calendar_block_occupancy(unsafe)

    def test_valid_fresh_occupancy_allows_non_conflicting_hsi_offer(self):
        live_payload = {
            "availability_blocks": [{
                "availability_status": "blocked",
                "source_event_id": "valid-block",
                "instructor_name": "Brian Ennis",
                "location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
                "start_datetime": "2026-07-04T15:00:00-04:00",
                "end_datetime": "2026-07-04T21:00:00-04:00",
            }]
        }
        occupancy = block_start_time_selector.build_occupancy(
            {
                "sessions_current": {"sessions": []},
                "schedule_future": {"sessions": []},
                "live_availability_snapshot": live_payload,
                "location_resource_map": block_start_time_selector.read_required_json(block_start_time_selector.LOCATION_RESOURCE_MAP_PATH),
            },
            {},
        )
        conflict, reason = block_start_time_selector.generate_dynamic_offers.has_conflict(
            datetime(2026, 7, 4, 21, 0),
            datetime(2026, 7, 4, 21, 45),
            occupancy,
            ":: Wilmington; Shipyard Blvd",
            {"display_name": "Brian Ennis"},
        )
        self.assertFalse(conflict, reason)


if __name__ == "__main__":
    unittest.main()
