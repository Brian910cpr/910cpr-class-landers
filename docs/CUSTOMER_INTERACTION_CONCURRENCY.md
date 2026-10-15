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
The runner now rejects nonempty PGHOSTADDR, PGSERVICE, PGSERVICEFILE and PGOPTIONS
before connection, as well as DSN hostaddr/service/options overrides. An explicit
host alone does not neutralize libpq's inherited hostaddr/service defaults.
Run ordinary Python: -O, -OO and PYTHONOPTIMIZE are refused before driver import
because proof assertions must remain active. Empty-schema/function checks also
use unconditional exceptions rather than assertions.

No-network guard regression:
`python -B -m unittest discover -s tests -p test_customer_interaction_concurrency_safety.py -v`
Seven tests cover opt-in, optimized interpreters, loopback/database validation,
environment and DSN overrides, secret-free refusal, and no writes when existing
public objects/functions are found. They use mocks/subprocess refusal only and
do not establish independent-session concurrency or clear any release gate.

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

Runner safety references checked 2026-10-15: https://www.postgresql.org/docs/current/libpq-envars.html and https://supabase.com/changelog.md. No Supabase API/schema convention changed.
