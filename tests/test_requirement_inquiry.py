from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BOOKING_HOME = ROOT / "docs" / "assets" / "booking-home.js"
FUNCTION = ROOT / "supabase" / "functions" / "requirement-inquiry" / "index.ts"
MIGRATION = ROOT / "supabase" / "migrations" / "20260730123000_requirement_inquiries.sql"


class RequirementInquiryTests(unittest.TestCase):
    def test_shared_component_uses_server_submission(self) -> None:
        source = BOOKING_HOME.read_text(encoding="utf-8")
        self.assertIn("Send this requirement to 910CPR", source)
        self.assertIn("/functions/v1/requirement-inquiry", source)
        self.assertNotIn("data-copy-requirement-help", source)
        self.assertNotIn("data-context-email-link", source)
        self.assertNotIn("mailto:info@910cpr.com", source)
        self.assertIn("sessionStorage.setItem(requirementSessionKey", source)
        self.assertIn("if (!response.ok || !result.sent || !result.inquiryId)", source)

    def test_endpoint_keeps_destination_server_side(self) -> None:
        source = FUNCTION.read_text(encoding="utf-8")
        self.assertIn('Deno.env.get("ADMIN_NOTIFY_EMAIL")', source)
        self.assertIn('Deno.env.get("RESEND_API_KEY")', source)
        self.assertIn("requirement_inquiry_rate_limited", source)
        self.assertIn("requirement_inquiry_sent", source)
        self.assertIn("MAX_PER_HOUR = 5", source)
        self.assertIn('phone.replace(/\\D/g, "").length < 7', source)
        self.assertNotIn("office@910cpr.com", source)
        self.assertNotIn("info@910cpr.com", source)

    def test_inquiry_table_is_private(self) -> None:
        source = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("enable row level security", source)
        self.assertIn("revoke all", source)
        self.assertIn("registration_id", source)


if __name__ == "__main__":
    unittest.main()
