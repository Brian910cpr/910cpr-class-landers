# Codex reply: Issue #174 Round 2

- Timestamp: 2026-09-11T10:53:00-04:00 (America/New_York)
- Assignment: GitHub issue #174, Round 2 closed-loop proof/repair
- Branch: `codex/issue-174-durable-wake-r2`
- Substantive commit: `e3d421e2123e4beb42aaf906c8b59756858ad1dd`
- Work-item state: `VERIFIED`
- Persistent-system evidence state: `PROVEN` (not yet `MONITORED` or `HEALTHY`)

## Findings and root cause

Facts:

- The one installed dispatcher is the per-user Windows Startup entry `910CPR Codex Wake`, which runs the hidden `Start-CodexWakeLoop.ps1` process from `%LOCALAPPDATA%\910CPR\CodexWake` every 15 minutes. No second Codex dispatcher Scheduled Task was found. The unrelated scheduled task `910CPR Contact Bot` remains untouched.
- The original loop continued after the first 90-minute lease expired, but cycles returned exit code 1 from 05:46 through 10:49 EDT.
- The first failure was PowerShell scalar/array handling after `gh issue list`: the JSON result could not be converted to an issue number because the pipeline produced a `System.Object[]` shape.
- After that was repaired, an attempted dispatch at 10:48 EDT reached `codex.exe` but failed because `-a` was placed after the `exec` subcommand. Codex 0.153.4 reported `unexpected argument '-a' found`.
- After correcting the invocation to `codex.exe -a never exec ...`, the genuinely automatic Startup loop cycle checked the queue at `2026-09-11T10:49:57.8889200-04:00`, selected preferred eligible issue #174 from 11 open `[CODEX]` items, resolved `codex.exe`, and launched PID 17932 at `2026-09-11T10:49:59-04:00` without Brian manually launching Codex.
- The launched process is this Round 2 Codex run. Its durable end-to-end result is this pushed repository-root receipt.

## Work performed

- Made GitHub issue JSON parsing deterministic for both scalar and multiple-result output.
- Preserved non-terminating native stderr while explicitly checking exit codes for `git` and `codex.exe`.
- Corrected Codex CLI global option ordering.
- Changed seeded work from a false active lease to a preferred issue, allowing the next automatic cycle to dispatch it.
- Kept the exclusive worker lock and 90-minute dispatch lease.
- Added launch-specific heartbeat fields so queue-check health can be distinguished from launch start, launch completion, and launch failure.
- Added the required receipt name to the #174 dispatch prompt and retained the explicit prohibition on the retired `ops/handoff/next_task.md` path.
- Reinstalled the repaired script into `%LOCALAPPDATA%\910CPR\CodexWake`; the installed and repository script SHA-256 hashes matched. A transient second loop process exited under the existing exclusive loop lock, leaving only PID 6704.

## Exact files changed

- `ops/scripts/Install-CodexWake.ps1`
- `ops/scripts/Invoke-CodexWake.ps1`
- `ops/scripts/README_CODEX_WAKE.md`
- `Codex_Reply_CodexWake_R2.md`

No generated public pages were rebuilt. No customer-facing files were intentionally changed or staged.

## Tests and checks

- PowerShell parser validation passed for `Install-CodexWake.ps1`, `Invoke-CodexWake.ps1`, and `Start-CodexWakeLoop.ps1`.
- `git diff --check` passed for the intended script/documentation changes.
- Installed/repository `Invoke-CodexWake.ps1` SHA-256 hashes matched after repair installation.
- Process inspection confirmed exactly one continuing Startup loop after the install-time contender exited via the exclusive lock.
- Live process inspection confirmed automatic `codex.exe` PID 17932, created at 10:49:59 EDT, with issue #174 and the required Round 2 receipt in its command line.
- Local state at dispatch recorded `last_check_at=2026-09-11T10:49:57.8889200-04:00`, `last_dispatch_at=2026-09-11T10:49:59.4130559-04:00`, `worker_state=working`, `current_task=174`, and `queue_count=11`.
- The substantive branch push succeeded before this receipt commit.

## Known unrelated state and dependency gates

- The original checkout contained unrelated modified/generated files and an untracked heartbeat. They were preserved and not staged.
- The clean Round 2 worktree also showed unrelated modifications to `docs/Earl/index.html` and `docs/PALS.html`; they were not staged or committed.
- Dependency issues #164 and #167 remain open. In accordance with issue #174, no customer-facing expansion was resumed.
- Cloudflare OAuth emitted a plugin warning in the launched Codex session, but it did not block repository/GitHub work and is not the dispatch root cause.

## Deployment and proof classification

- Local validation: passed as described above.
- CyberPC installation: repaired and active for the logged-on user.
- Push: substantive commit and this receipt are pushed on `codex/issue-174-durable-wake-r2`.
- Merge: not performed.
- Production deployment: not applicable; no customer-facing deployment was requested or changed.
- `PROVEN`: automatic Startup cycle -> eligible `[CODEX]` selection -> `codex.exe` launch -> issue work -> pushed `Codex_Reply_CodexWake_R2.md` completed.
- Not `MONITORED`/`HEALTHY`: the current mechanism is user-logon scoped and no independent remote observer currently alerts on a stale heartbeat. The new heartbeat fields improve diagnosis but do not by themselves provide an observer-of-observer.

## Remaining risks and next action

- Logged-off execution is not provided by the Startup-folder design. The least-invasive durable logged-off alternative is a Windows Scheduled Task running as the same user with `Run whether user is logged on or not`; this requires Windows to store/validate that account credential and was not silently substituted because the earlier Task Scheduler probe would not launch.
- The worker operates against a deliberately dirty primary checkout. Each dispatched Codex run must continue using a separate worktree and explicit staging, as this round did.

Recommended ChatGPT action: inspect commits `e3d421e2123e4beb42aaf906c8b59756858ad1dd` and this receipt commit, confirm the automatic launch evidence, then merge the narrow three-file repair if acceptable. Track stale-heartbeat remote observation and logged-off Task Scheduler execution as follow-up hardening rather than describing the system as `HEALTHY` today.

User/account-level action required: none for the currently logged-on Startup loop. A Windows credential/account action would be required only to enable the logged-off Scheduled Task alternative.
