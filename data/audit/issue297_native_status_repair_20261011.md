# Issue 297: native registration visibility correction

Observed and applied 2026-10-11 01:40 UTC (October 10 EDT). This is a narrow production data correction; the broader incident remains BLOCKED.

## Finding and authority

Execution was acknowledged before implementation at issue comment 6104245400. The owner's October 10 continuation requests two existing registrations on the October 13 09:00–11:00 EDT Heartsaver session. Live canonical SQL showed both attendees already attached to `eb020e4a-b74a-443e-acd8-05727c2a8170`, with status `active`. No move or new registration was necessary. The current owner and demand endpoints recognize `registered`, `confirmed`, and `completed`; `active` silently contributed zero. Only two canonical registrations globally had that anomalous status.

Authoritative code: `supabase/functions/_shared/external-roster-proof.ts`, `supabase/functions/canonical-scheduling-demand/index.ts`, and `supabase/functions/canonical-session-workspace/index.ts`. Their contract was preserved. This correction uses native Session/Registration relationships and moves toward Enrollware independence without inventing source roster truth. No new workflow or schema was introduced.

## Applied operation

`data/audit/issue297_native_registration_status_repair.sql` is the exact guarded transaction, defaulting to ROLLBACK. The production application changed only its final ROLLBACK to COMMIT. Target time, source, scope, lifecycle, registration source and two exact identities are checked under row locks. Each status correction creates one uniquely keyed `participant_lifecycle_events` audit event. A second committed application was a no-op.

Dry-run, application, and replay each returned:

```json
{"session_id":"eb020e4a-b74a-443e-acd8-05727c2a8170","registered_count":2,"audit_event_count":2,"target_relationship_count":2,"expected_registration_count":2}
```

Rollback was independently verified: before application both statuses remained `active`, with zero correction events. After application both were `registered`, with exactly two correction events. No registration was created or moved. All other registration fields, including existing notes/survey data, remained unchanged. Both source/target session records remained unchanged. Notes were not rewritten; actual table setup/accommodation fulfillment is not proven by this data correction.

Before/after invariants:

| Evidence | Before | After |
|---|---|---|
| Registration fields excluding status/updated_at, MD5 equality check | 4aaa5e8afb2400287e704e1309ac011c | 4aaa5e8afb2400287e704e1309ac011c |
| Both session records, MD5 equality check | 98b8ba5eb12b9e7640b1ddfbfc1c297f | 98b8ba5eb12b9e7640b1ddfbfc1c297f |
| Global registrations | 10848 | 10848 |
| Global registration orders | 8 | 8 |
| Correction audit events | 0 | 2 |

Neither affected registration has a `registration_orders` row, registration requirements, or a pre-existing participant lifecycle event. Therefore paid status, prior move provenance, and accommodation fulfillment cannot be reconstructed from these tables. The owner's already-paid instruction was not used to manufacture an order, payment, refund, requirement, or charge. External and other native billing tables were not changed.

## Verification

- SQL syntax and behavior: real production rollback, guarded commit, independent readback, committed idempotent replay.
- `node --check tests/issue297_native_status_repair.test.cjs`: passed.
- `node --test tests/issue297_native_status_repair.test.cjs tests/canonical_demand_endpoint.test.cjs tests/enrollware_roster_proof.test.cjs`: 24 passed, 0 failed. Regression reproduces anomalous zero, restores two existing identities under the established status contract, and preserves unrelated known/unknown demand.
- `git diff --check`: passed.
- Protected owner workspace workflow [38102617030](https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/38102617030): success; 68 sessions, 39 active relationships, 7 sessions with participants, 58 unknown counts. This global check verifies count/participant consistency; it does not separately publish a target-specific owner UI capture.
- Protected demand workflow [38102614367](https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/38102614367): success, repeated response equality, OPTIONS 204, anonymous 401. Exact target at `2026-10-11T01:40:43.813Z`: count 2, count_available true, demand_status current, workspace_projection_status current. Full PII-free target and summary: `data/audit/issue297_status_repair_endpoint_20261011.json`.
- Reconciliation observer [38102658022](https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/38102658022): expected failure; 35 gaps at `2026-10-11T01:41:29.020524+00:00`. Full list and watermark evidence: `data/audit/issue297_status_repair_health_20261011.json`. This correct failure must not be bypassed or relabeled green.

## Boundaries and continuation

Current end-to-end evidence is PROVEN for the native canonical relationship → protected demand count. The overall migration bridge is CONNECTED with active failure observation, not HEALTHY. Its expected source window remains 60 minutes. The latest prior full-source successful proof is documented in `Codex_Read_Issue297_CanonicalReconciliation_R4.md`; present health evidence shows most source watermarks still September 27 and two later partial refreshes expired. Database reads cannot renew source evidence.

Current browser inventory is exactly `{"apps":[],"browsers":[]}`. This dispatch has no authenticated Enrollware UI surface and no newly supplied completeness-guaranteed unattended roster/export feed. Current full-source reconciliation therefore stops at source acquisition. Recovery requires an authenticated current complete roster/lifecycle snapshot, then the existing `scripts/enrollware_roster_reconciliation.py` → `reconcile_enrollware_roster_batch` path. Retain cancellation/reschedule/empty-roster evidence and original owner location/deadline decisions. Then verify owner view, public Anchor/selector retention, and a later scheduled cycle. Do not re-run broad publishers against guessed counts.

The observer's newest scheduled run before this dispatch was 38097625803 at 00:12 UTC; this dispatch's manual health check proves it remains executable and correctly detects the 35-gap signature. Independent observer-of-observer health was not established here. The owner must not become the routine monitoring layer; unattended source provisioning remains an unresolved account-level dependency.

No app code, schema, Edge Function, or public static page was deployed. Public selector/Anchor refresh and accommodation setup remain unverified. No site generator ran. PR372 remains draft, unmerged and undeployed. The issue queue was scanned; no independent deep stream or existing assignment was taken over. Existing backend work was preserved.

The original dirty checkout was untouched. Git fetch encountered pre-existing `bad object refs/remotes/origin/codex/group-training-experience`; no ref cleanup was attempted. Current main objects were usable, so an isolated named worktree was created at `E:/GitHub/910cpr-issue297-status-proof-20261010`. Windows checkout exposes unrelated case-collision changes in `docs/Earl/index.html` and `docs/Jackson/index.html`; neither is staged. Downloads remain outside the repository under the OS temporary directory. Only explicitly named audit, SQL, regression and receipt files belong in the commit.
