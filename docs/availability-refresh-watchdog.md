# Availability publication recovery

The production BLS selector suppresses dynamic appointments when the published
feed's `validUntil` expires. On 2026-10-03 at 11:36 UTC, that one condition removed
7,612 of 7,619 offers, reducing Initial from 2,425 starts to one real class.
The configured ten-minute GitHub schedule actually ran roughly three to six
hours apart. Successful jobs therefore did not imply continuous availability.

## Recovery proved before implementation

The existing `refresh-admin-availability.yml` was dispatched immediately:
https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/37120275947

It succeeded at 11:45:40 UTC. GitHub Pages deployed commit
`7150450b1c1b5902581a36a61e5174f4e4ee09cd` at 11:46:28 UTC. At 11:55 UTC,
the deployed feed contained 7,643 course offers, 2,779 distinct date/start pairs,
and 80 dates. The browser rendered Initial appointments on October 5 again.
October 12 had only 09:00 Renewal, 12:00 HeartCode, and 17:00 Initial; its orphan
overnight and 12:45 appointments remained absent. Initial and Renewal registration
links still targeted Enrollware sessions 14135047 and 14184954 respectively.

## Smallest durable change

`worker/availability-refresh-watchdog.mjs` reads the existing public BLS feed
every five minutes through a Cloudflare Cron. When fewer than 60 minutes remain
on the unchanged 90-minute publication lease, it dispatches the existing bounded
GitHub refresh on `main`. It neither generates offers nor extends their leases.
All calendar, occupied-date, roster freshness, and course compatibility gates
continue to run inside the existing publisher.

Active/queued refreshes prevent duplicate dispatches. A ten-minute KV cooldown
covers delayed visibility of a just-dispatched run. Failed public feed reads also
request recovery. Upstream errors are sanitized and bodies are bounded. The
public HTTP endpoint only reads health; it cannot dispatch jobs.

This fixes publication cadence and introduces no additional Enrollware dependency.
It does not solve the separate missing unattended complete-roster collector.

## Deployment

Use `worker/wrangler.availability-refresh.jsonc`, never the root configuration,
which belongs to the existing free-time Worker. Keep its routes, bindings and
secrets unchanged. The new Worker uses namespace
`53b5ac2432a946efaf2c094c07142ba7` and a secret `GITHUB_ACTIONS_TOKEN`.
Prefer a repository-restricted fine-grained token with Actions read/write on
`Brian910cpr/910cpr-class-landers`. Do not put secrets in this repository, logs,
command arguments, PRs, or replies. Deploy through an authenticated Cloudflare
connector if local Wrangler authentication is location-blocked.

Local checks:

```text
node --check worker/availability-refresh-watchdog.mjs
node --test tests/availability_refresh_watchdog.test.mjs
wrangler deploy --config worker/wrangler.availability-refresh.jsonc --dry-run
```

## Proof and health contract

- Outcome: a fresh publication reaches the actual public booking page before the
  previous publication expires. A dispatch or successful build alone is not proof.
- Cadence: Cron every five minutes, refresh normally about every 30 minutes.
- Observer: the Worker reads the real public feed; `/health` exposes the observed
  expiry, offer count, last check, dispatch and active run ID without credentials.
- Failure: expired/missing public feed, a refresh pending for over 30 minutes,
  GitHub errors, or a heartbeat older than 12 minutes returns HTTP 503.
- Observer health: `verify-canonical-participants.yml` independently checks the
  Worker endpoint. GitHub's delayed schedules make this a delayed backup, not a
  five-minute alert guarantee. Cloudflare invocation logs retain each Cron result.
- Recovery: the timer dispatches the existing refresh. It does not cancel active
  publishers, bypass validation, invent availability, or mutate registrations.
- Escalation: credential revocation, persistent upstream outage, hung refresh or
  invalid generated inventory requires repair; the health result remains red.
- Acceptance: observe real Cron dispatch -> successful publisher -> fresh public
  feed -> rendered appointments, then a later timer cycle. Record exact times.

Until those real cycles are observed, classify this addition as BUILT/CONNECTED,
not HEALTHY. The manual recovery above is PROVEN separately.

## Local containment after the October 3 recurrence

At 16:53 Eastern the public page had again fallen back to its one Initial class.
The latest scheduled refresh had started at 15:13 Eastern and succeeded, but its
publication expired at 16:46:50. Another recovery was dispatched immediately:
https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/37153148134

While approval for the separate cloud credential remains pending, install the
same watchdog on the already authenticated computer:

```powershell
& .\ops\operator\Install-AvailabilityRefresh.ps1
Get-ScheduledTaskInfo -TaskName '910CPR Availability Refresh'
Get-Content "$env:LOCALAPPDATA\910CPR\AvailabilityRefresh\state\health.json"
```

The installer copies only the watchdog and its local adapter into
`%LOCALAPPDATA%\910CPR\AvailabilityRefresh`, creates a hidden five-minute Windows
scheduled task plus a logon trigger, and starts it immediately. It runs as the
current user without elevation. The adapter uses `gh api` with the existing
keyring login for only the fixed refresh workflow; it never reads, copies, saves,
or logs the token. Runtime state remains outside the repository. Overlapping
local task instances are ignored. Publication and active-run guards also prevent
unnecessary GitHub work.

This is local containment, dependent on this computer being awake, online, and
logged in. `health.json` includes actual publication expiry and the timer check;
evaluate its `checkedAt` age when reading it, since any stored `ok` is historical.
Task Scheduler exposes last execution and exit code. There is no independent
local-task observer yet, so do not call the overall persistent system HEALTHY.
The cloud timer remains the path to remove the computer uptime dependency.
Enable the existing independent cloud health job by setting repository variable
`AVAILABILITY_WATCHDOG_HEALTH_URL` to the deployed `/health` endpoint only after
activation. Its unset state explicitly skips that unavailable observer.

To stop this containment after cloud proof, disable exactly the named task:
`Disable-ScheduledTask -TaskName '910CPR Availability Refresh'`. Preserve its
state as evidence. Do not delete or modify the separate 910CPR operator worker.

CYBERPC activation uses the explicit physical-drive directory
`D:\Users\ten77\Documents\2020 -_ 2025 & Enrollware\910CPR-AvailabilityRefresh`.
Native Task Scheduler could not see the first app-private LocalAppData copy.
The installer now requires a fresh observation from the actual scheduled process
and restores any prior task if that proof fails. It uses the current PowerShell
host without changing execution policy. At 17:03:13 Eastern, Task Scheduler ran
the physical-drive installation successfully (exit 0), observed the fresh public
feed, and recorded 7,678 offers valid through 18:25:24 Eastern. This proves the
installed timer can read the publication; a future automatic refresh dispatch
must still be observed before claiming unattended recovery is proven.
