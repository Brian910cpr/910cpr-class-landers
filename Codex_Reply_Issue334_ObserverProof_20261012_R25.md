# Issue 334 — observer proof R25

Timestamp: 2026-10-12T06:12:00Z (UTC).
Branch: codex/issue334-observer-proof-r25.
Evidence commit: 2081bf07b7a70c4dbb2d8e7ffac9c2998197e0e0.
Work-item state: BLOCKED for independent-cloud activation; read-only verification completed.
Evidence level: PROVEN local publication; overall readiness AT RISK, not HEALTHY.

Execution acknowledged on originating issue before work:
https://github.com/Brian910cpr/910cpr-class-landers/issues/334#issuecomment-6118772537

## Findings and exact blockers
At 2026-10-12T06:10:33Z all eight live families evaluated 210/210 windows, zero failed windows. BLS: 4086 offers/89 dates, 4074 dynamic plus 12 seated, unexpired through 06:18:44Z. Heartsaver: 8509 offers/88 dates; October 14 retains 17:30 and 19:30 starts. Both public HTML GETs returned HTTP 200. These checks do not prove browser rendering, continuous absence of brief expiry gaps, or a fresh enrollment handoff.

Last completed sampled Pages deployment 38210779718 succeeded at 06:05:29Z, following refresh 38210507253. Refresh 38210900255 also succeeded; its Pages 38211226985 was in progress at capture. No competing dispatch was triggered.

The active verify-public-booking-inventory.yml workflow configures five-minute cron, but its entire returned run history still contains only manual runs 38198348377 (success) and 38197805655 (old-feed failure). Natural scheduled observer heartbeat and notification receipt remain unproven. Do not repeat the old failed run or create a duplicate incident.

GitHub API GET actions/variables/AVAILABILITY_WATCHDOG_HEALTH_URL returned HTTP 404 Not Found. Existing owner-recorded gate remains: repository-restricted Actions read/write credential must be securely provisioned as encrypted GITHUB_ACTIONS_TOKEN for the independent cloud timer. No credential value was accessed or printed; no activation retry performed. This check establishes missing health configuration, not the present contents of encrypted secrets.

CYBERPC awake/login/network remains a local dependency based on accepted prior proof; task/runtime were not mutated or freshly inspected here. Expected publication window is the live source-capped validUntil, not merely the nominal 90-minute lease. Expired publication, failed windows, or missing BLS/Heartsaver dynamic inventory are failure conditions. Public observer is configured but its natural heartbeat is unproven; independent observer health cannot be claimed. Recovery: retain current local timer and source/conflict gates, complete secure cloud activation through the existing stream, configure health URL, then prove natural cloud dispatch -> publisher -> Pages -> browser-visible starts before prior expiry, with observer heartbeat and escalation evidence. Brian must not become the routine monitor.

## Work and validation
Read issue body/history, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md and proof standard. Original E:/GitHub/910cpr-class-landers is dirty and fetch reported missing object 6e61cabca5981d1389e52c60d95424d9893bb50f. Preserved it; used fresh isolated clone E:/GitHub/910cpr-issue334-r25. Windows case-collision checkout changes docs/Earl/index.html and docs/Jackson/index.html remain excluded. No cleanup/reset performed.

Remote read-only audit passed (exit 0). Local unittest tests.test_family_publication_coverage: 4/4 passed. Python AST syntax validation passed. git diff --check passed. Existing generator/observer reused; no broad generator, source changes, booking, payment, merge or deployment. No new PR. Draft #372 and existing #383/#387 assignments preserved.

Open issue and PR queues scanned. No independent unassigned narrow backend quick win identified without entering existing assigned or gated workstreams. No other assignment was modified.

## Exact changed files
- data/audit/issue334_observer_r25_live.json — complete per-family timestamps, counts, hashes, window failures and landscape provenance.
- data/audit/issue334_observer_r25_runs.json — exact recent publication/deployment history.
- data/audit/issue334_observer_r25_observer.json — exact observer history (manual only).
- data/audit/issue334_observer_r25_http.json — public HTML HTTP results.
- Codex_Reply_Issue334_ObserverProof_20261012_R25.md — this receipt.

Persisted locally and committed; pushed branch tip is reported in issue/chat after push and GitHub Contents verification. No application changes merged/deployed by this dispatch. No new owner business decision requested. Account-level secure credential provisioning remains the existing escalation boundary. Keep #334 open; next supervisor action is continue the existing independent-cloud credential/health activation stream and check natural observer heartbeat, preserving #383 skills-edge compatibility. Do not infer overall health from current green output.
