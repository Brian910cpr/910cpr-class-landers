# Issue #371 — independent-session lock proof preparation

Timestamp: 2026-10-14 UTC (exact commit timestamp in Git history).
State: IN_PROGRESS / PR_OPEN; BUILT, locally validated only.
Branch: codex/issue371-concurrency-20261014
Existing draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/372
Substantive commit: 5eb3f99a3a31e83139923a941aa073195b51ff9d (includes runner/report commit 7d8ae5f0d).
Receipt commit: pushed tip containing this file; full SHA supplied in final response.

## Execution and preservation

Read issue body/comments, AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design ethos and proof standard. Actual execution acknowledgment before implementation: https://github.com/Brian910cpr/910cpr-class-landers/issues/371#issuecomment-6160848371 . Owner Path A remains controlling; arbitrary third-party comments supplied no authorization. Scanned open queue titles; preserved one deep stream and existing assignments/monitors. No unrelated issue changed.

Original E:/GitHub/910cpr-class-landers dirty files/untracked receipts preserved; its current checkout lacks the handoff protocol. Healthy D: repository supplied isolated E:/GitHub/910cpr-issue371-concurrency-20261014 at PR tip 75ca2e198e25ebce32bb3796ec960ecc6c95c73b. Windows case-collision changes docs/Earl/index.html and docs/Jackson/index.html remain unstaged in isolated worktree, excluded from commits. No cleanup/reset/restore/rebase/force push. Temporary issue reads outside repo; no intentional new untracked application artifacts.

## Exact files and review targets

- tests/customer_interaction_concurrency.py
- docs/CUSTOMER_INTERACTION_CONCURRENCY.md
- Codex_Reply_Issue371_Concurrency_20261014T_Run1.md

No application/migration/auth/UI changes. Canonical lifecycle and pending SQL reused, no Enrollware dependency added. Existing release context: docs/CUSTOMER_INTERACTION_PATH_A_SAFETY.md and data/audit/issue371_patha_metadata_20261012.json; historical metadata was not refreshed or claimed current.

## Validation and exact blocker

Python compile via compile(Path(...).read_text(), path, 'exec'): PASS; no bytecode artifact. --help exit 0. Missing consent flag exit 2: requires --apply-to-empty-local; no database contacted. Consent flag with missing driver exit 2: psycopg 3 missing; no database contacted/installed. git diff --check PASS.

Using cached PGLITE_MODULE=file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js:

    node --experimental-strip-types --test tests/customer_interruptions_sql.test.mjs
    tests 10; pass 10; fail 0; cancelled 0; skipped 0; todo 0

New runner's live database branch NOT EXECUTED. Syntax/refusal checks and existing PGlite tests do not prove simultaneous sessions. No browser assets changed; browser suite not rerun. No known executed-test failures.

Actual experiment blocked: PostgreSQL executables absent from PATH/checked common Program Files/tool roots; Python psycopg/psycopg2 absent. No install, Docker/WSL retry, cloud provisioning or production connection. Safe backend progress: opt-in executable concurrency experiment and evidence contract. No Brian action required for safe task-status/NEXT continuation.

## Deployment, proof contract and next action

Persisted locally, committed and to be pushed to existing draft PR372 and named codex branch before exit. No production DB write, function deployment, UI exposure, merge, origin expansion, generator or infrastructure changes. Gate OFF; PR draft/unmerged/undeployed.

Review and run five scenarios only on authorized empty numeric-loopback PostgreSQL with supplied psycopg 3; record server/migration versions and five real blocking observations. Do not clear concurrency gate based on this receipt. Continue task status/saved-only NEXT in same PR while runtime unavailable. Genuine owner-session UI/API/database recovery, usable backup/restore and separate explicit production GO remain required. No incomplete rollout approval requested.

Evidence level BUILT; real owner-session and simultaneous-session proof absent. On-demand expected outcome: no resolved interaction with outstanding obligations; request/rollback evidence survives. Local runner observes only when invoked. Missing PASS/receipt, lost obligation or incorrect resolved state fails proof. No deployed observer or observer-health proof; no MONITORED/HEALTHY claim. Preserve failed synthetic fixtures, diagnose privately and repeat in a fresh authorized database. Brian must not become routine monitoring layer; production observation remains unresolved.

## Full primary report

# Independent-session CRM lock proof

Status: runner BUILT; real concurrency experiment NOT RUN. Production gate remains closed.

`tests/customer_interaction_concurrency.py` prepares the experiment specified in
`docs/CUSTOMER_INTERACTION_PATH_A_SAFETY.md`. It uses two independent READ COMMITTED
writer sessions and a third observer. The first RPC remains uncommitted until
`pg_blocking_pids` proves the second RPC waits on that exact first backend. A sleep
or sequential result alone is never accepted as lock evidence. Statement/lock
timeouts bound failures; the first transaction rolls back on failed assertions.

Five synthetic scenarios: task creation before resume; resume before creation;
completion before resume; completed-task reopening before resume; two distinct
task writes. Assertions cover expected 40001 conflicts, atomic resume rollback,
unchanged exact-request replay, one immutable receipt per successful request,
no receipt for rejected writes, two distinct tasks, and no resolved interaction
with outstanding obligations. This is a focused regression experiment, not proof
that arbitrary lock schedules are deadlock-free or real owner authentication works.

## Opt-in execution

Prerequisites: an authorized disposable PostgreSQL server on numeric loopback,
an empty database named `issue371_*`, psycopg 3 in the chosen Python environment,
and cluster roles `anon`, `authenticated`, `service_role` already provisioned by
the test administrator. The login must be able to apply the pending migrations,
set role service_role, and observe blocking PIDs. Use synthetic credentials only.
This runner creates no cluster roles and installs nothing. It refuses non-loopback,
hostaddr/service overrides, missing consent flag, and nonempty public schemas.
Do not configure libpq environment/service settings that redirect connections.

```powershell
# Supply synthetic local connection settings through the environment, never GitHub.
$env:ISSUE371_LOCAL_DSN='host=127.0.0.1 port=5432 dbname=issue371_lockproof user=local_test_admin'
python tests/customer_interaction_concurrency.py --apply-to-empty-local
```

Expected output: five JSON PASS records with observed_blocking=true and exit 0.
Any missing scenario, FAIL, timeout, conflict mismatch, or nonzero exit leaves
the gate closed. Driver exception strings/DSNs are deliberately not printed.
The runner persists synthetic schema/fixtures for investigation and never drops,
resets, or cleans them. A second run requires a different empty database; disposal
is a separate explicit administrator action. Capture stdout, exit code, server
version and migration hashes as evidence outside any private data path.

Current dispatch: no PostgreSQL executable/runtime was found through PATH or
checked common install roots; psycopg and psycopg2 are absent. Therefore the actual
experiment is blocked on a supplied authorized local runtime/driver. No install,
cloud provisioning or production connection was attempted. Path A does not make
Docker/WSL/Synology prerequisites: this optional test can use ordinary PostgreSQL.
No Brian action is required for safe task-status/NEXT implementation in PR372.

Local checks: Python compile/help/refusal paths; existing PGlite transaction suite
10 passed / 0 failed. PGlite cannot execute this independent-session experiment.
The unexecuted runner must itself be reviewed and exercised before its results
are accepted. Keep feature gate OFF and PR372 draft/unmerged/undeployed.

Proof contract: expected outcome is on-demand concurrent RPC serialization without
lost obligations; success evidence is all five real server observations plus
durable receipt/invariant assertions. No successful real concurrency proof yet.
The local runner detects failures while invoked; no deployed observer or observer
health exists. Recovery: preserve failed synthetic database, inspect session/lock
diagnostics privately, fix source and repeat in a fresh authorized empty database.
Owner-session recovery, backup/restore and separate production GO remain gates.

References consulted read-only: PostgreSQL explicit locking documentation
https://www.postgresql.org/docs/current/explicit-locking.html and Supabase changelog
https://supabase.com/changelog.md on 2026-10-14. The HTTP TLS cipher deprecation
does not change this local PostgreSQL test contract. No platform API changed.

