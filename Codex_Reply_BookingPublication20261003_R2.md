# Recurring public offer expiry: local containment installed

- Timestamp: 2026-10-03T21:06:00Z (17:06 Eastern).
- Branch: `codex/booking-reliability-20261003`, pushed.
- Implementation commit: `bd0bf374fc1` (plus local adapter commit `9e2f2a6a8b6`).
- PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/343
- State at receipt: PR_OPEN; public recovery VERIFIED; local timer CONNECTED.

## Recurrence and immediate recovery

Brian challenged the earlier recovery screenshot. A fresh browser reload at
16:53 Eastern reproduced the failure: only October 12 17:00 Initial survived,
with the stale-publication message. The feed expired at 16:46:50 Eastern after
the successful 15:13 scheduled build. No cloud credential choice had been made,
so the prepared Cloudflare timer was still inactive.

Immediately dispatched existing refresh run 37153148134. Production Pages built
commit `69a0ccadca05b40c2f4cf578ded84f0fe63b1c18` at 20:58:47 UTC. Browser reloaded
and again showed October 5 Initial starts 07:45 through 10:15 with working-format
Enrollware registration links. This is recovery proof, not proof of permanence.

## Automatic local containment

Installed task `910CPR Availability Refresh`, five-minute repetition plus logon
trigger, hidden, current user, no elevation. It reuses the shared watchdog and
existing local `gh api` login. It never reads or copies a GitHub token. No global
execution policy was changed. The standalone local adapter dispatched another
real refresh (37153439228), which succeeded; no browser transaction was submitted.

Actual native scheduled execution was verified at 17:03:13 and the subsequent
timer trigger at 17:05:52 Eastern, with exit 0 and a fresh 17:05:53 observation.
The latter saw 7,678 published course offers, 80 dates, valid through 18:25:24
Eastern. The scheduled task correctly skipped a fresh feed.

Installation:
`D:\Users\ten77\Documents\2020 -_ 2025 & Enrollware\910CPR-AvailabilityRefresh`

State:
`D:\Users\ten77\Documents\2020 -_ 2025 & Enrollware\910CPR-AvailabilityRefresh\state\health.json`

The initial LocalAppData copy was invisible to native Task Scheduler, despite
being readable from this app's shell. Its failed launches were diagnosed before
claiming success. The working physical-drive installation is outside the Git
worktree. The installer now demands a fresh observation from the scheduled
process and restores a prior task if launch verification fails.

## Files and checks

New files: `ops/operator/Run-AvailabilityRefresh.mjs`,
`ops/operator/Install-AvailabilityRefresh.ps1`,
`tests/availability_refresh_local.test.mjs`, and this receipt.

Updated: `docs/availability-refresh-watchdog.md` and
`.github/workflows/verify-canonical-participants.yml`. The cloud health check is
explicitly skipped until `AVAILABILITY_WATCHDOG_HEALTH_URL` is configured, because
the Cloudflare timer is not yet active.

15 Node behavioral tests passed; Node and PowerShell syntax passed; workflow
YAML parse and earlier Wrangler dry-run passed. PR preflight, truncation guard,
and Cloudflare preview passed on implementation commit. No sitewide generator.
Unrelated case-collision changes `docs/Earl/index.html` and
`docs/Jackson/index.html` remain unstaged. Runtime state and diagnostic launcher
logs were not committed. The unused initial LocalAppData copy remains; the task
points exclusively to the physical-drive installation above.

## Exact limitations / next action

The local timer requires CYBERPC awake, online and this user logged in. Successful
scheduled checks are proved. The real dispatch path has been exercised locally,
but a naturally due scheduled refresh cycle still needs observation. There is no
independent observer for a powered-off local computer. Do not call the overall
system HEALTHY or say a screenshot proves recurrence permanently resolved.

Cloudflare activation remains pending Brian's credential choice; no credential
has been moved. After activation and real automatic recovery proof, disable only
the named local task. Until then it supplies automatic local containment while
the existing GitHub schedules remain a delayed fallback. No expiry guard,
occupied-date policy, or roster freshness requirement was weakened.

ChatGPT: preserve the exact diagnosed expiry failure, check fresh scheduled-task
evidence, and complete cloud activation when authorized. Do not ask Brian to
remember routine refreshes. Missing unattended Enrollware roster collection is
a separate unresolved dependency.
