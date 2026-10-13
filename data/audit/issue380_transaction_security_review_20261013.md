# Issue 380 R17 — local transaction security review

2026-10-13T05:06Z. Existing draft PR #381. Overall evidence: BUILT; all six acceptance criteria remain open. This is the requested security review prerequisite, not another advisory selector change and not approval to apply the SQL.

## Findings

Confirmed against PostgreSQL 16.4 using actual SET ROLE queries, not source-string assertions:

1. anon/authenticated cannot invoke the resolution RPC, read cards/events, update canonical resolution, insert events, delete events, or truncate events. Rejected statements leave the test card at version 1.
2. service_role cannot UPDATE, DELETE or TRUNCATE resolution events; an RPC-created event remains intact.
3. RLS denies all event rows even with a synthetic SELECT misgrant to anon/authenticated. Those grants are rolled back.
4. Both functions are SECURITY INVOKER with an empty search_path.
5. **OPEN rollout gate:** service_role retains table-wide card UPDATE from `supabase/migrations/20260812161043_production_board.sql`. It can directly change resolution_state to handled_manually without a resolution event or activity. The version trigger overrides a forged row_version=900 to 2, but creates no provenance. This is a trusted backend bypass, not anonymous access or a demonstrated public exploit. `production-board/index.ts` currently strips unknown update fields through clean(); that protects this one HTTP route, not all privileged callers.

The existing SQL guarantees atomic audit only for callers using production_board_resolve. It does not enforce that every privileged resolution transition uses that RPC. service_role also has INSERT on resolution events and supplies p_actor: append-only privileges do not make actor/payload authenticity independently trustworthy. An authenticated proxy must derive actor from verified server auth and never trust a browser-supplied actor. No new credential/account blocker was found.

## Required next implementation

Before rollout, enforce the resolution/audit invariant at a reviewed database boundary (including direct UPDATE/INSERT paths), or explicitly restrict privileged writers through a reviewed least-privilege execution role. Do not merely add another application boolean or grant browser roles access. Preserve legacy ordinary card edits and their version increments. Test direct resolution/reopen bypass rejection and rollback, then repeat contention cases. Review role/default grants on the actual deployment before authorization. Keep SQL outside migrations until coordinated review.

Then complete the authenticated canonical claim-or-skip/audit adapter and real pre-side-effect fencing, with owner-resolution racing a worker and durable idempotent skip proof. The resolution RPC is not a worker lease. Private evidence, owner dialog/history/counts, upload/browser tests and all original acceptance remain unfinished. Do not replace these with more selector-only hardening.

## Reproducibility and exact evidence

Test file: `tests/reconciliation/board_resolution_security.py` reuses the existing contention harness's explicit IPv4-loopback, issue380_test_* name, effective target and empty-database checks. It inherits/repeats five two-session cases, adds five security tests, and includes the target guard (11 test methods total). The bypass case intentionally asserts the observed insecure outcome and prints OPEN SECURITY GATE. A green test suite therefore **does not mean security approval**. After the boundary is repaired, replace this reproducer with a rejection test. No operational DSN is consumed, no existing database is dropped, and fixtures remain for inspection.

Dedicated existing local infrastructure reused:
- E:/GitHub/issue380-pg-portable/server/bin
- E:/GitHub/issue380-pg-portable/cluster-r16 (retained prior evidence)
- E:/GitHub/issue380-pg-env/Scripts/python.exe
- new empty database issue380_test_r17, synthetic data only
- E:/GitHub/issue380-pg-portable/r17-server.log

Commands:
```powershell
& E:/GitHub/issue380-pg-portable/server/bin/pg_ctl.exe -D E:/GitHub/issue380-pg-portable/cluster-r16 -l E:/GitHub/issue380-pg-portable/r17-server.log -o '-h 127.0.0.1 -p 55480' -w start
& E:/GitHub/issue380-pg-env/Scripts/python.exe -c "import psycopg; c=psycopg.connect('host=127.0.0.1 port=55480 user=issue380_local dbname=postgres',autocommit=True); c.execute('create database issue380_test_r17'); c.close()"
$env:ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 user=issue380_local dbname=issue380_test_r17'
& E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_resolution_security.py
& E:/GitHub/issue380-pg-portable/server/bin/pg_ctl.exe -D E:/GitHub/issue380-pg-portable/cluster-r16 -m fast -w stop
```

Full successful output (stdout/stderr interleaving normalized):
```text
test_reject_operational_or_indirect_targets (board_resolution_contention.TargetSafety.test_reject_operational_or_indirect_targets) ... ok
PostgreSQL: PostgreSQL 16.4, compiled by Visual C++ build 1940, 64-bit
psycopg: 3.2.10 libpq: 160009
test_distinct_request_stale_writer_rejected: observed contender Lock wait
test_distinct_request_stale_writer_rejected (__main__.ResolutionSecurity.test_distinct_request_stale_writer_rejected) ... ok
test_functions_are_invoker_with_fixed_search_path (__main__.ResolutionSecurity.test_functions_are_invoker_with_fixed_search_path) ... ok
test_identical_request_replays_once: observed contender Lock wait
test_identical_request_replays_once (__main__.ResolutionSecurity.test_identical_request_replays_once) ... ok
OPEN SECURITY GATE: service_role direct card UPDATE resolves without event/activity; version trigger alone is not an audit boundary
test_open_blocker_service_direct_write_bypasses_resolution_audit (__main__.ResolutionSecurity.test_open_blocker_service_direct_write_bypasses_resolution_audit) ... ok
test_request_reuse_across_cards_conflicts: observed contender Lock wait
test_request_reuse_across_cards_conflicts (__main__.ResolutionSecurity.test_request_reuse_across_cards_conflicts) ... ok
test_rls_still_denies_rows_if_untrusted_select_accidentally_granted (__main__.ResolutionSecurity.test_rls_still_denies_rows_if_untrusted_select_accidentally_granted) ... ok
test_rollback_releases_request_without_phantom_receipt: observed contender Lock wait
test_rollback_releases_request_without_phantom_receipt (__main__.ResolutionSecurity.test_rollback_releases_request_without_phantom_receipt) ... ok
test_same_request_changed_payload_conflicts: observed contender Lock wait
test_same_request_changed_payload_conflicts (__main__.ResolutionSecurity.test_same_request_changed_payload_conflicts) ... ok
test_service_event_history_cannot_update_delete_truncate (__main__.ResolutionSecurity.test_service_event_history_cannot_update_delete_truncate) ... ok
test_untrusted_roles_cannot_read_write_or_invoke (__main__.ResolutionSecurity.test_untrusted_roles_cannot_read_write_or_invoke) ... ok
Ran 11 tests in 1.943s
OK
Python AST syntax: passed
git diff --check: passed (no output)
waiting for server to shut down........ done
server stopped
```

No failed test. Existing JS suite not repeated because JS/SQL unchanged. Prior tests are historical evidence. Supabase remote advisors not run: no production schema change or migration prepared; local catalog/role checks are not remote advisor approval. Supabase security checklist reviewed: no JWT user_metadata authorization, no browser secret, no view/storage/dependency changes; invoker/RLS/role behavior tested here. HTTP auth and installed runtime not exercised.

Current documentation reviewed: [Supabase roles](https://supabase.com/docs/guides/database/postgres/roles), [PostgreSQL 16 GRANT](https://www.postgresql.org/docs/16/sql-grant.html). Changelog fetched via Windows verified HTTPS after web tool rejected markdown content type; the upcoming TLS 1.2 cipher change does not affect isolated local SQL tests. No external service selected or provisioned.

## Operational scope and handoff

Only new test/report/receipt persisted in isolated codex/issue380-r17-20261013, based on #381 head 6cea75dc1d28b8f9569256ef79af01e7a6d2bb91. Windows case-collision dirt docs/Earl/index.html and docs/Jackson/index.html excluded. Original E:/GitHub/910cpr-class-landers checkout untouched. Queue and #266 dependency read; no existing assignment displaced, #371 stays primary and #372 untouched/draft. No generators, production write, migration, runtime install/state change, merge or deployment.

Design remains native canonical card lifecycle/provenance, with no new Enrollware dependency; mature-pattern rationale remains in data/audit/issue380_resolution_preflight_20261011.md. Success boundary: actual owner resolution/evidence causes durable skip before worker side effects. Last real end-to-end proof: none. Failure: execution after resolved/stale state or missing durable audit. Observer/observer health and recovery are not integrated; no MONITORED/HEALTHY claim. Engineering recovery: retain evidence, keep rollout held, enforce reviewed write boundary and integrate/prove atomic adapter. No Brian/account action needed for this review. Separate rollout authorization still required.
