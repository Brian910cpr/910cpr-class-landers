# Issue #380 — R9 dispatch receipt

Timestamp: 2026-10-12 America/New_York.
State: PR_OPEN / IN_PROGRESS. Persistent-system evidence: BUILT only.
Local branch: codex/issue380-r9-20261012.
Pushed destination / existing draft PR #381: codex/issue380-manual-resolution-20261011.
Substantive commit: 58f5423fc8d16bbca9f5d9fa673a4a4f9e69f07f.

Execution acknowledged on originating issue before implementation. Full issue/comments, AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design/proof standards read. Original dirty checkout preserved. #371 remains primary; #372 untouched, unmerged and undeployed.

Findings/work: added fresh-read adapter wrapper with issue identity/version binding, fail-closed read and durable-audit acknowledgement handling, privacy allowlist, and two-phase fake-adapter regressions. No outcome grants execution permission. Concrete authenticated reader, atomic claim/skip/idempotency/audit storage and actual runtime/pre-mutation fencing are unfinished engineering gates, not a credential blocker. No real runtime wiring or atomic race protection claimed. Resolution/evidence/UI/history/count work remains unfinished; all six acceptance criteria open.

Exact changed files:
- supabase/functions/production-board/live-dispatch-check.mjs
- tests/live_dispatch_check.test.mjs
- data/audit/issue380_live_adapter_boundary_20261012.md
- Codex_Reply_Issue380_20261012_R9.md

Primary audit: data/audit/issue380_live_adapter_boundary_20261012.md (full findings, limits and proof contract). Relevant existing contract: supabase/functions/production-board/dispatch-reconciliation.mjs.

Validation locally: node --test tests/live_dispatch_check.test.mjs tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/owner_access.test.mjs — 48 tests, 48 passed, 0 failed. node --check both new modules and git diff --check passed. No broader suite rerun; previous baseline Python auth assertion failures remain outside this change. Fake-adapter proof only, no real end-to-end success. No generator or deployment.

Unrelated files left unstaged: inherited Windows case-collision changes docs/Earl/index.html and docs/Jackson/index.html. No intentionally untracked task files. Queue scanned; no other assignment changed or claimed.

Deployment: persisted locally and pushed for draft review; no merge, installation, production write, runtime/state/process/task change or deployment. Receipt existence is verified on GitHub after push; final chat/issue reports pushed tip.

Proof/health: expected useful outcome is blocked/resolved/stale jobs skipped with durable canonical audit at every selection/mutation. Last successful real end-to-end proof: none. Failure/staleness: such work launches/mutates or audit is missing. Observer/observer-health integration remains unfinished. Recovery: preserve state/evidence, use approved hold, implement isolated atomic adapter proof before rollout. Brian is not assigned routine monitoring.

Recommended next action for ChatGPT: review the three substantive files on existing draft #381. Continue concrete authenticated canonical intake and isolated transactional versioned/idempotent claim/skip persistence, then approved runtime/pre-mutation wiring. Keep #381 draft; no rollout authorization requested. User/account action required: none now. Separate review/authorization remains required before production changes.
