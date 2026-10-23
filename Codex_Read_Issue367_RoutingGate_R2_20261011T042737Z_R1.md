# Codex Read — Issue #367 Routing Diagnosis R2

- **Round:** 20261011T042737Z-I367-ROUTING-DIAGNOSIS-READ
- **Reply:** `Codex_Reply_Issue367_RoutingGate_20261011_R2.md`
- **Receipt tip:** `47ed08602cab8cb81f588055f1a754599f0eea66`
- **Draft PR:** #379

Reviewed the reported failing assertion and the corresponding generated/source code boundary.

Finding accepted: the regression is substantive, not a stale test. Both `docs/bls.html` and `scripts/build_bls_block_schedule_pilot.py` currently route the registration link directly to `course.appointmentUrl`; neither resolves a `nativeSessionId` and conditionally emits the canonical `/register/?session=...` URL required by the test.

No application change was made in this round, and none is safe before confirming current canonical eligibility and source identifiers. Do not delete or weaken the fail-closed test.

PR #379 remains draft, unmerged, and undeployed. Preserve the active #371/#372 deep stream. After the single-stream allocation is explicitly transferred to #367, reuse #379, validate canonical BLS identities/eligibility, make the narrow generator/output correction, then complete the broader family/manual/Stripe/webhook acceptance matrix and browser proof. No Brian credential action is required for this diagnostic.
