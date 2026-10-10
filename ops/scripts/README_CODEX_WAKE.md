# CyberPC Codex wake worker

`Install-CodexWake.ps1` idempotently installs the Windows Startup worker `910CPR Codex Wake`. A hidden, locked PowerShell loop starts at user logon and runs every 15 minutes. Installed scripts and local state live under `%LOCALAPPDATA%\910CPR\CodexWake`; the Startup launcher lives in the current user's Startup folder. This mode avoids stored passwords and elevation. It is used because this CyberPC session's Task Scheduler accepted task registration but refused to launch even a one-line probe task.

The worker uses an exclusive file lock for the entire Codex execution, reads every page of open issues, and accepts only titles starting `[CODEX]` created by `Brian910cpr`. Queue detection does not fetch Git or depend on the old damaged checkout. Install with an explicit healthy `-RepoPath`; the Startup launcher retains that path. Logs, session JSONL events, final responses, `state.json`, and `heartbeat.json` live under `%LOCALAPPDATA%\910CPR\CodexWake`. The retired `ops/handoff/` mailbox is never written.

The loop invokes each cycle in a child PowerShell process so a cycle's exit or failure cannot terminate the supervisor. A failed execution clears its dispatch lease and backs off for one hour. The exclusive execution lock, not the 90-minute timestamp alone, prevents overlap. An external/manual implementation session must create `manual-hold.json` in the state directory before editing and remove it when it yields; do not launch another deep workstream while that hold exists. A forgotten hold remains a blocker and is visible in heartbeat state.

After a successful run with a named receipt verifiable at its reported GitHub commit, the worker records the issue's post-run GitHub `updatedAt` value and suppresses that unchanged issue on later cycles. A new comment or edit makes it eligible again. **Limitation:** an owner update arriving during the run may be included in this watermark; execution sessions must reread the originating conversation before returning. A receipted blocked task is not an implemented task. `completed_issue_updates` means this revision was processed, not that the product is complete.

Heartbeat interpretation:

- `last_check_at`, `queue_count`, and `next_check_due` prove queue-check activity.
- `last_launch_status`, `last_launch_issue`, `last_dispatch_at`, and `last_launch_command` prove that the worker reached the Codex launch boundary.
- `last_session_id` and `last_events_path` identify the actual execution session. Exit zero alone is insufficient: normal runs must name a pushed root `Codex_Reply_*` file and full commit SHA that GitHub can resolve.
- `-IssueNumber 371 -ProofOnly` runs a bounded real session that reads the authorized issue and acknowledges it without implementation. It records `proof_completed` and never consumes the task's completion watermark.

Install or repair:

```powershell
pwsh -NoProfile -File .\ops\scripts\Install-CodexWake.ps1 -RepoPath 'D:\Users\ten77\Documents\2020 -_ 2025 & Enrollware\910cpr-customer-interaction-studio'
```

Safe check without dispatch:

```powershell
pwsh -NoProfile -File .\ops\scripts\Invoke-CodexWake.ps1 -CheckOnly
```

Inspect health:

```powershell
Get-Content "$env:LOCALAPPDATA\910CPR\CodexWake\loop.log"
Get-Content "$env:LOCALAPPDATA\910CPR\CodexWake\heartbeat.json"
```

## Proof and remaining monitoring boundary (Issue #371)

On October 10, 2026, real CLI session `01a127a2-d6b7-7411-977b-fb746dafefde` read #371, acknowledged it, and returned successfully. See `data/audit/issue371_intake_proof.json` and `Codex_Reply_Issue371_IntakeRepair_R1.md`. The September 15 log showed usage exhaustion; the loop was absent on October 10, and its Startup entry still referenced the checkout recorded as corrupted. No credentials needed changing for the successful October 10 proof.

Expected polling cadence is 15 minutes while the Windows user session is running and the machine is awake. Startup registration restores the loop at logon; it is not an always-on cloud executor. A check older than 30 minutes, a stopped loop PID, a persistent manual hold, or a failed execution is a stale/failure signal. Recovery is reinstalling/restarting this same loop after checking locks and active assignments. Auth/capacity failure requires the exact local login or usage action indicated in the local run log; never post credentials.

Evidence level: **PROVEN for one intake-to-session cycle, not MONITORED/HEALTHY**. The loop heartbeat is local. The existing ChatGPT Scheduled Tasks “910CPR Delta Watch” and “910CPR Deep Stability Review” are supervisors, not launchers, and were not changed. Their independent access to current launcher health is not proven. No new scheduler was created; a stopped/sleeping CyberPC is still an availability boundary. Do not claim continuous service or observer health until those existing supervisors can actually observe staleness.

Uninstall only when intentionally retiring the worker:

```powershell
Remove-Item "$([Environment]::GetFolderPath('Startup'))\910CPR Codex Wake.cmd"
```
