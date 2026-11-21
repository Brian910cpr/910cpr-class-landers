# Issue #380 — R28

Timestamp: 2026-10-14T02:49Z (UTC).
State: PR_OPEN; BUILT only, issue not complete. Existing draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/381
Local branch: codex/issue380-r28-20261014. Push target: codex/issue380-manual-resolution-20261011.
Substantive commit: 203b9503a5dfbcfd5805a3cdd333a53aab496af7. Receipt commit is the pushed branch tip, reported on originating issue after GitHub verification.

Execution acknowledged on #380 before implementation. Read full issue/history, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design/proof standards; #266 dependency inspected. Supabase skill applied. #371 remains primary; draft #372 untouched/unmerged/undeployed. Existing assignments and original dirty checkout preserved.

Findings/work: R27 initial INSERT forgery, provenance promotion and stale refresh now fail closed for routine writers through a BEFORE INSERT/UPDATE guard. Resulting authoritative rows require table-owner current_user. Routine updates of prior observations must downgrade to owner_assertion. No caller payload/role label proves inspection. Failed writes roll back prior card changes and preserve intake/version/activity; dispatch produces no reservation for all three denied paths. Owner assertion publication/replay and concurrency remain tested.

Exact changed files:
- data/audit/issue380_dispatch_transaction_draft.sql
- tests/reconciliation/board_intake_trust_boundary.py
- tests/reconciliation/board_dispatch_transaction.py
- data/audit/issue380_observation_quarantine_20261014.md
- Codex_Reply_Issue380_20261014_R28.md

Primary audit with exact commands/output/limitations: data/audit/issue380_observation_quarantine_20261014.md. Review the SQL guard and owner exemption plus all three denial subcases and explicit downgrade contention fixtures. Prior diagnostic: data/audit/issue380_provenance_attack_paths_20261014.md.

Validation: real local PostgreSQL 16.4 disposable issue380_test_r28_final at IPv4 loopback port 55480; psycopg 3.2.10/libpq 160009. 28/28 tests passed with 11 observed Lock waits. Four targeted Node suites: 50/50 passed. Python AST and git diff --check passed. Initial fixture failures and transient edit syntax failure corrected before final run. Portable createdb.exe absent; database created locally with psycopg. No new unrelated test failures. Test server stopped and pg_ctl confirmed no server running.

Persisted locally and committed for push to existing draft #381. SQL remains outside migrations/unapplied. No production DB/runtime/state mutation, generator, deploy or merge. Case-collision docs/Earl/index.html and docs/Jackson/index.html remain unstaged in isolated checkout; original unrelated work remains untouched. No temporary/runtime files staged; no ops/handoff/next_task.md use.

Exact remaining blocker: no reviewed independently authenticated collector/restricted write protocol or production ownership/membership/privilege proof. Table owner/administrative SQL can still forge observations or disable triggers; this quarantine is NOT collector attestation. Direct assertion/activity writes are not immutable authenticated audit. Installed no-launch consumer and atomic external side-effect fence/runtime race proof, private evidence/UI/history/counts/reopen/browser acceptance remain unfinished. All six acceptance criteria open. No production merge/deploy authorization; keep #381 draft. No account or Brian action required for next backend work.

Persistent proof: expected useful outcome is skip handled/blocked/already-corrected tasks before launch/mutation. Last production end-to-end proof: none; evidence level BUILT. Cadence not approved; draft five-minute freshness/sixty-second reservation are not operational guarantees. Failure/staleness: forged/missing/stale evidence, version mismatch, uncertain commit acknowledgement. Fail closed, retain request IDs, inspect authenticated source. Installed observer/observer health and escalation remain unproven engineering gates; no routine monitoring burden assigned to Brian.

Next reviewer action: review quarantine and owner exemption, then implement authenticated collector/restricted audited writes with membership/default-grant checks before installed consumer/fence or evidence/UI. Preserve denial and lock regressions. Open queue titles swept; no safe independent item selected from titles alone, no competing deep stream started.
