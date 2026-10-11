# Issue 334 renewal evidence R14

Assignment: Brian910cpr/910cpr-class-landers#334.
Timestamp: 2026-10-11T17:50:00Z (UTC).
Branch: codex/issue334-health-check-20261011-r14.
Evidence/base commit: 0aa48ae2b5d2fcb785cd30f92e0ed7e613f5e7ba. Receipt commit is the pushed branch tip reported on the originating issue and final response.
Work-item state: BLOCKED for independent cloud proof; renewal investigation remains open.
Persistent evidence: PROVEN local containment with recurring boundary misses; overall HEALTHY not claimed.

## Execution and current evidence

Read full issue and comment history in bounded sections, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Execution acknowledged before implementation at https://github.com/Brian910cpr/910cpr-class-landers/issues/334#issuecomment-6111884923 . Accepted repairs #376/#377/#378 preserved.

New cache-busted live GET evidence for https://www.910cpr.com/data/block-selector-availability/bls.json:

- 2026-10-11T17:48:38.7772947Z: generatedAt 2026-10-11T13:33:48.563851-04:00, validUntil 2026-10-11T13:48:47.396735-04:00, expired false.
- 2026-10-11T17:48:49.3877717Z: identical generatedAt/validUntil, expired true.
- Counts: 89 selectable dates, 1527 start times, 4015 offers; 439 input/normalized sources; 210 input windows, 208 evaluated, 2 failed, 2 uncertainty issues.

This proves the served feed crossed its effective lease boundary before replacement delivery. It does not measure rendered customer impact or cache-wide outage duration. Prior successful runs do not erase this or R11/R13 boundary misses.

Admin 38159968021 succeeded (updated 17:34:35Z); matching Pages 38160224781 succeeded (updated 17:35:54Z). Later admin 38161006488 is in progress at bounded inspection; selector/page rebuild step active, validation/commit still pending. No competing refresh dispatched. Latest observed live feed proof above is expired, not a claim of restoration.

Local evidence from D:/Users/ten77/Documents/2020 -_ 2025 & Enrollware/910CPR-AvailabilityRefresh/state/health.json:

```json
{"ok":true,"heartbeatStale":false,"publicationExpired":false,"checkedAt":"2026-10-11T17:45:53.485Z","lastDispatchAt":"2026-10-11T17:45:53.485Z","publication":{"validUntil":"2026-10-11T13:48:47.396735-04:00","generatedAt":"2026-10-11T13:33:48.563851-04:00","dates":89,"offers":4015,"expired":false,"refreshDue":true},"action":"refresh_dispatched","runtime":"local-task-scheduler","observedAt":"2026-10-11T17:45:55.974Z"}
```

Task Scheduler 910CPR Availability Refresh: last run 13:45:53 Eastern, result 0, next run 13:50:52 Eastern, missed runs 0. Dispatch correlates with existing admin run 38161006488. This earlier successful check does not override later expired live evidence.

Exact independent-cloud blocker: gh api repos/Brian910cpr/910cpr-class-landers/actions/variables/AVAILABILITY_WATCHDOG_HEALTH_URL returned HTTP 404 Not Found; repository variables list empty. Latest canonical observer 38143241251 failed reconciliation-health and skipped verify-publication-watchdog, verify-demand and verify-production. Cloudflare encrypted secret state was not inspected and cannot be inferred from missing GitHub configuration. Existing owner gate remains approve/create a repository-restricted fine-grained token with Actions read/write and store only as Cloudflare encrypted GITHUB_ACTIONS_TOKEN. No credential changes or repeated activation attempts.

## Scope, validation and queue

Only this receipt intentionally changed. Original dirty E:/GitHub/910cpr-class-landers preserved. Fetched main through existing healthy worktree and created E:/GitHub/910cpr-issue334-health-check-r14 on named branch. Existing/background docs/Earl/index.html and docs/Jackson/index.html changes preserved and excluded from staging. No cleanup, reset or rebase.

No application changes, generators, new session/registration, booking/payment, merge or deployment. Draft #372 untouched. No duplicate PR. Watchdog source/test diff against origin/main empty; reused recorded syntax and 12 passing watchdog tests, with no new test-pass claim. Receipt whitespace validated by git diff --cached --check. Known unrelated failure: canonical reconciliation observer above, separately assigned under #297.

Open issue/PR queue scanned. #371/#372 retains deep-stream allocation; #367/#379 allocation gate remains per owner acknowledgment R13; #297 remains complete-current-roster source gated (latest R16); fleet/auth streams retain existing assignments. Read #373 scope: substantial backend instrumentation/UI work explicitly must not interrupt Studio, so not a narrow independent quick win. No safe narrow independent unassigned backend change identified. Reused existing receipts/findings rather than duplicating implementation streams.

## Proof contract and next action

Expected outcome: current public inventory delivered before actual source-capped expiry. Local timer cadence five minutes; existing threshold 60 minutes, heartbeat staleness 12 minutes, pending refresh bound 30 minutes. Actual source-capped feed window approximately 15 minutes despite 90-minute maximum publication lease. Last valid feed observation: 17:48:38Z; expired observation 17:48:49Z. Last successful Pages proof 38160224781 at 17:35:54Z.

Failure signals: expired live feed, stale local heartbeat, stalled publisher/delivery. Local health diagnostics active, independent observer unproven/skipped. CYBERPC awake/online/authenticated dependency persists; Brian must not be routine monitoring layer. Recovery path: existing timer -> publisher -> Pages -> cache-busted feed and rendered appointments. Preserve active recovery and do not dispatch competing refreshes.

ChatGPT next: check existing admin 38161006488 and following Pages/live feed, retain this boundary miss with R11/R13, and keep #334 open. Prove timer-to-Pages delivery inside effective lease rather than treating green builds as continuity. After authorized encrypted-token provisioning, activate/verify cloud timer, configure AVAILABILITY_WATCHDOG_HEALTH_URL and prove independent observer plus rendered appointments across cycles. Existing account-level credential gate unchanged. No duplicate unchanged alert. Preserve #372 unmerged/undeployed and all other assignments.

Persisted locally; receipt to be pushed and verified via GitHub Contents API. No merge/deployment by this dispatch. Exact intended changed file: Codex_Reply_Issue334_HealthCheck_20261011T1750Z_R14.md.
