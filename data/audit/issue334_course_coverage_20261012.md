# Issue 334: all-course coverage and canonical venue failure

Observed 2026-10-12 01:16–01:19 UTC. PR #385. This is partial repair evidence, not closure of the P0 or proof of continuous health.

## Exact fault stage

`scripts/block_start_time_selector.py:build_occupancy` resolves canonical location labels using `data/config/location_resource_map.json`. The canonical label `910CPR Office - Shipyard Blvd` was absent. `scripts/layered_selector_adapter.py:build_shadow` consequently treated the existing office class as an unknown offsite location and demanded a directional travel rule to the primary Shipyard room. `scripts/layered_publication_adapter.py:calculate` caught that error and omitted the whole window's report.

This happened before candidate evaluation. Twenty of 210 windows failed in each family; three start on October 14 (00:00–06:30, 07:45–15:00, 17:30–midnight Eastern). Blank graph cells therefore do not mean occupied time. The exact inspectable window reason is `missing directional travel rule: 910CPR Office - Shipyard Blvd->:: Wilmington; Shipyard Blvd - B`. Existing reconciliationIssues contain these window failures; candidate rejection counts alone omit them.

The smallest correction adds that label to the existing venue aliases. It adds no room, capacity, appointment container, travel rule, course ID, Session or Registration. Existing room/instructor occupancy, freshness gates, qualification rules and unknown offsite failure remain intact. Native operational truth continues through the existing canonical source, moving toward LanderWare independence without adding an incumbent dependency.

## Public checkpoint and authenticated probe

The public checkpoint is `data/audit/issue334_live_family_coverage_20261012.json` (observed 01:16:29Z, landscape build `e0d632920517`). It retains HTTP payload hashes, per-course offer counts, exact window failure reasons, source-page candidate rejection counts, and generated/expiry timestamps. All family HTTP reads completed, but sequential reads can straddle a publication; matching counts are not a cryptographic same-build guarantee.

The existing authenticated read-only release probe succeeded: https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/38191338705 . It ran commit `50c56729a2d69dabc21dc54a3a7dba9364769487` and did not publish. Canonical input was generated at `2026-10-12T01:18:50.958Z`, containing 31 sessions. Every family used 444 projected sources and 210 selected windows; all 210 windows evaluated, zero failed windows and zero calculation issues. The retained summary is `data/audit/issue334_alias_probe_20261012.json`; the run artifact `v2-release-probe-38191338705` contains the full public-safe proof plus eight HTML and eight JSON previews. Downloaded copies remain ignored under `data/runtime/audit_previews/issue334_alias_probe/`.

| Family | Public offers / dates | Probe offers / dates | Public failed windows | Probe failed windows |
|---|---:|---:|---:|---:|
| BLS | 3991 / 87 | 4014 / 88 | 20 | 0 |
| Heartsaver | 8297 / 81 | 8369 / 87 | 20 | 0 |
| ACLS | 3 / 2 | 3 / 2 | 20 | 0 |
| PALS | 2 / 1 | 2 / 1 | 20 | 0 |
| ARC | 3980 / 78 | 4015 / 87 | 20 | 0 |
| HSI | 2739 / 78 | 2763 / 87 | 20 | 0 |
| USCG | 2742 / 81 | 2765 / 87 | 20 | 0 |
| Family CPR | 1241 / 78 | 1252 / 85 | 20 | 0 |

These are separate near-time input checkpoints, not a controlled same-input before/after experiment. The regression test supplies the controlled previous-map reproduction. Do not attribute every count delta solely to the map change.

## What is still wrong or unproven

October 14 remains constrained after the alias repair: Heartsaver has the retained 17:30 blended class and 19:30 attached offers; BLS, ARC, HSI and Family CPR have 19:30 attached offers. Full/free-day candidates do not reappear merely because normalization succeeds. The probe retains `existing_course_day_anchor`, `anchored_day_requires_attached_offer`, `full_course_count_unknown` and other precise candidate suppressions. Related draft PR #383 already owns empty-inventory versus demand/occupancy behavior; it was neither modified nor deployed. Reuse that stream for further analysis rather than bypassing uncertain source counts or duplicating its implementation.

ACLS/PALS remain sparse. Their checkpoint publication expiry equals generation time because the finalizer has no retained dynamic offer lease; direct seated-class entries are retained by the customer lease filter. Each probe records 4203 `instructor_not_qualified` reasons. Brian is explicitly excluded from ACLS/PALS in existing policy. This does not prove Amy availability is correct; an authoritative qualification/calendar comparison remains required. Do not manufacture clinical offers from Brian's free windows.

The new CLI `python -B -m scripts.audit_family_publication_coverage --live --output <path>` returns exit 1 when any published family reports failed windows. Its pre-fix live run intentionally returned 1. This is a tested coverage checkpoint, not an installed recurring observer. It does not yet prove the stronger invariant that every eligible free interval has an offer or inspectable per-course suppression. That invariant and alert wiring remain open.

Actual connected browser inspection was unavailable: `cua.listBrowsers()` returned `[]`; the in-app browser reported unavailable. Four local headless renderer tests passed; that is not live customer-interaction proof. No booking or payment was exercised.

## Validation and scope

`python -B -m unittest tests.test_shipyard_canonical_alias.CanonicalOfficeAliasTests tests.test_family_publication_coverage tests.test_layered_publication_adapter tests.test_layered_day_cache tests.test_publish_scheduling_landscape -q`: 59 tests, OK.

`python -B -m unittest tests.test_layered_publication_pipeline -q`: 4 tests, OK.

Python AST and JSON syntax checks: OK. Intended-file whitespace checks: OK. Regression preserves the exact occupied interval and active seat, restores legal full/skills edge offers, reproduces failure with the previous map, and retains unknown-offsite fail-closed behavior.

No public generators ran locally. The existing remote read-only probe refreshed runner inputs and rendered preview outputs only. No merge or production deployment was performed by this dispatch. A Cloudflare branch preview check is separate from production.

Original dirty/corrupt `E:/GitHub/910cpr-class-landers` was preserved. Healthy clone worktree: `E:/GitHub/910cpr-issue334-course-coverage`, branch `codex/issue334-course-coverage-20261012`. Test imports touched Earl/Jackson HTML and three tracked bytecode files; those incidental changes were explicitly excluded from commits and left in the isolated worktree. Other assignments, drafts #372/#383 and all pre-existing worktrees remain intact.

## Release gate and next action

PR #385 is reviewable with 63 local tests and the authenticated dry-run. Its merge would trigger the existing admin publication workflow, expected to modify roughly 60–70 generated/state files across selector HTML/feeds, schedule/admin JSON, class pages, audits and state. The user's repository rule requires approval before a sitewide generator; approval was requested after concrete validation. Do not claim deployed proof until this gate is satisfied and production output is verified.

After approved release, verify all eight public feeds and the matching landscape, then rendered dates/times and referenced assets. Observe repeated natural cycles beyond one effective lease. Continue the remaining day-anchor investigation through #383 with source counts intact. Keep #334 open.

Independent-cloud health remains blocked: `AVAILABILITY_WATCHDOG_HEALTH_URL` returned HTTP 404. Existing owner gate remains a repository-restricted Actions read/write token stored only as encrypted Cloudflare `GITHUB_ACTIONS_TOKEN`. Do not retry activation without that gate changing. Success means legal visible customer choices, not merely a green publisher; the observer itself still needs health evidence. Local containment has prior PROVEN cycles but is not overall HEALTHY.
