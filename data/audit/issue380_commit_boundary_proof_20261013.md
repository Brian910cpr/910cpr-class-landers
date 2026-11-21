# Issue 380 R18 — deferred transaction boundary proof

2026-10-13. IN_PROGRESS / BUILT overall; validated locally. Existing draft PR #381 remains unmerged and undeployed. This increment adds four real PostgreSQL regressions to `tests/reconciliation/board_resolution_security.py`. It changes no SQL or production behavior. No authenticated adapter or installed launcher integration was implemented in this increment. All six acceptance criteria remain open.

## Findings

- A resolution RPC may return version 2 while another connection still sees committed unresolved/version 1 and no resolution event. Rollback discards the provisional response; retry of the same request ID executes once, rather than replaying a phantom success.
- Resolve then justified reopen in one transaction commits both event/activity records with versions 2 and 3.
- Removing just the first activity in that transaction causes COMMIT to reject and roll back both transitions, both events and remaining activity, even though final state equals original unresolved. The deferred trigger validates each transition, not merely final state.
- Forcing pending constraint checks with SET CONSTRAINTS rejects an unaudited direct transition and rollback preserves version 1.

These tests support the existing deferred invariant; no new bypass was found in these cases. They do not prove independent actor authenticity, immutable legacy activity, remote fencing, HTTP authorization or an actual owner-to-worker end-to-end workflow. Idempotency replay remains historical output, never current execution permission. Adapters must wait for transaction commit before publishing success or starting a side effect.

## Reproduction

Dedicated retained local infrastructure from R16/R17; synthetic fixtures only. Existing target validation requires explicit IPv4 loopback, issue380_test_* database and empty database. No existing fixtures removed. New retained database: issue380_test_r18. Server stopped after tests.

```powershell
& E:/GitHub/issue380-pg-portable/server/bin/pg_ctl.exe -D E:/GitHub/issue380-pg-portable/cluster-r16 -l E:/GitHub/issue380-pg-portable/r18-server.log -o '-h 127.0.0.1 -p 55480' -w start
& E:/GitHub/issue380-pg-env/Scripts/python.exe -c "import psycopg; c=psycopg.connect('host=127.0.0.1 port=55480 user=issue380_local dbname=postgres',autocommit=True); c.execute('create database issue380_test_r18'); c.close()"
$env:ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 user=issue380_local dbname=issue380_test_r18'
& E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_resolution_security.py
& E:/GitHub/issue380-pg-portable/server/bin/pg_ctl.exe -D E:/GitHub/issue380-pg-portable/cluster-r16 -m fast -w stop
```

Full outcome, unittest class qualifiers and stdout/stderr interleaving normalized:

```text
PostgreSQL: PostgreSQL 16.4, compiled by Visual C++ build 1940, 64-bit
psycopg: 3.2.10 libpq: 160009
test_reject_operational_or_indirect_targets ... ok
test_distinct_request_stale_writer_rejected: observed contender Lock wait ... ok
test_forcing_deferred_checks_rejects_unaudited_transition ... ok
test_functions_are_invoker_with_fixed_search_path ... ok
test_identical_request_replays_once: observed contender Lock wait ... ok
test_missing_activity_rolls_back_card_and_event_at_commit ... ok
test_missing_intermediate_audit_rejects_even_when_final_state_is_original ... ok
test_multiple_transitions_in_one_commit_preserve_each_audit ... ok
test_ordinary_edits_and_justified_rpc_reopen_remain_supported ... ok
test_provisional_rpc_response_is_not_visible_and_rollback_is_not_proof ... ok
test_request_reuse_across_cards_conflicts: observed contender Lock wait ... ok
test_rls_still_denies_rows_if_untrusted_select_accidentally_granted ... ok
test_rollback_releases_request_without_phantom_receipt: observed contender Lock wait ... ok
test_same_request_changed_payload_conflicts: observed contender Lock wait ... ok
test_service_direct_resolution_and_reopen_require_audit ... ok
test_service_event_history_cannot_update_delete_truncate ... ok
test_untrusted_roles_cannot_read_write_or_invoke ... ok
Ran 17 tests in 2.578s
OK
server stopped
Python AST syntax: passed
git diff --check: passed (no output)
```

No failures. JS suites not repeated: JS and SQL unchanged; prior evidence remains historical. Source reviewed: `data/audit/issue380_resolution_transaction_draft.sql`, prior R17 report and existing harness. SQL stays outside migrations. No remote advisors run; no production schema proposed/applied in this increment.

Documentation checked: [PostgreSQL 16 SET CONSTRAINTS](https://www.postgresql.org/docs/16/sql-set-constraints.html). Supabase changelog fetched using verified Windows HTTPS after web tool rejected markdown content type. Upcoming HTTP TLS cipher changes and PG15/17 extension upgrade notices do not affect this isolated PG16 loopback test. Supabase security checklist reviewed; no new auth/RLS/storage/functions/grants/dependencies introduced.

## Scope and next action

Original dirty E:/GitHub/910cpr-class-landers preserved. Isolated codex/issue380-r18-20261013 based on #381 head 6eee63bb598d83aaa31b767725c05ed0e4bf086e. Windows case-collision changes in docs/Earl/index.html and docs/Jackson/index.html excluded. No generator, runtime install, production write, migration, merge or deployment. #371 remains primary; #372 untouched. Open issue queue and #266 dependency scanned; existing assignments not displaced.

No credential/account blocker encountered; authenticated atomic claim-or-skip/audit adapter and installed pre-side-effect fencing remain unimplemented engineering work, not owner blockers. Next: implement reviewed server-authenticated adapter with versioned/idempotent atomic claim/skip and explicit commit acknowledgement, then prove owner-resolution races before execution and before mutation. #266 permits Production Board dispatch only behind explicit worker-safe opt-in; issue prose is not executable authorization. Private evidence/upload failure handling, UI/history/counts and browser proof remain unfinished.

Expected operational outcome: canonical owner resolution yields durable skip before worker side effects. Last real end-to-end proof: none. Cadence: every claim and side effect. Failure: execution after resolution/stale version or success without durable audit. Observer/observer health not integrated; no MONITORED/HEALTHY claim. Recovery: hold rollout, retain local evidence, complete atomic adapter/runtime proof; separate rollout authorization remains required. No Brian/account action needed for this increment. Existing native card lifecycle/provenance design introduces no Enrollware dependency; incumbent rationale remains in issue380_resolution_preflight_20261011.md.
