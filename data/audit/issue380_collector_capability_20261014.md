# Issue 380 R30: restricted collector capability and automatic audit draft

2026-10-14T05:30Z. PR_OPEN / BUILT only. Baseline 3ee593612ab7034150a8cc0508693b7a82374dd5. Reuses draft PR #381; all six issue acceptance criteria remain open.

## Implementation and evidence

Added isolated-only SQL draft data/audit/issue380_collector_capability_draft.sql and tests/reconciliation/board_collector_capability.py. No existing draft was changed. Applying this draft requires a separately provisioned non-login, non-superuser, non-BYPASSRLS capability role with no inherited memberships. It assigns no membership, password, login, HTTP/JWT mapping or production configuration. Tests separately provision a temporary authenticated login with only collector capability membership.

The collector can read only card ID/version/resolution state and intake, touch updated_at (the existing trigger bumps version), and insert/update intake. Explicit RLS policies and SECURITY INVOKER functions retain authorization. It cannot resolve a card, delete intake, rewrite/delete events, assume service_role, bypass triggers, or read card title. The existing routine quarantine still denies service_role initial observation INSERT, promotion and stale refresh. A separately connected routine login cannot assume collector capability.

An AFTER trigger records every collector intake transition automatically, after the existing version bump trigger. Audit includes authenticated session_user (not supplied text), full prior/new intake, actual resulting version and timestamp. Two transitions in one transaction retain versions 3 and 4 and matching snapshot continuity. Initial INSERT retains null prior and version 2. A deliberate audit failure rolls back intake and version. Actor-spoof insertion fails the RLS check. All dispatch responses remain can_execute=false.

This is a capability/audit foundation, NOT an authenticated authoritative source collector, approved publication protocol or deployment-ready migration. Administrative owner exemption remains trusted. The collector itself is a trusted source: it can insert extra events under its own actor and fabricate source assertions if compromised; automatic auditing does not prove source truth. Events are append-only to routine roles, not tamperproof against database administrators. Existing owner assertions remain separately audited in activity. Source reference privacy/retention, data minimization, role and schema effective privileges, PUBLIC grants, function reachability and production memberships require review. The draft role guard checks role attributes and memberships, not absence of all pre-existing direct grants; use a clean reviewed capability role.

## Remaining gates / exact next engineering work

Implement a typed collector publisher with expected card version, idempotent request serialization/replay, explicit commit acknowledgement, and the established request/card advisory lock then intake-before-card lock protocol. Raw collector DML in this draft is NOT that protocol: it lacks expected-version checks and first-publication serialization; do not wire it to a production caller. Preserve these audit/denial tests and add collector-versus-owner/dispatcher contention and stale/replay tests. Then bind a narrow authoritative reader to canonical card/issue/source identity; authenticated connection alone is not source attestation. No arbitrary issue prose or third-party comments may authorize publication.

Actual production effective-privilege proof, installed no-launch consumer, external atomic side-effect fence/race proof, owner private evidence/history/counts/reopen and browser acceptance remain unfinished. No credential/account blocker is asserted. No Brian action required for continued backend engineering. #371 remains primary; #372 untouched/draft. Queue titles scanned; existing assignments preserved, no independent safe quick win selected from titles alone.

This retains native canonical card identity/history and adds no Enrollware dependency. Mature database capability separation and atomic audit are used to prevent the proven routine-writer forgery paths without inventing another board truth.

## Local validation and limitations

PostgreSQL 16.4; psycopg 3.2.10; libpq 160009. Existing dedicated portable local cluster; explicit IPv4 loopback port 55480 and empty database guard retained. Final database issue380_test_r30_proof. Test-only local trust authentication is not production authentication proof. Temporary collector/routine login roles removed; non-login capability and disposable fixtures retained locally. No production advisors/database accessed. Supabase skill security checklist reviewed; current changelog fetched. Upcoming HTTP TLS cipher retirement does not affect this loopback PostgreSQL test. PostgreSQL privilege reference: https://www.postgresql.org/docs/16/sql-grant.html .

Initial startup used default port 5432 and failed the explicit 55480 connection; corrected by restarting the same local test cluster on explicit IPv4/55480. Portable bundle has no createdb executable; database created via existing psycopg. Initial negative role test used an administrative session and was corrected to a separately authenticated non-superuser routine login. No failed run is counted as proof. Smart shutdown waited on connections; fast shutdown used for this dedicated test server.

Commands:
```powershell
$env:ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 user=issue380_local dbname=issue380_test_r30_proof'
& E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_collector_capability.py
python -c "import ast,pathlib; ast.parse(pathlib.Path('tests/reconciliation/board_collector_capability.py').read_text()); print('AST PASS')"
git diff --check
```
Final output follows. SQL parsed and executed by real PostgreSQL. No API/JavaScript change; no additional Node suite run. Windows case-collision files docs/Earl/index.html and docs/Jackson/index.html excluded from staging; original dirty checkout preserved. No generators, production writes, migration, installed runtime/state changes, merge or deployment.

```text
PostgreSQL: PostgreSQL 16.4, compiled by Visual C++ build 1940, 64-bit
psycopg: 3.2.10 libpq: 160009
test_authenticated_collector_write_is_audited_per_transition (__main__.CollectorCapability.test_authenticated_collector_write_is_audited_per_transition) ... ok
test_capability_cannot_resolve_delete_rewrite_audit_or_escalate (__main__.CollectorCapability.test_capability_cannot_resolve_delete_rewrite_audit_or_escalate) ... ok
test_collector_audit_failure_rolls_back_observation_and_version (__main__.CollectorCapability.test_collector_audit_failure_rolls_back_observation_and_version) ... ok
test_dispatch_audit_failure_rolls_back_reservation (__main__.CollectorCapability.test_dispatch_audit_failure_rolls_back_reservation) ... ok
test_dispatch_canonical_gates (__main__.CollectorCapability.test_dispatch_canonical_gates) ... ok
dispatch competing reservations: observed Lock wait
test_dispatch_competing_reservations_lock (__main__.CollectorCapability.test_dispatch_competing_reservations_lock) ... ok
test_dispatch_intake_change_invalidates_reservation (__main__.CollectorCapability.test_dispatch_intake_change_invalidates_reservation) ... ok
test_dispatch_intake_identity_cannot_move (__main__.CollectorCapability.test_dispatch_intake_identity_cannot_move) ... ok
test_dispatch_intake_writer_first_no_deadlock: observed Lock wait
test_dispatch_intake_writer_first_no_deadlock (__main__.CollectorCapability.test_dispatch_intake_writer_first_no_deadlock) ... ok
test_dispatch_reader_first_intake_writer_waits: observed Lock wait
test_dispatch_reader_first_intake_writer_waits (__main__.CollectorCapability.test_dispatch_reader_first_intake_writer_waits) ... ok
test_dispatch_reservation_replay_and_conflict (__main__.CollectorCapability.test_dispatch_reservation_replay_and_conflict) ... ok
test_dispatch_resolution_between_checks_skips (__main__.CollectorCapability.test_dispatch_resolution_between_checks_skips) ... ok
test_dispatch_roles (__main__.CollectorCapability.test_dispatch_roles) ... ok
test_dispatch_stale_source_and_expired_lease (__main__.CollectorCapability.test_dispatch_stale_source_and_expired_lease) ... ok
test_dispatch_then_publication_invalidates_pre_side_effect: observed Lock wait
test_dispatch_then_publication_invalidates_pre_side_effect (__main__.CollectorCapability.test_dispatch_then_publication_invalidates_pre_side_effect) ... ok
test_distinct_request_stale_writer_rejected: observed contender Lock wait
test_distinct_request_stale_writer_rejected (__main__.CollectorCapability.test_distinct_request_stale_writer_rejected) ... ok
test_identical_request_replays_once: observed contender Lock wait
test_identical_request_replays_once (__main__.CollectorCapability.test_identical_request_replays_once) ... ok
test_initial_insert_is_audited_and_private_card_text_denied (__main__.CollectorCapability.test_initial_insert_is_audited_and_private_card_text_denied) ... ok
DENIED: six privilege bypasses and promotion from nonadmin login
test_nonadmin_login_cannot_bypass_observation_guard (__main__.CollectorCapability.test_nonadmin_login_cannot_bypass_observation_guard) ... ok
test_owner_assertion_cannot_become_authoritative_reservation (__main__.CollectorCapability.test_owner_assertion_cannot_become_authoritative_reservation) ... ok
test_owner_republication_downgrades_previous_source_observation (__main__.CollectorCapability.test_owner_republication_downgrades_previous_source_observation) ... ok
test_publication_audit_failure_atomic_rollback_and_retry (__main__.CollectorCapability.test_publication_audit_failure_atomic_rollback_and_retry) ... ok
test_publication_competing_first_publishers: observed Lock wait
test_publication_competing_first_publishers (__main__.CollectorCapability.test_publication_competing_first_publishers) ... ok
test_publication_create_update_replay_conflict (__main__.CollectorCapability.test_publication_create_update_replay_conflict) ... ok
test_publication_rejects_stale_resolved_identity_and_time (__main__.CollectorCapability.test_publication_rejects_stale_resolved_identity_and_time) ... ok
test_publication_roles (__main__.CollectorCapability.test_publication_roles) ... ok
test_publication_then_dispatch_waits_and_rechecks: observed Lock wait
test_publication_then_dispatch_waits_and_rechecks (__main__.CollectorCapability.test_publication_then_dispatch_waits_and_rechecks) ... ok
test_request_reuse_across_cards_conflicts: observed contender Lock wait
test_request_reuse_across_cards_conflicts (__main__.CollectorCapability.test_request_reuse_across_cards_conflicts) ... ok
test_rollback_releases_request_without_phantom_receipt: observed contender Lock wait
test_rollback_releases_request_without_phantom_receipt (__main__.CollectorCapability.test_rollback_releases_request_without_phantom_receipt) ... ok
DENIED and rolled back: insert
DENIED and rolled back: promote
DENIED and rolled back: refresh
test_routine_observation_writes_denied_atomically (__main__.CollectorCapability.test_routine_observation_writes_denied_atomically) ... ok
test_same_request_changed_payload_conflicts: observed contender Lock wait
test_same_request_changed_payload_conflicts (__main__.CollectorCapability.test_same_request_changed_payload_conflicts) ... ok
test_trusted_dml_cannot_delete_and_rebind_canonical_intake (__main__.CollectorCapability.test_trusted_dml_cannot_delete_and_rebind_canonical_intake) ... ok
test_trusted_dml_cannot_rebind_issue_despite_bypassing_publisher (__main__.CollectorCapability.test_trusted_dml_cannot_rebind_issue_despite_bypassing_publisher) ... ok

----------------------------------------------------------------------
Ran 33 tests in 5.911s

OK
AST PASS
server stopped
```

Operational proof contract: expected useful outcome is skip resolved/blocked/already-corrected work before launch/mutation. Production end-to-end proof: none. Draft five-minute freshness and sixty-second reservations remain unapproved policy. Missing/stale evidence, version mismatch, uncertain commit or privilege bypass must fail closed. Installed observer, observer health, cadence, recovery and escalation remain unproven engineering work; Brian is not the routine monitoring layer. Preserve request/audit evidence when investigating. No HEALTHY claim.
