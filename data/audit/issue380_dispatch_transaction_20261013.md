# Issue 380 R19 — transactional dispatch reservation and skip boundary

## Result
BUILT / validated locally only. Existing draft PR #381 remains draft, unmerged and undeployed. All six original acceptance criteria remain open. This increment adds a concrete service-role RPC and owner-authenticated proxy route, not an installed dispatcher or permission to execute external side effects.

Native canonical card identity, version and resolution remain authoritative. Typed dispatch intake records issue identity, blocker, authoritative source observation/provenance and worker-safe opt-in. It is separate from issue prose and cannot be supplied by the client through the new route. No Enrollware dependency is added. Mature queue semantics preserved: durable identity, explicit reservation expiry, idempotent requests, locked canonical state and atomic audit rather than implicit lane inference. The source observation freshness limit (5 minutes) and reservation window (60 seconds) are conservative DRAFT choices requiring review, not owner-approved operational policy.

## Exact files
- data/audit/issue380_dispatch_transaction_draft.sql — additive review draft; depends on issue380_resolution_transaction_draft.sql; neither applied to production.
- supabase/functions/production-board/dispatch-decision.mjs — validates bounded typed input, rejects client provenance/authority fields, binds RPC parameters, acknowledges successful RPC response, hides uncertain transport outcomes.
- supabase/functions/production-board/index.ts — POST /production-board/:cardId/dispatch-decision after existing owner authentication; one server-authenticated transactional RPC with 10-second timeout.
- tests/production_dispatch_decision.test.mjs — validation, acknowledgement failures and actual route execution under isolated authentication/fetch adapters.
- tests/reconciliation/board_dispatch_transaction.py — real PostgreSQL role, rollback, reservation contention and resolution-between-checks proof, reusing existing strict local/empty-target guard and five resolution contention tests.
- this report and unique root R19 reply.

## Transaction behavior and safety
A request ID is serialized and replayed only for identical payload. Card row and intake are locked. Missing/wrong issue intake, stale card version, stale/unknown source, missing worker opt-in, missing/expired reservation fail closed. Canonical resolution and explicit blocker yield recorded skips. Eligible selection can reserve one current card version for 60 seconds; a competing request waits and records reservation_active. Intake changes bump the card version, invalidating old reservations. Intake card identity cannot move. Decision and activity persist together, or both roll back. Decisions cannot be updated/deleted by service_role. Replay is historical and does not extend reservations.

Every response retains can_execute=false. Pre-side-effect checks record a review or skip; a valid reservation still reports runtime_fence_required. No launcher imports this new route. No worker is launched. This deliberately prevents a DB reservation from being misrepresented as an atomic fence around an external API/Git operation.

PostgREST success is interpreted as transaction commit acknowledgement, including deferred constraints. Transport failure is indeterminate: committed=false means commit NOT CONFIRMED, not proof of database rollback. Caller must retry SAME request ID. Gateway/real DB tests are separate isolated tests; no live PostgREST end-to-end proof is claimed.

## Limitations and next engineering action
Review schema/privilege/lock order and windows before promotion. Trusted service_role can author intake and insert decision rows; this is a trust boundary, not cryptographic owner identity. The audit actor describes the authenticated gateway, not a specific human. No authenticated intake publisher exists yet. Do not copy GitHub text into worker-safe flags. Current existing owner auth permits existing owner sessions and legacy automation key; no new public credential path.

Intake writers lock intake then card, while RPC locks card then intake. Concurrent operations may deadlock; PostgreSQL aborts one transaction, preserving fail-closed safety. An absent-intake insertion can likewise race with the card lock. Safe same-ID retry and lock-order review remain required before runtime integration. No deadlock recovery or installed no-launch/pre-mutation proof is claimed.

Next: security review of this draft, consistent intake lock-order protocol plus authenticated typed intake publication/version binding, then runtime consumer/fencing proof and idempotent external mutation boundary. Preserve #266 worker-safe opt-in gates, P0 priority and #371 primary stream. Private evidence, resolution UI/history/counts remain unfinished. No Brian credential/account action required now.

## Proof and operational status
Expected useful outcome: dispatcher skips resolved/blocked cards and records why before launch, then rechecks before mutation. Success evidence here is isolated committed DB decisions/activity plus gateway tests only. Last local proof: 2026-10-13T08:37:21.270449+00:00. No production end-to-end proof, operational cadence, installed observer or observer-health evidence exists for this draft. Failure conditions are unavailable canonical intake, stale version/source, expired reservation, uncertain commit or missing external fence; each denies execution. Recovery is same-ID retry after fresh canonical reconciliation; review gates require engineering, production rollout requires separate authorization. Brian is not assigned routine monitoring.

## Reproduction and full PostgreSQL output
Dedicated existing local cluster only: E:/GitHub/issue380-pg-portable/cluster-r16, IPv4 loopback 127.0.0.1:55480. PostgreSQL 16.4, psycopg 3.2.10/libpq 160009. Fresh EMPTY database issue380_test_r19_final; synthetic retained fixtures; no operational DB. Server stopped after tests. No dependencies/binaries/cache committed.

```powershell
$env:ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 user=issue380_local dbname=issue380_test_r19_final'
E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_dispatch_transaction.py
node --test tests/production_dispatch_decision.test.mjs tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/live_dispatch_check.test.mjs tests/owner_access.test.mjs
node --check supabase/functions/production-board/dispatch-decision.mjs
# Python ast.parse on board_dispatch_transaction.py; git diff --check
```
The guard refuses an already initialized target; create a new dedicated empty issue380_test_* database for reruns, preserving retained fixtures.

```text
PostgreSQL: PostgreSQL 16.4, compiled by Visual C++ build 1940, 64-bit
psycopg: 3.2.10 libpq: 160009
test_dispatch_audit_failure_rolls_back_reservation (__main__.DispatchTransaction.test_dispatch_audit_failure_rolls_back_reservation) ... ok
test_dispatch_canonical_gates (__main__.DispatchTransaction.test_dispatch_canonical_gates) ... ok
dispatch competing reservations: observed Lock wait
test_dispatch_competing_reservations_lock (__main__.DispatchTransaction.test_dispatch_competing_reservations_lock) ... ok
test_dispatch_intake_change_invalidates_reservation (__main__.DispatchTransaction.test_dispatch_intake_change_invalidates_reservation) ... ok
test_dispatch_intake_identity_cannot_move (__main__.DispatchTransaction.test_dispatch_intake_identity_cannot_move) ... ok
test_dispatch_reservation_replay_and_conflict (__main__.DispatchTransaction.test_dispatch_reservation_replay_and_conflict) ... ok
test_dispatch_resolution_between_checks_skips (__main__.DispatchTransaction.test_dispatch_resolution_between_checks_skips) ... ok
test_dispatch_roles (__main__.DispatchTransaction.test_dispatch_roles) ... ok
test_dispatch_stale_source_and_expired_lease (__main__.DispatchTransaction.test_dispatch_stale_source_and_expired_lease) ... ok
test_distinct_request_stale_writer_rejected: observed contender Lock wait
test_distinct_request_stale_writer_rejected (__main__.DispatchTransaction.test_distinct_request_stale_writer_rejected) ... ok
test_identical_request_replays_once: observed contender Lock wait
test_identical_request_replays_once (__main__.DispatchTransaction.test_identical_request_replays_once) ... ok
test_request_reuse_across_cards_conflicts: observed contender Lock wait
test_request_reuse_across_cards_conflicts (__main__.DispatchTransaction.test_request_reuse_across_cards_conflicts) ... ok
test_rollback_releases_request_without_phantom_receipt: observed contender Lock wait
test_rollback_releases_request_without_phantom_receipt (__main__.DispatchTransaction.test_rollback_releases_request_without_phantom_receipt) ... ok
test_same_request_changed_payload_conflicts: observed contender Lock wait
test_same_request_changed_payload_conflicts (__main__.DispatchTransaction.test_same_request_changed_payload_conflicts) ... ok

----------------------------------------------------------------------
Ran 14 tests in 2.589s

OK

```
Node summary: 68 tests, 68 pass, 0 fail/cancelled/skipped/todo. Python AST, Node syntax and git diff --check pass. Actual index.ts route evaluated with Node stripTypeScriptTypes in isolated VM. No generator, public page, migration, production writes, runtime installation/state/task/process changes, merge or deployment.

## Repository hygiene and queue
Original E:/GitHub/910cpr-class-landers dirty work preserved. Isolated codex/issue380-r19-20261013 worktree based on PR #381 tip cd882d51741c7616f2eae43e372495af66cbd853. Windows case-collision dirt docs/Earl/index.html and docs/Jackson/index.html excluded. Local Python __pycache__ excluded. Only explicit assignment files staged. Open issue queue scanned; #371/#372 and existing assignments preserved; no competing deep stream started.
