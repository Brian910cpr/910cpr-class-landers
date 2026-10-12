# Issue 215 — production route discovery R3

Timestamp: 2026-10-12T16:12:25-04:00
Branch: codex/issue215-route-discovery-20261012
Base commit: d5887a57f5a341fa3bd9bdb77dc0bce1cca90a41
Existing substantive implementation: fe19a34598c43ade4a3967fb43056e760cbff36d
State: BLOCKED for coordinated production migration; diagnostic checkpoint complete.
Evidence level: BUILT for remembered-owner Worker implementation, validated locally; no new production end-to-end proof.
Receipt commit: discoverable as the pushed branch tip and reported with full SHA on issue #215 and in the dispatch response (avoids self-referential commit SHA).

## Execution and preservation

Read full issue body and all comments, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Originating execution acknowledgement: https://github.com/Brian910cpr/910cpr-class-landers/issues/215#issuecomment-6131807246 . Owner updates require remembered private access; withdrawn public-access instructions remain withdrawn. Third-party review comments were used only as evidence/context.

Preserved original E:\GitHub\910cpr-class-landers dirty work and corrupt Git references. Its fetch failed with bad object 6e61cabca5981d1389e52c60d95424d9893bb50f and bad refs/remotes/origin/codex/group-training-experience; no repair/cleanup attempted. Preserved dirty E:\GitHub\910cpr-issue215-worker-session-20261012. Fetched its remote branch successfully and created isolated named worktree E:\GitHub\910cpr-issue215-route-discovery-20261012 from FETCH_HEAD. Windows case collisions leave docs/Earl/index.html and docs/Jackson/index.html dirty here; neither staged. No generators, cleanup, merges, rebases, secret reads/changes, scheduling edits or deployment.

Scanned open CODEX queue and open PRs. Existing dashboard #216 / PR #388, documents #219 / PR #389, registration #367 and Studio #371 streams retained; no competing deep implementation or safe unassigned independent quick win selected from that scan. Existing issue215 Worker branch has no PR; no duplicate PR created. PR #372 remains draft, untouched, unmerged and undeployed. No ops/handoff/next_task.md used.

## New production evidence — remote, read-only

Cloudflare connector GET /accounts and GET /zones?name=910cpr.com both returned 200. One accessible account and one matching zone, each complete single-page result:
- Account 9acb24ab8037cc5abe5518f7758455fd.
- Zone dafc32f545bccb5fae2ff6f94cec92df, active 910cpr.com, owned by that account.

GET /zones/dafc32f545bccb5fae2ff6f94cec92df/workers/routes returned 200 with 11 routes. Relevant route:
- ID 468e5a5b9a224dcca82139e88a4797cf
- pattern schedule.910cpr.com/*
- script free-time-offer-worker
- request_limit_fail_open false
No separate /admin/finance/* route exists in the returned zone routes.

GET /accounts/9acb24ab8037cc5abe5518f7758455fd/workers/domains returned 200. schedule.910cpr.com is an enabled production custom domain for free-time-offer-worker, ID dde0f7b0b53f37aa2ac08dd8d9e6e3157e9d3eef. Both route and custom-domain evidence identify the same target.

GET /accounts/9acb24ab8037cc5abe5518f7758455fd/workers/scripts returned 200; 15 scripts, no landerware-financial-worker. Existing free-time-offer-worker modified_on: 2026-10-07T01:48:10.327455Z.

GET its /settings returned 200, compatibility_date 2026-06-05. Binding names/types only inspected/reported; no secret values copied:
- HOT_SYNC_ADMIN_KEY secret_text; HOT_SYNC_D1 d1; LANDERWARE_INBOX r2_bucket.
- GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN, GOOGLE_ROUTES_API_KEY, TRAVEL_CALENDAR_ID, TRAVEL_SYNC_WEBHOOK_SECRET, VOICE_SEARCH_BEARER_TOKEN: secret_text.
- ALLOW_PUBLIC_CREATION, CREATION_ENABLED, DRY_RUN, TRAVEL_EVENT_SYNC_ENABLED, TRAVEL_ROUTE_MARGIN_MINUTES: plain_text (values omitted).
- No STRIPE_SECRET_KEY and no service binding.

GET deployed script returned 200, multipart source string length 46606. Source inspection returned only nonsecret markers: one free-time-offer-worker.js module, handleAdminApi, generic /admin/ prefix gate, Hot Sync GET/POST, inbox GET/POST, and main dispatch to handleAdminApi. No /admin/finance string, handleFinanceApi, or X-LanderWare-Owner-Session marker. Raw source is not committed or printed into this receipt.

Fresh anonymous remote GETs:
- https://schedule.910cpr.com/admin/finance/invoices -> 401
- https://schedule.910cpr.com/admin/hot-sync/health -> 401
Both bodies exactly {"error":"Authentication failed.","code":"authentication_failed"}; Cache-Control: no-store, private.
These demonstrate anonymous denial only. Finance's 401 comes from the generic /admin/ handler, not evidence of a Finance handler or functioning invoice workflow. No authenticated request or financial write performed.

## Diagnosis and exact remaining gate

The prior instruction to locate the existing Finance route is now answered: the production URL is owned by free-time-offer-worker in the accessible account, and no separate Finance service is installed there. wrangler.finance.toml describes an absent target and absent specific route. Current evidence does NOT establish that Finance lives in another account, and an account-access request is not justified by this discovery alone.

Do not deploy worker/finance-worker.js over free-time-offer-worker: it would replace scheduling, offers, Hot Sync and inbox with a Finance-only entrypoint. Do not blindly deploy wrangler.finance.toml: that would create the expressly prohibited duplicate/new Worker and introduces missing Stripe/binding requirements. Existing deployed script also differs from the reviewed session-enabled source; remote bindings/settings must be preserved in any approved update.

Exact blocker: no existing deployed Finance handler/target or Stripe binding was found at the configured production URL. Safe coordinated cutover needs a reviewed hosting decision and approved existing Stripe credential binding source, without reading/revealing/copying secrets in chat. Either locate durable evidence of an existing Finance installation elsewhere, or have the owner authorize deliberate installation/integration into the confirmed existing service. Then validate packaging and routing, deploy only reviewed backend changes with remote configuration retained, verify accepted/revoked sessions and anonymous/corporate denials, and only afterward activate browser helper session forwarding. No unchanged failing Wrangler account/token attempt was repeated; historical closed #140 is not reused as blocker.

## Local validation

node --test tests/worker_owner_session.test.mjs tests/finance_auth_boundary.test.mjs tests/admin_auth.test.mjs tests/owner_access.test.mjs tests/owner_access_ui.test.mjs tests/admin_api.test.mjs
Results: tests 48; suites 0; pass 48; fail 0; cancelled 0; skipped 0; todo 0; duration_ms 5265.3882.
node --check passed for worker/owner-session-auth.js, worker/admin-api.js, worker/finance-worker.js.
Tests are deterministic local mocks, not deployed Worker/authenticated-browser proof. No code changed in this diagnostic checkpoint; prior R2 CI evidence retained rather than represented as new CI. Receipt whitespace/scope checked before commit.

## Changed files and publication

Only Codex_Reply_Issue215_20261012_RouteDiscovery_R3.md intentionally changed. Committed and pushed on the named diagnostic branch; GitHub exact-commit receipt readback and SHA reported on originating issue and in final response. No application changes, merge, manual preview build or production deployment. Original unrelated dirty files remain uncommitted.

Review paths: wrangler.finance.toml; wrangler.toml; worker/free-time-offer-worker.js; worker/admin-api.js; worker/finance-worker.js; worker/owner-session-auth.js; docs/admin/admin-auth.js; docs/admin/financial.html; tests/worker_owner_session.test.mjs; tests/finance_auth_boundary.test.mjs; Codex_Reply_Issue215_20261012_WorkerSessions_R2.md; Codex_Read_Issue215_WorkerSessions_20261012T1816Z_R2.md.

## Persistent proof and next action

Expected outcome: remembered private access across owner pages and Finance/Hot Sync/inbox, immediate revocation and lock clearing, automation/corporate separation. Last new proof: local 48-test boundary suite at receipt timestamp and current anonymous production denials. No new accepted-session end-to-end proof. Required future proof: accepted session loads real permitted data across pages; revoked session denied; lock/back-forward clears private state; authority outage fails closed without discarding unrelated valid access. Failure/staleness: denied legitimate remembered session, unavailable authority, restored stale private UI, or absent Finance route. Production cadence, observer and observer-health evidence remain unproven; no MONITORED/HEALTHY claim. Recovery: reconcile confirmed target/hosting/bindings then coordinated backend-first cutover. Brian must not be routine monitoring layer.

Next concrete supervisor action: review route discovery against the existing six-file implementation commit, resolve the Finance installation/binding decision on #215, then continue the same implementation stream. User-level decision is required only if no existing authorized Finance installation/credential binding source can be found. Another Cloudflare account grant is not currently proven necessary. Remaining separate issue scope: static-data/public-repository privacy, instructor identities/roles and operational monitoring.
