# Issue 380 R29: independent routine-login privilege proof

2026-10-14T03:48Z. PR_OPEN / BUILT only. Baseline 869664c669a85efa5c9b00465a184dbca7579c33. Reuses draft PR #381. All six acceptance criteria remain open.

## Findings and change

Existing role tests use SET ROLE on an administrative session. PostgreSQL permits role selection based on session-user membership/superuser status, so those connections cannot establish inability to switch back to the table owner. Added an independently connected, unique non-superuser login with only service_role membership. The test verifies its session identity and effective role, denies SET ROLE owner, SET SESSION AUTHORIZATION owner, replica trigger bypass, disabling the observation trigger, disabling RLS, and changing the guard to SECURITY DEFINER. Observation promotion is also denied. Positive control executes the intended owner-assertion publication RPC and checks version 3, assertion provenance and can_execute=false. Temporary login is removed in finally. No SQL behavior changed.

This proves only the dedicated synthetic cluster memberships. It does not establish production ownership/membership, parameter grants, arbitrary privileged function reachability, JWT authentication, collector attestation, or absence of other escalation paths. Administrative access remains trusted. Do not extrapolate this test to production safety.

Native canonical board identity/history remains the design center. This proof adds no Enrollware dependency or customer-facing capability.

## Validation

Existing portable PostgreSQL 16.4 at IPv4 loopback port 55480, psycopg 3.2.10/libpq 160009; strict empty disposable database guard retained. Final database issue380_test_r29_final. Local trust authentication is test infrastructure only; no passwords/credentials introduced. First run found a test constant typo (CALL rather than PUBLISH), corrected before final proof.

Commands:
```powershell
$env:ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 user=issue380_local dbname=issue380_test_r29_final'
& E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_intake_trust_boundary.py
python -c "import ast,pathlib; ast.parse(pathlib.Path('tests/reconciliation/board_intake_trust_boundary.py').read_text()); print('AST PASS')"
git diff --check
```
Final relevant outputs:
```text
DENIED: six privilege bypasses and promotion from nonadmin login
Ran 29 tests in 5.311s
OK
AST PASS
server stopped
```
Eleven observed Lock waits. Final diff check passed after trimming an extra EOF blank line. No application/API change; no additional Node run needed. Fixtures retained locally; server stopped. Supabase skill/security checklist read and changelog fetched; upcoming HTTP TLS cipher change does not affect loopback PostgreSQL proof. PostgreSQL role semantics: https://www.postgresql.org/docs/16/sql-set-role.html . No production advisors or database accessed.

## Review and next steps

Changed test: tests/reconciliation/board_intake_trust_boundary.py. Report: data/audit/issue380_routine_login_privileges_20261014.md. Unique root receipt is committed separately. Isolated codex/issue380-r29-20261014 preserves original checkout. Windows case-collision dirt docs/Earl/index.html and docs/Jackson/index.html excluded from explicit staging. Open queue titles scanned; existing deep assignments preserved, no independent safe backend item selected from titles alone. #371 remains primary, #372 untouched. No generator, production write, migration, installed dispatcher change, merge or deploy. SQL remains outside migrations and unapplied.

Exact rollout gates: separately authenticated authoritative collector/restricted audited writes plus effective production privilege inspection; installed canonical no-launch consumer and external atomic side-effect fence/race proof; private evidence/history/counts/reopen and browser acceptance remain unfinished. Next implement and review collector identity/write protocol against these tests, then consumer/fence and evidence/UI. No Brian/account action required for backend work. Keep #381 draft.

Operational proof contract remains BUILT: expected outcome skip resolved/blocked/already-corrected tasks before launch/mutation; production end-to-end proof none. Draft five-minute freshness/sixty-second reservation are not approved operating cadence. Missing/stale evidence, privilege bypass, version mismatch or uncertain commit must fail closed. Installed observer/observer-health/recovery/escalation remain unproven; engineering must implement them, Brian is not assigned routine monitoring. Preserve request IDs and audit when investigating. No HEALTHY claim.
