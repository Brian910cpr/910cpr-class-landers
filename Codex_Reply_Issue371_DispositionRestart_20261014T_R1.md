# Issue #371 — saved disposition restart evidence

Timestamp: 2026-10-14 (UTC; exact commit time in Git).
Branch: codex/issue371-recovery-proof-20261014.
Existing draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/372
Base: f7c6a57b2218dc9c2ce4243af13b38c6165f2952.
Substantive commit: ce31d15dd8415df6f320af91d6240fc50bbb7d1e.
State: IN_PROGRESS / PR_OPEN. Persistent evidence: BUILT, locally validated synthetic SQL only.

## Execution and preservation

Acknowledged actual execution before implementation on #371:
https://github.com/Brian910cpr/910cpr-class-landers/issues/371#issuecomment-6176628313
Read issue body/comments and repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Path A remains controlling; third-party commentary is not owner authorization. Open CODEX issue title sweep performed; no independent quick win selected because this bounded test increment avoids conflicts with existing assignments. No assignments, monitors or launcher changed.

Preserved original E:/GitHub/910cpr-class-landers dirty pages, scheduling data, caches, receipts and runtime files. Original old checkout lacks handoff protocol; current PR version read in isolated worktree E:/GitHub/issue371-recovery-proof. Worktree creation produced existing Windows case-collision dirt in docs/Earl/index.html and docs/Jackson/index.html; these are intentionally unstaged and unchanged by this assignment. No reset, restore, cleanup, rebase or force push. Only explicit intended paths staged.

## Findings and concrete work

Saved-only NEXT already exists in the PR. Extended existing restart suite to verify durable saved resolution and immutable retry history across two orderly disk close/reopen cycles. Old creation/resolution responses remain replayable but cannot overwrite current reopened state. Changed actor/payload and stale writes fail. Late task creation fails without consuming its request; explicit evidenced reopening permits retry of that same task envelope. A new resolution with outstanding obligation fails after restart. Audit counts and anonymous/authenticated privacy denials checked. No application behavior or schema modified; canonical interaction/task/provenance remains native LanderWare, no new Enrollware dependency.

Exact changed files:
- tests/customer_interaction_restart.test.mjs — one new disk-backed regression.
- docs/CUSTOMER_INTERACTION_PATH_A_SAFETY.md — section Saved disposition restart regression — 2026-10-14 contains complete report/proof boundaries.
- Codex_Reply_Issue371_DispositionRestart_20261014T_R1.md — this receipt.

Relevant unchanged SQL: supabase/migrations/20261010210607_customer_interaction_storage.sql; supabase/migrations/20261010211804_customer_interaction_interruptions.sql; supabase/migrations/20261010212019_customer_follow_up_task_mutations.sql.

## Exact validation

Reused cached module, no installation:
PGLITE_MODULE=file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js

node --check tests/customer_interaction_restart.test.mjs
PASS

node --experimental-strip-types --test tests/customer_interaction_restart.test.mjs tests/customer_interaction_next.test.mjs tests/customer_interruptions_sql.test.mjs
# tests 18
# suites 0
# pass 18
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 16011.6105

git diff --check -- tests/customer_interaction_restart.test.mjs docs/CUSTOMER_INTERACTION_PATH_A_SAFETY.md
PASS (only LF/CRLF warnings during staging).

No known targeted test failure. No generator, browser/UI changes or public output changes; browser rerun not warranted for test-only increment. Windows case-collision dirt remains unstaged as above.

## Evidence, exact blockers and next action

Persisted locally and committed; receipt and substantive work to be pushed to named branch and existing PR372 head with normal fast-forward pushes, then receipt verified using GitHub contents API at pushed SHA. No merge, production deployment, DB/API writes, origin expansion, gate enablement or installation.

Remaining release gates: independent READ COMMITTED concurrency proof (prior preflight found no authorized empty loopback PostgreSQL/runtime/client or psycopg 3); genuine owner-session browser/Edge/PostgREST/database recovery/conflict proof; usable backup/restore evidence; separate explicit production rollout GO. This dispatch did not retry installations or remote deployment. Ordinary PGlite reopen is NOT backup/restore, abrupt power loss or simultaneous lock proof. Gate remains OFF; PR remains draft. Broader email/context/discovery/reminder milestones remain unfinished.

Proof contract: on-demand saved disposition and historical receipts preserve current state/audit after orderly reopen. Last successful local synthetic proof: 2026-10-14, commands/results above. No genuine operational E2E timestamp exists. Failure: receipt replay overwrites current truth, missing audit, wrong versions or unauthorized access. Observer: on-demand local test runner; no deployed CRM observer or independently proven observer health. Recovery: identical uncertain retry; conflict export and fresh current-server review. No routine health duty assigned to Brian, no CONNECTED/PROVEN/MONITORED/HEALTHY claim.

Next same-stream action: review ce31d15dd8415df6f320af91d6240fc50bbb7d1e and the exact test/report above. Complete documented concurrency experiment (docs/CUSTOMER_INTERACTION_CONCURRENCY.md) only in authorized empty runtime, and prepare verifiable owner-session and backup/recovery evidence under Path A. Do not treat more synthetic tests as clearing operational release gates. Keep #372 draft/unmerged/undeployed. No owner action required for this safe test increment; do not revive Docker/WSL/Synology prerequisites. Production execution still requires separate explicit GO after safety review.
