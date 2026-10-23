# Issue 380 R31: typed locked collector publisher

2026-10-14T07:04Z. PR_OPEN / BUILT only. Baseline d2ce80daa5e9dbace0653bac954613848192cd9e. Isolated branch codex/issue380-r31-20261014 updates existing draft PR #381. All six acceptance criteria remain open. No production writes, installed runtime changes, migration, merge or deployment.

## Findings and implementation

R30 deliberately provided capability DML without expected-version/idempotency/first-publication serialization. Added `data/audit/issue380_collector_publication_draft.sql`, applied only to a disposable local database after the existing resolution, dispatch, owner-publication and collector-capability drafts. `production_board_publish_observation` is SECURITY INVOKER, requires the collector role, and uses authenticated session_user as actor. No caller-supplied actor or JWT/GUC identity is trusted. Only minimal card columns are read. No new membership/login/password/endpoint is provisioned by SQL.

The publisher validates typed input, locks request (namespace 382), then card advisory key (3820), then intake row, then card row. This shares the owner publisher/dispatch lock protocol and serializes missing intake rows. It rejects stale versions, resolved cards, changed issue identity and stale/future checks. Historical identical requests replay without changing intake/version/audit; changed payload conflicts. Replay never asserts present eligibility. All results have can_execute=false. The separate actor-scoped RLS publication receipt records request and resulting version. Existing automatic observation trigger preserves prior/new snapshots, authenticated actor and version. Receipt failure rolls the observation, version and audit back together.

`tests/reconciliation/board_collector_publication.py` adds six tests to R30's inherited suite. The test helper returns committed=true only after connection.commit succeeds; SQL output is provisional and contains no committed field. This is a test boundary, NOT a production client/HTTP acknowledgement implementation.

## Local proof

39/39 tests pass on PostgreSQL 16.4 / psycopg 3.2.10 / libpq 160009. Seventeen observed Lock waits: eleven inherited and six new. New evidence covers same-request concurrent first publication/replay; distinct-request stale rejection; rollback/retry without duplicate audit; collector-first owner/dispatch contention; owner-first collector contention; typed rejection/identity/resolved/freshness; private routine-role denial; receipt update/delete denial; provisional visibility/rollback and injected receipt insertion failure. AST syntax and git diff --check pass. SQL was parsed/executed by real PostgreSQL. No API/JS files changed; Node suites not rerun. No rendered public artifact changed or generator run.

Exact commands:

```powershell
& E:/GitHub/issue380-pg-portable/server/bin/pg_ctl.exe -D E:/GitHub/issue380-pg-portable/cluster-r16 -l E:/GitHub/issue380-pg-portable/r31-server.log -o '-h 127.0.0.1 -p 55480' -w start
$env:ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 user=issue380_local dbname=issue380_test_r31'
& E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_collector_publication.py
python -c "import ast,pathlib; ast.parse(pathlib.Path('tests/reconciliation/board_collector_publication.py').read_text()); print('AST PASS')"
git diff --check
```

The existing empty-database/explicit-loopback guard ran. Database created through psycopg against the dedicated local cluster. Test login roles removed by teardown. Disposable fixtures retained locally for review. Original checkout dirt untouched; new worktree's Windows case-collision changes to docs/Earl/index.html and docs/Jackson/index.html excluded from staging. No unrelated failure observed in the executed suite. Initial combined shell write/start command was rejected by tool policy before execution; retried as a reviewable apply_patch and separate server start, both succeeded. No approval or account action needed.

Supabase skill security checklist reviewed. Current changelog fetched locally after web markdown renderer rejected its content type. Relevant September PostgreSQL minor-release note reviewed: this draft adds no ltree, btree_gist, encrypted PGP data or custom operators. Local 16.4 synthetic proof is not production-version/privilege/advisor proof. Reference: https://supabase.com/changelog/postgres-15-19-17-11-breaking-changes . SECURITY INVOKER reference: https://www.postgresql.org/docs/16/sql-createfunction.html .

## Limits and next work

This protocol does not revoke R30's raw collector DML or receipt INSERT capability. A compromised collector can fabricate assertions, raw observations or its own publication receipt; actor authentication/audit is not source attestation. Cross-login request collision fails via unique constraint/rollback rather than disclosing another actor's receipt. Administrative owner remains trusted. No claim that this is a secure exclusive write gateway. Review restricting DML to a private least-privilege function owner before production; do not solve it by granting a broad SECURITY DEFINER owned by postgres. Preserve existing routine-writer denial and authenticated transition audit tests.

Next: bind a narrow authoritative reader to approved canonical issue/card/source identity and a restricted audited write gateway; test cross-actor/cross-card request misuse and dispatcher-first/resolve-versus-collector races. No arbitrary issue prose or third-party comments may grant source/owner authority. Effective production roles/PUBLIC grants, source minimization/retention and publication policy windows need review. Five-minute freshness remains unapproved draft policy. Keep SQL outside migrations/unapplied and PR #381 draft. Installed no-launch consumer, external atomic side-effect fencing, owner private evidence/uploads, UI/history/count/reopen and browser acceptance remain unfinished. No credential blocker is asserted; no Brian/account action required for further backend engineering.

Queue scan found existing independent assignments; no narrowly authorized conflicting change selected. #371 stays primary; #372 remains draft/untouched. This increment uses canonical card lifecycle/history and mature transactional locking, adds no Enrollware dependency, and advances native operational integrity without claiming incumbent replacement.

Operational proof contract: expected outcome is skip handled/blocked/already-corrected work before launch/mutation. Production end-to-end success: none. Missing/stale observations, uncertain commit or version mismatch must fail closed. Installed observer/cadence, observer health, recovery and escalation remain unproven. Retain durable request/audit evidence and diagnose at the smallest failing boundary. Brian must not be the routine monitoring layer. Overall evidence BUILT, not CONNECTED/PROVEN/MONITORED/HEALTHY.

## Exact local test output

```text
PostgreSQL: PostgreSQL 16.4, compiled by Visual C++ build 1940, 64-bit
psycopg: 3.2.10 libpq: 160009
test_authenticated_collector_write_is_audited_per_transition (__main__.CollectorPublication.test_authenticated_collector_write_is_audited_per_transition) ... ok
test_capability_cannot_resolve_delete_rewrite_audit_or_escalate (__main__.CollectorPublication.test_capability_cannot_resolve_delete_rewrite_audit_or_escalate) ... ok
test_collector_audit_failure_rolls_back_observation_and_version (__main__.CollectorPublication.test_collector_audit_failure_rolls_back_observation_and_version) ... ok
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
Ran 39 tests in 7.873s

OK
```
