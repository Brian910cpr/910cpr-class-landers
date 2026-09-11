[CmdletBinding()]
param(
    [string]$RepoPath = 'E:\GitHub\910cpr-class-landers',
    [string]$StateDirectory = "$env:LOCALAPPDATA\910CPR\CodexWake",
    [int]$LeaseMinutes = 90,
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'
$taskName = '910CPR Codex Wake'
$heartbeatPath = Join-Path $RepoPath 'ops\handoff\codex_heartbeat.json'
$statePath = Join-Path $StateDirectory 'state.json'
$lockPath = Join-Path $StateDirectory 'worker.lock'
$logPath = Join-Path $StateDirectory 'worker.log'
New-Item -ItemType Directory -Force -Path $StateDirectory | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $heartbeatPath) | Out-Null

function Read-State {
    if (-not (Test-Path -LiteralPath $statePath)) { return @{} }
    try {
        $object = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
        $result = @{}
        foreach ($property in $object.PSObject.Properties) { $result[$property.Name] = $property.Value }
        return $result
    }
    catch { return @{} }
}

function Write-Heartbeat([hashtable]$Values) {
    $prior = Read-State
    foreach ($key in $Values.Keys) { $prior[$key] = $Values[$key] }
    $prior['worker_name'] = $taskName
    $prior['repo_path'] = $RepoPath
    $json = $prior | ConvertTo-Json -Depth 6
    $json | Set-Content -LiteralPath $statePath -Encoding utf8
    $json | Set-Content -LiteralPath $heartbeatPath -Encoding utf8
}

function Get-IssueUpdateKey($Value) {
    return ([datetimeoffset]$Value).ToUniversalTime().ToString('o')
}

$lockStream = $null
try {
    $lockStream = [System.IO.File]::Open($lockPath, 'OpenOrCreate', 'ReadWrite', 'None')
} catch {
    exit 0
}

try {
    $now = Get-Date
    $next = $now.AddMinutes(15)
    Write-Heartbeat @{ last_check_at = $now.ToString('o'); worker_state = 'working'; next_check_due = $next.ToString('o'); blocked_reason = $null }

    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $fetchOutput = & git -C $RepoPath fetch --prune origin 2>&1
    $fetchExitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousPreference
    if ($fetchExitCode -ne 0) { throw "git fetch failed: $($fetchOutput -join ' ')" }
    $lastCommit = (& git -C $RepoPath rev-parse HEAD).Trim()

    $issuesJson = & gh issue list --repo Brian910cpr/910cpr-class-landers --state open --search '[CODEX] in:title' --limit 100 --json number,title,url,updatedAt 2>&1
    if ($LASTEXITCODE -ne 0) { throw "GitHub queue read failed: $($issuesJson -join ' ')" }
    $parsedIssues = ConvertFrom-Json -InputObject ($issuesJson -join [Environment]::NewLine)
    $issues = @()
    foreach ($issue in $parsedIssues) { $issues += $issue }
    $state = Read-State
    $completedIssueUpdates = @{}
    if ($state.completed_issue_updates) {
        foreach ($property in $state.completed_issue_updates.PSObject.Properties) {
            $completedIssueUpdates[$property.Name] = [string]$property.Value
        }
    }
    $eligible = @($issues | Where-Object {
        if ($_.title -notmatch '^\[CODEX\]') { return $false }
        $completedAtUpdate = $completedIssueUpdates[[string]$_.number]
        return (-not $completedAtUpdate) -or ($completedAtUpdate -ne (Get-IssueUpdateKey $_.updatedAt))
    } | Sort-Object @{ Expression = {
        if ($_.title -match '\bP0\b') { 0 } elseif ($_.title -match '\bP1\b') { 1 } else { 2 }
    } }, number)

    $currentTask = $state.current_task
    $lastDispatch = if ($state.last_dispatch_at) { [datetimeoffset]::Parse($state.last_dispatch_at) } else { $null }
    $leaseActive = $currentTask -and $lastDispatch -and (([datetimeoffset]::Now - $lastDispatch).TotalMinutes -lt $LeaseMinutes)
    $preferredTask = $state.preferred_task
    $selected = if ($preferredTask) {
        $eligible | Where-Object { [int]$_.number -eq [int]$preferredTask } | Select-Object -First 1
    } else { $null }
    if (-not $selected) { $selected = $eligible | Select-Object -First 1 }

    if ($CheckOnly -or $leaseActive -or -not $selected) {
        $reason = if ($CheckOnly) { 'check_only' } elseif ($leaseActive) { 'active_dispatch_lease' } else { 'queue_empty' }
        Write-Heartbeat @{ last_check_at = (Get-Date).ToString('o'); worker_state = 'idle'; current_task = $currentTask; last_commit = $lastCommit; next_check_due = (Get-Date).AddMinutes(15).ToString('o'); blocked_reason = $reason; queue_count = $eligible.Count }
        exit 0
    }

    $codex = (Get-Command codex.exe -ErrorAction Stop).Source
    $issueNumber = [int]$selected.number
    $requiredReceipt = if ($issueNumber -eq 174) { 'Codex_Reply_CodexWake_R2.md' } else { 'a unique repository-root Codex_Reply_*.md receipt' }
    $prompt = @"
Work GitHub issue #$issueNumber in Brian910cpr/910cpr-class-landers. Read the full issue and repository AGENTS.md and CODEX_HANDOFF_PROTOCOL.md first. The checkout at E:\GitHub\910cpr-class-landers may contain unrelated dirty work: preserve it and use a separate named codex/ branch/worktree when needed. Follow issue dependencies and safety gates, validate proportionately, commit and push only your intended files, and write the required unique repository-root Codex_Reply_*.md receipt. If blocked, record the exact blocker in that receipt and continue unrelated eligible backend work when safe.

For this dispatch, the required receipt is $requiredReceipt. Push it to GitHub before exiting, whether the task completes or becomes blocked. Never use ops/handoff/next_task.md.
"@
    Write-Heartbeat @{ last_dispatch_at = (Get-Date).ToString('o'); last_launch_status = 'started'; last_launch_issue = $issueNumber; last_launch_command = 'codex.exe'; worker_state = 'working'; current_task = $issueNumber; blocked_reason = $null; last_commit = $lastCommit; queue_count = $eligible.Count }
    "$(Get-Date -Format o) dispatching issue #$issueNumber" | Add-Content -LiteralPath $logPath
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & $codex -a never exec -C $RepoPath -s danger-full-access $prompt *>> $logPath
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousPreference
    if ($exitCode -ne 0) { throw "Codex exited with code $exitCode" }
    $completedIssueUpdates[[string]$issueNumber] = Get-IssueUpdateKey $selected.updatedAt
    Write-Heartbeat @{ last_check_at = (Get-Date).ToString('o'); last_launch_status = 'completed'; last_launch_completed_at = (Get-Date).ToString('o'); last_launch_exit_code = $exitCode; worker_state = 'idle'; current_task = $null; preferred_task = $null; last_completed_task = $issueNumber; completed_issue_updates = $completedIssueUpdates; last_commit = ((& git -C $RepoPath rev-parse HEAD).Trim()); next_check_due = (Get-Date).AddMinutes(15).ToString('o'); blocked_reason = $null }
} catch {
    $_ | Out-String | Add-Content -LiteralPath $logPath
    Write-Heartbeat @{ last_check_at = (Get-Date).ToString('o'); last_launch_status = 'failed'; last_launch_completed_at = (Get-Date).ToString('o'); last_launch_exit_code = $LASTEXITCODE; worker_state = 'error'; next_check_due = (Get-Date).AddMinutes(15).ToString('o'); blocked_reason = $_.Exception.Message }
    exit 1
} finally {
    if ($lockStream) { $lockStream.Dispose() }
}
