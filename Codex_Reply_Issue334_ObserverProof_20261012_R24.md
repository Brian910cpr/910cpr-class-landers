# Issue 334 — observer proof R24

Timestamp: 2026-10-12T05:00:00Z (UTC)
Branch: codex/issue334-observer-proof-r24
Evidence commit: e6f91131836f0048352602f1dde8acfaefc5ceeb (runtime hash path corrected in receipt commit).
State: BLOCKED on independent-cloud activation; publication diagnostic VERIFIED at sampled time. Keep #334 OPEN.

## Findings and work
Read issue body and complete comment history, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design ethos and proof standard. Acknowledged execution before implementation at issuecomment-6118025362. No application implementation was needed after accepted #385/#386 repairs.

Live read-only audit observed at 2026-10-12T04:57:49Z: all eight families evaluate 210/210 windows with zero failed windows. BLS 4018 offers/88 dates; Heartsaver 8370/87. Both unexpired; BLS generated 04:53:22.834278Z and valid through 05:08:22.141701Z. October 14 Heartsaver retains 17:30 seated and 19:30 skills starts. Other-family exact counts, per-course counts and suppression reasons are in the live evidence JSON. HTTP GETs for both public HTML pages returned 200. No fresh browser rendering or booking/payment proof claimed.

Timer source and physical runtime SHA256 both 7aed7695d4cb167b967bb310b9b506999149e6f88ca9c70223a63742bbf19bb5. Task last run 04:55:53Z, exit 0; health checked 04:55:53.439Z and observed 04:55:56.241Z. Dispatch correlates with admin run 38205778001, in progress at snapshot. Prior admin 38205446214 succeeded; Pages 38205644107 succeeded at 04:54:53Z for production commit 17410690258acf6f555a83b7325aca0dfcad79bb.

## Exact blockers and health contract
Independent cloud activation remains blocked by the existing repository-restricted Actions read/write credential approval/storage gate. No secret was read or changed. GET repository variable AVAILABILITY_WATCHDOG_HEALTH_URL returned HTTP 404. Do not retry activation without new credential/configuration evidence.

Scheduled observer remains unproven: workflow configured every five minutes, but full available run history contains only manual 38198348377 (success) and 38197805655 (old-payload failure). No natural scheduled heartbeat exists in this evidence. This does not establish a new failure cause or justify competing refreshes.

Evidence state: PROVEN local publication, not overall HEALTHY/cloud-independent. Expected outcome is unexpired, conflict-safe public dynamic choices; source window is about 15 minutes, local task ticks five minutes with 270000ms cooldown. Stale validUntil, missing BLS/Heartsaver dynamic inventory or nonzero window failures are failure signals. Public observer checks them, but its own scheduled heartbeat is unproven. Local task remains dependent on CYBERPC awake/login/network. Recovery: inspect current feed/run chain and deduplication before bounded existing publisher recovery; cloud account credential is escalation boundary. Brian must not be routine observer.

Next: prove a genuine scheduled public observer cycle, then activate/verify existing cloud timer only after secure credential gate is satisfied, configure health URL and require independent observer success. Preserve existing #383 compatibility work. No duplicate PR created; #372/#383/#387 and all existing assignments untouched.

## Files and validation
Only intended files committed:
- data/audit/issue334_observer_r24_live.json
- data/audit/issue334_observer_r24_runs.json
- data/audit/issue334_observer_r24_observer.json
- data/audit/issue334_observer_r24_local.json
- Codex_Reply_Issue334_ObserverProof_20261012_R24.md

Read-only live audit exit 0. Python AST syntax validation passed; evidence JSON parsing passed; git diff --cached --check passed. No source changes, so prior accepted behavioral tests reused rather than rerun. Source/runtime hashes verified. Initial hash read used wrong runtime root path, failed without mutation, then corrected to worker/availability-refresh-watchdog.mjs.

Original E:/GitHub/910cpr-class-landers dirty files preserved. Fetch failed with bad object 6e61cabca5981d1389e52c60d95424d9893bb50f and refs/remotes/origin/codex/group-training-experience; no ref repair/cleanup attempted. Used separate shallow clone E:/GitHub/910cpr-issue334-r24. Windows case collisions leave docs/Earl/index.html and docs/Jackson/index.html modified there; deliberately unstaged. No generators, installs, task changes, merge or deployment performed by this dispatch. Receipt/evidence persisted locally and pushed on named branch; remote verification recorded on originating issue.

Queue sweep reviewed open issue and PR inventory. Existing backend streams are assigned, gated or substantial; no independent narrow eligible backend change identified without inventing scope or disrupting existing assignments. No new competing deep stream started. Account-level action remains only the existing secure cloud credential gate; no new approval requested for this diagnostic.
