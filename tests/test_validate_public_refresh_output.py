from __future__ import annotations

import unittest

from scripts.validate_public_refresh_output import validate_admin_reconciliation, validate_public_demand
from scripts.fetch_canonical_scheduling_demand import validate_payload, SCHEMA_VERSION
from datetime import datetime, timedelta, timezone


class ValidatePublicRefreshOutputTests(unittest.TestCase):
    def demand(self, count=1):
        now = datetime(2026, 9, 27, 14, 0, tzinfo=timezone.utc)
        return now, {
            "schema_version": SCHEMA_VERSION, "generated_at": now.isoformat(),
            "non_session_sources": [], "sessions": [{
                "canonical_session_id": "canonical-incident", "external_class_id": "14361098",
                "active_registration_count": count, "count_available": True,
                "demand_basis": "canonical_active_registrations", "freshness_minutes": 60,
                "source_observed_at": (now - timedelta(minutes=59)).isoformat(),
            }],
        }

    def test_current_zero_and_positive_counts_allow_publication(self):
        for count in (0, 1):
            now, demand = self.demand(count)
            validate_public_demand([{"session_id": "14361098"}], validate_payload(demand, now=now))

    def test_source_expiring_during_build_refuses_publication_without_faking_zero(self):
        now, demand = self.demand()
        generated = [{"session_id": "14361098", "active_registration_count": 1, "count_available": True}]
        validate_public_demand(generated, validate_payload(demand, now=now))
        expired = validate_payload(demand, now=now + timedelta(minutes=2))
        with self.assertRaisesRegex(ValueError, "14361098: stale_reconciliation"):
            validate_public_demand(generated, expired)
        self.assertIsNone(expired["sessions"][0]["active_registration_count"])
        self.assertEqual(generated[0]["active_registration_count"], 1)

    def test_missing_and_ambiguous_relationships_refuse_publication(self):
        now, demand = self.demand()
        with self.assertRaisesRegex(ValueError, "14421081: missing_canonical_session"):
            validate_public_demand([{"session_id": "14421081"}], validate_payload(demand, now=now))
        duplicate = dict(demand["sessions"][0], canonical_session_id="another-canonical")
        demand["sessions"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "14361098: ambiguous"):
            validate_public_demand([{"session_id": "14361098"}], validate_payload(demand, now=now))

    def test_private_or_quarantined_sources_do_not_block_unrelated_public_rows(self):
        now, demand = self.demand()
        demand["sessions"].append({
            "canonical_session_id": "private-unreconciled", "external_class_id": "13895152",
            "active_registration_count": None, "count_available": False, "demand_basis": "unknown",
        })
        validate_public_demand([{"session_id": "14361098"}], validate_payload(demand, now=now))

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
