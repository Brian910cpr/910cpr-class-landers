# Issue 334 — R49 cloud gate and new coverage failure

Timestamp: 2026-10-13T23:58:00Z (UTC)
Branch: codex/issue334-cloud-gate-20261013-r49
Evidence commit: 9178bc2291dbb154a5e885b12189fcf3638da301
State: BLOCKED — independent cloud provisioning; current coverage validation fails.
Persistent evidence: prior publication PROVEN; overall HEALTHY not established.

Execution acknowledged before evidence writes:
https://github.com/Brian910cpr/910cpr-class-landers/issues/334#issuecomment-6157685151

## Current findings

Read-only live audit observed 2026-10-13T23:54:43.783928Z. All eight families report input_windows=189, evaluated_windows=187, failed_windows=2. Exact rejection: `missing directional travel rule: 4018 Shipyard Blvd, Room B, 910CPR Office->:: Wilmington; Shipyard Blvd - B` (two windows). This is a new coverage failure relative to R48, not evidence of expiry. BLS 3584 offers/87 dates; Heartsaver 7488/88. Both are unexpired through 2026-10-14T00:03:36Z. October14 BLS has no offers; Heartsaver has one 17:30 offer. The missing rule affects no October14 windows according to dayFailedWindows=0; do not infer it explains those date counts. No travel duration or alias equivalence guessed; safety gate preserved. Raw source-page rejection counts/hashes retained in evidence.

Canonical BLS/Heartsaver HTML GETs returned 200. No browser rendering, registration or payment exercised. Latest natural observer remains 38469671908, successful at21:19:34Z. Previous start gap5h03m18s does not prove configured five-minute cadence. Current authenticated AVAILABILITY_WATCHDOG_HEALTH_URL query returned HTTP404; this does not prove encrypted-secret absence. Existing secure account provisioning gate remains unchanged: repository-restricted fine-grained Actions read/write credential stored only as encrypted Cloudflare GITHUB_ACTIONS_TOKEN. No activation retry or competing refresh. Admin38486205266 succeeded23:49:05Z;38486703907 was in progress at check.

## Work and validation

Changed only these four evidence files and this receipt:
- data/audit/issue334_cloud_gate_r49_live.json
- data/audit/issue334_cloud_gate_r49_observer.json
- data/audit/issue334_cloud_gate_r49_health.txt
- data/audit/issue334_cloud_gate_r49_http.json
- Codex_Reply_Issue334_CloudGate_20261013_R49.md

Current official scripts/audit_family_publication_coverage.py fetched through GitHub Contents into local TEMP and executed with --live --continuity. Audit reports coverageAlert=true for all eight families (expected nonzero coverage result); independent AST check and three JSON evidence parses PASS; staged whitespace PASS. No application source changed; no generator/build/deploy/merge or duplicate PR. Local diagnostics persisted, committed and pushed separately. Draft #372 preserved.

Original dirty checkout preserved. Isolated worktree E:/GitHub/910cpr-issue334-r49 initially based on locally cached origin/main567c433f941; read current instructions/protocol/proof standard and official audit via GitHub API. Authenticated fetch succeeded after selecting gh credential helper, but repository automatic gc reports bad object refs/remotes/origin/codex/group-training-experience. No cleanup/reset/rebase performed. Unrelated docs/Earl/index.html modification appeared in isolated worktree and was excluded explicitly. Existing dirty files and assignments unchanged. No intentionally untracked assignment files. Receipt-only branch is not a production merge candidate.

Open CODEX issues and PR queue scanned: backend219/389,216/388,380/381,266/375,254/374,215/218 already have assigned/gated streams; no safe unassigned backend quick win selected. Existing deep work preserved. No ops/handoff/next_task.md used.

## Proof contract and next concrete actions

Outcome: timely genuine appointments through timer -> publication -> Pages -> public inventory. Effective source freshness about15min, observer configured5min. Last bounded unexpired feed proof23:54:43Z; coverage FAIL at same sample. Existing verify-public-booking-inventory observer last succeeded21:19:34Z; observer-of-observer health unproven. Failure conditions include expired dynamic offers, failed evaluation windows and missed cadence. Local containment depends on CYBERPC awake/online/logged in; Brian must not become routine observer.

Next engineering action: investigate the exact directional-rule failure against current canonical location aliases and source provenance in the existing schedule-truth stream; establish authoritative equivalence before a narrow mapping repair, then run focused negative travel/conflict tests and verify current rendered inventory. This dispatch does not authorize invented travel values. Record this new failure on334 without duplicating the existing cloud alert. Cloud next action remains secure account provisioning, then authenticated timer/health proof and natural customer-facing renewal; configure AVAILABILITY_WATCHDOG_HEALTH_URL after endpoint proof. Account-level action required only for existing secure provisioning gate. Keep334 open. No new deployment claimed.
