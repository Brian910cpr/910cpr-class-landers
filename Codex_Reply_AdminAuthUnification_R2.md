# Issue 215 R2: shared admin-auth prerequisite

- Assignment: Brian910cpr/910cpr-class-landers#215, independent eligible continuation during blocked #214.
- Timestamp: 2026-09-13T13:37:04-04:00 (America/New_York).
- State: **PR_OPEN / IN_PROGRESS**. Full #215 consolidation remains incomplete.
- Evidence level: **BUILT**, locally tested. Not an operational PROVEN/MONITORED/HEALTHY claim.
- Branch: `codex/issue-215-admin-auth-helper-r2`.
- Worktree: `E:\GitHub\910cpr-class-landers_codex_issue215_helper_r2`.
- Base commit: `c2ffef4a608007a54fd135d2f6efb1d7bc2dc2f8`, preserving #216's deployed dashboard.
- Implementation/report commit: `a7a4ffcc3313e84103134ff4c5866a8ebbd52c2e`.
- Draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/218 .
- This receipt is a separate commit referencing the implementation above; its pushed tip/content/blob readback is recorded on #215 after push.

## Findings and work performed

The R1 inventory established duplicated canonical owner credential plumbing, inconsistent denial handling and corporate-backed owner routes. Current main also contains #216's `now.html` monitor, its own page-local auth and updated Production Board; the old inventory must be refreshed before migration.

Implemented the independent shared helper prerequisite at `docs/admin/admin-auth.js`. It owns only `sessionStorage.hotSyncAdminKey` and `X-Hot-Sync-Admin-Key`, get/set/clear, nonsecret state hooks, explicitly declared API origins/path prefixes, current-session 401/403 invalidation, fail-closed storage errors, request abort/invalidation and guarded private rendering. A late response cannot restore a locked view or clear a replacement credential. Network/503 failures retain the key. Requests omit ambient cookies, reject corporate/bearer header mixing and refuse redirects. Duplicate script loading keeps one helper instance.

The helper is not loaded by any page yet and makes no requests on load. Pages migrated: **none**. No backend route, credential, corporate surface, page behavior or production configuration changed. This is a tested migration prerequisite, not satisfaction of #215 acceptance. No new owner decision blocks local coordinated migration; production parity/access and real browser proof remain separate gates.

## Exact changed files and review evidence

- `docs/admin/admin-auth.js` — 169-line shared helper.
- `tests/admin_auth.test.mjs` — 215-line synthetic behavior/race suite.
- `data/audit/admin_auth_helper_issue215_r2.md` — 62-line full implementation contract, evidence limits and coordinated adoption steps.
- Repository root `Codex_Reply_AdminAuthUnification_R2.md` — this receipt, separately committed.

Read the [full report at the implementation commit](https://github.com/Brian910cpr/910cpr-class-landers/blob/a7a4ffcc3313e84103134ff4c5866a8ebbd52c2e/data/audit/admin_auth_helper_issue215_r2.md), especially the synchronous `result.commit(render)` requirement, low-level ticket/redirect limitation, storage-remove failure semantics, server-authorization boundary and all remaining migration steps. The helper cannot make publicly served static data private, revoke an already accepted server mutation, or defend against arbitrary same-origin script execution.

Important prior evidence: `2e667eab30da6918985db594631f6c7b08a425c1:data/audit/admin_auth_review_issue215_r1.md` and `data/audit/admin_auth_inventory_issue215_r1.json`. Its JSON `source_commit`, `counts`, `files[].path`, `files[].storage`, `files[].token_lines`, `files[].direct_assets` and backend records describe the older snapshot; no JSON output was generated or overwritten here.

## Validation and exact results

```powershell
node --check docs/admin/admin-auth.js
node --check tests/admin_auth.test.mjs
node --test tests/admin_auth.test.mjs
git diff --cached --check
git diff c2ffef4a608007a54fd135d2f6efb1d7bc2dc2f8 HEAD --check
```

Both JavaScript syntax checks passed. Final test output:

```text
1..26
# tests 26
# suites 0
# pass 26
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 151.5256
```

The initial 23-case suite also passed; review added three cases and tightened reentrant hooks, delayed storage events and encoded-path checks. Final staged/base-to-head whitespace checks passed; exactly three substantive files (446 added lines) were committed before the receipt. No generated output, dependency install, operational data mutation or full build ran.

Coverage: two simulated page contexts sharing the same tab store; preserved corporate/draft storage; no fallback; canonical transport; origin/path containment; GET/POST 401/403; stale denial and success after lock; lock during JSON decode; deferred render guard; back/forward restoration; external storage changes; low-level status tickets; network/503 retention; caller cancellation; read/write/remove/getter storage failure; duplicate loads and reentrant lock callbacks. All fixture keys are synthetic.

These are local Node VM/Fetch API tests, not actual browser same-tab navigation, real XHR, backend authorization, GitHub CI, staging or production proof. Existing unrelated business suites were not rerun because existing application/backend files are unchanged. Known earlier R1 missing global CSS and #140 HTTP 401 remain unrelated; no attempt was made to conceal or repair them in this helper tranche.

## Exclusions, preservation and deployment

Explicitly excluded: `/corp/*`, Maxim, NHCSO, corporate authentication/session storage and the five NHCSO prototype pages identified in R1. Existing admin HTML/assets/backend files including #216's monitor remain unchanged. Original dirty LanderWare and ShiftCommander checkouts, four unpublished ShiftCommander commits and all earlier PRs/worktrees/receipts remain preserved. New worktree was clean before this work. Nothing is intentionally untracked on this branch after receipt commit.

One current worker, no second model launch, lock/lease/default changes, new timer or retired handoff. Active local model evidence: `gpt-6-astra` at `2026-09-13T17:25:29.766Z`, CLI `0.153.4`; local runtime fields, not provider attestation.

Status: code/report persisted locally, committed and pushed; draft PR #218 OPEN. Receipt is to be committed/pushed and all four file contents/blobs read back before exit. No merge, deployment, production authentication activation, service secret change, public-page migration, staffing change or member communication. No application URL or production-success claim is introduced by this prerequisite.

## Remaining work, proof and next action

Refresh the inventory to include #216, then coordinate migration of all true admin pages and canonical backend/CORS contracts. Remove owner-route corporate fallbacks without changing intentional corporate/public/redacted consumers. Adopt helper hooks on every read/write/detail/summary/upload path; clear private DOM/dialog state on lock and version all changed script references. Prefer fetch migration for XHR paths because ticket preparation cannot prohibit XHR redirects.

Verify the real one-unlock -> multiple same-tab admin pages -> one-lock -> denied/private-cleared behavior and back/forward recovery, alongside server authorization and business flows. Then verify the coordinated candidate with the approved live key privately, deploy through the established host and read back changed HTML/assets. #140's 2026-09-13T17:25:22Z verification still reports HTTP 401 after the owner secret update; exact deployed-secret parity requires private account-level reconciliation, not an alternate client key or weaker authentication. No unchanged failing account path was retried.

Expected success evidence is a real cross-page authenticated cycle with matching server denials and preserved corporate sessions. Last successful end-to-end timestamp for the consolidated system remains unknown. Checks are needed on migration/change and deployment. Repeated prompts, late private rendering, stale credential acceptance and crossed corporate/admin authority are failure conditions. Independent observer/heartbeat health is unproven; Brian must not be the routine monitor. Account-level action is required for production parity; ordinary local implementation remains eligible.

Exact next ChatGPT action: review draft PR #218 and the full report, retain #215 as IN_PROGRESS, and coordinate the complete client/server migration from current main under the existing authorization. Do not report the helper alone as admin unification or activate a partial corporate-backed route cutover. #214's required R12 blocked receipt is independently pushed at `52a7992d43c4215da11245215a5010c9eb798c0d`; that release gate has not changed.
