# Codex Reply: CodexWake

## Assignment

- Issue: `#174` — install durable Codex wake/dispatcher without legacy handoff polling
- Timestamp: `2026-09-11T04:32:00-04:00`
- Branch: `codex/issue-174-durable-wake`
- Substantive commits: `c1bed0cc6d4`, `7f0d7d299e5`
- Pull request: `#182`
- Work-item state: `PR_OPEN`
- Persistent-system evidence state: `PROVEN` for one automatic queue-check cycle; not yet `MONITORED` or `HEALTHY`

## Findings and root cause

No existing Codex watcher, service, Startup item, Codex automation, or relevant scheduled task was present. The existing `910CPR Contact Bot` Scheduled Task is unrelated and already failing; it was not changed.

A dedicated `910CPR Codex Wake` Scheduled Task was built and registered, but Task Scheduler on this CyberPC session refused to launch it. A separate one-line probe task also returned result `1` without creating its probe output, proving the problem was the execution environment rather than the wake script. Enabling the Task Scheduler Operational log requires elevation and was denied. The failed Codex task was removed so no duplicate dispatcher remains.

The working Windows-native fallback is a current-user Startup background PowerShell loop. It requires neither elevation nor a stored password and is active while the owner is logged on.

## Installed mechanism

- Name/type: `910CPR Codex Wake` — Windows Startup background loop
- Startup launcher: `C:\Users\ten77\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\910CPR Codex Wake.cmd`
- Installed worker directory: `C:\Users\ten77\AppData\Local\910CPR\CodexWake`
- Live process observed: PID `14844`
- Cadence: every 15 minutes
- Target checkout: `E:\GitHub\910cpr-class-landers`
- Intake: open GitHub issues whose titles begin `[CODEX]`
- Outbound mail: repository-root `Codex_Reply_*` files only
- Overlap protection: exclusive long-lived `loop.lock`, exclusive per-cycle `worker.lock`, and a 90-minute dispatch lease
- Heartbeat: `E:\GitHub\910cpr-class-landers\ops\handoff\codex_heartbeat.json` (ignored by Git)
- Local logs/state: `%LOCALAPPDATA%\910CPR\CodexWake`

## Automatic proof

The installer seeded issue `174` as the current leased work item so the new worker would not launch a duplicate Codex session while this assignment was already running.

The background loop started at `2026-09-11T04:31:07.9492086-04:00` with PID `14844`. Without a manual worker invocation, it completed its first delayed cycle at `2026-09-11T04:31:29.4588230-04:00` with `cycle_exit=0`. The heartbeat independently recorded:

- `last_check_at`: `2026-09-11T04:31:29.4371103-04:00`
- `worker_state`: `idle`
- `current_task`: `174`
- `blocked_reason`: `active_dispatch_lease`
- `next_check_due`: `2026-09-11T04:46:29.4391099-04:00`
- `last_commit`: `3e28feb146fb32dca41a85d99024044a1388f259`

This proves automatic startup-loop execution, repository fetch, GitHub queue read, heartbeat write, and lease-based duplicate suppression. Only one automatic cycle has been observed, so the worker is not yet classified as monitored or healthy.

## Files changed

- `.gitignore`
- `ops/scripts/Install-CodexWake.ps1`
- `ops/scripts/Invoke-CodexWake.ps1`
- `ops/scripts/Start-CodexWakeLoop.ps1`
- `ops/scripts/README_CODEX_WAKE.md`
- `Codex_Reply_CodexWake.md`

## Validation

- PowerShell parser validation passed for all three `.ps1` files.
- `git diff --check` passed for substantive changes.
- Installer was run on CyberPC and is idempotent.
- Safe direct worker check returned exit `0` and found the durable GitHub queue.
- Long-lived loop and per-cycle lock behavior were exercised during installation/retries; duplicate loop starts exit without creating a competing worker.
- One automatic background-loop cycle returned exit `0` and advanced the heartbeat.
- No application generator, public build, deployment, or production-data mutation was run.

## Unrelated local state preserved

The real checkout at `E:\GitHub\910cpr-class-landers` was already on `codex/durable-session-participant-linking` with modified/generated or cache files. It was not switched, cleaned, staged, or committed. The implementation was made in a separate worktree. Windows case-colliding generated pages (`docs/Earl/index.html`, `docs/HEARTSAVER.html`, `docs/PALS.html`) also appeared modified in that clean worktree and were intentionally left unstaged.

## Remaining risks and next action

- The Startup loop runs only while the user is logged on. A true logged-off/background service would require resolving Task Scheduler execution policy or installing a service with elevated authority.
- The worker is `PROVEN` by one automatic cycle, not yet `MONITORED` or `HEALTHY`. Confirm later heartbeat advancement and stale-process recovery before promoting its evidence state.
- The active issue-174 lease intentionally prevents a duplicate launch for 90 minutes. After this work is acknowledged/merged, clear or update the local current-task state so the next eligible issue may dispatch.
- Merge PR `#182` after review. Then observe at least one later 15-minute heartbeat cycle. If acceptable, acknowledge this file by renaming it to `Codex_Read_CodexWake.md`; Codex must not perform that rename.

No Brian-only credential or account action is currently required. Elevation is required only if the preferred logged-off Task Scheduler/service model is revisited.
