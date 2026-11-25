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
            source_file="landerware_public_orders",
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


    def test_same_slot_independent_leases_survive_adapter_dedup_and_one_expiry(self):
        # Two distinct customers can claim separate capacity-backed seats in
        # the SAME existing class. The exact occupied geometry matches; when A
        # leaves, B must not disappear during legacy/occupancy normalization.
        from tests.test_layered_publication_adapter import LayeredPublicationTests
        test = LayeredPublicationTests("test_source_records_not_mutated_and_explicit_activation_required")
        test.setUp()
        test.windows = []
        test.coverage = []
        test.window(11, "08:00", "18:00", next_day=False)
        test.policy["require_verified_day_gravity"] = True

        def lease(ident, expires):
            return dict(
                source_event_id="checkout-lease-" + ident, kind="hold",
                course_id="359474", instructor="Brian Ennis",
                resource=test.room, location_resolution="location_resource_map",
                start=test.at(11, "12:00").isoformat(),
                end=test.at(11, "14:30").isoformat(),
                source_file="landerware_public_orders",
                checkout_hold_status="admitted", hold_admission_attested=True,
                checkout_hold_capacity_claimed=True,
                checkout_hold_resource_verified=True,
                checkout_hold_id="hold-" + ident,
                checkout_order_id="order-" + ident,
                hold_admitted_at=test.at(5, "11:50").isoformat(),
                hold_expires_at=test.at(5, expires).isoformat(),
            )

        a, b = lease("A", "12:05"), lease("B", "12:20")
        # Same lease, different source-event alias is not a second claim.
        mirror = dict(b, source_event_id="mirror-of-B")
        test.sources = [a, b, mirror]
        before = test.calculation()
        self.assertEqual(before["counts"]["failed_windows"], 0, before["issues"])
        self.assertEqual({item["id"] for item in before["reports"][0]["normalized_occupancy"]},
                         {"checkout-lease-A", "checkout-lease-B"})
        self.assertFalse(before["reports"][0]["seated_offers"])

        test.now = test.at(5, "12:06")
        after = test.calculation()
        self.assertEqual(after["counts"]["failed_windows"], 0, after["issues"])
        self.assertEqual({item["id"] for item in after["reports"][0]["normalized_occupancy"]},
                         {"checkout-lease-B"})
        # The adapter may safely deduplicate an already-expired A before
        # the engine's ignored-sources diagnostics; B's survival is the invariant.
        self.assertTrue(any(candidate["mode"] == "barnacle"
                            for candidate in after["reports"][0]["accepted"]))
        self.assertFalse(after["reports"][0]["seated_offers"])

    def test_expired_offsite_lease_does_not_require_route_but_live_or_unproven_does(self):
        from tests.test_layered_publication_adapter import LayeredPublicationTests
        test = LayeredPublicationTests("test_source_records_not_mutated_and_explicit_activation_required")
        test.setUp()
        test.windows = []
        test.coverage = []
        test.window(11, "08:00", "18:00", next_day=False)
        lease = dict(source_event_id="fixture-offsite-lease", kind="hold",
            course_id="359474", instructor="Brian Ennis",
            location="fixture-unknown-offsite", resource="fixture-unknown-offsite",
            start=test.at(11, "12:00").isoformat(), end=test.at(11, "14:30").isoformat(),
            source_file="landerware_public_orders", checkout_hold_status="admitted",
            hold_admission_attested=True, checkout_hold_capacity_claimed=True,
            checkout_hold_resource_verified=True, checkout_hold_id="h", checkout_order_id="o",
            hold_admitted_at=test.at(5, "11:40").isoformat(),
            hold_expires_at=test.at(5, "11:55").isoformat())
        test.sources = [lease]
        expired = test.calculation()
        self.assertEqual(expired["counts"]["failed_windows"], 0, expired["issues"])
        self.assertEqual(expired["counts"]["normalized_sources"], 1)
        self.assertIn({"source_id": "fixture-offsite-lease", "reason": "checkout_hold_expired"},
                      expired["reports"][0]["ignored_sources"])
        self.assertTrue(any(c["mode"] == "free" for c in expired["reports"][0]["accepted"]))
        for change in ({"hold_expires_at": test.at(5, "12:05").isoformat()},
                       {"hold_admission_attested": False}):
            with self.subTest(change=change):
                test.sources = [dict(lease, **change)]
                blocked = test.calculation()
                self.assertEqual(blocked["counts"]["failed_windows"], 1)
                self.assertTrue(any("missing directional travel rule" in issue["reason"]
                                    for issue in blocked["issues"]))
        test.sources = [lease, dict(source_event_id="fixture-real-seat",
            kind="paid", course_id="359474", instructor="Brian Ennis",
            location="fixture-unknown-offsite", resource="fixture-unknown-offsite",
            start=test.at(11, "15:00").isoformat(), end=test.at(11, "17:00").isoformat(),
            source_file="canonical_class_sessions", count_available=True,
            active_registration_count=1)]
        self.assertEqual(test.calculation()["counts"]["failed_windows"], 1)

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
            resource=test.room, source_file="landerware_public_orders",
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
