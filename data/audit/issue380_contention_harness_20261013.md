# Issue 380 R15 — multi-session proof harness, execution blocked

2026-10-13 UTC. Existing draft PR #381. BUILT only; original acceptance criteria remain open.

## Work and review paths

Added `tests/reconciliation/board_resolution_contention.py`. It exercises the unchanged `data/audit/issue380_resolution_transaction_draft.sql` against the existing board migration using separate psycopg connections. The first transaction is held open until the admin connection observes the contender waiting on a PostgreSQL Lock; only then is it committed/rolled back. Five cases specify identical-request replay, changed-payload conflict, cross-card request conflict, distinct-request stale writer, and rollback followed by successful retry. Each asserts canonical card version/state and durable event/activity counts. Lock and statement timeouts bound failure.

Target gates require explicit ISSUE380_TEST_DSN, literal 127.0.0.1, an issue380_test_* database name, no service/hostaddr indirection, and an empty database. Effective libpq target is checked before fixture writes. DATABASE_URL is not read. The test creates missing cluster-global roles; use a dedicated disposable local cluster, never an existing operational cluster. Existing roles are not altered. Fixtures are retained for inspection, with no cleanup/drop command. No production migration or application behavior changed.

## Exact validation and limitation

- `python tests/reconciliation/board_resolution_contention.py --guards-only`: 1 passed. Rejects missing/remote/ordinary database and service/hostaddr indirection. This is target validation, NOT contention proof.
- `python tests/reconciliation/board_resolution_contention.py`: explicit BLOCKED error, no contention proof ran. Missing ISSUE380_TEST_DSN deliberately exits nonzero rather than reporting skipped tests as success.
- Python AST syntax parse: passed.
- `node --test tests/live_dispatch_check.test.mjs tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/owner_access.test.mjs`: 60 passed, 0 failed.
- In tests/reconciliation, `npm ci --ignore-scripts --no-audit --no-fund` then `node --test board-resolution.test.mjs`: 1 passed, 0 failed. PGlite is still single-connection proof only. No package/lockfile change.
- `git diff --check`: passed.

Exact local blocker: no postgres/psql/initdb/docker command on PATH; no PostgreSQL/Docker install in checked C:/Program Files/PostgreSQL, C:/Program Files, C:/tools, E:/tools, user Local or cached Codex runtimes. wsl.exe exists but reports Windows Subsystem for Linux is not installed. Python psycopg is also unavailable. No isolated PostgreSQL DSN was supplied. No live or operational database was used as a substitute. The five new multi-session scenarios have NOT run; this increment does not prove concurrency or remote atomic fencing.

## Next concrete engineering step

Provision a dedicated disposable local PostgreSQL cluster, install psycopg in its test environment, create an EMPTY issue380_test_<unique> database, explicitly set ISSUE380_TEST_DSN to its 127.0.0.1 DSN, then run `python tests/reconciliation/board_resolution_contention.py`. Inspect retained events and counts. Do not reuse that database for another run: initialization deliberately rejects existing fixture tables. Record server/driver versions and full output before claiming contention proof. No Brian credential/account action is required; local test infrastructure is an engineering dependency.

Then finish security review, authenticated canonical intake/transactional claim-or-skip/audit, actual runtime pre-mutation fencing, private evidence and UI/history/counts. SQL stays outside migrations until coordinated review/authorization. PR #381 remains draft/unmerged/undeployed; #372 untouched and #371 remains primary. No installed launcher/state/process/task or production mutation. Original dirty checkout preserved; isolated worktree's known Windows case-collision HTML changes excluded. Queue scanned; existing assignments preserved, no competing stream claimed.

Supabase skill and changelog reviewed (current HTTP TLS change does not affect local SQL); PostgreSQL explicit-lock documentation reviewed: https://www.postgresql.org/docs/current/explicit-locking.html. This advances native canonical card lifecycle proof without an Enrollware dependency or new business model.

Persistent proof contract unchanged: useful outcome is canonical resolved/blocked/stale work skipped with durable audit before launch/side effects. Last real end-to-end proof: none. Observer/observer heartbeat and automatic recovery are not integrated. Failure is execution despite canonical stop state or missing audit. Recovery: preserve evidence, keep deployment held, complete isolated proof and approved wiring. Engineering/review now; separate production authorization later. No HEALTHY/MONITORED claim and no routine Brian monitoring dependency is being accepted as a solution.
