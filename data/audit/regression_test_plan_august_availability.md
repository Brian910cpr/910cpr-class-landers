# Regression Test Plan: August Availability

Implemented checks:

- `tests.test_live_availability_snapshot_trace` verifies seed simulation sees August BLS availability while the active live snapshot does not, and records the divergence before Course Master gates.
- `tests.test_generate_dynamic_offers.DynamicOffersTest.test_august_live_snapshot_block_generates_august_bls_offer` verifies that when a valid August BLS live snapshot block exists, dynamic generation produces an August offer.
- Existing `tests.test_audit_august_seed_breakpoint` verifies August cannot silently disappear without the breakpoint report naming the upstream source mismatch.

Manual/read-only validation commands:

- `python -m scripts.audit_august_seed_breakpoint`
- `python -m unittest tests.test_audit_august_seed_breakpoint`
- `python -m unittest tests.test_live_availability_snapshot_trace`
- `python -m unittest tests.test_generate_dynamic_offers.DynamicOffersTest.test_august_live_snapshot_block_generates_august_bls_offer`
- `python -m scripts.public_offer_integrity_audit`
