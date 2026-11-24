# Issue #380 — R32

Timestamp: 2026-10-14T08:48:00Z. State: PR_OPEN / BUILT only.
Branch: codex/issue380-r32-20261014, updating existing draft PR #381 head codex/issue380-manual-resolution-20261011.
Substantive commit: bd8521ca5b2a64c9cac94457d95963a1a7b0a1f1.

Execution acknowledged on originating issue before implementation. Read full issue/history and repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design/proof gates. Preserved dirty original checkout through separate named worktree. #371 primary and #372 untouched; no merging/deploying.

Added three real local PostgreSQL tests proving collector/manual-resolution races in both orders, conflicting payload and cross-card request reuse, and cross-actor receipt privacy/collision rollback. Existing SQL behavior passes these new regressions; no application/SQL behavior fix claimed. Root limitation remains raw collector DML/direct receipt insertion and missing authoritative source binding.

Exact changed files:
- tests/reconciliation/board_collector_publication.py
- data/audit/issue380_collector_resolution_races_20261014.md (full final test output and commands)
- Codex_Reply_Issue380_20261014_R32.md

Validation locally: PostgreSQL 16.4 / psycopg 3.2.10: 42/42 tests, 20 observed Lock waits; AST syntax and git diff --check passed. No unrelated failure in executed suite. Node not rerun because no API/JS changes. Test server stopped (pg_ctl status: no server running); temporary login roles removed. Retained disposable test databases/raw output outside repository. No generator/public artifact changes.

Persistence: changed in repo, locally validated; intended files committed and pushed to existing draft PR #381. Receipt is in separate communication commit referencing substantive SHA above; final pushed tip reported on issue/UI and verified by GitHub Contents API. No production migration/write, installed runtime/state change, merge or deploy. Worktree case-collision dirt docs/Earl/index.html and docs/Jackson/index.html intentionally left unstaged; original dirty work unchanged. Nothing newly left untracked for this dispatch.

All six acceptance criteria remain open. Exact rollout gates: exclusive restricted audited collector gateway, authoritative reader/source attestation, effective production privilege proof, installed no-launch consumer and atomic external side-effect fence; owner private evidence/uploads/UI/history/count/reopen/browser acceptance unfinished. SQL stays outside migrations/unapplied. These are engineering gaps, not a claimed credential/account blocker. No Brian action required now. Queue scanned; existing assignments preserved and no unrelated safe quick win selected.

Next action for ChatGPT: review report/tests at substantive SHA; keep #381 draft/unmerged/undeployed. Continue exclusive least-privilege publisher and authoritative reader binding, retaining current rollback/denial/contention regressions. Cross-actor unique conflict is fail-closed SQL behavior, not a production error-sanitization guarantee.

Operational evidence: BUILT only. Expected outcome is skip handled/blocked/already-corrected work before launch/mutation. Last production end-to-end proof: none. Expected cadence/installed observer and observer health: unproven. Stale source/version mismatch/uncertain commit must fail closed; recovery inspects canonical card/intake/request/audit and retries against fresh approved source/version. Brian must not be the routine monitoring layer. No claim of CONNECTED/PROVEN/MONITORED/HEALTHY.
