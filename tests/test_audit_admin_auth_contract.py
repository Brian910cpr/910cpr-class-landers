import importlib.util
import json
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from pathlib import Path

spec = importlib.util.spec_from_file_location("audit_admin_auth_contract", Path(__file__).resolve().parents[1] / "scripts/audit_admin_auth_contract.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class AdminAuthInventoryTests(unittest.TestCase):
    def test_records_keys_without_values_or_prompt_arguments(self):
        result = audit.inspect_source("docs/admin/example.html", """
const value = 'SYNTHETIC_PRIVATE_VALUE';
sessionStorage.setItem('hotSyncAdminKey', value);
localStorage.setItem('oldAdminKey', 'SYNTHETIC_STORED_VALUE');
prompt('SYNTHETIC_PROMPT_VALUE');
""")
        self.assertEqual([r["key"] for r in result["storage"]], ["hotSyncAdminKey", "oldAdminKey"])
        output = json.dumps(result)
        self.assertNotIn("SYNTHETIC_", output)
        self.assertEqual(result["markers"]["prompt_calls"], [5])

    def test_constant_candidate_and_unknown_expression_are_explicit(self):
        result = audit.inspect_source("docs/admin/demo.html", """
const STORAGE_KEY = 'prototype-drafts';
localStorage.getItem(STORAGE_KEY);
sessionStorage.getItem(computeKey());
""")
        self.assertEqual(result["storage"][0]["key"], "prototype-drafts")
        self.assertEqual(result["storage"][0]["resolution"], "constant_candidate")
        self.assertIsNone(result["storage"][1]["key"])
        self.assertEqual(result["storage"][1]["resolution"], "unresolved")

    def test_ambiguous_constant_does_not_claim_a_key(self):
        result = audit.inspect_source("docs/admin/demo.html", "const KEY='first'; KEY='second'; sessionStorage.getItem(KEY)")
        self.assertIsNone(result["storage"][0]["key"])

    def test_normalizes_assets_without_url_values_or_external_fetches(self):
        result = audit.inspect_source("docs/admin/demo.html", """
<script src="/assets/shared.js?v=SYNTHETIC_QUERY"></script>
<script src="../assets/other.js#SYNTHETIC_FRAGMENT"></script>
<script src="https://example.invalid/x.js?secret=SYNTHETIC_EXTERNAL"></script>
<link rel="stylesheet" href="/admin/nav.css">
""")
        self.assertEqual(result["direct_assets"], ["docs/admin/nav.css", "docs/assets/other.js", "docs/assets/shared.js"])
        self.assertNotIn("SYNTHETIC_", json.dumps(result))

    def test_inventories_property_and_corporate_keys_without_conflating_them(self):
        result = audit.inspect_source("docs/admin/demo.js", "sessionStorage.hotSyncAdminKey; sessionStorage.getItem('maximPortalSession'); sessionStorage.clear();")
        self.assertEqual({r["key"] for r in result["storage"]}, {"maximPortalSession", "hotSyncAdminKey"})
        self.assertEqual(result["markers"]["storage_clear_calls"], [1])

    def test_complete_admin_inventory_retains_missing_asset_evidence(self):
        def fake_git(*args):
            if args[0] == "rev-parse":
                return "a" * 40
            if args[0] == "ls-tree":
                return "docs/admin/demo.html\ndocs/admin/orphan.js\ndocs/admin/style.css\n"
            if args[0] == "show":
                path = args[1].split(":", 1)[1]
                self.assertNotEqual(path, "docs/assets/missing.js")
                return '<script src="/assets/missing.js"></script>' if path.endswith("demo.html") else ""
            self.fail(f"Unexpected Git call: {args[0]}")
        with patch.object(audit, "git", side_effect=fake_git), patch.object(
            audit.subprocess, "run", return_value=SimpleNamespace(returncode=1, stdout="")
        ):
            result = audit.build_inventory("HEAD")
        self.assertEqual(result["counts"]["admin_files"], 3)
        self.assertEqual(result["counts"]["missing_referenced_assets"], 1)
        self.assertEqual(result["counts"]["endpoint_boundaries"], 7)
        missing = next(r for r in result["files"] if r["path"] == "docs/assets/missing.js")
        self.assertFalse(missing["exists_in_source_commit"])


if __name__ == "__main__":
    unittest.main()
