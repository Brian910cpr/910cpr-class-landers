from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RefreshAdminWorkflowTests(unittest.TestCase):
    def test_refresh_runs_every_thirty_minutes_and_keeps_manual_trigger(self):
        workflow = (ROOT / ".github" / "workflows" / "refresh-admin-availability.yml").read_text(encoding="utf-8")
        self.assertIn('cron: "*/30 * * * *"', workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("git diff --cached --quiet", workflow)

    def test_selector_publish_does_not_treat_appointment_shell_endpoint_as_inventory_authority(self):
        workflow = (ROOT / ".github" / "workflows" / "refresh-admin-availability.yml").read_text(encoding="utf-8")
        self.assertIn("apply_final_live_availability_guard", workflow)
        self.assertNotIn("apply_final_enrollware_appointment_guard", workflow)


if __name__ == "__main__":
    unittest.main()
