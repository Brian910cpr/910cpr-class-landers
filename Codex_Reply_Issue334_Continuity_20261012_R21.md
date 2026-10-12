# Issue #334 continuity/readiness R21

Timestamp: 2026-10-12T02:42:00Z (October 11 22:42 Eastern)
Branch: codex/issue334-continuity-r21
Substantive commit: 50260ad0bf77a802d2b81b9b1ce4a4e55506da6a
Work state: IN_PROGRESS; activation/release BLOCKED pending specific owner approval.
Evidence: existing publisher PROVEN; new cadence change BUILT and locally validated, not activated or HEALTHY.
Public booking readiness: AT RISK.

## Findings and exact evidence

Full owner issue body/comments, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md,
LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md read.
Execution acknowledged before implementation at issue comment 6116737934.
Latest owner correction followed: standard public selectors -> Enrollware;
/corp/maxim.html was not tested or changed. No registration/payment submitted.

Primary report: data/audit/issue334_continuity_r21.json (full structured evidence).
Exact JSON paths: publications[].sha, pagesRun, pagesCompletedAt,
families.bls.deliveryMarginSeconds, families.heartsaver.deliveryMarginSeconds;
live.bls and live.heartsaver hold timestamped counts, URLs and handoff failures.

Eight successful Pages publications were correlated with both family payloads.
Seven adjacent deployment-completion margins were positive: 159.394722,
234.229679, 160.292885, 194.627560, 289.213089, 419.701803, 510.248437 seconds.
These are repository/deployment timing proxies, not continuous browser proof.
The initially suspected 02:29:29 -> 02:31:12 gap was disproven by intervening
Pages 38195607809 at 02:24:40, publishing 1ec1ba674b7004d3e60729837aece45f63b47f5c
with expiry 02:38:11.701803. No outage duration can be assigned to that interval.
Owner screenshot around 22:20 ET and recovery around 22:24 ET are consistent
with a boundary event but do not establish exact seconds or the specific edge
payload. Recent collected publications do not explain that reported flicker.
Exact historical customer outage duration remains UNKNOWN; do not invent it.

Live GET observations 02:40:02.894134Z BLS / 02:40:03.583235Z Heartsaver:
- Both pages HTTP 200 and load their corresponding resolved availability feed.
- Both feeds unexpired through 02:53:22.461266Z.
- BLS: 3,991 offers, 87 dates, 1,512 start-time groups.
- Heartsaver: 8,297 offers, 81 dates, 1,506 start-time groups.
- Both: 209 input windows, 189 evaluated, 20 failed/uncertain windows.
- Exact representative appointment URLs are in live.*.sampleOffer.registrationUrl,
  retaining source course IDs and appointmentDayId=260786.
- Python verified-TLS GET to those Enrollware URLs failed CERTIFICATE_VERIFY_FAILED:
  certificate has expired. No TLS bypass performed.
- Independent Windows curl HEAD https://coastalcprtraining.enrollware.com/ reached
  HTTP 403 (Cloudflare); thus Python trust failure is not proof of a universal
  customer certificate outage. Browser/checkout handoff remains UNPROVEN.

Source coverage is effectively 15 minutes. The existing nominal 10-minute
watchdog dispatch spacing leaves only a small build/Pages reserve. Proposed
containment changes cooldown from 570,000ms to 270,000ms, permitting each existing
five-minute tick after completion, retaining 30-second jitter tolerance, active/
queued-run suppression, fixed-main workflow, error handling and freshness gates.
No TTL extension, course/conflict/checkout policy, source mapping or offer geometry
changed. This increases refresh load up to one per five-minute timer tick while
source lease is short. It cannot guarantee continuity during long build/Pages
queues. Existing Enrollware dependency is preserved temporarily; none added.

## Changed files and tests

Intended files only:
- worker/availability-refresh-watchdog.mjs
- tests/availability_refresh_watchdog.test.mjs
- docs/availability-refresh-watchdog.md
- scripts/audit_publication_continuity.py
- data/audit/issue334_continuity_r21.json
- Codex_Reply_Issue334_Continuity_20261012_R21.md

Commands/results:
node --check worker/availability-refresh-watchdog.mjs: passed.
node --test tests/availability_refresh_watchdog.test.mjs tests/availability_refresh_local.test.mjs:
18 tests, 18 passed, 0 failed. Includes new five-minute boundary/cooldown cases
and queued/in-progress/waiting/pending duplicate refusal; errors and allowlist retained.
Python ast.parse audit script and JSON/live evidence assertions: passed.
git diff --check intended source/test/doc files: passed.
Reusable read-only command:
python scripts/audit_publication_continuity.py --output data/audit/<unique-name>.json
It fetches GitHub/public feeds/pages and GETs a representative Enrollware link;
it never submits forms or registrations. It catches and records handoff failures.

Original E:\GitHub\910cpr-class-landers dirty/corrupt checkout preserved.
Prior r20 worktree preserved. New isolated worktree E:\GitHub\issue334-continuity-r21
also acquired unrelated docs/Earl/index.html and docs/Jackson/index.html edits
from another process; these remain unstaged/uncommitted. Never restored/cleaned.
No generator ran. No unexpected bulk generation. No new PR or competing scheduling
implementation stream created. Existing #385 venue repair and #383 constraints
remain open and untouched; #372 not merged/deployed. Queue scanned; no safe
unassigned narrow backend quick win found without duplicating existing assignments.

## Proof contract, release scope and next action

Last local timer proof: physical installation health checked 02:35:54.329Z,
dispatch same time, exit 0; correlated admin run 38196409024. The LocalAppData
health copy is obsolete (October 3); only physical-drive installation is active.
Task Scheduler reported last result 0 and next tick 02:40:52Z at observation.
Failure condition: missing/expired public feed or stale observer heartbeat.
Observer: existing five-minute local task, public-feed health; independent cloud
observer variable AVAILABILITY_WATCHDOG_HEALTH_URL still HTTP 404.
Observer health/independence remains unresolved; CYBERPC awake/login/network
continues as an operational dependency. Existing cloud-token gate unchanged.
Recovery: existing bounded publisher, no conflicting manual refresh dispatched.

Smallest release request on originating issue: approve activation of ONLY the
270,000ms cooldown change in the existing physical-drive local timer's
worker/availability-refresh-watchdog.mjs, after review/integration through the
existing #334 stream. No installer/task recreation, no secret changes, no
Cloudflare deploy, no sitewide generator, no #372 merge. Installed code replacement
is one runtime file; retain prior file/hash as rollback and preserve state/task.
Next natural ticks may run the already existing production publisher with its
normal workflow-owned generated output; this is not approval to broaden builders.
Rollback: restore only that saved runtime worker file; do not reset Git/worktrees
or delete timer state. Verify loaded file hash and two consecutive natural
renewals at the public page/feed before prior expiry, including browser-visible
BLS/Heartsaver starts and an unsubmitted Enrollware handoff. Retain longer watch.

No activation performed: owner comment explicitly limits move-forward to
investigation/code/tests/PR preparation and requires specific release approval.
No merge/deployment claimed. The branch/receipt are pushed; receipt-tip SHA is
reported in issue/final response (avoids self-referential SHA).

Next ChatGPT action: review the six exact paths, resolve the above narrowly scoped
activation decision on #334, and continue canonical Oct14 skills/neighbor analysis
in existing PR #385/#383 stream. Venue-mapping fix is independent of continuity.
Owner/account action: specific runtime activation approval; independent cloud
activation still needs the previously recorded restricted encrypted Actions token.
Do not ask Brian to become the recurring monitoring layer. Keep #334 OPEN.
