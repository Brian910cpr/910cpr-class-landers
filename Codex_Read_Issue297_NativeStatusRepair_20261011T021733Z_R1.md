# Codex Read — Issue #297 Native Status Repair

- **Round:** 20261011T021733Z-I297-NATIVE-STATUS-ACCEPT-R1
- **Reply reviewed:** `Codex_Reply_Issue297_NativeStatusRepair_20261011_R1.md`
- **Substantive commit:** `1df49fa934cf17507793d9a0bd11bd8575cd0b98`
- **Receipt tip:** `75dad74e3c083bcfdbd633da7f84f411198121d9`

Reviewed the handoff, audit report, guarded SQL, endpoint proof, health proof, and 24 focused tests.

## Acceptance

The narrow production correction is accepted as proven:

- The two October 13, 2026 9:00 AM Heartsaver registrations were already attached to canonical session `eb020e4a-b74a-443e-acd8-05727c2a8170`.
- Their anomalous `active` statuses were normalized to `registered`.
- Two uniquely keyed lifecycle correction events were added.
- No registrations were created or moved; global registration and order totals were unchanged.
- Non-status registration fields and the target session were unchanged.
- A committed replay was a no-op, establishing idempotence.
- Protected-demand and owner-consistency checks passed with canonical demand count 2.

Do not recreate or move these attendees. This evidence does not establish payment provenance, a canonical order, or accommodation fulfillment.

## Remaining #297 gate

The broader reconciliation remains open at 35 gaps because no authenticated, completeness-guaranteed roster/lifecycle source is available. Stage 6 remains gated.

Next repository/Codex action after the source is available: obtain a current complete roster and run the existing `scripts/enrollware_roster_reconciliation.py` flow into `reconcile_enrollware_roster_batch`, then verify the durable incident without duplicating unchanged gap reports.

Brian-only action: authorize or provision a completeness-guaranteed unattended Enrollware roster source.
