# Brian's NOW dashboard · Issue 216

Timestamp: 2026-09-13T16:59:43.756Z
Branch: codex/brian-monitor-dashboard
Substantive commit: 8bb2e55fe91008a9a983fa8b7eb302cd591bd661
Work-item state: PR_OPEN
Persistent-system evidence: BUILT / partial CONNECTED

## What changed
Always-open owner page at /admin/now.html with DO THIS, Brian prompts, one-hour snooze, Eastern clock, full screen, real GitHub handoffs and acknowledgements, eCard reconciliation and eProduct queues, and direct record links. Shared Operations key, private data, explicit source timestamps and missing-source states. Canonical admin-key access and card deep links added to Production Board while preserving its previously deployed attention route.

Files: docs/admin/{now.html,now.css,now.js,admin-nav.js,production.html,production.js}; supabase/functions/{owner-dashboard/index.ts,owner-dashboard/core.mjs,production-board/index.ts}; supabase/migrations/20260913164411_brian_monitor_dashboard.sql; tests/owner_dashboard.test.mjs; ops/owner-dashboard/README.md.

## Evidence
- Production SQL: 2 classes / 13 recorded completions missing linked eCard evidence; 1 person / 1 eProduct; 4 next-seven-day permanent class records.
- These are reconciliation counts, not proof that AHA has not already issued cards.
- 5 behavioral tests pass: reserves/obligations, stale/incomplete input, account separation, invalid bills, owner-action selection.
- Actual page-script DOM checks pass: rendering, drill-through, snooze/restore, filtering, escaping and lock/late-request handling. Syntax and diff checks pass.
- Database RPC denies anon/authenticated roles and allows service_role. Finance table is RLS enabled, no public reader/writer.
- Edge functions deployed: owner-dashboard v2; production-board v4, preserving live v3 attention behavior absent in the prior repo source.
- Anonymous owner-dashboard HTTP request returns 401. Existing older code was not accepted by canonical Operations auth. No credential was changed.
- Static publication and authenticated browser proof are separate from backend deployment. Browser could not reach localhost preview. No accepted current owner credential is available in this session for signed-in browser verification.

## Remaining work
Financial source is not connected: no verified available-cash plus complete upcoming-obligation feed. Private snapshot contract and fail-closed recommendation logic are implemented, with no invented financial facts or payment execution. Connect the AM/PM finance source and preserve its Google Workspace recovery record.

Monitor cadence: operations 60 seconds, handoffs 5-minute cache; stale banner after 2 minutes without a successful read. Cash expires independently. Observer is the open page; independent supervisor health is not proven. Do not classify MONITORED/HEALTHY or claim live worker heartbeats from receipt activity.

## Next action
Publish the static page after checking the PR and verify its public HTML/CSS/JS. Complete authenticated browser verification using the current Operations admin key. Review exact remaining finance connection on issue #216; retain the work item until the requested financial prompt workflow is connected and proven.

User/account action: current owner authentication is needed for the signed-in verification; finance source access may require an account-level connection. No approval needed for further reversible repository fixes. Git CLI push lacked credentials; the branch was persisted through the connected GitHub API instead.

## Supervisor acknowledgment
Processed 2026-09-13. PR #217, merge commit, tests/evidence, deployment status, and remaining gaps were reviewed. R2 supersedes the publication-status portion of this receipt; issue #216 remains open for authenticated proof and the verified finance-source connection.