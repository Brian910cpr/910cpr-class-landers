from __future__ import annotations

import unittest

from scripts import rendered_dynamic_offer_proof as proof


class RenderedDynamicOfferProofTest(unittest.TestCase):
    def test_constructs_audited_appointment_href_with_encoded_start_time(self) -> None:
        href = proof.appointment_href({
            "appointmentDayId": 260683,
            "start_time": "14:30",
            "course_id": "329495",
        })

        self.assertEqual(
            "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A30%20PM&courseId=329495",
            href,
        )

    def test_parser_captures_rendered_appointment_link_and_dynamic_marker(self) -> None:
        parser = proof.LinkContextParser()
        parser.feed("""
        <article class="slug-pill slug-appointment-option" data-source-type="seed">
          <span>AHA Heartsaver First Aid CPR AED - Blended</span>
          <a href="https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&amp;startTime=2%3A30%20PM&amp;courseId=329495">Check this date/time</a>
        </article>
        """)

        self.assertEqual(1, len(parser.links))
        self.assertEqual("Check this date/time", parser.links[0]["text"])
        self.assertTrue(parser.links[0]["distinguishable_as_dynamic"])
        self.assertIn("AHA Heartsaver", parser.links[0]["context_text"])

    def test_verdict_passes_only_when_all_public_dynamic_offers_render(self) -> None:
        status, reason = proof.verdict([
            {
                "rendered": True,
                "href_in_html_exactly_matches_audited_href": True,
                "link_or_button_text": ["Check this date/time"],
                "overlap_status": "no_overlap",
            },
            {
                "rendered": True,
                "href_in_html_exactly_matches_audited_href": True,
                "link_or_button_text": ["Check this date/time"],
                "overlap_status": "no_overlap",
            },
        ], {})

        self.assertEqual("PASS", status)
        self.assertIn("All public sellable dynamic", reason)

    def test_verdict_is_partial_when_any_public_dynamic_offer_is_missing_from_html(self) -> None:
        status, reason = proof.verdict([
            {
                "rendered": True,
                "href_in_html_exactly_matches_audited_href": True,
                "link_or_button_text": ["Check this date/time"],
                "overlap_status": "no_overlap",
            },
            {
                "rendered": False,
                "href_in_html_exactly_matches_audited_href": False,
                "link_or_button_text": [],
                "overlap_status": "no_overlap",
            },
        ], {})

        self.assertEqual("PARTIAL", status)
        self.assertIn("1 of 2", reason)

    def test_verdict_is_unsafe_for_rendered_overlap(self) -> None:
        status, reason = proof.verdict([
            {
                "rendered": True,
                "href_in_html_exactly_matches_audited_href": True,
                "link_or_button_text": ["Check this date/time"],
                "overlap_status": "overlaps_existing_class",
            },
        ], {})

        self.assertEqual("UNSAFE", status)
        self.assertIn("overlaps", reason)


if __name__ == "__main__":
    unittest.main()
