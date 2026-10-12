# 910CPR public booking release evidence

As of 2026-10-12T03:17:47.819580+00:00, the approved public booking repair is merged and deployed. Public BLS and Heartsaver selectors and representative Enrollware enrollment forms have been checked in desktop and mobile Chrome. Repeated publication evidence is sampled; overall cloud-independent HEALTHY status is not claimed. Incident #334 remains open.

## Root cause

The active layered adapter caps each dynamic offer at its underlying calendar observation plus 15 minutes. Its nominal 90-minute publication lease cannot override that source limit. The previous approximately ten-minute local dispatch spacing plus variable refresh, queue and Pages delivery left insufficient reserve. Once validUntil passes, resolved-selector-availability.js removes dynamic dates while preserving seated classes. Historical incident comments record actual stale intervals; the owner's approximate 22:20 screenshot does not establish an exact outage duration or edge payload, so that duration remains unknown.

Separately, canonical location label `910CPR Office - Shipyard Blvd` was absent from the authoritative venue aliases. Missing directional travel resolution aborted 20 entire availability windows per family before candidate evaluation, including three October 14 windows. Existing-course day consolidation then suppressed same-course skills alternatives even when the engine had validated attached edges.

## Repair and release

The owner approved the existing continuity branch's one-file installed timer activation at 02:43:51Z. The installed five-minute cooldown includes 30 seconds of jitter tolerance and retains active/queued-run suppression, fixed-main dispatch, source freshness and booking/conflict gates. It does not invent a longer source lease. Rollback and installed hash are in `data/audit/issue334_direct_p0_release_20261012.json` at `timer`. Source remains on `codex/issue334-continuity-r21`, commit `e159ea23a963b713f07b4bf598114448a8fcefa7`; the installed change is persisted locally, not merged from that separate branch. Before any timer reinstall, retain this approved five-minute version rather than reverting to main's older cooldown.

Existing PR #385 received the targeted skills-edge exception and read-only all-family inventory observer, preserving the original Shipyard alias repair. Full-course consolidation, occupied intervals, unknown-offsite fail-closed behavior, and detached-offer rejection remain. Source commit: `dbba9c496c0028429847ae8d6675991cb1920b50`. Owner explicitly approved the authenticated preview and gated production release. Probe 38197642582 passed at that head. PR #385 merged at 02:56:58Z as `10360ae40623f8f11277f5462750123989281c43`.

Production refresh 38197804838 succeeded; generated output commit `fc3e7ac592709e48a8b33591f42326cd6d379882`; GitHub Pages run 38198226870 succeeded at 03:04:06Z. Exactly 38 generated/state files changed, within the previously disclosed approximately 60–70-file scope; no unexpected paths. No application CSS/JavaScript asset changed. All seven referenced local asset URLs returned HTTP 200 in each of four production browser walkthroughs.

## October 14 instructor and anchor truth

Current public calendar projection confirms Brian's blocks at 06:30–07:45 and 15:00–17:30 Eastern. The canonical Heartsaver blended anchor is recorded as occupied 17:30–19:30 and remains untouched. A 16:30 skills candidate would require the blocked 16:30–17:30 hour, so it is not a legal actual pre-edge. The accepted post-edge starts at 19:30, instructs for 45 minutes and reserves another 15 for cleanup, ending consumption at 20:30. The 120-minute recorded anchor is not applied as the candidate skills duration.

The authenticated preview and actual deployed Heartsaver selector retain course 329495 at 17:30 and expose its 19:30 dynamic barnacle. Browser selection of both options was verified at 1440 and 390 pixels. The earlier option links to Enrollware class `id=14589762`; the later option carries `appointmentDayId=260785`, `courseId=329495`, and `startTime=7:30 PM`. Enrollware rendered Wednesday October 14 at 7:30 PM and the correct blended course. BLS Renewal course 359474 at the same date/time likewise reached its correct Enrollware form. No forms were submitted and no registration/payment occurred.

## Live family validation

| Family | Offers | Dates | Evaluated windows | Failed windows |
| --- | ---: | ---: | ---: | ---: |
| bls | 4018 | 88 | 209/209 | 0 |
| heartsaver | 8370 | 87 | 209/209 | 0 |
| acls | 3 | 2 | 209/209 | 0 |
| pals | 2 | 1 | 209/209 | 0 |
| arc | 4015 | 87 | 209/209 | 0 |
| hsi | 2763 | 87 | 209/209 | 0 |
| uscg_first_aid_cpr_aed | 2766 | 87 | 209/209 | 0 |
| family_cpr | 1252 | 85 | 209/209 | 0 |

This post-deployment audit returned exit 0. Before release the same audit detected 20 failed windows per family. Sparse ACLS/PALS inventory is not repaired by inventing Brian eligibility; the authenticated probe preserves qualification rejections and existing seated options. Exact rejection counts are under `probe.pages.*.rejection_reasons` in the release JSON.

Existing seated counts remain 12 BLS and 4 Heartsaver before/after the repair. The authenticated calculation used 31 current canonical sessions, 444 projected sources and 209 current input windows per family. Every window completed evaluation. The input count differs from the earlier 210-window checkpoint; comparisons are timestamped observations, not a controlled same-input offer-count experiment.

## Natural cycles and observation limits

Browser sampling began at 2026-10-12T02:44:18.449897+00:00 and currently ends at 2026-10-12T03:17:14.147817+00:00. BLS: 93 samples, 7 distinct delivered publications, 0 error/expired samples. Heartsaver: 93 samples, 7 publications, 0 error/expired samples. Minimum measured replacement margin at first browser observation: BLS 152.09s; Heartsaver 151.77s. Samples are approximately 20 seconds apart; maximum observed gap is 66.18s. A shorter outage between observations cannot be excluded.

Exact timestamped source generations, validUntil values, counts and margins: `browserPublications`. Every checkpoint: `browserSamples`. Timer heartbeat/last dispatch: `timer.health`. Production asset/UI/link checks: `productionWalkthrough`; original representative seated/dynamic handoffs: `handoffs`. Public October 14 blocks: `oct14InstructorBlocks`. Production changed paths: `productionPublication.generatedScope.files`.

Two routine renewals after the repaired deployment are verified: refresh 38198414104 -> Pages 38198690188 (03:11:05Z, output 53e608976556c32f60557b9bef9acff87a3a5c12), then refresh 38198743428 -> Pages 38198978345 (03:15:32Z, output e2304a1decff1a925878faf69fdc3027e63c8522). Both families were observed current at each replacement. Exact run records: `naturalPostDeploymentRenewals`. Windows idle sleep is currently disabled on AC and DC; the task does not wake a sleeping PC. These read-only power observations are under `localSleepSettings`; no power setting was changed.

## Detection and operational boundary

`.github/workflows/verify-public-booking-inventory.yml` schedules the existing read-only all-family audit every five minutes and retains timestamped evidence. It fails for failed evaluation windows, expired dynamic feeds, and absence of expected BLS/Heartsaver appointment inventory. It does not hide seated choices, create inventory, dispatch competing refreshes or modify registrations. Initial production observer run 38197805655 correctly failed on the old 20-window fault; corrected observer run 38198348377 succeeded after deployment. These real runs prove detector behavior; GitHub cron delivery and notification receipt are separate from those manual runs and must not be assumed timely.

The existing local five-minute timer supplies bounded recovery with active-run deduplication and exposes a fresh physical-drive health file. CYBERPC awake, logged-in, online operation remains required. Independent cloud timer activation is not proven; the existing restricted GitHub Actions read/write token stored only as Cloudflare encrypted `GITHUB_ACTIONS_TOKEN` remains the account gate. The GitHub variable lookup for `AVAILABILITY_WATCHDOG_HEALTH_URL` returned HTTP 404 in this session; no repeated authentication attempt was made. Do not describe this as a cloud-independent HEALTHY system or ask Brian to become the routine observer.

## Exact review files

PR #385 changed:
- `.github/workflows/verify-public-booking-inventory.yml`
- `Codex_Read_Issue334_AllCourseCoverage_20261012T0159Z.md`
- `Codex_Reply_Issue334_AllCourseCoverage_20261012T0122Z.md`
- `data/audit/issue334_alias_probe_20261012.json`
- `data/audit/issue334_course_coverage_20261012.md`
- `data/audit/issue334_direct_p0_live_20261012.json`
- `data/audit/issue334_live_family_coverage_20261012.json`
- `data/config/location_resource_map.json`
- `scripts/audit_family_publication_coverage.py`
- `scripts/layered_publication_adapter.py`
- `tests/test_family_publication_coverage.py`
- `tests/test_layered_publication_adapter.py`
- `tests/test_layered_publication_pipeline.py`
- `tests/test_shipyard_canonical_alias.py`

This release handoff additionally persists:
- `data/audit/issue334_direct_p0_release_20261012.json` — structured authenticated/browser/cycle evidence.
- `data/audit/issue334_direct_p0_deployed_20261012.json` — live all-family post-deployment audit.
- `data/audit/issue334_direct_p0_release_20261012.md` — this primary report.
- `Codex_Reply_Issue334_DirectP0_20261012.md` — root mailbox receipt.

Validation commands/results:
```
python -B -m unittest tests.test_family_publication_coverage tests.test_layered_publication_adapter tests.test_shipyard_canonical_alias.CanonicalOfficeAliasTests tests.test_layered_day_cache tests.test_publish_scheduling_landscape tests.test_layered_publication_pipeline -q
Ran 67 tests — OK
node --check worker/availability-refresh-watchdog.mjs
Passed
node --test tests/availability_refresh_watchdog.test.mjs tests/availability_refresh_local.test.mjs
18 tests, 18 passed, 0 failed
python scripts/audit_family_publication_coverage.py --live --continuity --output data/audit/issue334_direct_p0_deployed_20261012.json
LIVE_AUDIT_EXIT=0
```
Python AST syntax, workflow YAML parsing/read-only permissions and intended-file whitespace checks passed. Source-integrity/preflight and branch preview checks passed before merge. Four actual production browser walkthroughs passed; referenced local assets HTTP 200; no JavaScript errors.

Original dirty/corrupt checkout and existing streams are preserved. In the isolated review checkout, unrelated `docs/Earl/index.html` and `docs/Jackson/index.html` remain unstaged; they were excluded explicitly. Temporary preview downloads, browser scripts and rollback copy remain in the project chat's `work/` directory, not committed. Public screenshots are in the chat's `outputs/` directory. PR #383 remains unmerged with its own release-proof gate; its overlapping adapter changes must retain this skills-edge exception. PR #372 untouched. No reset, clean, force-push or destructive cleanup performed.

Next: retain the current timer, continue natural-cycle checks, verify scheduled observer heartbeat, and resolve independent cloud activation before removing the CYBERPC dependency. Keep #334 open until those health conditions are proven.
