from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import build_slug_hubs
from scripts.landerware_agent_interface import find_availability
from scripts.public_dynamic_inventory import collect_public_dynamic_inventory, merge_appointment_seed_offers


EMPTY_SCHEDULE = {"timezone": "America/New_York", "sessions": []}


class PublicDynamicInventoryParityTests(unittest.TestCase):
    def test_hub_uses_shared_merge_implementation(self) -> None:
        self.assertIs(build_slug_hubs.merge_appointment_seed_offers, merge_appointment_seed_offers)

    def test_legacy_loader_and_agent_share_only_proposed_rows(self) -> None:
        fixture = Path(__file__).parent / "fixtures" / "customer_facing_offers.json"
        original = build_slug_hubs.CUSTOMER_FACING_OFFERS_PATH
        build_slug_hubs.CUSTOMER_FACING_OFFERS_PATH = fixture
        try:
            normalized = build_slug_hubs.load_customer_facing_offers()
        finally:
            build_slug_hubs.CUSTOMER_FACING_OFFERS_PATH = original
        contract = collect_public_dynamic_inventory(
            legacy_requestable_by_course=normalized, universal_by_hub={}, modeled_seed_by_hub={},
            public_sellable_seed_by_hub={}, generated_at="2026-08-08T12:00:00-04:00",
        )
        result = find_availability(
            {"course_key": "bls-renewal"}, schedule=EMPTY_SCHEDULE, offers={}, course_master={},
            public_dynamic_inventory=contract,
        )
        self.assertEqual(["bls-renewal-wilmington-20260813-1300"], [row["offering_id"] for row in result["options"]])

    def test_presentation_policy_row_is_normalized_once_then_shared(self) -> None:
        source = {
            "course_id": "329495", "course_title": "AHA Heartsaver First Aid CPR AED - Blended",
            "course_family": "Heartsaver", "date": "2026-08-14", "start_time": "14:30",
            "appointment_display_start": "2026-08-14T14:30:00-04:00",
            "appointment_display_end": "2026-08-14T15:15:00-04:00",
            "location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
            "instructor_display_name": "Brian Ennis", "appointmentDayId": 260724,
            "render_source": "dynamic_offer_presentation_policy",
        }
        catalog = {"329495": {"course_id": "329495", "course_key": "aha_heartsaver_first_aid_cpr_aed_blended", "family": "Heartsaver", "appointment_allowed": True}}
        normalized = build_slug_hubs.build_hub_seed_offer_from_public_sellable("policy-offer-1", source, catalog, [], {})
        self.assertIsNotNone(normalized)
        contract = collect_public_dynamic_inventory(
            legacy_requestable_by_course={}, universal_by_hub={}, modeled_seed_by_hub={},
            public_sellable_seed_by_hub={"heartsaver": [normalized]}, generated_at="2026-08-08T12:00:00-04:00",
        )
        self.assertEqual([normalized], contract["appointment_seed_by_hub"]["heartsaver"])
        result = find_availability(
            {"course_id": "329495"}, schedule=EMPTY_SCHEDULE, offers={}, course_master={}, public_dynamic_inventory=contract,
        )
        self.assertEqual("policy-offer-1", result["options"][0]["offering_id"])
        self.assertEqual(normalized["appointment_registration_url"], result["options"][0]["registration_url"])

    def test_public_sellable_gate_fails_closed_before_collection(self) -> None:
        blocked_catalog = {"329495": {"course_id": "329495", "course_key": "blocked", "family": "Heartsaver", "appointment_allowed": False}}
        row = build_slug_hubs.build_hub_seed_offer_from_public_sellable(
            "blocked-offer", {"course_id": "329495", "course_family": "Heartsaver", "date": "2026-08-14", "start_time": "14:30", "appointmentDayId": 260724},
            blocked_catalog, [], {},
        )
        self.assertIsNone(row)
        contract = collect_public_dynamic_inventory(
            legacy_requestable_by_course={}, universal_by_hub={}, modeled_seed_by_hub={}, public_sellable_seed_by_hub={},
        )
        self.assertEqual({}, contract["appointment_seed_by_hub"])

    def test_approved_seed_and_universal_sources_preserve_precedence(self) -> None:
        url = "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260724&startTime=2%3A30%20PM&courseId=329495"
        universal = {"hub_slug": "heartsaver", "course_id": "329495", "course_key": "hs", "course_title": "HS", "start_datetime": "2026-08-14T14:30:00-04:00", "display_item_type": "appointment_seed_offer", "appointment_registration_url": url, "source_offer_id": "universal-1"}
        duplicate_modeled = dict(universal, source_offer_id="modeled-duplicate", render_source="auto_public_appointment_seed")
        request_only = {"hub_slug": "heartsaver", "course_id": "329495", "course_key": "hs", "course_title": "HS", "start_datetime": "2026-08-15T14:30:00-04:00", "display_item_type": "request_only_availability_offer", "request_url": "/request_group_session.html?course=329495", "offer_id": "request-1"}
        contract = collect_public_dynamic_inventory(
            legacy_requestable_by_course={}, universal_by_hub={"heartsaver": [universal, request_only]},
            modeled_seed_by_hub={"heartsaver": [duplicate_modeled]}, public_sellable_seed_by_hub={},
        )
        self.assertEqual("universal-1", contract["appointment_seed_by_hub"]["heartsaver"][0]["source_offer_id"])
        self.assertEqual(2, len(contract["universal_by_hub"]["heartsaver"]))
        result = find_availability(
            {"course_id": "329495"}, schedule=EMPTY_SCHEDULE, offers={}, course_master={}, public_dynamic_inventory=contract,
        )
        self.assertEqual({"universal-1", "request-1"}, {row["offering_id"] for row in result["options"]})

    def test_contract_round_trips_as_build_artifact(self) -> None:
        contract = collect_public_dynamic_inventory(
            legacy_requestable_by_course={}, universal_by_hub={}, modeled_seed_by_hub={}, public_sellable_seed_by_hub={},
            generated_at="2026-08-08T12:00:00-04:00",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "public_dynamic_inventory.json"
            from scripts.public_dynamic_inventory import write_public_dynamic_inventory
            write_public_dynamic_inventory(path, contract)
            self.assertEqual(contract, json.loads(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
