# Issue 380 R28: routine observation write quarantine

2026-10-14T02:48Z. PR_OPEN / BUILT only. Baseline 418aa5f75c3c383ceaf527aadf729971458746c9. Reuses draft PR #381; all six acceptance criteria remain open.

## Change and limits

R27 demonstrated first INSERT forgery, UPDATE provenance promotion, and stale-observation refresh without provenance assignment. A BEFORE INSERT/UPDATE guard now rejects any resulting authoritative_observation row unless current_user is the intake table owner. Routine service_role writes fail with authoritative_collector_required before version/activity mutation. No timestamp, reference, role label, or caller payload is promoted to attestation. Existing typed owner publication remains SECURITY INVOKER and writes owner_assertion, including downgrade on republication. Direct writers editing an old observation must explicitly downgrade it; inherited lock tests now do so.

This is a fail-closed quarantine, NOT an authenticated collector implementation. Table-owner/administrative SQL remains trusted and can forge observations or disable triggers. No collector privilege, credential, SECURITY DEFINER function, migration, installed runtime, or production change was introduced. Direct assertion writes and privileged activity inserts remain insufficient for immutable authenticated audit. Effective production memberships, ownership/default grants and role escalation must be reviewed before rollout. No new routine caller can establish an authoritative observation; this intentionally restricts draft capability until the collector is reviewed. Replaying old decisions remains historical and non-executable; every response still can_execute=false.

Replaced the three diagnostic vulnerability controls with insert/promote/refresh denial subcases. Each proves rollback of a preceding card write, unchanged intake/version/activity, and no reservation after denial. Owner publication/replay, audit rollback, identity protection, DELETE/TRUNCATE denial, resolution-between-checks, competing reservations, and publication/dispatch contention remain covered. No live source truth was inspected. All fixtures are synthetic.

Native canonical board state/history remains the design center, no Enrollware dependency added. This advances backend integrity toward native operation but proves no customer-facing replacement.

## Local validation

Dedicated existing portable PostgreSQL 16.4 cluster; psycopg 3.2.10/libpq 160009. Strict empty-database/IPv4-loopback guards retained. Database issue380_test_r28_final at 127.0.0.1:55480. Created via psycopg because this portable distribution lacks createdb.exe. Initial run found two contention tests still writing authoritative rows; explicit assertion downgrade repaired their fixtures. A subsequent edit briefly failed Python parsing; corrected before final tests.

Commands:
```powershell
$env:ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 user=issue380_local dbname=issue380_test_r28_final'
& E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_intake_trust_boundary.py
node --test tests/production_intake_publication.test.mjs tests/production_dispatch_decision.test.mjs tests/dispatch_reconciliation.test.mjs tests/live_dispatch_check.test.mjs
python -c "import ast,pathlib; [ast.parse(pathlib.Path(p).read_text()) for p in ['tests/reconciliation/board_dispatch_transaction.py','tests/reconciliation/board_intake_trust_boundary.py']]; print('AST PASS')"
git diff --check
```
Final output:
```text
DENIED and rolled back: insert
DENIED and rolled back: promote
DENIED and rolled back: refresh
Ran 28 tests in 5.049s
OK
# tests 50
# pass 50
# fail 0
AST PASS
pg_ctl: no server running
```
Eleven observed real Lock waits. Server stopped after validation. No production database/advisors/migrations accessed. Supabase skill/security checklist reviewed; changelog fetched via Invoke-WebRequest after browser content-type failure. TLS HTTP cipher change does not affect this local PostgreSQL work. Official RLS reference: https://supabase.com/docs/guides/database/postgres/row-level-security . This guard supplements grants; it does not replace RLS or authenticate source truth.

## Review handoff and operational gates

Changed source: data/audit/issue380_dispatch_transaction_draft.sql (outside migrations, unapplied). Tests: tests/reconciliation/board_intake_trust_boundary.py; tests/reconciliation/board_dispatch_transaction.py. Report: data/audit/issue380_observation_quarantine_20261014.md. Unique root receipt also committed. No generator, broad build, launcher changes, ops/handoff mailbox or deployment. Original dirty checkout preserved; case-collision docs/Earl/index.html and docs/Jackson/index.html excluded from explicit staging in isolated codex/issue380-r28-20261014. Open queue titles scanned; no independent narrow item was selected from titles alone or competing deep assignment started. #371/#372 preserved; #266 still requires explicit worker-safe sources.

Exact rollout blocker: no reviewed independently authenticated authoritative collector/restricted storage mutation protocol or production privilege proof; no installed canonical no-launch consumer/external atomic side-effect fence/runtime race proof. Private attachments, resolved history/counts, reopen workflow, and browser proof remain unfinished. Separate review/authorization required before production migration/merge/deploy. No Brian/account action needed for next backend implementation.

Proof contract: expected outcome is skip handled/blocked/already-corrected work before launch and mutation. Last production end-to-end proof: none. Draft freshness five minutes and reservation sixty seconds are not approved operational cadence. Failure includes stale/forged/missing source evidence, version mismatch and uncertain commit acknowledgement; fail closed and retain request IDs for recovery. Installed observer/observer-health/escalation are unproven engineering gates; Brian is not assigned routine monitoring. Do not call this CONNECTED/PROVEN/MONITORED/HEALTHY.

Next review: verify owner exemption is confined to administrative fixtures and review production membership/ownership; implement separately authenticated collector with audited restricted mutation and least privilege, preserving these denial regressions. Then installed no-launch consumer and atomic external fence, followed by private evidence/UI acceptance. Keep #381 draft and SQL unapplied.
