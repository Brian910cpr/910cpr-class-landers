# Codex reply — Issue #327

Timestamp: 2026-10-14T20:48:34.7615570-04:00
Assignment: https://github.com/Brian910cpr/910cpr-class-landers/issues/327
Branch: codex/issue327-history-20261014
Substantive commit SHA: 92491d37d884593309e184b5cf403711757633d8
PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/401 (draft)
State: PR_OPEN; production rollout BLOCKED. Persistent-system evidence: BUILT.

## Findings and work performed

Acknowledged actual execution on #327 before implementation. Read complete issue (no prior comments), checkout and current AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design ethos, proof standard, #325 and related PR state. Primary checkout E:/GitHub/910cpr-class-landers had extensive unrelated dirty work and an older branch without the handoff protocol; current protocol was read from origin/main. Isolated worktree E:/GitHub/910cpr-issue327-20261014 preserves that work.

Root cause: September 29 security lockdown ea88f2ec46f9d9b5e5825118afaa054a366db595 removed the public prototype that the old loader scraped/evaluated. Current loader deliberately empties history. Archived prototype has 69 summaries; existing canonical database contains 80 NHCSO historical sessions, all with organization/course relationships and unique external IDs, no overlap with the seven live classes. Dates: 2022-02-16 to 2026-08-19. No private historical values were republished.

Added organization/source/scope-restricted authenticated read-only history action, 40-record pagination, local timezone formatting, count/error/retry status, older-record browsing and live/history duplicate suppression. Selection displays a read-only summary without changing the editable form. Existing lifecycle/finalize/unlock functions are preserved; no per-class requests. This reuses canonical imported truth and removes the old public prototype dependency.

## Exact intentional files

- docs/corp/nhcso/index.html
- supabase/functions/nhcso-workspace/index.ts
- supabase/functions/nhcso-workspace/history.js
- tests/nhcso_history.test.cjs
- tests/nhcso_history_browser.py
- data/audit/issue327_history_recovery_20261014.md
- Codex_Reply_Issue327_History_20261015T004834Z.md (this communication-only commit)

Primary audit and source/proof references: data/audit/issue327_history_recovery_20261014.md. Review especially history.js organization/source/scope projection, index.ts authorization placement, index.html authenticated loading/read-only selection, and both new tests. No audit JSON with private rows was created; aggregate SQL results and exact command outcomes are in the audit.

## Validation

- node --test tests/nhcso_history.test.cjs: 6 passed, 0 failed; includes inline script syntax.
- python -B tests/nhcso_history_browser.py: PASS; 80 synthetic cards, offsets [0,40], rail client height 396 / scroll height 8508 / overflow auto, last record reachable, no browser page errors or write actions.
- npx --yes deno check --check-js supabase/functions/nhcso-workspace/history.js: PASS.
- node --check supabase/functions/nhcso-workspace/history.js: PASS.
- Browser test Python AST syntax: PASS.
- git diff --check: PASS.
- Remote authenticated SQL: read-only canonical source/schema/aggregate verification; no database writes.

Known unrelated failures: roster workflow suite 7/8; the old finalize prompt assertion fails at baseline and is already repaired in open PR #324. Full Edge Function Deno check has five errors, all reproduced against unmodified baseline 8e08de5ca5eb2525bf578bd7ace77971d39efd5b: two Postgrest-builder .catch errors and three instructor relation type errors. See exact baseline/branch locations and commands in the audit. These are not fixed here because the lifecycle/backend stream must be preserved; the .catch failures may also be runtime defects in existing audit writes.

## Delivery and remaining proof

Persisted locally, committed and pushed to GitHub; draft PR #401 open. Not merged, not deployed, not live-verified. No generator, migration, backfill, source import, paid environment or database write. CSS/JS external assets are unchanged; changed logic is inline HTML. #326 is merged; #324 is left intact. #372 remains draft, unmerged and undeployed.

Exact rollout blockers: full existing endpoint validation still fails with the five baseline errors; authenticated real endpoint/browser proof has not run. Supabase branch inventory is empty; no isolated preview was created. No missing credentials or lack of historical data is alleged. Do not call restoration PROVEN, MONITORED or HEALTHY. Last successful restoration end-to-end proof: none in production; synthetic rendered proof succeeded during this dispatch.

Success contract: authorized browser obtains 80 unique historical summaries across stable pages, reaches the oldest record, cannot edit through history selection, and preserves live lifecycle behavior; unauthorized requests fail. Expected cadence is sign-in and manual load-older. Visible count/error/retry observes immediate failures, with local automated tests as diagnostics. No deployed recurring end-to-end observer/observer-health proof exists; routine monitoring remains an unresolved workspace dependency rather than Brian's assigned duty.

Next concrete action for ChatGPT: review draft #401 and the exact audit paths, coordinate baseline backend errors with the owning lifecycle/backend workstream, then run authorized isolated endpoint/browser proof. Deploy only the NHCSO function before publishing this HTML; verify authenticated production browsing and unchanged live lifecycle behavior. Do not merge/deploy #372. Account-level action is not requested now; staging/session choices may require account authorization if no existing authorized route is available.

## Preserved work and queue

All open [CODEX] issues were scanned. No competing deep stream or duplicate #327 PR existed; #324 is a separate #325 lifecycle workstream. No unassigned safe independent backend quick win was selected because existing issue branches already cover the candidate backend items. This issue's backend work advanced without waiting on its lifecycle neighbor. Primary dirty files/receipts/caches remain untouched. Unrelated docs/Earl/index.html and docs/Jackson/index.html appeared dirty in the isolated worktree and were deliberately left unstaged/uncommitted. No cleanup, reset, rebase, or changes to ops/handoff/next_task.md.
