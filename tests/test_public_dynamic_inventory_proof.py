from __future__ import annotations

import unittest

from scripts import public_dynamic_inventory_proof as proof


class PublicDynamicInventoryProofTest(unittest.TestCase):
    def test_parses_rendered_appointment_seed_card_from_html(self) -> None:
        parser = proof.AppointmentCardParser()
        parser.feed("""
        <article class="slug-pill slug-appointment-option" data-source-type="seed">
          <div class="slug-pill-subtitle">AHA Heartsaver First Aid CPR AED - Blended</div>
          <a class="button small primary" href="https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&amp;startTime=2%3A30%20PM&amp;courseId=329495">Check this date/time</a>
        </article>
        """)

        self.assertEqual(1, len(parser.cards))
        self.assertIn("AHA Heartsaver", parser.cards[0]["text"])
        self.assertEqual(1, len(parser.cards[0]["links"]))
        self.assertIn("appointmentDayId=260683", parser.cards[0]["links"][0]["href"])

    def test_matches_rendered_href_to_seed_preview_and_integrity_record(self) -> None:
        pages = [{
            "page_path": "docs/heartsaver.html",
            "appointment_cards": [{
                "text": "AHA Heartsaver First Aid CPR AED - Blended Available class option",
                "links": [{
                    "href": "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A30%20PM&courseId=329495",
                    "text": "Check this date/time",
                }],
            }],
        }]
        seed_lookup = {
            ("260683", "329495", "14:30"): {
                "seed_id": "seed-1",
                "source_offer_id": "offer-1",
                "appointmentDayId": 260683,
                "course_id": "329495",
                "course_title": "AHA Heartsaver First Aid CPR AED - Blended",
                "date": "2026-07-04",
                "start_time": "14:30",
                "location": "Shipyard",
                "instructor_display_name": "Brian Ennis",
            }
        }
        integrity_records = {
            "offer-1": {
                "course_key": "Heartsaver",
                "display_course_name": "AHA Heartsaver First Aid CPR AED - Blended",
                "instructor": "Brian Ennis",
                "location": "Shipyard",
                "source_availability_block_used": "availability-1",
                "nearest_existing_enrollware_class_same_day_instructor_location": None,
                "overlap_status": "no_overlap",
            }
        }

        records = proof.dynamic_render_records(
            pages,
            seed_lookup,
            integrity_records,
            validate_urls=False,
        )

        self.assertEqual(1, len(records))
        self.assertTrue(records[0]["rendered_on_page"])
        self.assertTrue(records[0]["button_link_exists"])
        self.assertTrue(records[0]["trace_matched_seed_preview"])
        self.assertTrue(records[0]["trace_matched_integrity_record"])
        self.assertEqual("no_overlap", records[0]["overlap_status"])
        self.assertEqual("260683", records[0]["appointmentDayId"])
        self.assertEqual("329495", records[0]["courseId"])
        self.assertEqual("2:30 PM", records[0]["startTime"])

    def test_verdict_fails_when_public_dynamic_offers_do_not_render(self) -> None:
        status, reason = proof.verdict(
            {
                "public_sellable_dynamic_offers": 3,
                "rendered_dynamic_offers": 0,
            },
            [],
            {},
        )

        self.assertEqual("FAIL", status)
        self.assertIn("no appointment-seed cards", reason)

    def test_verdict_fails_when_public_sellable_output_drops_all_dynamic_offers(self) -> None:
        status, reason = proof.verdict(
            {
                "public_sellable_dynamic_offers": 0,
                "rendered_dynamic_offers": 0,
            },
            [],
            {},
        )

        self.assertEqual("FAIL", status)
        self.assertIn("No public sellable dynamic", reason)

    def test_verdict_is_unsafe_for_untraceable_rendered_offer(self) -> None:
        status, reason = proof.verdict(
            {
                "public_sellable_dynamic_offers": 1,
                "rendered_dynamic_offers": 1,
            },
            [{
                "overlap_status": "no_overlap",
                "button_link_exists": True,
                "url_validates_against_enrollware_page": True,
                "trace_matched_seed_preview": False,
                "trace_matched_integrity_record": True,
            }],
            {},
        )

        self.assertEqual("UNSAFE", status)
        self.assertIn("missing traceability", reason)


if __name__ == "__main__":
    unittest.main()
