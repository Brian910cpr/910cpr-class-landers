# Issue 215 — Finance hosting provenance R4

Timestamp: 2026-10-12T18:45:48.0643193-04:00
Branch: codex/issue215-finance-hosting-20261012
Base: 201bba36855c9ee3b26f4cc9285aad38df14d553
Substantive commit: 1b24d3fb4daa9190b4d4624a7408bf38f0224e9d
State: BLOCKED for coordinated production cutover; local backend safety checks advanced.
Persistent evidence: BUILT, validated locally. No new accepted-session production proof.
Receipt commit: pushed branch tip, reported with full SHA on #215 and dispatch response.

## Execution and preservation

Read full #215 body and all owner comments, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Execution acknowledged before implementation at https://github.com/Brian910cpr/910cpr-class-landers/issues/215#issuecomment-6134046010 . Remembered private access supersedes withdrawn anonymous access. No arbitrary third-party comment treated as authorization.

Created isolated E:\GitHub\910cpr-issue215-finance-hosting-20261012 from fetched existing route-discovery stream. Original E: checkout and existing worktrees untouched. New worktree has existing Windows case-collision modifications docs/Earl/index.html and docs/Jackson/index.html; neither staged. No generators, cleanup, secret value reads, auth retries, merge or deployment. PR #372 remains draft, unmerged and undeployed. No ops/handoff/next_task.md used. Existing PRs preserved; no competing PR created. Branch inherits older operational data and must not be published wholesale.

## Findings and exact blocker

Reused prior remote evidence in Codex_Read_Issue215_RouteDiscovery_20261012T2122Z_R3.md and Codex_Reply_Issue215_20261012_RouteDiscovery_R3.md; did not repeat remote discovery or pretend it is fresh. That evidence identifies free-time-offer-worker at schedule.910cpr.com, no Finance handler, no separate Finance Worker and no Stripe binding. Another-account access is not established as required.

New local provenance evidence:
- wrangler.finance.toml names landerware-financial-worker with worker/finance-worker.js and schedule.910cpr.com/admin/finance/*; comments require HOT_SYNC_ADMIN_KEY, STRIPE_SECRET_KEY and existing HOT_SYNC_D1. It contains no actual D1 binding declaration.
- git log --all --format='%H %s' -- wrangler.finance.toml returned bdb5e5b67bdb1a11ea9ba4311c99545fafc17510 (Retire expired public class pages) and c6861d9d718c01f7c4d83c887fa4fca2da65b859 (Refresh canonical LanderWare schedule and calendar feed). Both carry the same intended Finance config. Their presence proves source intent, not deployment.
- Searching .github/workflows found no Finance deployment workflow; git log --all for Finance workflow paths returned no entries. Available local refs are not exhaustive remote history.
- gh secret list names no STRIPE_SECRET_KEY repository Actions secret. Only names/timestamps were listed; values were neither available nor read. This does not establish absence in all environments or services.
- docs/admin/financial.html points to https://schedule.910cpr.com/admin/finance. worker/finance-api.js requires STRIPE_SECRET_KEY before dispatching invoice reads or outside-payment writes.

Exact blocker remains a reviewed Finance hosting/install decision and approved credential-binding source, not a generic auth failure. Do not replace the scheduling entrypoint with finance-worker.js, blindly create the absent Worker, or infer secret parity from names. No configured production Finance installation or approved binding source was established by the checked records.

Next decision on #215: authorize deliberate isolated Finance installation with the existing intended path/D1 requirements, or choose reviewed integration into the existing Worker; identify an approved server-side Stripe binding source through connected access. Do not ask Brian to paste credentials. Preserve remote bindings and validate package/routes before backend-first deployment. Then prove accepted/revoked owner sessions, anonymous/corporate denial and invoice read; activate browser forwarding only afterward. Financial writes require separate intentional test evidence and must not be used casually for sign-in proof.

## Work and validation

Changed tests/finance_auth_boundary.test.mjs only, plus this receipt. Added two regression tests:
1. Authorized invoice GET and outside-payment POST without Stripe binding return 503 stripe_unavailable, no-store, with no upstream request.
2. Anonymous invoice GET with missing Stripe configuration returns 401 authentication_failed and makes no upstream request, preserving authorization before configuration disclosure.

Command:
node --test tests/worker_owner_session.test.mjs tests/finance_auth_boundary.test.mjs tests/admin_auth.test.mjs tests/owner_access.test.mjs tests/owner_access_ui.test.mjs tests/admin_api.test.mjs
Exact summary: tests 50; suites 0; pass 50; fail 0; cancelled 0; skipped 0; todo 0; duration_ms 5264.3508.
node --check tests/finance_auth_boundary.test.mjs passed. git diff --check passed.
Local mocked evidence only; no Stripe call, financial mutation, application migration, browser test or production deployment. No new CI result claimed.

Review paths: tests/finance_auth_boundary.test.mjs; wrangler.finance.toml; wrangler.toml; worker/finance-worker.js; worker/finance-api.js; worker/owner-session-auth.js; docs/admin/admin-auth.js; docs/admin/financial.html; prior R2 and R3 receipts. Full audit findings relevant to this checkpoint are included above; no separate audit artifact generated.

## Queue and operational proof

Scanned open CODEX issues and open PRs. Active independent backend work already has PRs #388 (dashboard), #389 (documents), #387 (native checkout), #381 (execution preflight), #375/#374 (fleet); retained those assignments. No safe unassigned narrow backend quick win was established, so no competing deep stream started. Advanced this stream's independently testable missing-binding boundary while deployment is blocked.

Expected outcome: remembered private access across owner pages, Finance/Hot Sync/inbox with revocation and corporate/automation separation. Last successful accepted-session Finance end-to-end proof: none established. Current success evidence is the local 50-test suite; prior September owner proof covers other APIs only. Failure condition: missing handler/binding, legitimate-session denial, authority outage, or stale private UI restoration. Production cadence, observer and observer-health proof remain unestablished; no MONITORED or HEALTHY claim. Recovery is the hosting/binding decision followed by reviewed backend deployment and real session proof. Brian must not become routine monitoring layer.

Publication: intended test and unique root receipt committed/pushed only. Original unrelated dirty files preserved. No merge or production deployment. Issue remains open/BLOCKED for deployment. Owner/supervisor hosting authorization is needed only for the absent Finance installation; account grant is not yet justified. Remaining privacy, roles and monitoring requirements remain unchanged.

