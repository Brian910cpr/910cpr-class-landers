from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "cloudflare" / "maxim-email" / "src" / "index.js"
WRANGLER = ROOT / "cloudflare" / "maxim-email" / "wrangler.toml"
BRIDGE = ROOT / "supabase" / "functions" / "maxim-link-email" / "index.ts"
SITE_THEME = ROOT / "docs" / "assets" / "site-theme.js"


class MaximSendLinkEmailTests(unittest.TestCase):
    def test_cloudflare_worker_sends_requested_reminder_from_brian(self) -> None:
        source = WORKER.read_text(encoding="utf-8")
        self.assertIn("brian@910cpr.com", source)
        self.assertIn("replyTo: FROM", source)
        self.assertIn("Maxim has asked me to remind you that your CPR Card is expiring soon", source)
        self.assertIn("910-395-5193", source)
        self.assertIn("910-251-8990", source)
        self.assertIn("env.EMAIL.send", source)
        self.assertIn("MAXIM_EMAIL_SECRET", source)
        self.assertIn("Requested by is required", source)

    def test_cloudflare_email_binding_restricts_sender(self) -> None:
        source = WRANGLER.read_text(encoding="utf-8")
        self.assertIn('name = "910cpr-maxim-email"', source)
        self.assertIn('name = "EMAIL"', source)
        self.assertIn('allowed_sender_addresses = [ "brian@910cpr.com" ]', source)

    def test_supabase_bridge_uses_authenticated_employee_record_and_marks_sent_after_delivery(self) -> None:
        source = BRIDGE.read_text(encoding="utf-8")
        self.assertIn("maxim_portal_sessions", source)
        self.assertIn("customers(first_name,email)", source)
        self.assertIn("MAXIM_EMAIL_WORKER_URL", source)
        self.assertIn("MAXIM_EMAIL_WORKER_SECRET", source)
        self.assertLess(source.index("const mailResponse = await fetch"), source.index("link_sent_at: sentAt"))
        self.assertIn("emailSent: true", source)

    def test_confirmation_modal_requires_review_before_send(self) -> None:
        source = SITE_THEME.read_text(encoding="utf-8")
        self.assertIn("Confirm scheduling reminder", source)
        self.assertIn("Send to", source)
        self.assertIn("maximSendCourse", source)
        self.assertIn("maximSendBilling", source)
        self.assertIn("Requested by (Maxim member)", source)
        self.assertIn("Confirm & Send", source)
        self.assertIn("Review the details before anything is sent.", source)
        self.assertIn("requestedBy.focus()", source)
        self.assertIn("Enter the Maxim member requesting this reminder.", source)

    def test_confirmation_prefills_course_and_billing_but_allows_changes(self) -> None:
        source = SITE_THEME.read_text(encoding="utf-8")
        self.assertIn('option value="BLS">AHA BLS', source)
        self.assertIn('option value="HS Total">Heartsaver Total', source)
        self.assertIn('option value="#031">Maxim #031', source)
        self.assertIn('option value="#0852">MaximBH #0852', source)
        self.assertIn('option value="#502">MaximDSP #502', source)
        self.assertIn('course.value = String(person.course || "").includes("BLS") ? "BLS" : "HS Total"', source)
        self.assertIn('billing.value = ["#031", "#0852", "#502"].includes(person.billing)', source)
        self.assertIn("course: course.value", source)
        self.assertIn("billingAccount: billing.value", source)
        self.assertIn("requestedBy: requester", source)

    def test_bridge_persists_confirmed_current_cycle_values_after_delivery(self) -> None:
        source = BRIDGE.read_text(encoding="utf-8")
        self.assertIn('allowedCourses = new Set(["BLS", "HS Total"])', source)
        self.assertIn('allowedBillingAccounts = new Set(["#031", "#0852", "#502"])', source)
        self.assertIn("required_training: input.course", source)
        self.assertIn("billing_account: input.billingAccount", source)
        self.assertIn("Requested by ${input.requestedBy}", source)
        self.assertIn("requestedBy: input.requestedBy", source)
        self.assertLess(source.index("const mailResponse = await fetch"), source.index("required_training: input.course"))

    def test_current_billing_change_does_not_rewrite_registration_history(self) -> None:
        source = BRIDGE.read_text(encoding="utf-8")
        self.assertIn("maxim_employee_profiles?id=eq.", source)
        self.assertNotIn("maxim_registration_requests?id=eq.", source)
        self.assertNotIn("billing_account: input.billingAccount", source[source.index("const mailResponse = await fetch"):source.index("const sentAt = new Date().toISOString()")])

    def test_maxim_send_link_click_uses_email_bridge_not_local_mail_client(self) -> None:
        source = SITE_THEME.read_text(encoding="utf-8")
        self.assertIn("installMaximSendLinkEmail", source)
        self.assertIn("functions/v1/maxim-link-email", source)
        self.assertIn("employeeId: pendingPerson.id", source)
        self.assertIn("Scheduling reminder sent to", source)
        maxim_override = source[source.index("window.emailScheduleLink = function"):]
        self.assertNotIn("mailto:", maxim_override)


if __name__ == "__main__":
    unittest.main()
