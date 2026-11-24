# Issue 380 R32: collector/manual-resolution contention proof

PR_OPEN / BUILT only. Baseline 37df660fb631f177ee48963a8e657c82660faff1.
Isolated branch codex/issue380-r32-20261014; reuse draft PR #381.

## Findings

Added three real PostgreSQL regression tests in tests/reconciliation/board_collector_publication.py. No SQL or application behavior changed.

- Collector publication first: owner resolution waits, then rejects stale version; canonical card remains unresolved at version 2, without a fabricated resolution event.
- Manual resolution first: collector waits, then rejects stale version; handled_manually/version 2 remains canonical, with no intake, observation audit or publication receipt. Retrying with the current version rejects card_resolved.
- Same collector request with conflicting payload waits and rejects idempotency_conflict; first receipt/audit remain unchanged. Cross-card reuse also conflicts without touching the second card.
- Another authenticated collector cannot read the first actor's receipt. Request reuse fails with UniqueViolation; the second card's observation, version, audit and receipt all roll back. The first actor's replay still succeeds. This is fail-closed database behavior, not a sanitized production API error contract.

## Validation

Local PostgreSQL 16.4 / psycopg 3.2.10 / libpq 160009: 42/42 tests pass, 20 observed Lock waits, including three new waits. AST syntax and git diff --check pass. SQL drafts parsed/executed by real PostgreSQL. Existing empty-database/explicit-loopback guard retained. Initial run before cross-actor test: 41/41; final run uses a separate empty database. No unrelated failures in executed tests. API/JS unchanged, so Node suites not repeated.

Commands:

```powershell
& E:/GitHub/issue380-pg-portable/server/bin/pg_ctl.exe -D E:/GitHub/issue380-pg-portable/cluster-r16 -l E:/GitHub/issue380-pg-portable/r32-server.log -o '-h 127.0.0.1 -p 55480' -w start
# Create empty issue380_test_r32_final via psycopg on dedicated local cluster.
$env:ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 user=issue380_local dbname=issue380_test_r32_final'
& E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_collector_publication.py
python -c "import ast,pathlib; ast.parse(pathlib.Path('tests/reconciliation/board_collector_publication.py').read_text()); print('AST PASS')"
git diff --check
& E:/GitHub/issue380-pg-portable/server/bin/pg_ctl.exe -D E:/GitHub/issue380-pg-portable/cluster-r16 -m fast -w stop
```

Local raw final output: E:/GitHub/issue380-pg-portable/r32-final-tests.txt; full output appended below. Test login roles removed, test server stopped; disposable fixtures retained. Original dirty checkout untouched. Worktree Windows case-collision dirt docs/Earl/index.html and docs/Jackson/index.html excluded from commits. No generator, production migration/write, runtime install/state change, merge/deployment or #372 change.

## Remaining gates

All six issue acceptance criteria remain open. Raw collector DML and direct receipt insertion remain available; authenticated actor is not authoritative source attestation. Next implement exclusive least-privilege audited gateway and bind authoritative reader to canonical issue/card/source identity. Then prove production privileges and installed no-launch consumer/external atomic side-effect fence; owner private evidence/UI/history/counts/reopen/browser proof remain unfinished. SQL stays outside migrations/unapplied; PR #381 stays draft. No Brian/account action required for continued backend engineering. Queue scanned; existing assignments preserved, #371 primary; no unrelated safe quick win selected.

Operational expected outcome: handled/blocked/already-corrected cards skip before launch/mutation. No production end-to-end proof or installed observer/cadence/observer-health evidence. Stale source, version mismatch or uncertain commit must fail closed. Recovery: inspect canonical card/intake/request/audit and retry only against fresh approved source/version. Escalate account decisions only when actually needed; Brian must not be the routine observer. This extends canonical lifecycle/concurrency integrity without adding Enrollware dependency.

## Full final local output

```text
PostgreSQL: PostgreSQL 16.4, compiled by Visual C++ build 1940, 64-bit
psycopg: 3.2.10 libpq: 160009
test_authenticated_collector_write_is_audited_per_transition (__main__.CollectorPublication.test_authenticated_collector_write_is_audited_per_transition) ... ok
test_capability_cannot_resolve_delete_rewrite_audit_or_escalate (__main__.CollectorPublication.test_capability_cannot_resolve_delete_rewrite_audit_or_escalate) ... ok
test_collector_and_manual_resolution_serialize_both_orders: observed Lock wait
test_collector_and_manual_resolution_serialize_both_orders: observed Lock wait
test_collector_and_manual_resolution_serialize_both_orders (__main__.CollectorPublication.test_collector_and_manual_resolution_serialize_both_orders) ... ok
test_collector_audit_failure_rolls_back_observation_and_version (__main__.CollectorPublication.test_collector_audit_failure_rolls_back_observation_and_version) ... ok
test_collector_conflicting_request_contention_preserves_first_receipt: observed Lock wait
test_collector_conflicting_request_contention_preserves_first_receipt (__main__.CollectorPublication.test_collector_conflicting_request_contention_preserves_first_receipt) ... ok
test_collector_first_publication_contention_replay_stale_and_rollback: observed Lock wait
test_collector_first_publication_contention_replay_stale_and_rollback: observed Lock wait
test_collector_first_publication_contention_replay_stale_and_rollback: observed Lock wait
test_collector_first_publication_contention_replay_stale_and_rollback (__main__.CollectorPublication.test_collector_first_publication_contention_replay_stale_and_rollback) ... ok
test_collector_provisional_response_and_receipt_failure_roll_back (__main__.CollectorPublication.test_collector_provisional_response_and_receipt_failure_roll_back) ... ok
test_collector_publication_replay_conflict_and_audit (__main__.CollectorPublication.test_collector_publication_replay_conflict_and_audit) ... ok
test_collector_publisher_roles_and_receipt_immutability (__main__.CollectorPublication.test_collector_publisher_roles_and_receipt_immutability) ... ok
test_collector_rejects_invalid_stale_resolved_identity_and_time (__main__.CollectorPublication.test_collector_rejects_invalid_stale_resolved_identity_and_time) ... ok
test_collector_serializes_owner_and_dispatch: observed Lock wait
test_collector_serializes_owner_and_dispatch: observed Lock wait
test_collector_serializes_owner_and_dispatch: observed Lock wait
test_collector_serializes_owner_and_dispatch (__main__.CollectorPublication.test_collector_serializes_owner_and_dispatch) ... ok
test_dispatch_audit_failure_rolls_back_reservation (__main__.CollectorPublication.test_dispatch_audit_failure_rolls_back_reservation) ... ok
test_dispatch_canonical_gates (__main__.CollectorPublication.test_dispatch_canonical_gates) ... ok
dispatch competing reservations: observed Lock wait
test_dispatch_competing_reservations_lock (__main__.CollectorPublication.test_dispatch_competing_reservations_lock) ... ok
test_dispatch_intake_change_invalidates_reservation (__main__.CollectorPublication.test_dispatch_intake_change_invalidates_reservation) ... ok
test_dispatch_intake_identity_cannot_move (__main__.CollectorPublication.test_dispatch_intake_identity_cannot_move) ... ok
test_dispatch_intake_writer_first_no_deadlock: observed Lock wait
test_dispatch_intake_writer_first_no_deadlock (__main__.CollectorPublication.test_dispatch_intake_writer_first_no_deadlock) ... ok
test_dispatch_reader_first_intake_writer_waits: observed Lock wait
test_dispatch_reader_first_intake_writer_waits (__main__.CollectorPublication.test_dispatch_reader_first_intake_writer_waits) ... ok
test_dispatch_reservation_replay_and_conflict (__main__.CollectorPublication.test_dispatch_reservation_replay_and_conflict) ... ok
test_dispatch_resolution_between_checks_skips (__main__.CollectorPublication.test_dispatch_resolution_between_checks_skips) ... ok
test_dispatch_roles (__main__.CollectorPublication.test_dispatch_roles) ... ok
test_dispatch_stale_source_and_expired_lease (__main__.CollectorPublication.test_dispatch_stale_source_and_expired_lease) ... ok
test_dispatch_then_publication_invalidates_pre_side_effect: observed Lock wait
test_dispatch_then_publication_invalidates_pre_side_effect (__main__.CollectorPublication.test_dispatch_then_publication_invalidates_pre_side_effect) ... ok
test_distinct_request_stale_writer_rejected: observed contender Lock wait
test_distinct_request_stale_writer_rejected (__main__.CollectorPublication.test_distinct_request_stale_writer_rejected) ... ok
test_identical_request_replays_once: observed contender Lock wait
test_identical_request_replays_once (__main__.CollectorPublication.test_identical_request_replays_once) ... ok
test_initial_insert_is_audited_and_private_card_text_denied (__main__.CollectorPublication.test_initial_insert_is_audited_and_private_card_text_denied) ... ok
DENIED: six privilege bypasses and promotion from nonadmin login
test_nonadmin_login_cannot_bypass_observation_guard (__main__.CollectorPublication.test_nonadmin_login_cannot_bypass_observation_guard) ... ok
test_other_collector_request_collision_rolls_back_without_receipt_disclosure (__main__.CollectorPublication.test_other_collector_request_collision_rolls_back_without_receipt_disclosure) ... ok
test_owner_assertion_cannot_become_authoritative_reservation (__main__.CollectorPublication.test_owner_assertion_cannot_become_authoritative_reservation) ... ok
test_owner_republication_downgrades_previous_source_observation (__main__.CollectorPublication.test_owner_republication_downgrades_previous_source_observation) ... ok
test_publication_audit_failure_atomic_rollback_and_retry (__main__.CollectorPublication.test_publication_audit_failure_atomic_rollback_and_retry) ... ok
test_publication_competing_first_publishers: observed Lock wait
test_publication_competing_first_publishers (__main__.CollectorPublication.test_publication_competing_first_publishers) ... ok
test_publication_create_update_replay_conflict (__main__.CollectorPublication.test_publication_create_update_replay_conflict) ... ok
test_publication_rejects_stale_resolved_identity_and_time (__main__.CollectorPublication.test_publication_rejects_stale_resolved_identity_and_time) ... ok
test_publication_roles (__main__.CollectorPublication.test_publication_roles) ... ok
test_publication_then_dispatch_waits_and_rechecks: observed Lock wait
test_publication_then_dispatch_waits_and_rechecks (__main__.CollectorPublication.test_publication_then_dispatch_waits_and_rechecks) ... ok
test_request_reuse_across_cards_conflicts: observed contender Lock wait
test_request_reuse_across_cards_conflicts (__main__.CollectorPublication.test_request_reuse_across_cards_conflicts) ... ok
test_rollback_releases_request_without_phantom_receipt: observed contender Lock wait
test_rollback_releases_request_without_phantom_receipt (__main__.CollectorPublication.test_rollback_releases_request_without_phantom_receipt) ... ok
DENIED and rolled back: insert
DENIED and rolled back: promote
DENIED and rolled back: refresh
test_routine_observation_writes_denied_atomically (__main__.CollectorPublication.test_routine_observation_writes_denied_atomically) ... ok
test_same_request_changed_payload_conflicts: observed contender Lock wait
test_same_request_changed_payload_conflicts (__main__.CollectorPublication.test_same_request_changed_payload_conflicts) ... ok
test_trusted_dml_cannot_delete_and_rebind_canonical_intake (__main__.CollectorPublication.test_trusted_dml_cannot_delete_and_rebind_canonical_intake) ... ok
test_trusted_dml_cannot_rebind_issue_despite_bypassing_publisher (__main__.CollectorPublication.test_trusted_dml_cannot_rebind_issue_despite_bypassing_publisher) ... ok

----------------------------------------------------------------------
Ran 42 tests in 8.093s

OK
```
