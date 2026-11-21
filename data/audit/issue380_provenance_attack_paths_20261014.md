# Issue 380 R27: provenance attack-path proof

2026-10-14T01:28Z. State: PR_OPEN / BUILT only. Baseline c2cb198c97b7757b6c5700fe282f8f0841eba138. Existing draft PR #381; no merge/deploy authorization. All six acceptance criteria remain open.

## Findings
Two additional real PostgreSQL negative controls close gaps in the R25/R26 security review:

1. Routine service_role INSERT can create the first intake row with authoritative_observation, action_required, worker_safe=true and current checked_at. There is no publication receipt or intake mutation audit. Dispatch creates a reservation at card version 2, with can_execute=false.
2. On an existing authoritative fixture, a six-minute-old observation correctly produces source_check_stale at version 3. Routine service_role UPDATE of checked_at and source_ref alone preserves authoritative_observation, creates no intake mutation audit, and produces a reservation at version 4. No assignment to provenance is needed.

These passing tests deliberately prove vulnerabilities, not secure attestation or execution. The previous UPDATE provenance control remains. No SQL behavior was changed. No customer/source truth was inspected: every record is synthetic in a disposable local database.

## Required repair boundary
Protecting only UPDATE(provenance), or only DELETE, is insufficient. The restricted collector design must cover first INSERT and all changes to an observation's identity, revision, source outcome, blocked/worker-safe flags, reference and freshness. Noncollector modifications must fail or atomically downgrade to owner_assertion, with immutable audit. A role-name check alone is not independent source authentication. No caller-supplied timestamp, actor label or reference proves inspection.

Current SECURITY INVOKER publication needs direct INSERT/UPDATE and explicitly resets provenance on republication. Revoking these grants blindly breaks ordinary owner publication. Before rollout implement separate authenticated collector authority and reviewed restricted storage mutation protocol, with least privilege and effective membership/default-grant review. Keep transaction locks, identity/version/idempotency and commit acknowledgment. Convert all three forgery controls to denial/downgrade tests; preserve owner publication/replay and concurrency proofs. Test prior authoritative rows as well as missing rows.

This diagnostic deliberately avoids inventing a broad SECURITY DEFINER public RPC or a new paid integration. Native canonical board identity/history remains the design center; no Enrollware dependency added. Installed no-launch consumer, atomic external side-effect fence, private attachments, resolved history/counts and browser proofs remain separate unfinished engineering gates. No account action is required from Brian for this review.

## Validation
Local PostgreSQL 16.4, psycopg 3.2.10/libpq 160009. Dedicated existing portable test cluster started on IPv4 loopback port 55480, empty database issue380_test_r27. Strict target/empty-database guard retained. Server stopped and pg_ctl status confirmed no server running after tests. No operational DB accessed.

Exact commands (PowerShell):
```powershell
$env:ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 user=issue380_local dbname=issue380_test_r27'
& E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_intake_trust_boundary.py
python -c "import ast,pathlib; ast.parse(pathlib.Path('tests/reconciliation/board_intake_trust_boundary.py').read_text()); print('AST PASS')"
git diff --check
```
Key output:
```text
NEGATIVE CONTROL: initial INSERT forged observation without publication/audit
NEGATIVE CONTROL: refresh revived stale observation without provenance assignment/audit
Ran 30 tests in 5.471s
OK
AST PASS
pg_ctl: no server running
```
Eleven real Lock waits observed in inherited concurrency tests. Syntax and diff checks passed. Backend Node suite not rerun: no backend/SQL behavior changed. No new unrelated test failures.

Supabase skill applied. Current changelog fetched with Invoke-WebRequest after browser markdown content-type failure; latest TLS HTTP cipher change does not affect local PostgreSQL. Official RLS guidance reviewed: https://supabase.com/docs/guides/database/postgres/row-level-security . No production advisors or migration commands executed.

## Persistence, proof and next action
Files intentionally changed: tests/reconciliation/board_intake_trust_boundary.py; this report data/audit/issue380_provenance_attack_paths_20261014.md; unique root Codex_Reply receipt. Original dirty E:/GitHub/910cpr-class-landers untouched. Isolated codex/issue380-r27-20261014 based on #381; Windows case-collision docs/Earl/index.html and docs/Jackson/index.html excluded from staging. No generators or ops/handoff/next_task.md. Queue titles swept; no unrelated implementation claimed or competing deep stream started; #371/#372 preserved.

Expected useful outcome remains skip handled/blocked work before launch and before every side effect. No production end-to-end proof exists for this draft, no installed observer or observer-health proof; do not call this connected/proven/healthy. Existing draft freshness five minutes/reservation sixty seconds are not an approved operational cadence. Failure conditions include forged/stale/missing source evidence, unresolved commit acknowledgment or version mismatch. Recovery: retain request IDs, investigate authenticated source state, fail closed. Observer/recovery integration remains an engineering gate, not Brian's routine monitoring assignment.

Next action for reviewer: review both new negative controls and the complete observation-field write boundary, then implement restricted authoritative collector/write protocol and convert controls to denial/downgrade regressions before runtime integration. Keep #381 draft and SQL outside migrations/unapplied. This dispatch adds diagnostic proof only and does not resolve issue #380.
