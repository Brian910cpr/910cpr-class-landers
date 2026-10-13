# Issue #371 — task/resume transactional boundary

Timestamp: 20261013T222344Z (UTC)
Work-item state: IN_PROGRESS / PR_OPEN
Branch: codex/issue371-task-resume-20261013
Existing PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/372
Substantive commit: d8846f943cbe39aaca312441a6f00b9c2dbefc98
Receipt commit: discoverable as the pushed tip containing this file (avoids self-referential SHA).

## Execution and scope
Read the full issue body/comments, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md before implementation. Execution acknowledgment: https://github.com/Brian910cpr/910cpr-class-landers/issues/371#issuecomment-6156430013 . Reused draft PR372; no duplicate PR, merge, deployment, production write, origin widening, installation, generator, assignment or monitor changes. No third-party comment was used as new owner authorization. Queue titles were scanned; existing unrelated assignments were preserved.

E: primary checkout has unrelated dirty files and previously documented broken-ref trouble; it lacks CODEX_HANDOFF_PROTOCOL.md at its current checkout. Healthy D: repository fetched the existing PR branch and supplied isolated E:/GitHub/910cpr-issue371-task-resume-20261013. Original E:/D: dirty work preserved. Unrelated docs/Earl/index.html and docs/Jackson/index.html changes appeared in the isolated worktree; neither staged nor committed. No cleanup/reset/restore performed. No intentional untracked application artifacts added. Temporary acknowledgment/comment reads outside the repo were not committed.

## Exact intended changed files
- supabase/migrations/20261010210607_customer_interaction_storage.sql
- supabase/migrations/20261010212019_customer_follow_up_task_mutations.sql
- tests/customer_interruptions_sql.test.mjs
- docs/CUSTOMER_INTERACTION_PATH_A_SAFETY.md
- Codex_Reply_Issue371_TaskResume_20261013T222344Z_R1.md

These migrations remain pending/unapplied in the last read-only production audit at data/audit/issue371_patha_metadata_20261012.json; no new live catalog assertion was made. If applied elsewhere, prepare a separate corrective migration instead of replaying history.

## Full primary increment report
## Task/resume consistency increment — 2026-10-13

State: BUILT / locally validated / PR_OPEN. Gate stays OFF. No production operation or deployment.

The browser's paginated follow-up read and resume RPC were separate transactions. An obligation created between them could leave a resolved call with an outstanding task. This increment keeps the existing canonical task/interaction model and immutable provenance; it adds no Enrollware dependency or new customer workflow. It preserves the mature lifecycle distinction between recording a promise and completing it. The 910CPR advantage is retaining promised work while returning to an interrupted customer case.

Pending migration changes (same three-file rollout, no new migration):
- `supabase/migrations/20261010210607_customer_interaction_storage.sql`: after the interaction advisory lock, refuse `resolved` when any linked task is proposed, pending or snoozed; SQLSTATE `40001` maps to existing HTTP 409 conflict handling. Atomic resume invokes this save inside the two-record transaction, so failure also rolls back the previous-case save and audit.
- `supabase/migrations/20261010212019_customer_follow_up_task_mutations.sql`: after exact-request receipt lookup, acquire the SAME interaction advisory lock (hash seed 1) before link validation and task lock. Creating/reopening a noncomplete task against a resolved interaction conflicts. Explicitly reopen the interaction before retrying the retained task. Completion still requires immutable audit evidence. Earlier successful request receipts remain replayable even after later resolution.

The lock order is request receipt -> interaction(s) -> task; switches retain sorted interaction locking. Under the existing PostgREST READ COMMITTED transaction model, task creation/disposition and resolution serialize on the same interaction. Task-first forces a fresh follow_up_due disposition or evidenced completion. Resolution-first rejects late obligations without consuming the request or discarding the client draft. Direct privileged table writes are outside this RPC guarantee and must not become an alternate application write path. Higher isolation/snapshot modes are not validated by this increment.

`tests/customer_interruptions_sql.test.mjs` adds three SQL regressions covering all outstanding statuses, rollback of both saved records/audits, both serialized orderings, explicit reopening, original receipt retries, and direct interaction-save protection. Full existing CRM/auth suite: 71 passed, 0 failed. Targeted SQL suite: 10 passed. Node syntax and git diff checks passed. Tests compile and execute the pending SQL in local PGlite, including service-role permission checks.

Evidence limit: PGlite is a single-session engine. These tests prove durable sequential orderings and rollback, NOT simultaneous separate-session lock waiting/deadlock behavior or a real owner-session/Edge/PostgREST cycle. Before clearing the transactional concurrency gate, run two independent READ COMMITTED PostgreSQL sessions: hold task create/update uncommitted while resume waits, then commit and require conflict/retained obligations; reverse the order and require late task rejection; repeat completion/reopening and two-task writes. Verify no deadlocks, duplicate events or resolved interaction with outstanding tasks, including exact-request retries. The test environment must be authorized; this dispatch made no remote schema changes.

Release gates remain: actual two-session concurrency proof, task status controls/saved-only NEXT, real owner-session UI/API/database recovery/conflict proof, usable backup/restore evidence, then separate explicit production GO. No owner action is needed for further safe local code/test preparation. Existing Studio conflict/export/reload handling remains in place; no UI assets changed in this increment. Never reinterpret this report as rollout authorization.

References checked: https://www.postgresql.org/docs/current/explicit-locking.html and https://supabase.com/changelog.md (retrieved via PowerShell after the browser tool rejected markdown content type). No new SDK/platform feature is introduced.


## Reproducible validation
Use the existing cached PGlite module (no dependency installation):

    $env:PGLITE_MODULE='file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js'
    $tests = @(Get-ChildItem tests/customer_interaction*.test.mjs | ForEach-Object FullName) + @((Resolve-Path tests/customer_interruptions_sql.test.mjs).Path,(Resolve-Path tests/admin_auth.test.mjs).Path)
    node --experimental-strip-types --test @tests
    node --check tests/customer_interruptions_sql.test.mjs
    git diff --check

Exact aggregate output:

    1..71
    # tests 71
    # suites 0
    # pass 71
    # fail 0
    # cancelled 0
    # skipped 0
    # todo 0

Focused test: node --experimental-strip-types --test tests/customer_interruptions_sql.test.mjs => 10 passed / 0 failed. SQL syntax validated by executing all three migrations in PGlite; Node syntax and git diff checks exit 0. No browser tests rerun because no browser assets changed. No known test failures.

## Persistent-system proof contract and blockers
Evidence level: BUILT, validated locally with synthetic data. Last real owner-session end-to-end CRM proof: none established. Expected useful outcome: saved customer obligation survives interruption/resume/reload and resolved work cannot silently retain uncompleted obligations. Window: per owner save/resume, not a scheduled worker. Local success evidence: transaction results and immutable event assertions in the named test; not live operational health.

Production release blocked by: simultaneous independent-session locking evidence absent (PGlite single-session cannot supply it); task status/saved-only NEXT controls unfinished; genuine owner-session UI/API/database recovery proof absent; usable backup/restore evidence absent. Earlier no-isolated-preview gate was superseded by owner Path A; Docker/WSL/Synology are not prerequisites and were not retried. Separate explicit rollout GO is still required after gates pass. No account action requested for safe local continuation.

Observer: local test runner for this increment; no deployed CRM outcome/staleness observer or observer-health proof. No MONITORED/HEALTHY claim; owner must not become routine observer. Failure: any unresolved obligation on a resolved interaction, missing request/event, conflict that discards a draft, or failure to reload confirmed state. Recovery: leave gate OFF, retain/export drafts, review fresh server records and reconcile explicitly; do not drop tables/audit or generate replacement requests after uncertain commits. Account-level escalation applies only to authorized target/backup access or final rollout; ordinary code/test fixes remain Codex work.

## Next exact action
Review substantive commit d8846f943cbe39aaca312441a6f00b9c2dbefc98, especially lock acquisition order and both rejection predicates. Prepare/run the two-independent-session READ COMMITTED experiment specified in the primary report before declaring concurrency PROVEN; finish task status controls and saved-only NEXT in this same PR. Then genuine owner-session and restorable-backup proof. Keep PR372 draft/unmerged/undeployed and flag OFF. Do not produce another unchanged blocker-only receipt while safe backend/code/test work remains.
