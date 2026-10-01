# P0 availability expiry recovery

- Incident: 910CPR public calendars showed zero valid dates after PR #322 release.
- Timestamp: 2026-10-01 11:59 UTC / 07:59 America/New_York.
- State: VERIFIED recovery; persistent process PROVEN, not MONITORED or HEALTHY.
- Production branch: main. Receipt branch: codex/p0-availability-expiry-20261001.
- Repairs: 034e76d23c4d5613ebf41564c1360da97cd003bc and e5e5b2896b374887fb8bb9dc9c7ef6548f8c6423.
- Output: admin 16bf9a95; public 97ea8610 (discover full SHAs on main).

## Root cause and accountability

The new publication expiry closes all selector dates after 20 minutes. The last prior public feed expired around 10:29 UTC. No later publisher succeeded. Queued admin run 36846836916 checked out the merge event SHA, then conflicted when trying to rebase generated schedule output over the already completed public refresh. It correctly refused overwrite. Earlier release continuation stopped there but left the feed-expiry operational consequence unresolved. That was insufficient release closure.

The public workflow additionally skipped its rebuild when iCal and canonical demand hashes were unchanged, even when the publication lease had expired.

## Work performed

1. Changed .github/workflows/refresh-admin-availability.yml checkout to ref: main with fetch-depth: 0, after shared publication concurrency acquisition.
2. Changed .github/workflows/refresh-public-site.yml canonical rebuild decision: missing, invalid, expired, or within ten minutes of expiry feeds require fresh source validation/full rebuild even if source inventory hashes are unchanged.
3. Preserved stop-on-conflict safeguards, existing reconciliation architecture, occupied dates, private occupancy, unknown roster visibility, and offer expiry. Did not manufacture fresh timestamps or extend leases.
4. Admin recovery run 36856894218/job 110351411500 passed every step, including reconciliation tests, live source fetch, landscape generation, output validation and publication.
5. Public run 36857731561/job 110354150169 passed all tests, full validated build, strict links, output validation and publication.
6. GitHub Pages deployment 36857730829 restored admin output; deployment 36858451326 then successfully deployed final public output.
7. Source integrity 36857731568 and Cloudflare preflight 36857731513 passed.

## Live proof

Browser and HTTP checks at approximately 11:58-11:59 UTC:

- BLS, Heartsaver, ACLS and PALS all display selectable dates.
- BLS October 2 Initial: only real 12:45 PM class, Enrollware 14501248.
- BLS October 12 Initial: only real 5 PM class, Enrollware 14135047. Midnight through 04:30 and 12:45 PM orphan offers absent.
- BLS October 12 Renewal: only real 9 AM class, Enrollware 14184954.
- October 3: public BLS unavailable; fresh Landscape retains canonical Heartsaver commitment 9-11:30 AM and closed/private HeartCode 12:30-1:30 PM. Unknown HeartCode roster is explicitly reported, not zero.
- October 7: Landscape shows STALE ROSTER and HARD BLOCK COLLISION for 14354087, real occupancy retained, zero public offers, 59 candidates suppressed.
- Landscape publication builtAt 2026-10-01T11:48:14.685929+00:00, buildId 034e76d23c4d, visible reconciliation errors.
- Final public feed generatedAt 2026-10-01T07:51:08.628017 (Eastern local naive source time).
- Final feed validUntil UTC: BLS 12:13:04.463428; Heartsaver 12:13:45.685604; ACLS 12:13:52.700226; PALS 12:13:57.258658. Dates respectively 81,79,4,4.

## Remaining operational risk and exact next action

Configured admin cron is every ten minutes; public cron is twice per hour. A fresh scheduled admin cycle has not been observed during recovery. Successful push-triggered cycles prove recovery, not a dependable recurring cadence. GitHub public workflow page shows no disabled banner; exact dispatch-gap cause is unproven. Browser is signed out and connector has no workflow dispatch or workflow/account settings operation. Do not claim the schedule is disabled or monitored.

Staleness detectors: customer selector publication expiry and Landscape STALE PUBLICATION. No independently proven observer/escalation heartbeat exists in this evidence. Owner must not remain the routine monitoring layer.

Next supervisor action: verify a fresh scheduled admin run from current main reaches publication/Pages before 12:13 UTC; if no run is dispatched, use authenticated GitHub workflow/account settings to diagnose missing scheduled dispatch and dispatch Refresh admin availability from current main as immediate recovery. Do not rerun the stale merge event run or force overwrite. Restore a proven automatic cadence/observer before declaring the persistent system HEALTHY. Browser/account authentication or a connector workflow dispatch capability is needed for that settings/dispatch path in this environment.

Known unrelated failures: stale/missing canonical roster reconciliation remains visible for several actual classes and continues to block synthesis safely. No scheduling architecture changes are needed for this P0 recovery.
