# Issue 380 R24: owner assertion provenance boundary

State: BUILT / validated locally only. PR #381 remains draft, unmerged and undeployed. All six acceptance criteria remain open.

## Finding and repair
The owner publication API correctly labelled acknowledgements and activity as assertions, but canonical intake lacked that distinction. Dispatch could reserve an owner-asserted action_required/worker_safe declaration as if an authoritative source had been inspected. All existing responses remained can_execute=false, so this was a reservation/provenance defect, not demonstrated execution.

Added canonical provenance with fail-closed owner_assertion default. Dispatch requires authoritative_observation before reservation. The owner publisher inserts assertions and explicitly downgrades prior observations on update. Client provenance is rejected. Synthetic privileged test fixtures explicitly declare observation provenance; these are not real source verification. Blocked and recorded-resolution skip behavior remains ahead of this gate. Versions still invalidate prior reservations.

## Security review limits
RLS enabled; anon/authenticated have no table/RPC grants; invoker RPCs use empty search_path; no new grants or public data. service_role remains trusted and has direct DML: it can forge observation provenance, bypass publication audit, or violate lock ordering. The new field is NOT a cryptographic attestation or trusted-role security boundary. Before rollout, narrow writes through a reviewed authoritative collector with source-specific evidence, identity binding, atomic audit and concurrency protocol. A collector must never derive verified state from arbitrary issue comments or this owner assertion. Worker-safe opt-in must be independently reviewed. No collector, installed consumer, external side-effect fence, UI, private evidence upload or live proof delivered here.

Supabase skill applied. Current changelog fetched (latest TLS cipher HTTP change does not affect these isolated SQL changes); RLS guidance reviewed: https://supabase.com/docs/guides/database/postgres/row-level-security . No production advisor run because drafts remain outside migrations and no production changes authorized.

## Validation
Dedicated existing local test cluster, PostgreSQL 16.4 / psycopg 3.2.10 / libpq 160009. Explicit empty database issue380_test_r24, loopback port 55480. Test server started only for proof and stopped afterwards. Fixtures retained locally outside repo. Initial test invocation found a quoting syntax error in the new fixture; corrected before execution. Final 25/25 PostgreSQL cases pass with 11 observed Lock waits, including two new provenance regressions. Node backend/auth suite 83/83 passes. Python AST and git diff --check pass. No negative-control run claimed.

Commands:
- ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 user=issue380_local dbname=issue380_test_r24' E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_intake_publication.py
- node --test tests/production_intake_publication.test.mjs tests/production_dispatch_decision.test.mjs tests/live_dispatch_check.test.mjs tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/admin_auth.test.mjs

Full PostgreSQL output:
```
PostgreSQL: PostgreSQL 16.4, compiled by Visual C++ build 1940, 64-bit
psycopg: 3.2.10 libpq: 160009
test_dispatch_audit_failure_rolls_back_reservation (__main__.IntakePublication.test_dispatch_audit_failure_rolls_back_reservation) ... ok
test_dispatch_canonical_gates (__main__.IntakePublication.test_dispatch_canonical_gates) ... ok
dispatch competing reservations: observed Lock wait
test_dispatch_competing_reservations_lock (__main__.IntakePublication.test_dispatch_competing_reservations_lock) ... ok
test_dispatch_intake_change_invalidates_reservation (__main__.IntakePublication.test_dispatch_intake_change_invalidates_reservation) ... ok
test_dispatch_intake_identity_cannot_move (__main__.IntakePublication.test_dispatch_intake_identity_cannot_move) ... ok
test_dispatch_intake_writer_first_no_deadlock: observed Lock wait
test_dispatch_intake_writer_first_no_deadlock (__main__.IntakePublication.test_dispatch_intake_writer_first_no_deadlock) ... ok
test_dispatch_reader_first_intake_writer_waits: observed Lock wait
test_dispatch_reader_first_intake_writer_waits (__main__.IntakePublication.test_dispatch_reader_first_intake_writer_waits) ... ok
test_dispatch_reservation_replay_and_conflict (__main__.IntakePublication.test_dispatch_reservation_replay_and_conflict) ... ok
test_dispatch_resolution_between_checks_skips (__main__.IntakePublication.test_dispatch_resolution_between_checks_skips) ... ok
test_dispatch_roles (__main__.IntakePublication.test_dispatch_roles) ... ok
test_dispatch_stale_source_and_expired_lease (__main__.IntakePublication.test_dispatch_stale_source_and_expired_lease) ... ok
test_dispatch_then_publication_invalidates_pre_side_effect: observed Lock wait
test_dispatch_then_publication_invalidates_pre_side_effect (__main__.IntakePublication.test_dispatch_then_publication_invalidates_pre_side_effect) ... ok
test_distinct_request_stale_writer_rejected: observed contender Lock wait
test_distinct_request_stale_writer_rejected (__main__.IntakePublication.test_distinct_request_stale_writer_rejected) ... ok
test_identical_request_replays_once: observed contender Lock wait
test_identical_request_replays_once (__main__.IntakePublication.test_identical_request_replays_once) ... ok
test_owner_assertion_cannot_become_authoritative_reservation (__main__.IntakePublication.test_owner_assertion_cannot_become_authoritative_reservation) ... ok
test_owner_republication_downgrades_previous_source_observation (__main__.IntakePublication.test_owner_republication_downgrades_previous_source_observation) ... ok
test_publication_audit_failure_atomic_rollback_and_retry (__main__.IntakePublication.test_publication_audit_failure_atomic_rollback_and_retry) ... ok
test_publication_competing_first_publishers: observed Lock wait
test_publication_competing_first_publishers (__main__.IntakePublication.test_publication_competing_first_publishers) ... ok
test_publication_create_update_replay_conflict (__main__.IntakePublication.test_publication_create_update_replay_conflict) ... ok
test_publication_rejects_stale_resolved_identity_and_time (__main__.IntakePublication.test_publication_rejects_stale_resolved_identity_and_time) ... ok
test_publication_roles (__main__.IntakePublication.test_publication_roles) ... ok
test_publication_then_dispatch_waits_and_rechecks: observed Lock wait
test_publication_then_dispatch_waits_and_rechecks (__main__.IntakePublication.test_publication_then_dispatch_waits_and_rechecks) ... ok
test_request_reuse_across_cards_conflicts: observed contender Lock wait
test_request_reuse_across_cards_conflicts (__main__.IntakePublication.test_request_reuse_across_cards_conflicts) ... ok
test_rollback_releases_request_without_phantom_receipt: observed contender Lock wait
test_rollback_releases_request_without_phantom_receipt (__main__.IntakePublication.test_rollback_releases_request_without_phantom_receipt) ... ok
test_same_request_changed_payload_conflicts: observed contender Lock wait
test_same_request_changed_payload_conflicts (__main__.IntakePublication.test_same_request_changed_payload_conflicts) ... ok

----------------------------------------------------------------------
Ran 25 tests in 6.001s

OK
```

## Proof contract and continuation
Expected outcome: unchanged blocked/handled work skipped before launch or side effect. Cadence: each selection and pre-side-effect boundary, fresh source check within draft five-minute window. Last successful production end-to-end proof: none. Local component proof: this report, 2026-10-13T20:03:59.259153+00:00. Failure: assertion-only, absent/stale source/version, uncertain commit, resolved card or missing fence denies execution. Observer and observer health: no deployed observer for this draft; engineering tests only. Recovery: preserve request ID on uncertain commit, refresh canonical/source state, investigate conflicts before authorization. No Brian routine monitoring/account action assigned.

Next: reviewed authoritative collector and restricted publication privileges; installed no-launch consumer and atomic external fence/race proof; resolution/private evidence/history/counts and browser proof. These are unfinished engineering gates, not account blockers. Preserve #371 as primary and #372 draft. Reuse #381; separate review/authorization before migration/merge/deployment.

## Hygiene
Fresh shallow named codex/issue380-r24-20261013 checkout after existing corrupt remote ref prevented fetch; no ref cleanup. Original dirty checkout preserved. Fresh Windows case collision dirt docs/Earl/index.html and docs/Jackson/index.html excluded. No generators, production/runtime changes or ops/handoff/next_task.md writes.

Changed source/tests: data/audit/issue380_dispatch_transaction_draft.sql; data/audit/issue380_intake_publication_draft.sql; tests/reconciliation/board_dispatch_transaction.py; tests/reconciliation/board_intake_publication.py; tests/production_intake_publication.test.mjs. Primary report: data/audit/issue380_assertion_provenance_20261013.md.
