from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "docs/admin/all-classes.html").read_text(encoding="utf-8")
JS = (ROOT / "docs/admin/all-classes.js").read_text(encoding="utf-8")
PERSON_HTML = (ROOT / "docs/admin/person-record.html").read_text(encoding="utf-8")
PERSON_JS = (ROOT / "docs/admin/person-record.js").read_text(encoding="utf-8")
NAV = (ROOT / "docs/admin/admin-nav.js").read_text(encoding="utf-8")


class AllClassesWorkspaceTests(unittest.TestCase):
    def test_owner_workspace_uses_canonical_schedule_and_secure_admin_key(self):
        self.assertIn("canonical-session-workspace", JS)
        self.assertIn("LanderWareAdminAuth.fetch", JS)
        self.assertNotIn("sessionStorage.getItem('hotSyncAdminKey')", JS)
        self.assertIn("noindex,nofollow,noarchive", HTML)

    def test_owner_can_see_rosters_and_create_operational_classes(self):
        self.assertIn("CanonicalSessionModel.participantRows", JS)
        self.assertIn("schedule.910cpr.com/admin/hot-sync", JS)
        self.assertIn("Save Class to Schedule", HTML)
        self.assertIn("Print Pre-Class Roster", HTML)
        self.assertIn("Download AHA eCard Import CSV", HTML)

    def test_class_record_exposes_credentials_people_files_and_intake(self):
        self.assertIn("eCard / Credential", JS)
        self.assertIn("/admin/person-record.html?id=", JS)
        self.assertIn("data-view-document", JS)
        self.assertIn("data-download-document", JS)
        self.assertIn("Drop Data Into This Class", HTML)
        self.assertIn("Attach &amp; Parse", HTML)
        self.assertIn("action=intake", JS)
        self.assertIn("action=person", PERSON_JS)
        self.assertIn("Canonical participant identity", PERSON_HTML)

    def test_active_selection_and_finalized_warning_are_explicit(self):
        css = (ROOT / "docs/admin/all-classes.css").read_text(encoding="utf-8")
        self.assertIn(".event.selected", css)
        self.assertIn("Finalized class.", HTML)
        self.assertIn("do not change a credential already issued", HTML)
        self.assertIn("['/admin/all-classes.html','ALL Classes']", NAV)


if __name__ == "__main__":
    unittest.main()
