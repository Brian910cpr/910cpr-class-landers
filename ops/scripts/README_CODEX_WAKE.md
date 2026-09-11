# CyberPC Codex wake worker

`Install-CodexWake.ps1` idempotently installs the Windows Scheduled Task `910CPR Codex Wake`. It runs every 15 minutes while the owner is logged on and invokes the installed copy of `Invoke-CodexWake.ps1` from `%LOCALAPPDATA%\910CPR\CodexWake`. Interactive-token mode avoids storing a password and does not require elevation.

The worker uses an exclusive file lock to prevent overlap, fetches the real checkout at `E:\GitHub\910cpr-class-landers`, reads open `[CODEX]` GitHub issues, and maintains `ops/handoff/codex_heartbeat.json`. A 90-minute dispatch lease prevents repeated launches for the same active item. Logs and authoritative local state live under `%LOCALAPPDATA%\910CPR\CodexWake`.

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
Get-ScheduledTask -TaskName '910CPR Codex Wake'
Get-ScheduledTaskInfo -TaskName '910CPR Codex Wake'
Get-Content E:\GitHub\910cpr-class-landers\ops\handoff\codex_heartbeat.json
```

Uninstall only when intentionally retiring the worker:

```powershell
Unregister-ScheduledTask -TaskName '910CPR Codex Wake' -Confirm:$false
```
