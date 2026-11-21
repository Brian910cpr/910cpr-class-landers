# Issue #371 — evidenced task disposition preparation

- Timestamp: 2026-10-14T09:25:07.8694331Z (UTC)
- Branch: codex/issue371-taskstatus-20261014
- Existing draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/372
- Substantive commit: e9cec3c76bfcb79e5e07f33eba423b6468050cd6
- Work-item state: IN_PROGRESS / PR_OPEN
- Evidence level: BUILT, validated locally with synthetic data; no genuine owner-session end-to-end proof.

## Execution and authority
Read issue title/body/comments and repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Actual execution acknowledged before implementation at https://github.com/Brian910cpr/910cpr-class-landers/issues/371#issuecomment-6165129697 . Continued existing stream from 0f319cc4d81768f72c602cee55eaea88039f7cb2 in separate named worktree E:/GitHub/910cpr-issue371-taskstatus-20261014. No assignment, launcher or monitor changes. Owner instructions govern; third-party review comments were not treated as authorization.

## Findings and work performed
Existing capture supports promised tasks but status controls/NEXT are unfinished. Added createFollowUpTaskDisposition to the existing task module, reusing canonical stored task identity/linkage/source evidence/version and existing immutable retry coordinator. Status changes require explicit owner evidence; completion also supplies completion_evidence; snooze requires a valid explicit due time. Invalid/incomplete/no-op dispositions fail before any request. Reopening records evidence without carrying a completion claim. Mutation drafts are cloned and keep stale-version conflicts subject to server authority. Source evidence remains immutable; disposition_evidence lives in existing immutable task event input. No reminder scheduling or external action is claimed.

This extends the existing native LanderWare task lifecycle, rather than introducing another task catalog or Enrollware dependency. Existing case/interaction/provenance separation is preserved. Helper is prepared but not wired to visible status controls; no HTML/import URL changes or public generated output changes were required. Runtime Studio behavior is unchanged.

## Exact intended files
- docs/admin/customer-interaction-task.mjs
- tests/customer_interaction_task.test.mjs
- Codex_Reply_Issue371_TaskDisposition_20261014T_R1.md

## Validation and exact relevant output
Reused cached PGlite dependency; no installation:
PGLITE_MODULE=file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js

Command: node --experimental-strip-types --test tests/customer_interaction_task.test.mjs tests/customer_interruptions_sql.test.mjs tests/customer_interaction_client.test.mjs
Result: tests 24; pass 24; fail 0; skipped 0.

New tests cover versioned status-only input, clone protection, explicit completion/reopen evidence, no-op rejection, incomplete stored records and snooze due validation. Existing composed coordinator/transport/actual handler/real local SQL test now uses the new helper for completion, proving lost-response exact retry, durable audit evidence, stale/duplicate rejection. Existing task/resume transaction and privacy regressions pass. PGlite is single-session synthetic evidence, not simultaneous lock waiting proof.

node --check docs/admin/customer-interaction-task.mjs: passed.
node --check tests/customer_interaction_task.test.mjs: passed.
git diff --check: passed (line-ending normalization warnings only).
No browser tests this round: helper is not wired to UI; browser behavior unchanged. No generator invoked.

## Persistence, exclusions and deployment
Intended code and this receipt committed/pushed on named review branch and existing PR372 head via fast-forward only. Receipt push is verified by GitHub contents API before dispatch exits. No merge, production write, function/schema deployment, gate enablement, CORS expansion or installation. PR remains draft; gate OFF. Platform-triggered branch CI/preview is not claimed as operational proof.
Unrelated E: checkout changes/untracked files preserved. Isolated checkout has existing Windows case-collision changes docs/Earl/index.html and docs/Jackson/index.html; explicitly excluded from staging. No cleanup/reset/restore. Queue title sweep performed; no competing deep workstream started or existing assignments altered.

## Exact blockers and proof boundary
Independent-session concurrency experiment remains blocked on absent authorized local PostgreSQL runtime/client and psycopg 3, as documented by prior preflight in docs/CUSTOMER_INTERACTION_CONCURRENCY.md; not rerun or installed here. Genuine owner-session UI/API/database recovery and usable backup/restore evidence remain unproven. Prior local runtime/backup authorization constraints remain; no production fallback. No successful real end-to-end proof timestamp exists for this feature. Test invocation observes synthetic regressions on demand only; no deployed CRM observer or observer-health proof exists. Failed/uncertain receipts block navigation in the coordinator; recover through identical retry or retained-draft export/reload on conflict. Brian is not represented as a routine monitoring layer.

## Next concrete action / review handoff
Review the two exact source/test paths above and substantive commit. Continue same PR with task status controls using createFollowUpTaskDisposition, retained uncertain/conflict drafts, browser tests, asset version updates, and saved-only NEXT. No automatic Board completion or external action. Run the five independent-session scenarios only on authorized empty localhost PostgreSQL per docs/CUSTOMER_INTERACTION_CONCURRENCY.md. Then genuine owner-session and backup/restore proof, and separate explicit rollout GO. Do not merge/deploy PR372. No owner action required for safe code/test continuation; missing runtime/backup authorization must be resolved before those proof steps.
