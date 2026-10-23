# Issue 380 R25: trusted intake write review

State: BUILT / PR_OPEN, validated locally. Draft PR #381 stays unmerged/undeployed. All six acceptance criteria remain open.

## Findings and targeted repair
Real PostgreSQL negative controls at baseline 53d93d84b6da9c1e20d0725fa575b25c3ff794fe proved:
1. After legitimate owner publication, service_role can UPDATE provenance to authoritative_observation and refresh source_ref/checked_at with no new activity event. Dispatch then creates a reservation. can_execute remains false. This is not source verification or demonstrated execution.
2. The publisher rejects issue_id changes, but direct service_role UPDATE bypassed that identity gate and committed a changed issue ID plus incremented card version.

Repaired finding 2 in the existing intake trigger: changing issue_id raises intake_issue_immutable. A real role regression verifies rejection and rollback of identity/version. Existing card-ID immutability is preserved. This does not prevent DELETE/reinsert by the trusted role; it closes UPDATE identity mutation only. No claim of protection from superusers, trigger disabling, forged audit inserts, or hostile shared service credentials.

Finding 1 remains an explicit rollout gate. A diagnostic negative control deliberately asserts the remaining forgery; a passing suite must NOT be read as proof of secure attestation. Replace that control with a denial test when restricted collector writes exist.

## Required collector/privilege protocol before rollout
- Owner gateway publishes owner assertions only. Arbitrary issue comments, source URLs, free text, or actor strings cannot attest source truth or worker-safe permission.
- Reviewed source-specific collector binds canonical card/issue identity, expected version, actual source identity/revision, observation time, outcome and private evidence reference. Authenticate the collector independently of assertions; treat unavailable or ambiguous sources as review.
- Separate caller authority from storage mutation authority. Revoke direct intake write privileges from routine callers only with a reviewed replacement RPC/role design and role tests. Current SECURITY INVOKER RPCs need these privileges: blindly revoking them breaks publication/dispatch. Do not solve this by granting broad SECURITY DEFINER access in public.
- Preserve request lock then per-card advisory lock then intake then card order; version/idempotency and immutable audit must commit atomically. Prove absent-row races, rollback/retry, provenance replay, source changes and owner resolution during inspection.
- Protect identity across DELETE/reinsert, audit/event forgery and all collector write paths; review effective role membership/default grants. RLS alone does not constrain service_role.
- Installed no-launch consumer and external pre-side-effect fence remain separate requirements. No backend reservation authorizes execution. Private evidence, history/count UI and browser proofs remain unfinished.

This is native board integrity work; no new Enrollware dependency or training-business workflow. Existing canonical card lifecycle/audit pattern retained.

## Validation and exact evidence
Local PostgreSQL 16.4, psycopg 3.2.10/libpq 160009. Empty guarded loopback databases issue380_test_r25 (negative controls) and issue380_test_r25_fixed (repair), port 55480. Existing dedicated portable cluster only; stopped after proof. No operational database accessed.
First startup omitted explicit port and used local 5432; test timed out at 55480 and createdb.exe was unavailable in portable bin. Stopped it, restarted explicitly on IPv4 loopback:55480, created empty databases using psycopg; no retries against operational targets.
Baseline: 27/27 including both reproduced bypasses. Final: 27/27 including UPDATE denial and remaining provenance negative control; 11 real Lock waits observed. Node backend/auth: 83/83. AST parse and git diff --check pass.

Commands:
```
ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 user=issue380_local dbname=issue380_test_r25_fixed' E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_intake_trust_boundary.py
node --test tests/production_intake_publication.test.mjs tests/production_dispatch_decision.test.mjs tests/live_dispatch_check.test.mjs tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/admin_auth.test.mjs
```

Final PostgreSQL output:
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
test_trusted_dml_cannot_rebind_issue_despite_bypassing_publisher (__main__.IntakeTrustBoundary.test_trusted_dml_cannot_rebind_issue_despite_bypassing_publisher) ... ok

----------------------------------------------------------------------
Ran 27 tests in 4.682s

OK

```

## Proof and hygiene
Expected outcome: skip blocked/handled work before selection and every side effect. No production end-to-end proof; no deployed observer/observer-health evidence. Draft source freshness window five minutes, reservation sixty seconds; policy still needs review. Failure includes absent/stale/forged source provenance, uncertain commit, resolution/version mismatch or missing external fence. Recovery: retain request IDs, refresh authenticated state, investigate before retry/authorization. No Brian routine monitoring or account action assigned.

Original dirty E:/GitHub/910cpr-class-landers untouched. Isolated named branch codex/issue380-r25-20261013 reuses #381. Windows case-collision docs/Earl/index.html and docs/Jackson/index.html excluded. Queue titles swept; no competing deep workstream started; #371/#372 and assignments preserved. No generators, runtime/state/task changes, production migration, merge/deploy or ops/handoff/next_task.md writes.

Supabase skill applied; changelog fetched locally after browser markdown content-type failure. Latest TLS cipher HTTP change does not affect local SQL. Security guidance reviewed: https://supabase.com/docs/guides/database/postgres/row-level-security . No production advisor run; SQL remains an unapplied review draft outside migrations.

Files changed: data/audit/issue380_dispatch_transaction_draft.sql; tests/reconciliation/board_intake_trust_boundary.py; this report data/audit/issue380_intake_trust_review_20261013.md; unique root receipt.
Next: review the UPDATE invariant and remaining provenance negative control; implement restricted authoritative collector protocol with denial/atomic concurrency tests, then installed consumer/fence and private evidence/UI. Engineering gates, not credential blockers. Keep #381 draft and preserve primary #371.
