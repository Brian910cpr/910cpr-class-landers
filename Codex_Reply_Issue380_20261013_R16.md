# Issue #380 — R16

Timestamp: 2026-10-13T03:48:38.8234917Z
Branch: codex/issue380-r16-20261013; pushed to existing PR #381 head codex/issue380-manual-resolution-20261011.
Substantive commit: 4dd4987daca044654f51df0ee21133b1755acd59
State: PR_OPEN; issue unfinished. Overall persistent evidence: BUILT with isolated resolution-transaction contention proof.

## Findings and work
Cleared R15's local test infrastructure blocker using dedicated portable PostgreSQL 16.4 and a Python venv with psycopg 3.2.10/libpq 160009. Ran all five real two-session contention scenarios successfully; each observed Lock before release. Test diagnostics now print versions and observations. SQL unchanged, outside migrations. Dedicated local server stopped after inspection; fixtures retained outside repo.

Exact intended changed files:
- tests/reconciliation/board_resolution_contention.py
- data/audit/issue380_contention_proof_20261013.md
- Codex_Reply_Issue380_20261013_R16.md

Primary report contains complete output, binary origin/hash, local paths, commands, initial setup failures and limitations. Review report and harness with data/audit/issue380_resolution_transaction_draft.sql and tests/reconciliation/board-resolution.test.mjs.

Validation: 6/6 passed (one target guard + five contention cases); Python AST syntax and git diff --check passed. Canonical inspection: five handled cards at version 2, five resolution events; per-card assertions verify exactly one activity/event. Existing migration seed accounts for other rows. No unrelated suite rerun or new 60-test claim. Initial missing createdb binary/database was corrected with psycopg on this dedicated cluster; first attempt produced no test proof. Python HTTPS certificate error corrected by verified Windows HTTPS, no validation bypass.

Unrelated dirty work preserved in original checkout. Worktree case-collision HTML dirt docs/Earl/index.html and docs/Jackson/index.html intentionally unstaged. No binaries, caches, venv, fixtures or logs committed; outside-repo local infrastructure retained explicitly for reproducibility. No generated public pages rebuilt. Queue scanned; existing assignments preserved.

Deployment: locally validated; this receipt and intended files pushed to existing draft PR #381. No merge, production SQL, deployment, installed runtime/state/process/task change. #371 remains primary; #372 untouched. Verify pushed receipt at branch tip using GitHub Contents API; final pushed SHA supplied in issue/UI because it cannot be self-referenced inside this commit.

Remaining: authenticated canonical intake/claim-or-skip/audit, runtime pre-mutation fencing, security/advisor review, private evidence, UI/history/counts and upload/browser proof. All six acceptance criteria open. Next ChatGPT action: review report/harness and narrow contention proof, keep #381 draft; continue concrete authenticated atomic transaction/adapter and isolated pre-mutation proof. No Brian/account action required now.

Persistent proof contract: useful outcome is canonical resolved/blocked/stale work skipped with durable audit before launch/side effects. Last real end-to-end proof: none. Observer/observer health and automatic recovery not integrated; failure is execution despite stop state or absent audit. Recovery is preserve evidence, hold rollout and finish approved wiring/proof. No MONITORED/HEALTHY claim. This clears isolated contention infrastructure only, not production fencing or owner workflow.
