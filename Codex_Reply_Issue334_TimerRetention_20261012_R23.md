# Issue #334 — approved timer source retention R23

Timestamp: 2026-10-12T04:23:00Z (UTC).
Branch: codex/issue334-timer-retention-r23.
Substantive commit: d56e93ad15146db35f6322badf244ee216d299a2.
State: PR_OPEN; independent-cloud portion BLOCKED.
PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/386
Execution acknowledgment: https://github.com/Brian910cpr/910cpr-class-landers/issues/334#issuecomment-6117668692

## Findings and work

Read the complete #334 issue/comment history, current repository AGENTS.md,
CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_PROOF_AND_HEALTH_STANDARD.md,
LANDERWARE_DESIGN_ETHOS.md and docs/CODEX_INSTRUCTIONS.md before implementation.
Accepted link/native/#385 fixes are preserved. Owner's latest remaining scope
includes retaining the already-approved physical timer source and proving the
scheduled observer; cloud activation remains gated. No open PR covered timer
retention; #386 is a narrow continuation of the R21 change, not another scheduling
engine stream. R21 history and PR #383 remain intact.

Main still held the former nominal ten-minute cooldown although the approved
physical timer uses nominal five minutes. A reinstall from main could regress
continuity. Reused exactly R21's worker/test delta: DISPATCH_COOLDOWN becomes
5 * MINUTE - 30_000 (270000ms), preserving the active-run guard, fixed main workflow,
source expiry, conflict and scheduling gates. Documentation now states the
actual cooldown and 15-minute upstream freshness constraint. No new cloud API,
binding, secret, framework or generation behavior introduced. This retains local
containment; it does not remove Enrollware or CYBERPC dependencies.

Installed runtime and repository source both SHA256:
7aed7695d4cb167b967bb310b9b506999149e6f88ca9c70223a63742bbf19bb5

Physical runtime inspected read-only:
D:\Users\ten77\Documents\2020 -_ 2025 & Enrollware\910CPR-AvailabilityRefresh\worker\availability-refresh-watchdog.mjs
State inspected read-only:
D:\Users\ten77\Documents\2020 -_ 2025 & Enrollware\910CPR-AvailabilityRefresh\state\health.json
Task: 910CPR Availability Refresh; last result 0.
checkedAt/lastDispatchAt: 2026-10-12T04:15:54.423Z.
action: refresh_dispatched; heartbeatStale=false; publicationExpired=false.
No installer, runtime replacement or task/state mutation performed.

## Exact intended files

- worker/availability-refresh-watchdog.mjs
- tests/availability_refresh_watchdog.test.mjs
- docs/availability-refresh-watchdog.md
- data/audit/issue334_retention_r23_live.json
- Codex_Reply_Issue334_TimerRetention_20261012_R23.md

Primary exact structured evidence is data/audit/issue334_retention_r23_live.json:
$.observedAt, $.families.<family>.counts, $.families.<family>.validUntil,
$.families.<family>.publicationExpired, $.families.<family>.failedWindowReasons,
$.landscape.sourcePages. No participant data or credentials recorded.

## Validation and operational evidence

Commands/results:
- node --check worker/availability-refresh-watchdog.mjs: exit 0.
- node --test tests/availability_refresh_watchdog.test.mjs: 15 tests,15 pass,0 fail.
- node --test tests/availability_refresh_local.test.mjs: 3 tests,3 pass,0 fail.
- git diff --check: exit 0.
- python scripts/audit_family_publication_coverage.py --live --continuity --output data/audit/issue334_retention_r23_live.json: exit 0.

Live read-only checkpoint 2026-10-12T04:20:03.935260+00:00:
All eight families evaluate 209/209 windows with zero failed windows.
BLS 4018 offers/88 dates; Heartsaver 8370/87; ACLS 3/2; PALS 2/1;
ARC 4015/87; HSI 2763/87; USCG 2766/87; Family 1252/85.
BLS generatedAt 2026-10-12T00:14:39.470371-04:00;
validUntil 2026-10-12T00:29:38.415506-04:00; not expired.
October14 Heartsaver retains17:30 seated and19:30 skills.
Counts are not a new browser/checkout proof. No registration/payment submitted.

Last inspected successful delivery: Pages38203040604, source
0091bb6e1c67be2a9f263c3ae670cea3bfd146a9, deploy completed04:16:20Z.
Recent natural local dispatches continue at five-minute intervals. No competing
refresh dispatched. Earlier screenshot outage duration remains unknown; this
checkpoint does not erase prior observed lease-boundary outages.

## Proof contract and exact blockers

Evidence level: PROVEN local publication; overall public readiness AT RISK,
not overall HEALTHY or cloud-independent MONITORED.
Expected outcome: fresh genuine public offers reach customers before prior expiry.
Window: five-minute timer; upstream calendar freshness15minutes, regardless of90minute
outer TTL. Failure: expired/missing feed, no dynamic BLS/HS offers, failed windows,
stalled publisher or stale heartbeat. Local observer is the existing task/feed
check; Task Scheduler exit0 and04:15:54Z health timestamp evidence its execution.

New public observer: verify-public-booking-inventory.yml configured */5 cron, but
GitHub history still contains only manual38197805655(failed old payload) and
38198348377(success). No natural scheduled heartbeat is yet evidenced.
Independent cloud URL query:
gh api repos/Brian910cpr/910cpr-class-landers/actions/variables/AVAILABILITY_WATCHDOG_HEALTH_URL
Result: HTTP404 Not Found. Existing owner-approved repository-restricted Actions
read/write encrypted GITHUB_ACTIONS_TOKEN setup remains unresolved; no new
credential or permission assumed. Canonical observer38192972069(event schedule)
failed reconciliation-health; verify-demand,verify-publication-watchdog and
verify-production skipped. That unrelated reconciliation failure is preserved,
not repaired or bypassed by this timer change.

Recovery: retain current physical timer; inspect active publisher/Pages before any
bounded recovery to avoid competing refreshes. CYBERPC awake/login/network remains
required. Observer monitoring and notification delivery are unproven. Brian must
not become the routine check layer; unresolved dependency remains explicit.

## Persistence, review and next action

Intended source/docs/audit changes persisted locally, committed and pushed.
PR386 open; initial source-integrity/preflight checks pass, newest checks/preview
pending at checkpoint. No merge or deployment performed by this dispatch.
Physical timer was already owner-approved/activated in the prior stream; this
assignment only retains its matching source. No broad generator ran.
Draft372 remains open/untouched;383 remains draft/untouched and needs independent
compatibility validation against merged385 before any future release.

Original E:\GitHub\910cpr-class-landers dirty files and corrupt Git reference
(bad object6e61cabca5981d1389e52c60d95424d9893bb50f) preserved. Healthy existing clone
used to create isolated worktree E:\GitHub\issue334-timer-retention-r23.
Checkout also shows unrelated docs/Earl/index.html and docs/Jackson/index.html
changes; both explicitly excluded from staging and remain uncommitted. No cleanup.
Queue scanned; existing drafts/gated implementation assignments preserved. No
independent unassigned narrow backend quick win justified without another stream.

ChatGPT next: review worker/test/docs in386 and integrate approved source retention
when checks pass; preserve installed task/state and prior rollback. Observe a real
scheduled public observer cycle and correlate subsequent natural Pages renewals
with prior validUntil. Satisfy existing encrypted cloud token/health URL gate before
activation; independently prove observer health. Keep334OPEN. No further owner
approval needed for investigation/source preparation; account action remains only
the existing secure cloud credential gate. Do not merge/deploy372.