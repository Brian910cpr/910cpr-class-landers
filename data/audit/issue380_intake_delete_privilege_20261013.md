# Issue 380 R26: preserve canonical intake across routine deletes

State: BUILT / PR_OPEN. Validated locally; not deployed. All six issue acceptance criteria remain open. Existing draft PR #381 reused; #371/#372 and existing assignments preserved.

## Finding and repair
At baseline dfe24bb44a6f3d93613b70831da79f90a0c2a14b, service_role could DELETE a published intake and INSERT a different issue_id for the same card. The R25 UPDATE invariant did not protect this path. The new denial regression failed before repair with `AssertionError: Error not raised`; both DELETE and replacement INSERT completed inside the test transaction. The assertion failure rolled that negative-control transaction back; no production target was involved.

Remove DELETE from the explicit service_role intake grant. The draft already revokes all table privileges first, so applying the entire draft to an empty isolated database gives SELECT/INSERT/UPDATE only. Publication and dispatch are SECURITY INVOKER and do not need DELETE. TRUNCATE also remains denied. This is a least-privilege repair, not an invented retention workflow or SECURITY DEFINER workaround. Canonical card/issue identity and its audit/replay history should survive ordinary caller writes; future retention or exceptional identity correction requires an explicit reviewed protocol. No Enrollware dependency added.

Regression proves denied DELETE/reinsert and TRUNCATE, rollback of an earlier intake UPDATE in the failed transaction, unchanged issue/blocked/version/activity, original request replay and successful subsequent audited in-place publication. Ordinary first publication and concurrency suites remain passing.

## Limitations / next engineering gate
The retained diagnostic provenance-forgery test still passes by reproducing the unresolved bypass: service_role can UPDATE authoritative_observation and obtain a non-executable reservation without mutation audit. This suite is NOT proof of secure collector attestation. No executable response is introduced; can_execute remains false.

Effective inherited memberships, live defaults, privileged table owners/superusers, trigger disabling, audit forgery and restricted authoritative collector writes remain unproven. This source grant change does not repair an existing deployed table: SQL remains outside migrations and unapplied. Do not run it against production as an incremental migration. Next implement/review a restricted collector mutation protocol with real deny/atomic provenance tests, followed by installed no-launch consumer, external side-effect fence/race proof and private evidence/history/count UI/browser proof. No Brian/account action required now.

## Validation
Dedicated existing portable PostgreSQL 16.4 cluster only, IPv4 loopback port 55480; psycopg 3.2.10/libpq 160009. Guarded empty databases issue380_test_r26_negative and issue380_test_r26_fixed. Existing operational databases were not accessed. Local test server stopped after proof.

Commands:
```
ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 user=issue380_local dbname=issue380_test_r26_negative' E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_intake_trust_boundary.py IntakeTrustBoundary.test_trusted_dml_cannot_delete_and_rebind_canonical_intake
ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 user=issue380_local dbname=issue380_test_r26_fixed' E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_intake_trust_boundary.py
node --test tests/production_intake_publication.test.mjs tests/production_dispatch_decision.test.mjs tests/live_dispatch_check.test.mjs tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/admin_auth.test.mjs
```
Negative: 1 failure as expected before repair. Final PostgreSQL: 28/28, 11 observed Lock waits. Node: 83/83, zero skipped/failures. Python AST syntax and git diff --check pass. Existing baseline broad Python board suite has previously documented obsolete auth assertions; not rerun for this SQL-only change.

Final exact PostgreSQL output:
```text
PostgreSQL: PostgreSQL 16.4, compiled by Visual C++ build 1940, 64-bit
psycopg: 3.2.10 libpq: 160009
test_dispatch_audit_failure_rolls_back_reservation (__main__.IntakeTrustBoundary.test_dispatch_audit_failure_rolls_back_reservation) ... ok
test_dispatch_canonical_gates (__main__.IntakeTrustBoundary.test_dispatch_canonical_gates) ... ok
dispatch competing reservations: observed Lock wait
test_dispatch_competing_reservations_lock (__main__.IntakeTrustBoundary.test_dispatch_competing_reservations_lock) ... ok
test_dispatch_intake_change_invalidates_reservation (__main__.IntakeTrustBoundary.test_dispatch_intake_change_invalidates_reservation) ... ok
test_dispatch_intake_identity_cannot_move (__main__.IntakeTrustBoundary.test_dispatch_intake_identity_cannot_move) ... ok
test_dispatch_intake_writer_first_no_deadlock: observed Lock wait
test_dispatch_intake_writer_first_no_deadlock (__main__.IntakeTrustBoundary.test_dispatch_intake_writer_first_no_deadlock) ... ok
test_dispatch_reader_first_intake_writer_waits: observed Lock wait
test_dispatch_reader_first_intake_writer_waits (__main__.IntakeTrustBoundary.test_dispatch_reader_first_intake_writer_waits) ... ok
test_dispatch_reservation_replay_and_conflict (__main__.IntakeTrustBoundary.test_dispatch_reservation_replay_and_conflict) ... ok
test_dispatch_resolution_between_checks_skips (__main__.IntakeTrustBoundary.test_dispatch_resolution_between_checks_skips) ... ok
test_dispatch_roles (__main__.IntakeTrustBoundary.test_dispatch_roles) ... ok
test_dispatch_stale_source_and_expired_lease (__main__.IntakeTrustBoundary.test_dispatch_stale_source_and_expired_lease) ... ok
test_dispatch_then_publication_invalidates_pre_side_effect: observed Lock wait
test_dispatch_then_publication_invalidates_pre_side_effect (__main__.IntakeTrustBoundary.test_dispatch_then_publication_invalidates_pre_side_effect) ... ok
test_distinct_request_stale_writer_rejected: observed contender Lock wait
test_distinct_request_stale_writer_rejected (__main__.IntakeTrustBoundary.test_distinct_request_stale_writer_rejected) ... ok
test_identical_request_replays_once: observed contender Lock wait
test_identical_request_replays_once (__main__.IntakeTrustBoundary.test_identical_request_replays_once) ... ok
test_owner_assertion_cannot_become_authoritative_reservation (__main__.IntakeTrustBoundary.test_owner_assertion_cannot_become_authoritative_reservation) ... ok
test_owner_republication_downgrades_previous_source_observation (__main__.IntakeTrustBoundary.test_owner_republication_downgrades_previous_source_observation) ... ok
test_publication_audit_failure_atomic_rollback_and_retry (__main__.IntakeTrustBoundary.test_publication_audit_failure_atomic_rollback_and_retry) ... ok
test_publication_competing_first_publishers: observed Lock wait
test_publication_competing_first_publishers (__main__.IntakeTrustBoundary.test_publication_competing_first_publishers) ... ok
test_publication_create_update_replay_conflict (__main__.IntakeTrustBoundary.test_publication_create_update_replay_conflict) ... ok
test_publication_rejects_stale_resolved_identity_and_time (__main__.IntakeTrustBoundary.test_publication_rejects_stale_resolved_identity_and_time) ... ok
test_publication_roles (__main__.IntakeTrustBoundary.test_publication_roles) ... ok
test_publication_then_dispatch_waits_and_rechecks: observed Lock wait
test_publication_then_dispatch_waits_and_rechecks (__main__.IntakeTrustBoundary.test_publication_then_dispatch_waits_and_rechecks) ... ok
test_request_reuse_across_cards_conflicts: observed contender Lock wait
test_request_reuse_across_cards_conflicts (__main__.IntakeTrustBoundary.test_request_reuse_across_cards_conflicts) ... ok
test_rollback_releases_request_without_phantom_receipt: observed contender Lock wait
test_rollback_releases_request_without_phantom_receipt (__main__.IntakeTrustBoundary.test_rollback_releases_request_without_phantom_receipt) ... ok
test_same_request_changed_payload_conflicts: observed contender Lock wait
test_same_request_changed_payload_conflicts (__main__.IntakeTrustBoundary.test_same_request_changed_payload_conflicts) ... ok
NEGATIVE CONTROL: trusted DML forged observation; no mutation audit; reservation only
test_trusted_dml_can_forge_observation_without_publication_audit (__main__.IntakeTrustBoundary.test_trusted_dml_can_forge_observation_without_publication_audit) ... ok
test_trusted_dml_cannot_delete_and_rebind_canonical_intake (__main__.IntakeTrustBoundary.test_trusted_dml_cannot_delete_and_rebind_canonical_intake) ... ok
test_trusted_dml_cannot_rebind_issue_despite_bypassing_publisher (__main__.IntakeTrustBoundary.test_trusted_dml_cannot_rebind_issue_despite_bypassing_publisher) ... ok

----------------------------------------------------------------------
Ran 28 tests in 4.877s

OK

```

## Persistence, hygiene and operational proof
Changed files: data/audit/issue380_dispatch_transaction_draft.sql; tests/reconciliation/board_intake_trust_boundary.py; this report data/audit/issue380_intake_delete_privilege_20261013.md; unique root receipt.
Isolated named branch codex/issue380-r26-20261013. Original dirty checkout untouched. Worktree Windows case-collision docs/Earl/index.html and docs/Jackson/index.html excluded from staging. Queue titles swept, no unrelated safely independent backend item selected over existing assignments. No generator, installed runtime/state/process/task change, production migration, merge/deployment or retired mailbox write.

Supabase skill applied; changelog fetched with local HTTP after browser markdown content-type failure. Current TLS cipher API change does not affect loopback SQL. Security grants/RLS guidance reviewed: https://supabase.com/docs/guides/database/postgres/row-level-security . No production advisor or live role inspection claimed.

Expected end-to-end success is blocked/handled work skipped before launch and every side effect, with durable canonical decision evidence. No production end-to-end proof or deployed observer/observer-health evidence exists for this draft. Failure includes stale/forged source, uncertain commit, resolution/version mismatch or absent external fence. Recovery is authenticated refresh/reconciliation with preserved request IDs, not blind retries. Policy windows (five-minute source, sixty-second reservation) remain review gates. Brian is not assigned routine monitoring. Keep #381 draft/unmerged/undeployed.
