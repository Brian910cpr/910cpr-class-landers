# Issue 334 R57: current all-family branch probe

2026-10-14 UTC. Branch `codex/issue334-location-proof-20261014-r56`; existing draft PR #393 reused. State PR_OPEN; production release BLOCKED pending specific output-scope approval. No application changes this round.

Execution acknowledged before probe: https://github.com/Brian910cpr/910cpr-class-landers/issues/334#issuecomment-6165780008 . Full issue history, AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md reviewed. Original E:/GitHub/910cpr-class-landers dirty work and all assignments preserved. Its shared Git fetch fails `fatal: bad object refs/remotes/origin/codex/group-training-experience`; clean clone E:/GitHub/910cpr-issue334-r57 uses the SAME PR branch, based on latest supervisor acknowledgment 4983a974a31043b6c21fe8e1383f18ff611a74c5. No reset, cleanup, rebase, force-push or competing deep stream.

## Current source probe

Command: `gh workflow run refresh-admin-availability.yml --repo Brian910cpr/910cpr-class-landers --ref codex/issue334-location-proof-20261014-r56 -f v2_release_probe=true`.

Run https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/38546492384 succeeded 10:01:57Z against 4983a974a31043b6c21fe8e1383f18ff611a74c5. Production refresh job SKIPPED. Existing runner-local schedule/calendar reads and preview generator only; no production publication. Output `data/runtime/audit_previews/v2_release_probe/` on runner, eight JSON/eight HTML/proof.json (17 files). Artifact 11884104621, `v2-release-probe-38546492384`, archive digest sha256:e93c227144750ba94a3e3cb3946c04c1f5be83c336acdebc557f5ff2650543c5. Local artifact directory E:/GitHub/910cpr-issue334-r57-probe is excluded from commits.

437 input/normalized sources, 23 current canonical sessions, 190 input/evaluated windows, zero failed windows and zero calculation issues in EVERY family:

| Family | Offers | Dates |
|---|---:|---:|
| BLS | 3625 | 88 |
| Heartsaver | 7574 | 89 |
| ACLS | 3 | 2 |
| PALS | 2 | 1 |
| ARC | 3625 | 88 |
| HSI | 2498 | 88 |
| USCG | 2500 | 89 |
| Family CPR | 1127 | 87 |

These are dry-run counts, not production after-counts. ACLS/PALS remain seated-only; no new qualified dynamic availability is inferred. All precise rejection reasons and day patterns remain in data/audit/issue334_probe_r57_original.json. The workflow release_passed flag alone is weaker than acceptance: independent checker explicitly asserts evaluated=input AND failed=0 plus occupied-window preservation.

## November 3 conflict proof

Authenticated Supabase SELECT-only read of exact session dfa08088-1266-4dd6-ad7d-14856b7f845a established start_at=2026-11-03T17:00:00+00:00, end_at=2026-11-03T19:00:00+00:00 (12:00-14:00 Eastern), Location FK fd44e20f-af86-4198-ab7c-fa13dad6a7fd, resource_id=null, source label `4018 Shipyard Blvd, Room B, 910CPR Office`, joined Location `910CPR Office - Shipyard Blvd`. No room assignment inferred, created or changed.

Each family preview retains this exact occupied interval. Independent checker finds zero November 3 dynamic offers overlapping it. BLS retains noon seated Renewal and legal 09:30 classroom plus 11:00/14:00 skills starts. Heartsaver retains legal 09:30 classroom/10:15 CPR and 11:00/14:00 skills starts. Skills consume 60 minutes (45 instruction +15 cleanup); classroom BLS consumes 150 minutes ending at noon. Exact course IDs, source session/edge IDs, appointmentDayIds, resources, occupiedUntil and registration targets are persisted in data/audit/issue334_probe_r57.json.

55 focused tests PASS in clean clone (6.686s); same 55 passed in original PR worktree. AST/config JSON PASS. Reproducible artifact checker: `python -B data/audit/issue334_probe_r57_check.py <downloaded-artifact-directory>`; PASS. HTML previews externalize feeds to production-relative URLs, so merely opening preview HTML would read production data; no live browser/customer rendering proof is claimed. Existing renderer regressions pass. Post-release browser proof remains required.

## Live baseline and operational limits

Read-only live audit at 10:03:46Z in data/audit/issue334_live_r57.json: all eight families 190 input/188 evaluated/2 failed windows, exact missing directional travel rule unchanged. BLS 3622/88 dates, HS7565/88, both unexpired through10:14:27Z. Audit intentionally exits1 for coverage alerts. October14 failedWindows=0; don't attribute today's sparse choices to November3 failures. Current preview/live sources are close observations, not a pinned before/after replay; counts can shift with source changes.

Health URL repository variable still HTTP404. Existing secure encrypted repository-restricted Actions read/write credential gate unchanged. Latest natural booking observer38514856448 failed05:06:20Z; prior38469671908 succeeded. Five-minute sustained observer cadence and independent cloud recovery remain unproven. No activation retry, secret inspection, duplicate alert, refresh dispatch or new monitor.

Persistent state: repair BUILT/validated locally and authenticated dry-run; historical publication PROVEN, overall HEALTHY unestablished. Desired outcome continuous legal selectable starts; expected publication before effective source expiry (~15min), observer configured5min. Failure signals expired feed or failed/unevaluated windows. Public booking observer plus supervisor are the observers, but schedule gaps and missing cloud health prevent trusted observer health. CYBERPC awake/online/login remains unresolved dependency. Recovery: specific reviewed release then live all-family/November3/browser/asset proof and successive timely renewals. Account escalation remains secure cloud provisioning; Brian must not be routine monitor.

## Exact release gate / next action

Approve ONLY PR #393 venue alias + conservative existing primary-room fallback and its normal `refresh-admin-availability.yml` generated-output publication. Expected 40-60 workflow-owned files:17 configured selector/alias/redirect HTML,8 family feeds, matching canonical/admin/landscape/anchor/ical data, current native class pages, calendar snapshots and workflow-allowlisted audit/status files. Exact allowlist: workflow commit step and data/config/block_schedule_pages.json. Full original scope/rollback: data/audit/issue334_location_r56.md. No full sitewide class/hub rebuild; stop on >10 unexpected files. Revert only PR config/adapter via reviewed commit for rollback; do not reset dirty work or weaken guards.

After explicit approval, use existing PR393, recheck main compatibility (especially separate383), merge only approved files, let normal publisher run, verify all eight LIVE failed_windows=0 plus actual Nov3 rendered BLS/HS choices, referenced assets and GET registration handoff, then successive renewal/observer cycles. Keep334open. No inferred approval from arbitrary comments or past385 release. Draft372 remains unmerged/undeployed.

Open issue/PR queue swept:393 is primary;383 scheduling,387 checkout,389 documents,388 finance,381 manual resolution,375/374 fleet and372 studio remain existing assigned/gated streams. No safe independent unassigned narrow backend change selected; none displaced. No ops/handoff/next_task.md use.
