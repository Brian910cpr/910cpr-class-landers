# Issue 380 R16 — isolated PostgreSQL contention executed

2026-10-13T03:48Z. Draft PR #381. Local proof only; all six issue acceptance criteria remain open.

## Result and scope

The five previously unexecuted contention scenarios now pass on separate PostgreSQL connections. Each test observes pg_stat_activity.wait_event_type = Lock before releasing the first transaction. Assertions verify one canonical transition/event/activity, identical-request replay, changed-payload conflict, cross-card request conflict, stale distinct-request rejection, and rollback/retry without a phantom event. The SQL draft is unchanged and remains outside migrations.

Only test diagnostics changed: server/driver/libpq versions and explicit lock observations are printed. No production data, API, runtime, launcher, UI, evidence storage or deployed schema changed. This advances native canonical card lifecycle reliability without adding an Enrollware dependency. Earlier design rationale remains in data/audit/issue380_resolution_preflight_20261011.md.

## Local infrastructure and reproducibility

Dedicated infrastructure outside all worktrees:
- E:/GitHub/issue380-pg-portable/server (portable test binaries)
- E:/GitHub/issue380-pg-portable/cluster-r16 (dedicated retained test cluster)
- E:/GitHub/issue380-pg-env (Python venv, psycopg[binary]==3.2.10)
- E:/GitHub/issue380-pg-portable/r16-server.log and r16-tests.txt

Binary artifact downloaded with Windows Invoke-WebRequest certificate verification enabled:
https://repo.maven.apache.org/maven2/io/zonky/test/postgres/embedded-postgres-binaries-windows-amd64/16.4.0/embedded-postgres-binaries-windows-amd64-16.4.0.jar
SHA256: 5748a1b03f3771cd7a6d8aa624975e2777f62525694bf63af9640deaa48cc87a
Archive contains postgres-windows-x86_64.txz, extracted locally. This old pinned release is used only for disposable synthetic tests, not an operational service. No binaries/venv/data committed. Initial Python HTTPS attempt failed certificate validation; Windows verified HTTPS succeeded without disabling verification.

Commands executed (PowerShell; paths abbreviated below by executable name only):
```powershell
python -m venv E:/GitHub/issue380-pg-env
E:/GitHub/issue380-pg-env/Scripts/python.exe -m pip install 'psycopg[binary]==3.2.10'
initdb.exe -D E:/GitHub/issue380-pg-portable/cluster-r16 -U issue380_local --auth=trust --no-locale --encoding=UTF8
pg_ctl.exe -D E:/GitHub/issue380-pg-portable/cluster-r16 -l E:/GitHub/issue380-pg-portable/r16-server.log -o '-h 127.0.0.1 -p 55480' -w start
```
Binaries are under E:/GitHub/issue380-pg-portable/server/bin. createdb.exe is not included; the first harness invocation failed because the target database did not yet exist (no tests ran). Created the empty database with psycopg autocommit connection to the dedicated cluster's postgres database: `create database issue380_test_r16`. No operational cluster used. Local trust authentication bound exclusively to IPv4 loopback; no service, startup entry or scheduled task installed.

```powershell
$env:ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 user=issue380_local dbname=issue380_test_r16'
E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_resolution_contention.py
```
The empty-database guard prevents reusing this initialized database. For another run, start this dedicated cluster and create a fresh empty issue380_test_* database; do not drop retained evidence or use an operational cluster.

## Full successful output
```texttest_reject_operational_or_indirect_targets (__main__.TargetSafety.test_reject_operational_or_indirect_targets) ... ok
PostgreSQL: PostgreSQL 16.4, compiled by Visual C++ build 1940, 64-bit
psycopg: 3.2.10 libpq: 160009
test_distinct_request_stale_writer_rejected: observed contender Lock wait
test_distinct_request_stale_writer_rejected (__main__.ResolutionContention.test_distinct_request_stale_writer_rejected) ... ok
test_identical_request_replays_once: observed contender Lock wait
test_identical_request_replays_once (__main__.ResolutionContention.test_identical_request_replays_once) ... ok
test_request_reuse_across_cards_conflicts: observed contender Lock wait
test_request_reuse_across_cards_conflicts (__main__.ResolutionContention.test_request_reuse_across_cards_conflicts) ... ok
test_rollback_releases_request_without_phantom_receipt: observed contender Lock wait
test_rollback_releases_request_without_phantom_receipt (__main__.ResolutionContention.test_rollback_releases_request_without_phantom_receipt) ... ok
test_same_request_changed_payload_conflicts: observed contender Lock wait
test_same_request_changed_payload_conflicts (__main__.ResolutionContention.test_same_request_changed_payload_conflicts) ... ok

----------------------------------------------------------------------
Ran 6 tests in 1.176s

OK
```

Post-test inspection:
```text
Card states: [(1, 'unresolved', 25), (2, 'handled_manually', 5)]
Events: 5
Activities: 29
AST syntax: passed
waiting for server to shut down........ done
server stopped
```
Counts include 24 seed cards/activities from the existing base migration plus six test cards (one deliberately unresolved cross-card contender). Per-card assertions verify exactly one resolution event/activity for each successful test card.

`git diff --check`: passed. Python AST parse: passed. Existing JS suite not repeated: no JS/SQL behavior changed; prior 60/60 evidence remains historical, not a new test claim. Supabase skill/changelog reviewed; current HTTP TLS change does not affect this isolated SQL test. PostgreSQL explicit locking documentation reviewed: https://www.postgresql.org/docs/current/explicit-locking.html.

## Remaining gates and proof contract

Overall system remains BUILT, with narrow isolated transaction contention proof now recorded. No actual owner resolution/upload/customer workflow or installed dispatcher pre-mutation cycle has been proven. No MONITORED/HEALTHY claim. Authenticated canonical intake, transactional claim/skip/audit and runtime fencing remain unfinished, as do private evidence, UI/history/counts, advisor/security review and browser/upload proof. SQL must stay unapplied pending coordinated review/authorization. Next engineering step: security review and concrete authenticated canonical claim-or-skip transaction/adapter, followed by isolated pre-side-effect concurrency proof; do not substitute additional advisory hardening.

Success boundary: canonical resolved/blocked/stale work skipped with durable audit before launch/side effects. Last real end-to-end proof: none. Observer/observer health and automatic recovery are not integrated. Failure condition: execution despite canonical stop state or absent durable audit. Recovery: preserve evidence, hold rollout, finish reviewed atomic wiring/proof. No Brian/account action required now; separate rollout authorization remains required.

PR #381 remains draft/unmerged/undeployed; #372 untouched, #371 primary preserved. Original E:/GitHub/910cpr-class-landers dirty work preserved. Worktree-local Windows case-collision changes docs/Earl/index.html and docs/Jackson/index.html excluded. Queue scanned; existing assignments preserved; no competing deep stream claimed.
