"""Fail-closed proof that admitted checkout leases shape provisional gravity only."""
import copy
import unittest

from scripts.layered_scheduling_engine import run


class ProvisionalCheckoutHoldTests(unittest.TestCase):
    def fixture(self, now="2026-12-07T08:10:00-05:00"):
        return dict(
            name="isolated-provisional-hold",
            now=now,
            availability=[dict(instructor="Brian Ennis", location="Room B",
                start="2026-12-07T08:00:00-05:00",
                end="2026-12-07T18:00:00-05:00")],
            capabilities={"Brian Ennis": ["bls", "hs"]},
            courses={
                "bls": dict(family="BLS", kind="full", duration_minutes=120, locations=["Room B"]),
                "hs": dict(family="Heartsaver", kind="full", duration_minutes=90, locations=["Room B"]),
            },
            sources=[],
            policy=dict(slot_minutes=30, cleanup_minutes=0, lead_minutes=0,
                require_verified_day_gravity=True, full_class_consolidation_scope="course",
                paid_full_positions_per_family_day=1, business_timezone="America/New_York"),
        )

    def hold(self, ident="A", course="bls", start="12:00", end="14:00",
             admitted="08:00", expires="08:15"):
        day = "2026-12-07T"
        return dict(
            id="lease-"+ident, kind="hold", course=course, instructor="Brian Ennis",
            location="Room B", start=day+start+":00-05:00",
            end=day+end+":00-05:00",
            source_file="canonical_checkout_hold_ledger",
            checkout_hold_status="admitted", hold_admission_attested=True,
            checkout_hold_capacity_claimed=True, checkout_hold_resource_verified=True,
            checkout_hold_id="hold-"+ident, checkout_order_id="order-"+ident,
            hold_admitted_at=day+admitted+":00-05:00",
            hold_expires_at=day+expires+":00-05:00",
        )

    def test_admitted_hold_is_provisional_gravity_but_not_seated_public_offer(self):
        fixture = self.fixture()
        fixture["sources"].append(self.hold())
        result = run(fixture)
        self.assertEqual([b["source_ids"] for b in result["blocks"]], [["lease-A"]])
        self.assertFalse(result["seated_offers"])
        self.assertTrue(any(c["course"] == "hs" and c["mode"] == "barnacle"
                            and c["start"].hour == 15 and c["start"].minute == 30
                            for c in result["accepted"]))
        self.assertFalse(any(c["course"] == "bls" and c["mode"] == "barnacle"
                             for c in result["accepted"]))
        self.assertIn("full_course_already_paid_seated", result["rejection_reasons"])

    def test_mirrored_or_unproven_hold_blocks_interval_without_fabricating_gravity(self):
        for change in (
            {"source_file": "canonical_class_sessions"},
            {"hold_admission_attested": False},
            {"checkout_hold_capacity_claimed": False},
            {"checkout_hold_resource_verified": False},
            {"checkout_hold_status": "pending"},
            {"instructor_unassigned": True},
            {"hold_expires_at": "not-a-time"},
        ):
            with self.subTest(change=change):
                fixture = self.fixture()
                fixture["sources"].append({**self.hold(), **change})
                result = run(fixture)
                self.assertEqual(result["blocks"], [])
                self.assertTrue(result["normalized_occupancy"])
                self.assertTrue(any(c["mode"] == "free" for c in result["accepted"]))
                self.assertFalse(any(c["mode"] == "barnacle" for c in result["accepted"]))

    def test_expiring_a_releases_only_a_while_b_keeps_own_gravity(self):
        fixture = self.fixture()
        fixture["sources"] = [
            self.hold(),
            self.hold("B", "hs", "10:00", "11:30", admitted="08:05", expires="08:25"),
        ]
        before = run(copy.deepcopy(fixture))
        self.assertEqual(len(before["blocks"]), 2)
        fixture["now"] = "2026-12-07T08:16:00-05:00"
        after = run(fixture)
        self.assertEqual([b["source_ids"] for b in after["blocks"]], [["lease-B"]])
        self.assertEqual({b["id"] for b in after["normalized_occupancy"]}, {"lease-B"})
        self.assertIn({"source_id": "lease-A", "reason": "checkout_hold_expired"},
                      after["ignored_sources"])
        self.assertFalse(after["seated_offers"])
        self.assertTrue(any(c["course"] == "bls" and c["mode"] == "barnacle"
                            for c in after["accepted"]))
        # Later both leases expire: no old schedule snapshot is restored.
        fixture["now"] = "2026-12-07T08:26:00-05:00"
        later = run(fixture)
        self.assertFalse(later["blocks"])
        self.assertFalse(later["normalized_occupancy"])
        self.assertTrue(any(c["mode"] == "free" for c in later["accepted"]))


    def test_publication_applies_hold_gravity_without_joinable_seat(self):
        # The publisher may see source-attested demand even in a different
        # availability window; it must collapse open-day offers without
        # inventing a seated registration URL for an unpaid hold.
        from tests.test_layered_publication_adapter import LayeredPublicationTests
        test = LayeredPublicationTests("test_source_records_not_mutated_and_explicit_activation_required")
        test.setUp()
        test.windows = []
        test.coverage = []
        test.window(11, "08:00", "18:00", next_day=False)
        clear = test.calculation()
        self.assertTrue(any(o.get("scheduleRole") == "open_day"
                            for o in test.payload(calculation=clear)["offers"]))
        source = dict(source_event_id="private-hold-source",
            kind="hold", course_id="359474", instructor="Brian Ennis",
            resource=test.room, source_file="canonical_checkout_hold_ledger",
            start=test.at(11, "12:00").isoformat(),
            end=test.at(11, "14:00").isoformat(),
            checkout_hold_status="admitted", hold_admission_attested=True,
            checkout_hold_capacity_claimed=True, checkout_hold_resource_verified=True,
            checkout_hold_id="h", checkout_order_id="o",
            hold_admitted_at="2026-10-05T11:50:00-04:00",
            hold_expires_at="2026-10-05T12:05:00-04:00")
        clear["projected_sources"] = [source]
        provisional = test.payload(calculation=clear)
        self.assertFalse(any(o.get("offerType") == "seated_class"
                             for o in provisional["offers"]))
        self.assertFalse(any(o.get("scheduleRole") == "open_day"
                             for o in provisional["offers"]))
        self.assertIn("anchored_day_requires_attached_offer",
                      provisional["rejectionReasonCounts"])
        # A's expiration removes only the provisional day gravity, not a
        # second independent commitment or a stored snapshot.
        source["hold_expires_at"] = "2026-10-05T11:59:00-04:00"
        restored = test.payload(calculation=clear)
        self.assertTrue(any(o.get("scheduleRole") == "open_day"
                            for o in restored["offers"]))


if __name__ == "__main__":
    unittest.main()
