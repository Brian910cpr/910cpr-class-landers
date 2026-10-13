# Issue 380 R20 — consistent intake/card lock ordering

BUILT / validated locally. PR #381 stays draft, unmerged, undeployed. All six original acceptance criteria remain open. No execution permission is added: every dispatch response still has can_execute=false.

## Finding and repair
R19 locked card then intake, while ordinary intake UPDATE/DELETE locks intake then the AFTER trigger updates card. A real two-session negative control reproduced DeadlockDetected against unchanged R19 SQL. The dispatcher now takes intake FOR SHARE before card FOR UPDATE, matching intake DML. Future authenticated publisher/version-check RPCs must follow this order. Request advisory locking remains first for the dispatcher; intake DML takes no request advisory lock.

Mature transactional practice is consistent lock acquisition rather than depending on deadlock victim recovery. Canonical card/version/history remain authoritative; no new object or Enrollware dependency is introduced. This advances native queue integrity without changing incumbent training workflows.

Existing-row update/delete cannot slip between intake observation and commit because the SHARE lock lasts for the transaction. Missing intake has no gap lock: a concurrent insert may remain unseen and yield canonical_intake_required review. That is conservative and must not be treated as proof of absence or permission to execute. Multi-card/bulk writer ordering, arbitrary trusted-role card-first writes, authenticated publication, and installed external mutation fencing remain separate review gates; this repair does not promise universal deadlock freedom.

## Files changed
- data/audit/issue380_dispatch_transaction_draft.sql (unapplied review SQL, outside migrations)
- tests/reconciliation/board_dispatch_transaction.py
- data/audit/issue380_intake_lock_order_20261013.md (this report)
- unique root R20 receipt

## Isolated proof
Existing dedicated local PostgreSQL 16.4 cluster: E:/GitHub/issue380-pg-portable/cluster-r16, explicitly started with -h 127.0.0.1 -p 55480. psycopg 3.2.10, libpq 160009. Fresh empty targets issue380_test_r20_negative and issue380_test_r20_final. Synthetic fixtures retained; server stopped afterward. No production DB or migration runner used.

Initial tooling setup: portable distribution has no createdb.exe; initial server launch omitted port override and test connection timed out (0 tests). Stopped it, restarted explicitly on loopback:55480, created empty databases through local psycopg admin connection. No credential or account blocker.

Commands (from E:/GitHub/910cpr-issue380-r20-20261013):
```powershell
$env:ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 user=issue380_local dbname=issue380_test_r20_negative'
E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_dispatch_transaction.py DispatchTransaction.test_dispatch_intake_writer_first_no_deadlock
# Negative control before SQL repair:
# observed Lock wait; psycopg.errors.DeadlockDetected: deadlock detected
# CONTEXT: while locking tuple in production_board_dispatch_intake
# Ran 1 test; FAILED (errors=1)

$env:ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 user=issue380_local dbname=issue380_test_r20_final'
E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_dispatch_transaction.py
node --test tests/production_dispatch_decision.test.mjs tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/live_dispatch_check.test.mjs tests/owner_access.test.mjs
# Python ast.parse on changed test; git diff --check
```
Final PostgreSQL output:
```text
PostgreSQL: PostgreSQL 16.4, compiled by Visual C++ build 1940, 64-bit
psycopg: 3.2.10 libpq: 160009
test_dispatch_audit_failure_rolls_back_reservation ... ok
test_dispatch_canonical_gates ... ok
test_dispatch_competing_reservations_lock ... observed Lock wait; ok
test_dispatch_intake_change_invalidates_reservation ... ok
test_dispatch_intake_identity_cannot_move ... ok
test_dispatch_intake_writer_first_no_deadlock ... observed Lock wait; ok
test_dispatch_reader_first_intake_writer_waits ... observed Lock wait; ok
test_dispatch_reservation_replay_and_conflict ... ok
test_dispatch_resolution_between_checks_skips ... ok
test_dispatch_roles ... ok
test_dispatch_stale_source_and_expired_lease ... ok
test_distinct_request_stale_writer_rejected ... observed Lock wait; ok
test_identical_request_replays_once ... observed Lock wait; ok
test_request_reuse_across_cards_conflicts ... observed Lock wait; ok
test_rollback_releases_request_without_phantom_receipt ... observed Lock wait; ok
test_same_request_changed_payload_conflicts ... observed Lock wait; ok
Ran 16 tests in 3.315s
OK
```
Node: 68 tests, 68 pass, 0 fail/cancelled/skipped/todo. Python AST and git diff --check pass. Actual SQL parsed/executed in isolated database. Writer-first test observes dispatcher waiting, commits blocker/version update, then dispatcher sees stale_card_version. Reader-first test observes writer waiting until decision commit; later pre-side-effect check sees stale version. Both deny execution.

## Operational contract and next action
Expected outcome remains skip resolved/blocked work before launch and recheck before side effects. Last local lock-order proof: 2026-10-13T10:36Z; no production end-to-end proof exists. No deployed cadence/observer/observer-health proof exists for this draft. Stale/missing intake/version/commit/fence must deny execution. Recovery: fresh reconciliation, same-ID retry for uncertain outcome; engineering reviews publisher provenance/version binding and lock protocol before runtime integration. Brian is not assigned monitoring or account work.

Next: authenticated typed-intake publication with expected-version/idempotency/audit and consistent lock protocol, policy/provenance review, then installed no-launch/pre-mutation and external fence proof. Private evidence and resolution/history/count UI remain unfinished. No production mutation, runtime/state/task change, merge or deploy authorized/performed. #371/#372 and all assignments preserved. Queue scanned; no competing deep stream opened.

## Hygiene
Original E:/GitHub/910cpr-class-landers contains unrelated dirty work and fetch fails on bad object 6e61cabca5981d1389e52c60d95424d9893bb50f. Left intact. Used healthy existing clone/worktree machinery to create codex/issue380-r20-20261013 from PR tip 6c17d9724c0f5266afc9b5ed469f52cdf7106fc7. Windows case-collision dirt docs/Earl/index.html and docs/Jackson/index.html excluded from staging. No generators run, caches/binaries committed, cleanup or unrelated edits.
