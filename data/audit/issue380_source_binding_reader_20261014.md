# Issue 380 R35: canonical source binding reader

PR_OPEN / BUILT only. Baseline 4bc28f3056918b9fd4a69c9413f9ec4e12c61ef9. Isolated codex/issue380-r35-20261014; reuses draft PR #381. All six acceptance criteria remain open.

## Change

Added private SECURITY INVOKER source-binding reader after the existing gateway draft, outside migrations. It requires the restricted collector role and authenticated session membership, reads canonical card/version/resolution and existing intake issue identity in one statement snapshot, and constructs the fixed-repository issue URL from that identity. It does not accept a caller-supplied issue/version/ref, expose card text, trust arbitrary stored source URLs, create a first binding, publish an observation, or grant execution. Missing/invisible intake and unsupported JavaScript issue IDs require review; resolved cards skip. Read does not mutate version/audit. Routine API roles cannot invoke it. RLS remains enforced.

This is a SQL reader foundation, NOT an integrated authenticated DB-to-GitHub collector. Existing intake bootstrap can still encode an incorrect identity; database existence alone is not source attestation. The R34 GitHub lifecycle reader remains separate. Open/closed metadata must never become authoritative action_required/already_corrected evidence. The locked publisher remains responsible for rejecting stale versions after acquisition; a regression proves a read followed by publication-changing version cannot publish using the prior version.

## Local validation

Dedicated existing portable PostgreSQL 16.4 at 127.0.0.1:55480, psycopg 3.2.10/libpq 160009. Final empty disposable database issue380_test_r35_final. 47/47 real PostgreSQL tests pass (43 inherited gateway/publication/rollback/contention tests plus four reader tests). Twenty inherited lock waits. Python AST and git diff --check pass. No HTTP/public asset behavior changed; no generator or production advisors run.

Initial launch omitted the prior explicit port option and attempted absent createdb; corrected by restarting this dedicated cluster with -p 55480 -h 127.0.0.1 and creating database via existing psycopg. First suite had one fixture failure: max(issue_id)-based helper inherited deliberately oversized ID. Positive fixture now explicitly uses issue 380; final fresh database passes. Failed runs are not proof. No operational database accessed. Test log retained locally at E:/GitHub/issue380-pg-portable/r35-final-tests.txt.

Commands:
```powershell
$env:ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 user=issue380_local dbname=issue380_test_r35_final'
& E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_source_binding_reader.py
python -c "import ast,pathlib; ast.parse(pathlib.Path('tests/reconciliation/board_source_binding_reader.py').read_text()); print('AST PASS')"
git diff --check
```

Supabase skill/security checklist read; current changelog fetched locally (r35-changelog.md). Recent minor-upgrade extension/operator changes do not alter this local 16.4 reader. Official function guidance reviewed: https://supabase.com/docs/guides/database/functions . Reader is invoker, uses empty search_path/schema-qualified tables, private schema, explicit execute revocations, no JWT/custom-GUC authority, and a real RLS invisibility regression. No credentials added or exposed.

## Remaining gates and proof contract

Next: reviewed authenticated DB client bridge using this existing binding, lifecycle-vs-operational observation type/attestation and exclusive publisher enforcement; first-binding authority, production effective privileges, installed no-launch consumer/external atomic side-effect fence; private owner evidence/UI/history/counts/reopen/browser proof. These are engineering gates, not Brian/account blockers. SQL stays unapplied and #381 draft; no merge or deployment authorized. No new paid integration or Enrollware dependency. Canonical identity and immutable history remain the design center, following the established audit/version pattern.

Expected outcome: skip resolved/blocked/already-corrected cards before launch/mutation. Last production end-to-end proof: none. No cadence/observer/observer-health proof established here. Missing/stale/unsupported binding or source ambiguity must fail closed. Recovery: reacquire authenticated binding and underlying state, then publish with expected-version and committed receipt; never use cached lifecycle metadata as authority. Escalate genuine account/business decisions only; Brian is not the routine monitor. Overall BUILT, not CONNECTED/PROVEN/MONITORED/HEALTHY.

Preserved original dirty checkout, all assignments, #371 primary and #372 draft. Local Windows case-collision dirt docs/Earl/index.html and docs/Jackson/index.html excluded. Queue titles swept; no independent unassigned safe backend work selected over existing streams. No installed runtime/state/task changes, production writes, migration, generator, merge, deployment or destructive cleanup.

Changed: data/audit/issue380_source_binding_reader_draft.sql; tests/reconciliation/board_source_binding_reader.py; this report; unique root R35 receipt. Existing historical unrelated failures not rerun or claimed fixed.

## Exact final database test output

```text
PostgreSQL: PostgreSQL 16.4, compiled by Visual C++ build 1940, 64-bit
psycopg: 3.2.10 libpq: 160009
test_authenticated_collector_write_is_audited_per_transition (__main__.SourceBindingReader.test_authenticated_collector_write_is_audited_per_transition) ... ok
test_binding_is_not_lease_publisher_rejects_new_version (__main__.SourceBindingReader.test_binding_is_not_lease_publisher_rejects_new_version) ... ok
test_capability_cannot_resolve_delete_rewrite_audit_or_escalate (__main__.SourceBindingReader.test_capability_cannot_resolve_delete_rewrite_audit_or_escalate) ... ok
test_collector_and_manual_resolution_serialize_both_orders: observed Lock wait
test_collector_and_manual_resolution_serialize_both_orders: observed Lock wait
test_collector_and_manual_resolution_serialize_both_orders (__main__.SourceBindingReader.test_collector_and_manual_resolution_serialize_both_orders) ... ok
test_collector_audit_failure_rolls_back_observation_and_version (__main__.SourceBindingReader.test_collector_audit_failure_rolls_back_observation_and_version) ... ok
test_collector_conflicting_request_contention_preserves_first_receipt: observed Lock wait
test_collector_conflicting_request_contention_preserves_first_receipt (__main__.SourceBindingReader.test_collector_conflicting_request_contention_preserves_first_receipt) ... ok
test_collector_first_publication_contention_replay_stale_and_rollback: observed Lock wait
test_collector_first_publication_contention_replay_stale_and_rollback: observed Lock wait
test_collector_first_publication_contention_replay_stale_and_rollback: observed Lock wait
test_collector_first_publication_contention_replay_stale_and_rollback (__main__.SourceBindingReader.test_collector_first_publication_contention_replay_stale_and_rollback) ... ok
test_collector_provisional_response_and_receipt_failure_roll_back (__main__.SourceBindingReader.test_collector_provisional_response_and_receipt_failure_roll_back) ... ok
test_collector_publication_replay_conflict_and_audit (__main__.SourceBindingReader.test_collector_publication_replay_conflict_and_audit) ... ok
test_collector_publisher_roles_and_receipt_immutability (__main__.SourceBindingReader.test_collector_publisher_roles_and_receipt_immutability) ... ok
test_collector_rejects_invalid_stale_resolved_identity_and_time (__main__.SourceBindingReader.test_collector_rejects_invalid_stale_resolved_identity_and_time) ... ok
test_collector_serializes_owner_and_dispatch: observed Lock wait
test_collector_serializes_owner_and_dispatch: observed Lock wait
test_collector_serializes_owner_and_dispatch: observed Lock wait
test_collector_serializes_owner_and_dispatch (__main__.SourceBindingReader.test_collector_serializes_owner_and_dispatch) ... ok
test_dispatch_audit_failure_rolls_back_reservation (__main__.SourceBindingReader.test_dispatch_audit_failure_rolls_back_reservation) ... ok
test_dispatch_canonical_gates (__main__.SourceBindingReader.test_dispatch_canonical_gates) ... ok
dispatch competing reservations: observed Lock wait
test_dispatch_competing_reservations_lock (__main__.SourceBindingReader.test_dispatch_competing_reservations_lock) ... ok
test_dispatch_intake_change_invalidates_reservation (__main__.SourceBindingReader.test_dispatch_intake_change_invalidates_reservation) ... ok
test_dispatch_intake_identity_cannot_move (__main__.SourceBindingReader.test_dispatch_intake_identity_cannot_move) ... ok
test_dispatch_intake_writer_first_no_deadlock: observed Lock wait
test_dispatch_intake_writer_first_no_deadlock (__main__.SourceBindingReader.test_dispatch_intake_writer_first_no_deadlock) ... ok
test_dispatch_reader_first_intake_writer_waits: observed Lock wait
test_dispatch_reader_first_intake_writer_waits (__main__.SourceBindingReader.test_dispatch_reader_first_intake_writer_waits) ... ok
test_dispatch_reservation_replay_and_conflict (__main__.SourceBindingReader.test_dispatch_reservation_replay_and_conflict) ... ok
test_dispatch_resolution_between_checks_skips (__main__.SourceBindingReader.test_dispatch_resolution_between_checks_skips) ... ok
test_dispatch_roles (__main__.SourceBindingReader.test_dispatch_roles) ... ok
test_dispatch_stale_source_and_expired_lease (__main__.SourceBindingReader.test_dispatch_stale_source_and_expired_lease) ... ok
test_dispatch_then_publication_invalidates_pre_side_effect: observed Lock wait
test_dispatch_then_publication_invalidates_pre_side_effect (__main__.SourceBindingReader.test_dispatch_then_publication_invalidates_pre_side_effect) ... ok
test_distinct_request_stale_writer_rejected: observed contender Lock wait
test_distinct_request_stale_writer_rejected (__main__.SourceBindingReader.test_distinct_request_stale_writer_rejected) ... ok
test_identical_request_replays_once: observed contender Lock wait
test_identical_request_replays_once (__main__.SourceBindingReader.test_identical_request_replays_once) ... ok
test_initial_insert_is_audited_and_private_card_text_denied (__main__.SourceBindingReader.test_initial_insert_is_audited_and_private_card_text_denied) ... ok
test_missing_resolved_and_unsupported_bindings_fail_closed (__main__.SourceBindingReader.test_missing_resolved_and_unsupported_bindings_fail_closed) ... ok
DENIED: six privilege bypasses and promotion from nonadmin login
test_nonadmin_login_cannot_bypass_observation_guard (__main__.SourceBindingReader.test_nonadmin_login_cannot_bypass_observation_guard) ... ok
test_other_collector_request_collision_rolls_back_without_receipt_disclosure (__main__.SourceBindingReader.test_other_collector_request_collision_rolls_back_without_receipt_disclosure) ... ok
test_owner_assertion_cannot_become_authoritative_reservation (__main__.SourceBindingReader.test_owner_assertion_cannot_become_authoritative_reservation) ... ok
test_owner_republication_downgrades_previous_source_observation (__main__.SourceBindingReader.test_owner_republication_downgrades_previous_source_observation) ... ok
test_publication_audit_failure_atomic_rollback_and_retry (__main__.SourceBindingReader.test_publication_audit_failure_atomic_rollback_and_retry) ... ok
test_publication_competing_first_publishers: observed Lock wait
test_publication_competing_first_publishers (__main__.SourceBindingReader.test_publication_competing_first_publishers) ... ok
test_publication_create_update_replay_conflict (__main__.SourceBindingReader.test_publication_create_update_replay_conflict) ... ok
test_publication_rejects_stale_resolved_identity_and_time (__main__.SourceBindingReader.test_publication_rejects_stale_resolved_identity_and_time) ... ok
test_publication_roles (__main__.SourceBindingReader.test_publication_roles) ... ok
test_publication_then_dispatch_waits_and_rechecks: observed Lock wait
test_publication_then_dispatch_waits_and_rechecks (__main__.SourceBindingReader.test_publication_then_dispatch_waits_and_rechecks) ... ok
test_raw_writes_and_executor_escalation_denied (__main__.SourceBindingReader.test_raw_writes_and_executor_escalation_denied) ... ok
test_reader_binds_identity_without_private_text_or_arbitrary_url (__main__.SourceBindingReader.test_reader_binds_identity_without_private_text_or_arbitrary_url) ... ok
test_reader_denies_routine_roles_and_preserves_rls (__main__.SourceBindingReader.test_reader_denies_routine_roles_and_preserves_rls) ... ok
test_request_reuse_across_cards_conflicts: observed contender Lock wait
test_request_reuse_across_cards_conflicts (__main__.SourceBindingReader.test_request_reuse_across_cards_conflicts) ... ok
test_rollback_releases_request_without_phantom_receipt: observed contender Lock wait
test_rollback_releases_request_without_phantom_receipt (__main__.SourceBindingReader.test_rollback_releases_request_without_phantom_receipt) ... ok
DENIED and rolled back: insert
DENIED and rolled back: promote
DENIED and rolled back: refresh
test_routine_observation_writes_denied_atomically (__main__.SourceBindingReader.test_routine_observation_writes_denied_atomically) ... ok
test_same_request_changed_payload_conflicts: observed contender Lock wait
test_same_request_changed_payload_conflicts (__main__.SourceBindingReader.test_same_request_changed_payload_conflicts) ... ok
test_trusted_dml_cannot_delete_and_rebind_canonical_intake (__main__.SourceBindingReader.test_trusted_dml_cannot_delete_and_rebind_canonical_intake) ... ok
test_trusted_dml_cannot_rebind_issue_despite_bypassing_publisher (__main__.SourceBindingReader.test_trusted_dml_cannot_rebind_issue_despite_bypassing_publisher) ... ok

----------------------------------------------------------------------
Ran 47 tests in 10.281s

OK
```
