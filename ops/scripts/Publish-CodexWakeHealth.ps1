[CmdletBinding()]
param(
    [string]$StateDirectory = "$env:LOCALAPPDATA\910CPR\CodexWake",
    [int]$LoopProcessId,
    [int]$WorkerProcessId = 0
)
$ErrorActionPreference = 'Stop'
$configPath = Join-Path $StateDirectory 'health-publish.json'
if (-not (Test-Path -LiteralPath $configPath)) { return }
try {
    $config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
    if ([string]$config.comment_id -notmatch '^\d+$') { throw 'Invalid health comment id' }
    $loop = Get-Process -Id $LoopProcessId -ErrorAction Stop
    $state = Get-Content -LiteralPath (Join-Path $StateDirectory 'state.json') -Raw | ConvertFrom-Json
    # Explicit allowlist: never publish paths, prompts, raw errors or credentials.
    $signal = [ordered]@{
        schema_version = 1
        worker_name = '910CPR Codex Wake'
        published_at = [datetimeoffset]::UtcNow.ToString('o')
        loop_started_at = $loop.StartTime.ToUniversalTime().ToString('o')
        loop_pid = $LoopProcessId
        execution_process_alive = [bool]($WorkerProcessId -and (Get-Process -Id $WorkerProcessId -ErrorAction SilentlyContinue))
        manual_hold = Test-Path -LiteralPath (Join-Path $StateDirectory 'manual-hold.json')
        last_check_at = $state.last_check_at
        worker_state = $state.worker_state
        current_task = $state.current_task
        last_completed_task = $state.last_completed_task
        last_session_id = $state.last_session_id
        last_launch_status = $state.last_launch_status
        next_check_due = $state.next_check_due
        retry_after = $state.retry_after
    }
    $body = "<!-- 910CPR-CODEX-WAKE-HEALTH-V1 -->`nLauncher health; updated by the existing Windows loop. Supervisors must check published_at, not GitHub issue activity.`n``````json`n$($signal | ConvertTo-Json -Depth 4)`n```````n"
    $payload = @{ body = $body } | ConvertTo-Json -Depth 6 -Compress
    $null = $payload | & gh api --method PATCH "repos/Brian910cpr/910cpr-class-landers/issues/comments/$($config.comment_id)" --input - 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'GitHub health publication failed' }
    $signal | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $StateDirectory 'published-health.json') -Encoding utf8
} catch {
    # Publication failure must never stop intake. Remote timestamps become stale.
    "$(Get-Date -Format o) health publication failed; inspect local authentication/network/config" | Add-Content -LiteralPath (Join-Path $StateDirectory 'loop.log')
}
