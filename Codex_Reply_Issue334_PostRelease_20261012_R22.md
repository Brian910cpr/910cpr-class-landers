# Issue #334 — post-release verification R22

Timestamp: 2026-10-12 03:21 UTC.
Branch: `codex/issue334-postrelease-r22`.
Evidence commit: `a39b2fb3ac7420a6613530fdc8629124270d6745`.
Work-item state: VERIFIED diagnostic checkpoint; BLOCKED overall independent-health acceptance. Issue remains OPEN.
Persistent evidence: PROVEN publication and repaired live feeds; overall HEALTHY is not established.

## Findings and scope

Read full #334 issue/comments, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_PROOF_AND_HEALTH_STANDARD.md, LANDERWARE_DESIGN_ETHOS.md and owner intake instructions. Acknowledged actual execution before implementation at https://github.com/Brian910cpr/910cpr-class-landers/issues/334#issuecomment-6117106819 . Latest owner correction applies: Maxim uses standard public booking and Enrollware, not the corporate portal.

PR #385 was already owner-approved, merged and released by the existing deep stream. No duplicate implementation, PR, merge, generator, refresh dispatch, runtime installation or deployment was performed in this dispatch. PR #372 and #383 remain untouched. This checkpoint verifies the existing release rather than claiming a new production fix.

The original E:/GitHub/910cpr-class-landers dirty checkout and all assignments were preserved. Used a separate named branch/worktree at E:/GitHub/issue334-postrelease-r22 based on e2304a1decff1a925878faf69fdc3027e63c8522. The clean checkout presents existing case-collision changes to docs/Earl/index.html and docs/Jackson/index.html; neither was edited or staged by this dispatch.

## Current public evidence

Read-only all-family audits at 03:17:40Z and 03:19:07Z both exited 0. Each family evaluates 209/209 current windows with zero failures. BLS and Heartsaver are unexpired through 03:28:48.075959Z in both observations.

| Family | Offers | Dates |
| --- | ---: | ---: |
| BLS | 4018 | 88 |
| Heartsaver | 8370 | 87 |
| ACLS | 3 | 2 |
| PALS | 2 | 1 |
| ARC | 4015 | 87 |
| HSI | 2763 | 87 |
| USCG | 2766 | 87 |
| Family CPR | 1252 | 85 |

BLS separates 4006 dynamic and 12 seated offers. Heartsaver separates 8366 dynamic and 4 seated offers. October 14 BLS has three course choices at 19:30; Heartsaver has seven choices across 17:30 and 19:30, with course 329495 retained at both times. The former 20 failed windows per family are absent. Input count is now 209, not the earlier 210: do not invent a missing window from timestamp-varying inputs. Sparse ACLS/PALS availability does not establish qualification or complete free-window coverage.

Both public HTML pages and all seven referenced local CSS/JS URLs per page returned HTTP 200. Asset hashes are recorded. This is static HTTP validation, not rendered browser proof. No application or asset changes were made.

## Consecutive renewal proof

Fetched pinned BLS/Heartsaver JSON from the exact deployed commits and Pages job completion records:

| Pages run | Output commit | Deploy job completed UTC | Margin before prior feed expiry |
| --- | --- | --- | ---: |
| 38198226870 | fc3e7ac592709e48a8b33591f42326cd6d379882 | 03:04:05 | baseline |
| 38198690188 | 53e608976556c32f60557b9bef9acff87a3a5c12 | 03:11:04 | 375.355337 seconds |
| 38198978345 | e2304a1decff1a925878faf69fdc3027e63c8522 | 03:15:31 | 525.710731 seconds |

All Pages runs succeeded; both subsequent replacements precede prior expiry for both families. These are exact deploy-job times (the workflow updatedAt is approximately one second later). Assertions passed for successful deployment, positive margins, unexpired feeds at delivery, and zero coverage alerts. This proves two timely deliveries; it cannot exclude a short cache/browser outage between observations. Exact earlier screenshot outage length remains unknown. No fabricated outage duration or ETA.

## Validation

- `python -B -m unittest tests.test_family_publication_coverage tests.test_shipyard_canonical_alias tests.test_layered_publication_adapter tests.test_layered_publication_pipeline`: 56 tests PASS.
- `node --check worker/availability-refresh-watchdog.mjs`: PASS.
- `node --test tests/availability_refresh_watchdog.test.mjs`: 15 tests PASS.
- Python AST syntax check and all four audit JSON parse checks: PASS.
- `git diff --cached --check`: PASS.
- Existing public observer run 38198348377 succeeded, event `workflow_dispatch`; prior 38197805655 failed against old production. Latest observer history inspected contains only these manual runs, so scheduled delivery is not proven.

## Exact files changed and review handoff

Only these four evidence files and this receipt are intentional changes:
- `data/audit/issue334_postrelease_r22_live_1.json`
- `data/audit/issue334_postrelease_r22_live_2.json`
- `data/audit/issue334_postrelease_r22_cycles.json`
- `data/audit/issue334_postrelease_r22_http.json`
- `Codex_Reply_Issue334_PostRelease_20261012_R22.md`

Review `families.*.counts`, `families.*.publicationExpired`, `families.*.dayPerCourse`, and `landscape.sourcePages` in the live audits; `records[*].pages`, `records[*].families` and `records[*].priorExpiryMarginSeconds` in the cycles audit; `pages.*.assets` in HTTP audit. No PII or credentials were recorded.

Existing primary release handoff, independently pushed by its original stream during this dispatch: `data/audit/issue334_direct_p0_release_20261012.md`, `data/audit/issue334_direct_p0_release_20261012.json`, and `Codex_Reply_Issue334_DirectP0_20261012.md` at 05f04ad67a20484be3d0556bb1d39f467361c5f9 on codex/issue334-course-coverage-20261012. It records 93 browser samples per family, seven publications, zero sampled expiry/errors from 02:44:18–03:17:14Z, max sample gap 66.18 seconds, desktop/mobile forms and assets. Those are prior-stream evidence, not fresh browser actions by this dispatch. Preserve that report and its limitations.

## Exact blockers and persistent proof contract

Expected outcome: genuine public BLS/Heartsaver appointment choices remain usable across renewal, with conflicts and source freshness preserved. Success evidence: public-feed timestamps/counts, Pages chain and customer browser/handoff. Cadence: currently five-minute physical timer, bounded by active-run deduplication; effective calendar-source freshness is 15 minutes. Last own successful feed proof: 03:19:07Z. Stale/failure: expired dynamic publication, no expected BLS/Heartsaver appointments, or failed evaluation windows.

Observer: read-only `.github/workflows/verify-public-booking-inventory.yml`, configured every five minutes. Observer health: failure and success detectors demonstrated manually; natural scheduled heartbeat and notification receipt not yet proven. Independent cloud health variable API returns HTTP 404 (`AVAILABILITY_WATCHDOG_HEALTH_URL`); existing repository-restricted Actions read/write token encrypted as Cloudflare `GITHUB_ACTIONS_TOKEN` gate remains. No repeated auth or secret inspection attempted. CYBERPC awake/login/network remains the local recovery dependency. Brian must not become the routine monitor.

Fresh browser verification blocked: requested Edge browser was unavailable; `cua.getState()` returned `apps: [], browsers: []`. Do not infer a customer-wide browser problem. The current feed and HTTP checks remain usable. No registrations, payments or confirmations submitted.

Source/runtime drift: latest existing release receipt states physical 270000ms watchdog cooldown is activated with backup, while source remains on existing R21 branch, unmerged. This dispatch did not overwrite it. Next integration must preserve that reviewed source before reinstalling; do not reinstall older main runtime over the active timer.

Queue and PR scan performed. Nearby backend work (#371/#380/#266/#254/#367) already has active draft streams and safety gates; no safe independent unassigned backend change was identified that would justify displacing P0 verification or duplicating assignments. No unrelated source work started.

## Disposition and next action

Public flow readiness: AT RISK, currently proven restored at the recorded checkpoints. No new public repair release blocker: #385 is already deployed. Overall acceptance remains blocked by independent observer/token gate, unproven natural observer schedule, CYBERPC dependency and lack of fresh browser in this session. Keep #334 open.

Supervisor next: inspect this checkpoint alongside the primary direct-P0 release handoff, retain active timer, integrate reviewed R21 source through the existing continuity stream without runtime/task recreation, then prove scheduled observer heartbeat and independent cloud recovery. Reconcile #383 with merged skills-edge behavior before its release. Account-level action only for the existing scoped encrypted cloud token; no new broad approval request. No reason to merge/deploy #372.

Persisted locally and committed; this receipt and evidence are pushed on the named branch before exit. No merge or deployment in this dispatch. Deliberately unstaged: the two case-collision HTML paths above. No intentionally untracked task artifacts in this worktree.
