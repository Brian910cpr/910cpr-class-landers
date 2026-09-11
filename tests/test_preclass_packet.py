from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "docs/admin/all-classes.html").read_text(encoding="utf-8")
JS = (ROOT / "docs/admin/all-classes.js").read_text(encoding="utf-8")
EDGE = (ROOT / "supabase/functions/preclass-packet/index.ts").read_text(encoding="utf-8")
MANIFEST = (ROOT / "supabase/functions/preclass-packet/manifest.ts").read_text(encoding="utf-8")


class PreclassPacketTests(unittest.TestCase):
    def test_session_workspace_exposes_intentional_packet_options(self):
        self.assertIn('id="preclassPacket"', HTML)
        self.assertIn('id="printSkillsDescriptors" type="checkbox"', HTML)
        self.assertNotIn('id="printSkillsDescriptors" type="checkbox" checked', HTML)
        self.assertIn("printSkillsDescriptors:$('printSkillsDescriptors').checked", JS)

    def test_manifest_is_course_aware_and_preserves_supplied_sources(self):
        self.assertIn("aha_heartsaver_first_aid_cpr_aed", MANIFEST)
        self.assertIn("aha_heartsaver_first_aid_cpr_aed_blended", MANIFEST)
        for name in (
            "HS__Adult-CPR-AED-Skils-Testing-Sheet.pdf",
            "HS__Child-CPR-AED-Skills-Checklist.pdf",
            "HS__Infant-CPR-AED-Skills-Checklist-1.pdf",
            "HS__First-Aid-Skills-Testing.pdf",
        ):
            self.assertIn(name, MANIFEST)
        self.assertIn('student_pages:[1]', MANIFEST)
        self.assertEqual(MANIFEST.count('[2]'), 3)
        self.assertIn('student_copy_rule:"per_participant"', MANIFEST)
        self.assertIn('descriptor_copy_rule:"conditional_per_packet"', MANIFEST)

    def test_roster_is_ten_per_landscape_page_with_restrained_type(self):
        self.assertIn("offset+=10", EDGE)
        self.assertIn("i<10", EDGE)
        self.assertIn("pdf.addPage([792,612])", EDGE)
        sizes = [int(value) for value in re.findall(r"size:(\d+)", EDGE)]
        self.assertTrue(sizes)
        self.assertLessEqual(max(sizes), 16)
        roster = EDGE[EDGE.index("function drawRoster"):EDGE.index("function drawMaterials")]
        self.assertNotRegex(roster.lower(), r"purchase|material|fulfillment|addon")

    def test_materials_are_paid_outstanding_only_and_descriptors_once(self):
        self.assertIn("status=eq.paid", EDGE)
        self.assertIn("FULFILLED", EDGE)
        self.assertIn("outstanding(s.selected_addons)", EDGE)
        self.assertRegex(EDGE, r"if\(descriptors\)for\(const number of document\.descriptor_pages\)")
        self.assertIn("pdf.addPage(copied)}if(descriptors)for(const number of document.descriptor_pages", EDGE)
        self.assertIn("Required protected packet source is unavailable", EDGE)


if __name__ == "__main__":
    unittest.main()
