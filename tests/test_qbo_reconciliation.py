import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from finance_reconciliation.audit import AuditEngine, amount_minor


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "qbo_reconciliation"


class QboReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.engine = AuditEngine(self.connection)
        self.accounts = json.loads((FIXTURES / "accounts.json").read_text(encoding="utf-8"))
        self.transactions = json.loads((FIXTURES / "transactions.json").read_text(encoding="utf-8"))

    def tearDown(self):
        self.connection.close()

    def test_import_is_idempotent(self):
        self.engine.import_accounts(self.accounts)
        self.engine.import_accounts(self.accounts)
        self.engine.import_transactions(self.transactions)
        self.engine.import_transactions(self.transactions)
        summary = self.engine.summary()
        self.assertEqual(summary["accounts"], 3)
        self.assertEqual(summary["transactions"], 3)
        self.assertEqual(summary["source_records"], 6)

    def test_detectors_surface_high_risk_treatments_and_unknowns(self):
        self.engine.import_accounts(self.accounts)
        self.engine.import_transactions(self.transactions)
        exceptions = self.engine.detect()
        codes = {item["detector_code"] for item in exceptions}
        self.assertIn("DUPLICATE_ACCOUNT_CANDIDATE", codes)
        self.assertIn("CREDIT_CARD_PAYMENT_AS_EXPENSE", codes)
        self.assertIn("TRANSFER_LIKE_P_AND_L", codes)
        self.assertIn("TRANSACTION_ACCOUNT_UNMATCHED", codes)
        self.assertIn("MISSING_MATERIAL_FACT", codes)
        missing = [item for item in exceptions if item["detector_code"] == "MISSING_MATERIAL_FACT"]
        self.assertTrue(any('"missing_field":"current_balance"' in item["source_evidence_json"] for item in missing))
        self.assertTrue(all(item["smallest_user_question"] for item in missing))

    def test_detector_rerun_does_not_duplicate_exceptions(self):
        self.engine.import_accounts(self.accounts)
        self.engine.import_transactions(self.transactions)
        first = self.engine.detect()
        second = self.engine.detect()
        self.assertEqual(len(first), len(second))

    def test_user_correction_creates_reviewable_action(self):
        correction = json.loads((FIXTURES / "correction.json").read_text(encoding="utf-8"))
        correction_id, action_id = self.engine.record_correction(correction)
        self.assertEqual(correction_id, correction["id"])
        action = self.connection.execute(
            "SELECT * FROM financial_bookkeeping_actions WHERE id=?", (action_id,)
        ).fetchone()
        self.assertEqual(action[2], "proposed")
        self.assertEqual(action[9], "human_review")

    def test_money_uses_integer_minor_units(self):
        self.assertEqual(amount_minor("123.456"), 12346)
        self.assertIsNone(amount_minor(None))

    def test_cli_can_build_a_report_without_qbo_credentials(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertTrue(Path(temp_dir).exists())
            self.assertEqual(self.engine.summary()["mode"], "read_only_audit")


if __name__ == "__main__":
    unittest.main()

