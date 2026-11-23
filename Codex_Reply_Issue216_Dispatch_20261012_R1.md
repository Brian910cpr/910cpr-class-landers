# Issue 216 dispatch — backend validation and remaining proof gates

- Assignment: Brian910cpr/910cpr-class-landers#216.
- Timestamp: 2026-10-12 (America/New_York, UTC-04:00).
- Branch: codex/issue216-proof-20261012.
- Substantive commit SHA: 69caf820e49afc6f69d40f99a5ef6d4f945b4a47. Receipt commit is the subsequent branch tip.
- Work-item state: BLOCKED for full dashboard acceptance; backend repair committed for review.
- Evidence state: BUILT for this repair; existing dashboard partial CONNECTED. No new authenticated end-to-end proof, MONITORED or HEALTHY claim.

## Execution and findings
Read full issue #216 and owner comments, current AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md before implementation. Execution acknowledged on originating issue: https://github.com/Brian910cpr/910cpr-class-landers/issues/216#issuecomment-6126190525.

Original E:/GitHub/910cpr-class-landers has unrelated dirty work and an old branch without the handoff protocol. Fetch failed with bad object 6e61cabca5981d1389e52c60d95424d9893bb50f and corrupt refs/remotes/origin/codex/group-training-experience. Preserved everything; no cleanup, reset, merge, or repairs to that repository. Used a separate clean shallow clone at E:/GitHub/910cpr-issue216-20261012 and named branch. Windows case collisions left docs/Earl/index.html and docs/Jackson/index.html dirty in the new clone; neither is staged or committed.

Finance validation previously dereferenced null account/bill rows, throwing rather than returning unavailable. Added bounded row guards and rejected non-string/blank account identifiers. All recorded obligations still must validate before any payment prompts are returned. Corrected a stale regression expectation that contradicted the issue: a decision-lane card without Production Manager's structured owner_action is not a Brian task. No new catalog, financial source, auth mechanism, fulfillment lifecycle or Enrollware dependency was added.

## Exact files changed
- supabase/functions/owner-dashboard/core.mjs
- tests/owner_dashboard.test.mjs
- Codex_Reply_Issue216_Dispatch_20261012_R1.md

## Validation
- Before repair: node --test tests/owner_dashboard.test.mjs tests/owner-dashboard/core.test.mjs — 8 tests, 7 pass, 1 fails (obsolete board:2 expectation).
- After repair: same command — 9 tests, 9 pass, 0 fail.
- node --check supabase/functions/owner-dashboard/core.mjs — pass.
- node --check docs/admin/now.js — pass.
- git diff --check — pass.
- Read-only HTTPS verification: https://www.910cpr.com/admin/now.html and referenced /admin/now.css?v=20260923-2 and /admin/now.js?v=20260923-2 each HTTP 200; UTF-8 content equals checkout after CRLF normalization. Initial raw-byte comparisons differed due to checkout line endings. An intermediate verification used a malformed doubled /admin URL and returned 404; corrected urljoin verification passed for all three actual URLs.
- No generators, public rebuilds, private database writes, migrations or deployments run.

## Exact blockers and dependencies
1. Authenticated owner browser read and count drill-through remain unproven. No owner/admin/Supabase credential variables were available in this process; no accepted owner session was established or credentials changed. This is a proof limitation, not evidence of an auth outage. Next: use an authorized existing owner browser session/access flow and verify NOW source reads and drill-through end to end. Never paste credentials in issue/receipt.
2. Current bank available balances and complete upcoming obligations have no connected trusted ingester identified in repository scripts/ops/workflows. Existing private contract: ops/owner-dashboard/README.md, owner_dashboard_finance_snapshots. Need authorized current source and completeness/ownership evidence; do not seed schema examples as facts or invent cash prompts.
3. Independent observer health is unproven. Existing expected outcome: owner unlock -> current source reads -> actionable prompt -> exact roster/order/decision. Cadence: UI 60 seconds, GitHub/report cache 5 minutes; refresh stale condition after 2 minutes, cash source expires separately. Open browser tab is the present observer; clock/last-success stamp does not prove an independent observer. Last historical component proof recorded in #216 is September 23 RPC/asset verification, not authenticated browser end-to-end proof. Recovery: inspect bounded source/auth failures and reconnect authorized sources. Account-level escalation only for actual unavailable authorization or missing financial source authority.

## Queue/safety review
Swept open [CODEX] issues and open PRs. Existing #245 owner-action translation remains authoritative; do not manufacture Brian tasks from technical blockers. #215 shared auth has existing PR #218; #368 owns per-line fulfillment/document work. Preserved those assignments and did not start competing implementations. Draft #372 remains open, draft, unmerged and undeployed; no changes to its branch. Other backend work has existing active streams and gates; the independent finance validation repair above was completed without modifying them. No arbitrary third-party comments were used as owner authorization.

## Deployment and next action
Persisted locally, syntax/behavior validated locally; commit and receipt to be pushed on review branch. Not merged or deployed. Full #216 stays open. ChatGPT should review the two-file backend diff, then arrange authorized owner-session proof and identify the trusted balance/obligation source before claiming acceptance. Use existing PRs for their assignments; no draft #372 merge/deploy. Owner action may be needed only if authorized session/source access cannot be supplied through existing tools; no speculative Brian card added.
