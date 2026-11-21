# Issue 380 R33: exclusive collector publisher draft

PR_OPEN / BUILT only; baseline 33ecd52a256952bd9ee91b1947545c78a50d1b99; existing draft PR #381.

## Behavior and security boundary

R31/R32 allowed collector raw intake/card writes and direct event/receipt insertion. This additive review draft revokes those writes and moves the typed publisher to production_board_private. Its SECURITY DEFINER owner is a separate NOLOGIN, NOSUPERUSER, NOBYPASSRLS executor with no role memberships; collector logins cannot SET ROLE it. RLS remains effective. Search path remains empty, all relation references qualified. The authenticated session must belong to the collector capability; actor remains session_user. Existing expected-version, request/card/intake locks, historical replay, atomic audit/receipt rollback and can_execute=false are preserved. Draft application is transactional.

The executor has only the original transaction's required column/table permissions, not table ownership or resolution authority. Administrative owner remains trusted. Public/API roles cannot execute; private schema placement avoids a public RPC. This is a direct PostgreSQL connection contract, not JWT/auth.uid authentication. It needs reviewed production connection/role mapping before use. Raw reads retain prior scope; broader read minimization remains review work.

## Files and proof

- data/audit/issue380_collector_gateway_draft.sql
- tests/reconciliation/board_collector_gateway.py
- data/audit/issue380_collector_gateway_20261014.md

Local PostgreSQL 16.4, psycopg 3.2.10/libpq 160009. Dedicated existing portable cluster at 127.0.0.1:55480; explicit empty issue380_test_r33_proof database. No operational database accessed. Test-only trust-authenticated collector login removed after suite. 43/43 tests pass, including publisher contention, resolution races, replay/privacy, raw write/escalation denial and audit/receipt rollback. Python AST and git diff --check pass. Twenty observed Lock waits. No application/HTTP suite rerun because only SQL draft and local SQL fixtures changed.

Initial command assumed absent createdb and incorrect test role; existing reports identified issue380_local and psycopg creation. First gateway suite passed 43/43 before private-schema move. Schema move exposed two test-helper defaults still targeting old public function; fixed helper to use private function and reran fresh database. Failed runs are not proof.

Supabase skill/security checklist reviewed; changelog fetched 2026-10-14. HTTP cipher retirement and 15/17 minor upgrades do not alter this isolated 16.4 transaction proof; no production upgrade claim. PostgreSQL function security reference: https://www.postgresql.org/docs/16/sql-createfunction.html . Production advisors/privilege inspection not run; those remain rollout gates.

## Remaining gates and operational limits

All six acceptance criteria remain open. Authenticated collector role is not authoritative source attestation: publisher still accepts caller-provided issue/source state/reference. Next bind an approved authoritative reader to canonical card/issue/source identity and reject unsupported or mismatched observations; then independently prove production privileges and installed no-launch/pre-side-effect consumer with atomic external fence. Owner evidence/private storage/UI/history/counts/reopen/browser proof remain unfinished. No Brian/account action required for continued backend work. SQL stays outside migrations/unapplied; #381 remains draft/unmerged/undeployed. No generator, runtime install/state change, production mutation, #372 change or other assignment change. Original dirty checkout preserved; worktree case-collision docs/Earl/index.html and docs/Jackson/index.html excluded. Queue swept; no unrelated safe quick win selected over existing assignments/#371 primary.

Expected operational outcome is skip handled/blocked/already-corrected work before launch/mutation. No production end-to-end proof, cadence, installed observer or observer-health proof exists. Stale source/version mismatch/uncertain commit must fail closed. Recovery: inspect canonical intake/card/audit/request, reacquire authoritative source, retry against fresh version. Escalate only actual account/business decisions; Brian is not designated routine monitor. This strengthens native canonical lifecycle integrity without adding Enrollware dependency.

## Exact local command

ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 dbname=issue380_test_r33_proof user=issue380_local' E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_collector_gateway.py

## Full final local output

```text
PostgreSQL: PostgreSQL 16.4, compiled by Visual C++ build 1940, 64-bit
psycopg: 3.2.10 libpq: 160009
test_authenticated_collector_write_is_audited_per_transition (__main__.CollectorGateway.test_authenticated_collector_write_is_audited_per_transition) ... ok
test_capability_cannot_resolve_delete_rewrite_audit_or_escalate (__main__.CollectorGateway.test_capability_cannot_resolve_delete_rewrite_audit_or_escalate) ... ok
test_collector_and_manual_resolution_serialize_both_orders: observed Lock wait
test_collector_and_manual_resolution_serialize_both_orders: observed Lock wait
test_collector_and_manual_resolution_serialize_both_orders (__main__.CollectorGateway.test_collector_and_manual_resolution_serialize_both_orders) ... ok
test_collector_audit_failure_rolls_back_observation_and_version (__main__.CollectorGateway.test_collector_audit_failure_rolls_back_observation_and_version) ... ok
test_collector_conflicting_request_contention_preserves_first_receipt: observed Lock wait
test_collector_conflicting_request_contention_preserves_first_receipt (__main__.CollectorGateway.test_collector_conflicting_request_contention_preserves_first_receipt) ... ok
test_collector_first_publication_contention_replay_stale_and_rollback: observed Lock wait
test_collector_first_publication_contention_replay_stale_and_rollback: observed Lock wait
test_collector_first_publication_contention_replay_stale_and_rollback: observed Lock wait
test_collector_first_publication_contention_replay_stale_and_rollback (__main__.CollectorGateway.test_collector_first_publication_contention_replay_stale_and_rollback) ... ok
test_collector_provisional_response_and_receipt_failure_roll_back (__main__.CollectorGateway.test_collector_provisional_response_and_receipt_failure_roll_back) ... ok
test_collector_publication_replay_conflict_and_audit (__main__.CollectorGateway.test_collector_publication_replay_conflict_and_audit) ... ok
test_collector_publisher_roles_and_receipt_immutability (__main__.CollectorGateway.test_collector_publisher_roles_and_receipt_immutability) ... ok
test_collector_rejects_invalid_stale_resolved_identity_and_time (__main__.CollectorGateway.test_collector_rejects_invalid_stale_resolved_identity_and_time) ... ok
test_collector_serializes_owner_and_dispatch: observed Lock wait
test_collector_serializes_owner_and_dispatch: observed Lock wait
test_collector_serializes_owner_and_dispatch: observed Lock wait
test_collector_serializes_owner_and_dispatch (__main__.CollectorGateway.test_collector_serializes_owner_and_dispatch) ... ok
test_dispatch_audit_failure_rolls_back_reservation (__main__.CollectorGateway.test_dispatch_audit_failure_rolls_back_reservation) ... ok
test_dispatch_canonical_gates (__main__.CollectorGateway.test_dispatch_canonical_gates) ... ok
dispatch competing reservations: observed Lock wait
test_dispatch_competing_reservations_lock (__main__.CollectorGateway.test_dispatch_competing_reservations_lock) ... ok
test_dispatch_intake_change_invalidates_reservation (__main__.CollectorGateway.test_dispatch_intake_change_invalidates_reservation) ... ok
test_dispatch_intake_identity_cannot_move (__main__.CollectorGateway.test_dispatch_intake_identity_cannot_move) ... ok
test_dispatch_intake_writer_first_no_deadlock: observed Lock wait
test_dispatch_intake_writer_first_no_deadlock (__main__.CollectorGateway.test_dispatch_intake_writer_first_no_deadlock) ... ok
test_dispatch_reader_first_intake_writer_waits: observed Lock wait
test_dispatch_reader_first_intake_writer_waits (__main__.CollectorGateway.test_dispatch_reader_first_intake_writer_waits) ... ok
test_dispatch_reservation_replay_and_conflict (__main__.CollectorGateway.test_dispatch_reservation_replay_and_conflict) ... ok
test_dispatch_resolution_between_checks_skips (__main__.CollectorGateway.test_dispatch_resolution_between_checks_skips) ... ok
test_dispatch_roles (__main__.CollectorGateway.test_dispatch_roles) ... ok
test_dispatch_stale_source_and_expired_lease (__main__.CollectorGateway.test_dispatch_stale_source_and_expired_lease) ... ok
test_dispatch_then_publication_invalidates_pre_side_effect: observed Lock wait
test_dispatch_then_publication_invalidates_pre_side_effect (__main__.CollectorGateway.test_dispatch_then_publication_invalidates_pre_side_effect) ... ok
test_distinct_request_stale_writer_rejected: observed contender Lock wait
test_distinct_request_stale_writer_rejected (__main__.CollectorGateway.test_distinct_request_stale_writer_rejected) ... ok
test_identical_request_replays_once: observed contender Lock wait
test_identical_request_replays_once (__main__.CollectorGateway.test_identical_request_replays_once) ... ok
test_initial_insert_is_audited_and_private_card_text_denied (__main__.CollectorGateway.test_initial_insert_is_audited_and_private_card_text_denied) ... ok
DENIED: six privilege bypasses and promotion from nonadmin login
test_nonadmin_login_cannot_bypass_observation_guard (__main__.CollectorGateway.test_nonadmin_login_cannot_bypass_observation_guard) ... ok
test_other_collector_request_collision_rolls_back_without_receipt_disclosure (__main__.CollectorGateway.test_other_collector_request_collision_rolls_back_without_receipt_disclosure) ... ok
test_owner_assertion_cannot_become_authoritative_reservation (__main__.CollectorGateway.test_owner_assertion_cannot_become_authoritative_reservation) ... ok
test_owner_republication_downgrades_previous_source_observation (__main__.CollectorGateway.test_owner_republication_downgrades_previous_source_observation) ... ok
test_publication_audit_failure_atomic_rollback_and_retry (__main__.CollectorGateway.test_publication_audit_failure_atomic_rollback_and_retry) ... ok
test_publication_competing_first_publishers: observed Lock wait
test_publication_competing_first_publishers (__main__.CollectorGateway.test_publication_competing_first_publishers) ... ok
test_publication_create_update_replay_conflict (__main__.CollectorGateway.test_publication_create_update_replay_conflict) ... ok
test_publication_rejects_stale_resolved_identity_and_time (__main__.CollectorGateway.test_publication_rejects_stale_resolved_identity_and_time) ... ok
test_publication_roles (__main__.CollectorGateway.test_publication_roles) ... ok
test_publication_then_dispatch_waits_and_rechecks: observed Lock wait
test_publication_then_dispatch_waits_and_rechecks (__main__.CollectorGateway.test_publication_then_dispatch_waits_and_rechecks) ... ok
test_raw_writes_and_executor_escalation_denied (__main__.CollectorGateway.test_raw_writes_and_executor_escalation_denied) ... ok
test_request_reuse_across_cards_conflicts: observed contender Lock wait
test_request_reuse_across_cards_conflicts (__main__.CollectorGateway.test_request_reuse_across_cards_conflicts) ... ok
test_rollback_releases_request_without_phantom_receipt: observed contender Lock wait
test_rollback_releases_request_without_phantom_receipt (__main__.CollectorGateway.test_rollback_releases_request_without_phantom_receipt) ... ok
DENIED and rolled back: insert
DENIED and rolled back: promote
DENIED and rolled back: refresh
test_routine_observation_writes_denied_atomically (__main__.CollectorGateway.test_routine_observation_writes_denied_atomically) ... ok
test_same_request_changed_payload_conflicts: observed contender Lock wait
test_same_request_changed_payload_conflicts (__main__.CollectorGateway.test_same_request_changed_payload_conflicts) ... ok
test_trusted_dml_cannot_delete_and_rebind_canonical_intake (__main__.CollectorGateway.test_trusted_dml_cannot_delete_and_rebind_canonical_intake) ... ok
test_trusted_dml_cannot_rebind_issue_despite_bypassing_publisher (__main__.CollectorGateway.test_trusted_dml_cannot_rebind_issue_despite_bypassing_publisher) ... ok

----------------------------------------------------------------------
Ran 43 tests in 8.731s

OK

```
