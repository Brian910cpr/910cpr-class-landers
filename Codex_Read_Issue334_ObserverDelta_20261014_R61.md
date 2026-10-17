# Issue 334 observer delta R61

Timestamp: 2026-10-14T15:38:00Z (UTC).
Branch: codex/issue334-location-proof-20261014-r56. Existing draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/393 .
Base commit: f6334b99a1194dede3c26aed479a2e7bd8136a6a. Receipt commit: discoverable pushed branch tip and originating issue completion comment (avoids self-referential SHA).
State: BLOCKED for production release. Keep #334 open.

Execution acknowledged before evidence work: https://github.com/Brian910cpr/910cpr-class-landers/issues/334#issuecomment-6172083672 . Read repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design ethos, proof standard and issue history/release gates. Original E:/GitHub/910cpr-class-landers has unrelated dirty work and older instructions; missing handoff there. Used existing clean isolated clone E:/GitHub/910cpr-issue334-r58 on SAME #393 branch, with current protocol. Fetch confirmed remote branch unchanged at base. No worktree cleanup, reset, rebase, merge or other assignment displacement.

## Original scheduled observer evidence

Downloaded existing artifact only; no new workflow dispatch:
`gh run download 38586047253 --repo Brian910cpr/910cpr-class-landers --name public-booking-observation-38586047253 --dir E:/GitHub/issue334-r61-observer`

Run https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/38586047253 : schedule, failure, created 2026-10-14T15:03:59Z, finished 15:04:10Z, head d04974deec51c281f7461fc509433a970e87a328. Artifact 11905601383; original JSON retained byte-for-byte at data/audit/issue334_observer_r61.json. SHA256 5bd3bcf754fd19f7191a82fc20c66d44bbfaff52dc65e06bddad9170c2f26a5b. Observation 15:04:05.802690Z, landscape build fcbc9116bc25, built 14:56:57.734791Z.

All eight families: 437 input/normalized sources; 190 input windows, 188 evaluated, two failed. Exact reason in EACH family:
`missing directional travel rule: :: Wilmington; Shipyard Blvd - B->4018 Shipyard Blvd, Room B, 910CPR Office` (count 2).

Comparison to retained data/audit/issue334_observer_r58.json: same endpoints and counts, but OPPOSITE directional example. R58 reports native label -> Shipyard B; R61 reports Shipyard B -> native label. Initial exact-string equality assertion failed; corrected comparison explicitly asserts both exact directions. This is not a new proven root cause, and a one-way guessed travel rule is unsafe. Original artifact lacks individual failed-window dates; November 3 attribution is retained prior provenance, not newly proved by this artifact. No room identity or travel duration inferred.

| Family | Offers | Dates |
|---|---:|---:|
| BLS | 3622 | 88 |
| Heartsaver | 7565 | 88 |
| ACLS | 3 | 2 |
| PALS | 2 | 1 |
| ARC | 3621 | 87 |
| HSI | 2495 | 87 |
| USCG | 2497 | 88 |
| Family CPR | 1126 | 86 |

Every offer count matches R58. BLS/Heartsaver unexpired at sample, valid until 15:11:19.193822Z. ACLS/PALS seated-only and publicationExpired=true; no dynamic qualification proof inferred. October14 dayFailedWindows=0 across all eight families: today's sparse inventory cannot be attributed to these two failed windows. Heartsaver retains one 17:30 course329495 offer; BLS today zero. No new rendered-browser or checkout proof; no registration/payment submission.

## Validation and scope

Local Python JSON assertions PASS for eight family counts, exact opposite failure directions against R58, unchanged offer totals, October14 zero failures and BLS/HS freshness at sample. Byte equality against downloaded original PASS; existing data/audit/issue334_probe_r57_check.py AST syntax PASS. Whitespace check before commit. Coverage itself remains FAIL by design; passing evidence checks do not mean production recovery. Previous 55 focused tests and authenticated all-family 190/190 zero-failure branch probe 38546492384 reused because no implementation changed; full evidence and reproducible checker: data/audit/issue334_probe_r57.md, data/audit/issue334_probe_r57_original.json, data/audit/issue334_probe_r57.json, data/audit/issue334_probe_r57_check.py.

Exact files changed: data/audit/issue334_observer_r61.json and this root receipt. Only these explicit files staged/committed/pushed. Download directory outside repo intentionally excluded. Original dirty checkout/untracked receipts/runtime artifacts preserved. No application/config/generated-page changes, generator, competing publisher, activation retry, merge or production deployment. Draft #372 untouched. Automatic branch preview is not production proof.

Queue sweep: open CODEX issues and 40 open PRs checked. Existing backend streams #383 scheduling, #387 checkout, #389 documents, #388 finance, #381 manual resolution, #375/#374 fleet and #218 admin auth remain assigned/gated. No safe independent unassigned narrow backend change identified; no duplicate PR or competing deep stream created.

## Exact blocker and next action

Specific owner approval for PR #393 plus documented normal-publisher 40-60 expected generated/state files remains absent. PR reviews empty; Cloudflare bot preview and prior Codex owner-account receipt comments are not new owner authorization. Latest owner triage at15:15Z explicitly retains gate. Existing release request remains concrete in data/audit/issue334_location_r56.md and data/audit/issue334_probe_r57.md: venue-only normalization/conservative existing primary-room fallback; 17 selector/alias/redirect HTML, eight feeds, workflow-allowlisted canonical/admin/landscape/anchor/ical data, native class pages, calendar snapshots/audits/status. No full class/hub rebuild, guessed Room B or travel values. Stop above ten unexpected files. Rollback: reviewed revert of specific PR source/config changes, preserving dirty work and fail-closed gates.

Next: obtain the already-requested specific release decision on #334; after approval recheck #383 compatibility, reuse #393, normal publisher only, verify all eight LIVE families zero failures, preserved November3 noon-2PM occupied interval, rendered BLS/HS legal starts and matching assets/GET registration handoff, then successive renewals before expiry. No duplicate owner notification while unchanged.

Independent cloud gate also unchanged: repository variable AVAILABILITY_WATCHDOG_HEALTH_URL API returned HTTP404. Existing encrypted repository-restricted Actions read/write credential provisioning remains account-level requirement; no secret values read or transmitted. Secure provisioning, health endpoint configuration and independent recovery proof required; no activation retry.

## Persistent proof contract

Repair BUILT/authenticated dry-run validated; historical publication PROVEN, overall HEALTHY unestablished. Last retained customer-flow proof data/audit/issue334_direct_p0_release_20261012.md; no new customer proof here. Latest component sample admin38589998610 and Pages38589453709 succeeded; admin38590736990 running/Pages38590653039 queued at bounded check. Component activity cannot override failed coverage. Separate participant observer38589379962 failed; not retried/diagnosed here.

Expected outcome legal selectable starts renewed before effective source expiry (~15min); booking observer configured five minutes. Failure signals expired feeds or failed/unevaluated windows. Public booking observer plus supervisor observe failures; new natural observer proves detection, not sustained cadence/independent observer health. Missing cloud health and local CYBERPC awake/online/login dependency remain unresolved. Brian must not be routine monitor. Recovery/escalation: scoped release decision, live proof and successive renewals, then secure account provisioning and independent cloud health/recovery proof. Owner action required only for existing specific release decision and secure credential gate.
