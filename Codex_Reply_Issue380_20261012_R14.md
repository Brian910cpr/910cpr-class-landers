# Issue 380 — R14

Timestamp: 2026-10-12 UTC (dispatch completed 2026-10-13 UTC).
Branch: `codex/issue380-r14-20261012`, pushed to existing PR #381 head `codex/issue380-manual-resolution-20261011`.
Substantive commit: `01921544008cefc4a6b52ba9d9e140631acbda93`.
State: IN_PROGRESS / PR_OPEN (draft). Persistent-system evidence: BUILT only.

Advanced canonical transactional storage instead of further advisory-only hardening. Additive SQL draft implements row versioning on all card updates, explicit canonical resolution, expected-version row lock, request-id serialization, exact idempotent replay/conflict, justified reopen, append-only service-role resolution events, and atomic card/event/activity writes. Backend authority is restricted to service role; owner authentication must still be implemented in proxy. Draft is outside migrations and has not been applied anywhere persistent.

Exact changed files:
- `data/audit/issue380_resolution_transaction_draft.sql`
- `tests/reconciliation/board-resolution.test.mjs`
- `data/audit/issue380_resolution_transaction_20261012.md`
- `Codex_Reply_Issue380_20261012_R14.md`

Full report: `data/audit/issue380_resolution_transaction_20261012.md`. SQL request fields: card UUID, expected bigint version, request UUID, proxy-bound actor, target state, explanation, source, completed_at. No attachment/evidence verification claim is stored.

Validation: ephemeral PGlite executes existing board migration plus new draft; 1 integration test passed (replay/conflict/stale write/reopen/version invalidation/event immutability/forced audit rollback/browser-role denial). Existing focused backend suite 60/60 passed. Node syntax and diff checks passed. Existing pinned local dependency installed without package changes. Single-connection engine does NOT prove multi-session lock contention or runtime pre-mutation fencing. No known new failures; broader baseline suite not rerun.

Persisted locally, committed and pushed for review only. No generator, migration deployment, production write, runtime/state/task/process changes, merge or deployment. #371 remains primary; #372 untouched/draft. Original dirty checkout preserved; case-collision dirt `docs/Earl/index.html`, `docs/Jackson/index.html` excluded. No temporary/runtime files staged; other assignments unchanged.

Remaining engineering gates (not an owner credential blocker): authenticated canonical intake/owner proxy, transactional claim/skip/lease audit and actual runtime fencing, multi-session concurrency proof, private evidence/storage/upload, coordinated UI/history/counts and browser tests. All six issue acceptance criteria remain open. Next reviewer action: review transaction draft/security and promote only through migration tooling with coordinated API readiness; continue typed canonical claim/skip integration. Keep #381 draft/unmerged/undeployed. No Brian/account action needed now.

Operational proof contract: expected skip before every launch/side effect with durable canonical reason. Last real end-to-end proof: none. Failure/staleness: resolved/blocked/stale work executes or audit is absent. Observer and observer health not integrated. Recovery: preserve state/evidence, use approved hold, finish transactional/runtime proof before rollout. Escalation: engineering and review, then separate production authorization. Automated monitoring remains unfinished; Brian is not an acceptable routine monitoring layer.
