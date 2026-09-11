# CyberPC Codex wake worker

`Install-CodexWake.ps1` idempotently installs the Windows Startup worker `910CPR Codex Wake`. A hidden, locked PowerShell loop starts at user logon and runs every 15 minutes. Installed scripts and local state live under `%LOCALAPPDATA%\910CPR\CodexWake`; the Startup launcher lives in the current user's Startup folder. This mode avoids stored passwords and elevation. It is used because this CyberPC session's Task Scheduler accepted task registration but refused to launch even a one-line probe task.

The worker uses an exclusive file lock to prevent overlap, fetches the real checkout at `E:\GitHub\910cpr-class-landers`, reads open `[CODEX]` GitHub issues, and maintains `ops/handoff/codex_heartbeat.json`. A 90-minute dispatch lease prevents repeated launches for the same active item. Logs and authoritative local state live under `%LOCALAPPDATA%\910CPR\CodexWake`.

Heartbeat interpretation:

- `last_check_at`, `queue_count`, and `next_check_due` prove queue-check activity.
- `last_launch_status`, `last_launch_issue`, `last_dispatch_at`, and `last_launch_command` prove that the worker reached the Codex launch boundary.
- `last_launch_completed_at`, `last_launch_exit_code`, and `last_completed_task` prove that the launched process returned successfully. A pushed root `Codex_Reply_*` file remains the end-to-end work receipt.

Install or repair:

```powershell
pwsh -NoProfile -File .\ops\scripts\Install-CodexWake.ps1
```

Safe check without dispatch:

```powershell
pwsh -NoProfile -File .\ops\scripts\Invoke-CodexWake.ps1 -CheckOnly
```

Inspect health:

```powershell
Get-Content "$env:LOCALAPPDATA\910CPR\CodexWake\loop.log"
Get-Content E:\GitHub\910cpr-class-landers\ops\handoff\codex_heartbeat.json
```

Uninstall only when intentionally retiring the worker:

```powershell
Remove-Item "$([Environment]::GetFolderPath('Startup'))\910CPR Codex Wake.cmd"
```
