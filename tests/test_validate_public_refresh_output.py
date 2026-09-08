from __future__ import annotations

import unittest

from scripts.validate_public_refresh_output import validate_admin_reconciliation


class ValidatePublicRefreshOutputTests(unittest.TestCase):
    def test_allows_durable_manual_but_rejects_stale_enrollware(self) -> None:
        current = {"sessions": [{"session_id": "ew-current"}]}
        admin = {"sources": {"hot_sync": {"available": True}}, "sessions": [
            {"session_id": "ew-current", "source": "enrollware_ical"},
            {"session_id": "hs-durable", "source": "hot_sync_manual", "hot_sync": True},
            {"session_id": "13963996", "source": "enrollware_ical"},
        ]}
        with self.assertRaisesRegex(ValueError, "13963996"):
            validate_admin_reconciliation(current, admin)

        admin["sessions"].pop()
        self.assertEqual({"ew-current", "hs-durable"}, validate_admin_reconciliation(current, admin))

    def test_rejects_manual_copy_of_same_durable_lineage(self) -> None:
        admin = {"sources": {"hot_sync": {"available": True}}, "sessions": [
            {"session_id": "hs-durable", "source": "hot_sync_manual", "hot_sync": True},
            {"session_id": "manual-copy-hs-durable", "source": "hot_sync_manual", "hot_sync": True},
        ]}
        with self.assertRaisesRegex(ValueError, "duplicate durable sessions"):
            validate_admin_reconciliation({"sessions": []}, admin)

    def test_rejects_admin_output_built_without_authoritative_hot_sync(self) -> None:
        admin = {"sources": {"hot_sync": {"available": False}}, "sessions": []}
        with self.assertRaisesRegex(ValueError, "authoritative HOT_SYNC"):
            validate_admin_reconciliation({"sessions": []}, admin)


if __name__ == "__main__":
    unittest.main()
