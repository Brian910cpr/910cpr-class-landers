from __future__ import annotations

import csv
import json
import unittest

from scripts import build_course_master, export_course_master_review_sheet as review_sheet


class CourseMasterReviewSheetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        build_course_master.run()
        review_sheet.run()
        cls.master = json.loads(build_course_master.COURSE_MASTER_PATH.read_text(encoding="utf-8"))
        cls.summary = json.loads(review_sheet.JSON_PATH.read_text(encoding="utf-8"))
        with review_sheet.CSV_PATH.open(newline="", encoding="utf-8") as handle:
            cls.csv_rows = list(csv.DictReader(handle))

    def test_review_sheet_has_one_row_per_course_master_record(self) -> None:
        self.assertEqual(len(self.master["courses"]), len(self.summary["rows"]))
        self.assertEqual(len(self.master["courses"]), len(self.csv_rows))

    def test_every_row_has_exact_review_columns(self) -> None:
        expected = review_sheet.REVIEW_COLUMNS
        self.assertEqual(expected, self.summary["review_columns"])
        for row in self.summary["rows"]:
            self.assertEqual(set(expected), set(row.keys()))
        for row in self.csv_rows:
            self.assertEqual(set(expected), set(row.keys()))

    def test_public_sellable_offer_courses_are_marked(self) -> None:
        public_payload = json.loads(review_sheet.PUBLIC_SELLABLE_PATH.read_text(encoding="utf-8"))
        public_course_ids = {
            str(offer.get("course_id"))
            for offer in public_payload.get("offers", [])
            if isinstance(offer, dict)
        }
        marked_course_ids = {
            str(row["enrollware_course_id"])
            for row in self.summary["rows"]
            if row["used_by_public_sellable_dynamic_offer"]
        }
        self.assertTrue(public_course_ids)
        self.assertEqual(public_course_ids, marked_course_ids)

    def test_course_master_remains_non_authoritative(self) -> None:
        self.assertFalse(self.master["authoritative"])
        self.assertFalse(self.summary["course_master_authoritative"])

    def test_review_flags_are_booleans(self) -> None:
        for row in self.summary["rows"]:
            self.assertIsInstance(row["review_needed_for_scheduling"], bool)
            self.assertIsInstance(row["review_needed_for_rendering"], bool)
            self.assertIsInstance(row["review_needed_for_pricing_or_cards"], bool)


if __name__ == "__main__":
    unittest.main()
