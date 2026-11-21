import unittest
from copy import deepcopy
from scripts.audit_instructor_intake_qualification import audit_qualification


class QualificationAuditTests(unittest.TestCase):
    def setUp(self):
        self.profiles = {"instructors": [{"instructor_key": "amy", "allowed_course_groups": ["ACLS", "PALS"]}]}
        self.catalog = {"instructors": [{"instructor_id": "amy", "active": True, "can_teach_course_ids": ["reviewed-fixture-id"], "can_teach_course_families": ["ACLS", "PALS"], "certifications": [{"certification_code": "fixture", "source": "synthetic evidence", "expiration_date": "2099-01-01"}]}]}

    def check(self):
        return audit_qualification(self.profiles, self.catalog, "amy")

    def test_static_pass_never_authorizes_publication(self):
        result = self.check()
        self.assertEqual([], result["reasons"])
        self.assertEqual("STATIC_CHECKS_PASSED", result["state"])
        self.assertFalse(result["can_publish"])

    def test_family_ceiling_does_not_substitute_for_exact_courses(self):
        self.catalog["instructors"][0]["can_teach_course_ids"] = []
        self.assertIn("exact_course_qualifications_unreviewed", self.check()["reasons"])

    def test_duplicate_identity_fails_closed(self):
        self.catalog["instructors"] *= 2
        self.assertIn("qualification_record_missing_or_ambiguous", self.check()["reasons"])

    def test_unknown_expiry_and_mismatched_families_require_review(self):
        self.catalog["instructors"][0]["certifications"][0]["expiration_date"] = "UNKNOWN"
        self.profiles["instructors"][0]["allowed_course_groups"].append("BLS")
        self.assertIn("certification_expiry_unreviewed", self.check()["reasons"])
        self.assertIn("profile_and_qualification_family_mismatch", self.check()["reasons"])

    def test_missing_instructor_does_not_borrow_another_record(self):
        self.assertIn("qualification_record_missing_or_ambiguous", audit_qualification(self.profiles, self.catalog, "nick")["reasons"])

    def test_audit_is_nonmutating(self):
        before = deepcopy(self.catalog)
        self.check()
        self.assertEqual(before, self.catalog)


if __name__ == "__main__":
    unittest.main()
