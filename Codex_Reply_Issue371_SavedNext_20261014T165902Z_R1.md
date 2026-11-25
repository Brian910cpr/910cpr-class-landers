# Issue #371 — saved disposition / NEXT

- Timestamp: 2026-10-14T16:59:02Z (UTC).
- Branch: codex/issue371-saved-next-20261014.
- Existing draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/372
- Base: 34bb5282cb17258c5680c263942fa11164f597f1.
- Substantive commit: c60a4f0ce0ec96b4fb89a71764e79b81a84e131b.
- State: IN_PROGRESS / PR_OPEN. Evidence: BUILT / validated locally with synthetic fixtures; no genuine operational end-to-end proof.

## Actual execution and preservation

Acknowledged before implementation: https://github.com/Brian910cpr/910cpr-class-landers/issues/371#issuecomment-6173613525 . Read full issue body/comments, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design ethos, proof standard, prior task-controls receipt and Path A safety findings. Owner Path A instructions control; third-party comments are not authorization. Open [CODEX] issue title sweep performed; retained one deep stream and existing assignments/monitors. No independent queue item was changed in this dispatch.

E:/GitHub/910cpr-class-landers has unrelated dirty pages/data/caches/receipts and broken refs: fetch failed with bad object refs/remotes/origin/codex/group-training-experience, missing object 6e61cabca5981d1389e52c60d95424d9893bb50f. Original checkout lacks root handoff protocol; read current PR version from healthy D: object storage. Preserved all original work untouched. A full separate clone completed at E:/GitHub/910cpr-issue371-next-20261014; implementation uses E:/GitHub/910cpr-issue371-next-shallow-20261014 on the named codex branch, a shallow clone of existing PR372 tip with Earl/Jackson case-collision paths excluded through sparse checkout. No cleanup, reset, restore, force push or unrelated staging. Separate completed clone is retained, not part of the pushed change.

## Findings and work

Finish/NEXT was disabled despite existing confirmed task/status controls. Added evidenced interaction disposition and explicit reopening, using the existing save RPC/audit. Only confirmed interaction and task edits allow submission. Matching canonical disposition receipt is required before automatic advancement. Uncertain writes freeze editing and retry identical request; conflicts retain evidence/document/request for private export and current-server review. Lock clears private evidence. Pending mixed task/disposition drafts are retained in export.

NEXT traverses fresh paginated interaction/task collections, detects cursor loops and ranks active call, due follow-up, then new/in-progress work with stable created_at/ID ordering. Paused, resolved, data/approval-blocked and future-snoozed-only work remains stored and manually accessible. Current interaction is excluded. Candidate is fetched again and eligibility rechecked before opening. Read failure retains confirmed disposition and offers read-only Retry NEXT without another write. Interrupted calls keep atomic Resume previous. Production Board remains read-only. No send, payment, refund, reschedule, eCard, AI policy promotion, task inference or reminder is connected. All module references versioned 20261014-next1; gate remains disabled.

Mature-object rationale reused from docs/CUSTOMER_INTERACTION_STORAGE.md: canonical case, interaction, person, task and immutable provenance remain separate. This extends native LanderWare lifecycle without Enrollware dependence. Selection is not a cross-collection transaction/reservation; another tab may change after selection, and writes remain version-fenced. Full scans need scale/retention evaluation. Unconfirmed fields remain memory-only and may be lost on process death. Resolved-with-outstanding-task invariant still belongs to existing SQL/RPC, not browser reads.

## Exact changed files and review targets

1. docs/admin/customer-interaction-checkpoint.mjs — saved-base/evidence-required disposition.
2. docs/admin/customer-interaction-client.mjs — canonical disposition acknowledgment validation before cache.
3. docs/admin/customer-interaction-next.mjs — paginated deterministic eligibility/selection.
4. docs/admin/customer-interaction-studio.mjs — controls, confirmed-only advancement, retry/conflict/export/privacy.
5. docs/admin/customer-learning.html — default-disabled disposition fields and asset reference.
6. tests/customer_interaction_next.test.mjs — five unit/composed SQL regressions.
7. tests/customer_interaction_studio_browser.py — four new Chromium workflows, explicit reopening assertion.
8. docs/CUSTOMER_INTERACTION_PATH_A_SAFETY.md — primary report, section Saved disposition / NEXT — 2026-10-14; full safety findings, proof contract, gates and next steps.
9. Codex_Reply_Issue371_SavedNext_20261014T165902Z_R1.md — this unique root receipt (separate communication commit).

Unchanged authoritative API/schema: supabase/functions/customer-interactions/handler.ts; supabase/migrations/20261010210607_customer_interaction_storage.sql; supabase/migrations/20261010211804_customer_interaction_interruptions.sql; supabase/migrations/20261010212019_customer_follow_up_task_mutations.sql. Independent-session experiment: docs/CUSTOMER_INTERACTION_CONCURRENCY.md.

## Validation and exact material output

Cached PGlite and Python Playwright/Chromium reused; no installation.

PGLITE_MODULE=file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js

node --experimental-strip-types --test tests/customer_interaction_next.test.mjs tests/customer_interaction_checkpoint.test.mjs tests/customer_interaction_client.test.mjs tests/customer_interaction_task.test.mjs tests/customer_interruptions_sql.test.mjs tests/admin_auth.test.mjs

# tests 48
# pass 48
# fail 0
# cancelled 0
# skipped 0
# duration_ms 2454.5005

Final affected NEXT suite after explicit reopening support:
node --experimental-strip-types --test tests/customer_interaction_next.test.mjs
# tests 5
# pass 5
# fail 0
# duration_ms 1451.2841

Final Chromium run:
python tests/customer_interaction_studio_browser.py
Ran 19 tests in 17.147s
OK

All four changed JavaScript modules: node --check passed. Python AST parse passed. git diff --check passed. No known outstanding test failure. Only Git LF/CRLF normalization warnings. No generator.

New local composition proves checkpoint -> client -> actual handler -> real SQL resolution, immutable raw notes/evidence, response loss, one committed version/audit and identical retry. Browser tests prove no advancement during uncertain response, selection-read retry without second write, conflict export/privacy clearing, confirmed-task guard, blocked queue retention and explicit reopening. Auth/API browser fixtures are synthetic; PGlite is single-session. None proves real owner-session/Edge/PostgREST runtime or simultaneous lock waiting/deadlocks.

Current Supabase changelog/security/TLS docs reviewed read-only; no custom API convention change required. References: https://supabase.com/changelog.md ; https://supabase.com/docs/guides/api/securing-your-api ; https://supabase.com/changelog/cbc-tls-ciphers-deprecated . No live production DB/data query or write.

## Persistence, deployment and remaining blockers

Persisted locally and committed on named review branch. Receipt will be pushed with eight substantive files to both named codex branch and existing PR372 head, fast-forward only; remote receipt presence must be verified before final response. No merge, deployment, production DB/API write, origin expansion, gate enablement, infrastructure installation, reboot, generator, assignment or monitor changes. Branch CI/preview is not production deployment or operational proof.

Production NO-GO remains: independent READ COMMITTED concurrency proof (prior preflight found no authorized empty loopback PostgreSQL/runtime/client or psycopg 3), genuine owner-session browser/Edge/PostgREST/database save/reload/resume/conflict/recovery proof, and usable backup/restore evidence. This dispatch did not retry missing runtime or install infrastructure. Path A supersedes Docker/WSL/Synology prerequisites; no repeated prerequisite request. Separate explicit rollout GO is required after safety gates pass. This dispatch explicitly prohibits merge/deploy. No Brian action required for safe code/test continuation.

Proof contract: on-demand disposition -> matching immutable evidence -> eligible stored NEXT without losing unconfirmed work. Last successful local synthetic proof: 2026-10-14, exact test commands above. Genuine operational E2E timestamp absent. Failure/staleness: missing/mismatched receipt, conflict, auth loss or incomplete reads; mutation/navigation freezes or selection retries without another write. Observer is on-demand local runners only; no deployed CRM outcome observer or observer-health proof exists. Recovery: identical retry after uncertainty, private retained-draft export/reload/server review after terminal conflict, read-only Retry NEXT after read failure. Brian is not represented as routine monitoring layer. No CONNECTED/PROVEN/MONITORED/HEALTHY claim.

## Exact next action for ChatGPT / same stream

Review substantive commit and eight exact files above, especially new receipt validation/selection and SQL composition. Continue existing PR372 through the documented independent-session concurrency experiment in an authorized empty local runtime, genuine owner-session integration/recovery evidence and usable backup/restore proof; keep gate OFF and draft unmerged/undeployed. Prepare exact production go/no-go only after evidence supports it. Broader asynchronous discovery, email/customer lookup and reminder milestones remain unfinished; this receipt does not narrow the original issue or claim CRM completion.
