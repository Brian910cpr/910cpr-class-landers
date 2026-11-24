# Issue 380 R22 — dispatch acknowledgement privacy review

State: PR_OPEN; BUILT, validated locally only. PR #381 remains draft/unmerged/undeployed. All six acceptance criteria remain open.

Execution acknowledged before edits: https://github.com/Brian910cpr/910cpr-class-landers/issues/380#issuecomment-6150675203 . Branch codex/issue380-r22-20261013 starts at d2f6bc15e9c1cbdc9560e6e4ab97e02fe8d69daa. Full issue/history, AGENTS.md, handoff/design/proof gates read. Original checkout lacks current handoff protocol; current PR checkout supplies it. Queue scanned; #371/#372 and all assignments preserved. No competing deep stream started.

## Finding and repair
The owner-intake publisher already allowlists successful responses; dispatchDecision instead spread the entire RPC result. Unexpected database fields could therefore be forwarded to the owner client, and arbitrary reason/version strings could receive committed=true. Replaced spread with seven explicit fields, restricted reasons to current SQL vocabulary, and validated positive canonical decimal PostgreSQL bigint version range. Unknown/malformed acknowledgement returns private generic 503 with committed=false and can_execute=false. That false means not confirmed by this gateway, not proof of database rollback; retain same request ID for uncertain retries. Known responses remain compatible. No SQL or authentication change.

## Security/policy limits
Owner assertion remains an assertion, not authoritative-source verification. Trusted service-role direct DML/provenance and policy windows still require full review. This closes a concrete proxy disclosure gap, not mandatory gateway enforcement or external side-effect fencing. Reasons intentionally fail closed when SQL vocabulary changes until coordinated review. Owner-only authorization and server-only key remain covered by existing actual-route tests. No evidence attachment is claimed.

Supabase skill applied. Web fetch failed; local Invoke-WebRequest fetched current changelog and edge auth documentation at https://supabase.com/changelog.md and https://supabase.com/docs/guides/functions/auth.md . TLS deprecation notice reviewed; this change modifies no TLS/SDK/auth configuration. No live advisors run because no schema or deployment change.

## Changed source/test paths
- supabase/functions/production-board/dispatch-decision.mjs
- tests/production_dispatch_decision.test.mjs
- data/audit/issue380_dispatch_ack_privacy_20261013.md
- Codex_Reply_Issue380_20261013_R22.md (separate receipt commit)

## Exact validation
Commands:
```
node --test tests/production_intake_publication.test.mjs tests/production_dispatch_decision.test.mjs tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/live_dispatch_check.test.mjs tests/owner_access.test.mjs
node --check supabase/functions/production-board/dispatch-decision.mjs
git diff --check
```
Output summary: tests 77; suites 0; pass 77; fail 0; cancelled 0; skipped 0; todo 0. Syntax/diff checks exit 0. Two new tests exercise extra private fields, unknown/private reason, malformed decimal and overflow versions, and max valid bigint. Actual-route tests execute stripped TypeScript with fake transport; no live database/production query performed. SQL unchanged, so prior PostgreSQL proof was reused rather than rerun. Known unrelated baseline board Python auth failures not rerun.

## Persistent proof and continuation
Expected outcome: resolved/blocked/stale work is suppressed before launch and mutation. BUILT only; no production end-to-end proof or deployed observer/observer-health evidence. Current success evidence is local proxy/auth tests on 2026-10-13. Expected cadence remains each selection and side effect; missing canonical source/version, uncertain acknowledgement and absent fence must deny execution. Recovery: refresh canonical state, retain request identity, investigate conflicts. Brian is not assigned routine monitoring or account action.

Next engineering: finish policy/trusted-role review, authoritative collector and installed no-launch consumer, atomic external pre-side-effect fence and race proof; then private evidence/resolution/history/count UI with upload/browser proof. Production integration remains gated by those unfinished engineering items and separate review/authorization, not missing owner credentials. SQL remains outside migrations. No migration, installed runtime/state/task change, generator, merge or deployment performed.

## Hygiene
Windows case-collision dirt docs/Earl/index.html and docs/Jackson/index.html was present after worktree creation and excluded. Original E:/GitHub/910cpr-class-landers unrelated dirt untouched. Explicit paths staged only. Reuse existing #381 head by ordinary fast-forward push. No ops/handoff/next_task.md used; no Codex_Read file created or renamed.
