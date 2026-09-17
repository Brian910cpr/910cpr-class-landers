[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$StateDirectory,

    [int]$HeartbeatSeconds = 60,

    [string]$RepoSlug = 'Brian910cpr/910cpr-class-landers'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$identityPath = Join-Path $StateDirectory 'identity.json'
$heartbeatPath = Join-Path $StateDirectory 'heartbeat.json'
$inboxPath = Join-Path $StateDirectory 'inbox'
$resultPath = Join-Path $StateDirectory 'results'
$disabledPath = Join-Path $StateDirectory 'disabled.flag'
$lockPath = Join-Path $StateDirectory 'worker.lock'
$logPath = Join-Path $StateDirectory 'worker.log'

function Write-WorkerLog {
    param([string]$Message)
    $stamp = (Get-Date).ToUniversalTime().ToString('o')
    Add-Content -LiteralPath $logPath -Value "$stamp $Message" -Encoding utf8
}

function Write-Heartbeat {
    param([object]$Identity,[string]$State,[string]$Detail)
    [ordered]@{
        schema_version = 1
        worker_id = $Identity.worker_id
        worker_name = $Identity.worker_name
        machine_name = $env:COMPUTERNAME
        process_id = $PID
        worker_version = $Identity.worker_version
        state = $State
        detail = $Detail
        control_plane = $Identity.control_plane
        observed_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $heartbeatPath -Encoding utf8
}

function Get-ResultPath {
    param([string]$JobId)
    $safeJobId = ($JobId -replace '[^A-Za-z0-9_.-]', '_')
    return (Join-Path $resultPath "$safeJobId.json")
}

function Write-Result {
    param([object]$Identity,[string]$JobId,[string]$JobType,[string]$Status,[string]$Message,[Nullable[int]]$IssueNumber)
    $path = Get-ResultPath -JobId $JobId
    [ordered]@{
        schema_version = 1
        worker_id = $Identity.worker_id
        worker_name = $Identity.worker_name
        job_id = $JobId
        job_type = $JobType
        status = $Status
        message = $Message
        github_issue = $IssueNumber
        completed_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $path -Encoding utf8
    return $path
}

function Invoke-AllowlistedJob {
    param([object]$Identity,[string]$JobId,[string]$JobType,[Nullable[int]]$IssueNumber)
    $existingResult = Get-ResultPath -JobId $JobId
    if (Test-Path -LiteralPath $existingResult) {
        Write-WorkerLog "Duplicate job suppressed: $JobId"
        return $existingResult
    }

    switch ($JobType) {
        'selftest.ping' {
            Write-Heartbeat -Identity $Identity -State 'working' -Detail "Executing allowlisted self-test job $JobId"
            $path = Write-Result -Identity $Identity -JobId $JobId -JobType $JobType -Status 'PASS' -Message 'Worker accepted and executed the allowlisted self-test exactly once.' -IssueNumber $IssueNumber
            Write-WorkerLog "PASS $JobId $JobType"
            return $path
        }
        default {
            $path = Write-Result -Identity $Identity -JobId $JobId -JobType $JobType -Status 'REJECTED' -Message 'Job type is not allowlisted by this worker version.' -IssueNumber $IssueNumber
            Write-WorkerLog "REJECTED $JobId $JobType"
            return $path
        }
    }
}

function Test-GitHubReady {
    $gh = Get-Command gh.exe -ErrorAction SilentlyContinue
    if (-not $gh) { return $false }
    & $gh.Source auth status -h github.com *> $null
    return ($LASTEXITCODE -eq 0)
}

function Invoke-GitHubQueue {
    param([object]$Identity)
    if (-not (Test-GitHubReady)) { return }

    $search = ('"[WORKER] {0}" in:title' -f $Identity.worker_name)
    $json = & gh issue list --repo $RepoSlug --state open --search $search --limit 20 --json number,title,url 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-WorkerLog "GitHub queue read failed: $($json -join ' ')"
        return
    }

    $issues = @()
    if (($json -join '').Trim()) { $issues = @(ConvertFrom-Json -InputObject ($json -join [Environment]::NewLine)) }
    $escapedWorker = [regex]::Escape([string]$Identity.worker_name)
    $pattern = '^\[WORKER\]\s+' + $escapedWorker + '\s+([A-Za-z0-9_.-]+)\s+([A-Za-z0-9_.-]+)$'

    foreach ($issue in ($issues | Sort-Object number)) {
        $m = [regex]::Match([string]$issue.title, $pattern)
        if (-not $m.Success) { continue }

        $jobType = $m.Groups[1].Value
        $jobId = $m.Groups[2].Value
        $issueNumber = [int]$issue.number
        $resultFile = Get-ResultPath -JobId $jobId

        $viewJson = & gh issue view $issueNumber --repo $RepoSlug --json comments 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-WorkerLog "GitHub issue view failed for #$issueNumber"
            continue
        }
        $view = ConvertFrom-Json -InputObject ($viewJson -join [Environment]::NewLine)
        $resultMarker = "910CPR_WORKER_RESULT worker_id=$($Identity.worker_id) job_id=$jobId"
        $alreadyReceipted = @($view.comments | Where-Object { [string]$_.body -like "$resultMarker*" }).Count -gt 0
        if ($alreadyReceipted) {
            Write-WorkerLog "GitHub receipt already present; skipping #$issueNumber / $jobId"
            continue
        }

        if (-not (Test-Path -LiteralPath $resultFile)) {
            $claim = "910CPR_WORKER_CLAIM worker_id=$($Identity.worker_id) worker_name=$($Identity.worker_name) job_id=$jobId observed_at_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
            & gh issue comment $issueNumber --repo $RepoSlug --body $claim *> $null
            if ($LASTEXITCODE -ne 0) {
                Write-WorkerLog "Failed to claim GitHub issue #$issueNumber"
                continue
            }
            Invoke-AllowlistedJob -Identity $Identity -JobId $jobId -JobType $jobType -IssueNumber $issueNumber | Out-Null
        }

        if (Test-Path -LiteralPath $resultFile) {
            $result = Get-Content -LiteralPath $resultFile -Raw | ConvertFrom-Json
            $receipt = "$resultMarker status=$($result.status) completed_at_utc=$($result.completed_at_utc)`n`n$($result.message)"
            & gh issue comment $issueNumber --repo $RepoSlug --body $receipt *> $null
            if ($LASTEXITCODE -eq 0) {
                & gh issue close $issueNumber --repo $RepoSlug --reason completed *> $null
                Write-WorkerLog "GitHub result receipted for #$issueNumber / $jobId / $($result.status)"
            } else {
                Write-WorkerLog "Failed to publish GitHub result for #$issueNumber / $jobId"
            }
        }
    }
}

New-Item -ItemType Directory -Force -Path $StateDirectory, $inboxPath, $resultPath | Out-Null
if (-not (Test-Path -LiteralPath $identityPath)) { throw "Worker identity missing: $identityPath" }
$identity = Get-Content -LiteralPath $identityPath -Raw | ConvertFrom-Json
if (-not $identity.worker_id -or -not $identity.worker_name) { throw 'Worker identity is invalid.' }

$lockStream = $null
try {
    $lockStream = [System.IO.File]::Open($lockPath,[System.IO.FileMode]::OpenOrCreate,[System.IO.FileAccess]::ReadWrite,[System.IO.FileShare]::None)
} catch {
    Write-WorkerLog 'Another worker runtime already owns the local lock; exiting.'
    exit 0
}

try {
    Write-WorkerLog "Worker starting: $($identity.worker_name) / $($identity.worker_id)"
    while ($true) {
        if (Test-Path -LiteralPath $disabledPath) {
            Write-Heartbeat -Identity $identity -State 'disabled' -Detail 'Local revocation flag present; no jobs will be claimed.'
            Start-Sleep -Seconds $HeartbeatSeconds
            continue
        }

        $githubReady = Test-GitHubReady
        $detail = if ($githubReady) { 'Runtime healthy; GitHub control plane connected; waiting for an allowlisted job.' } else { 'Runtime healthy; GitHub control plane unavailable; local allowlisted jobs only.' }
        Write-Heartbeat -Identity $identity -State 'idle' -Detail $detail

        $jobs = @(Get-ChildItem -LiteralPath $inboxPath -Filter '*.json' -File -ErrorAction SilentlyContinue | Sort-Object Name)
        foreach ($jobFile in $jobs) {
            $processingPath = "$($jobFile.FullName).processing"
            try { Move-Item -LiteralPath $jobFile.FullName -Destination $processingPath -ErrorAction Stop } catch { continue }
            try {
                $job = Get-Content -LiteralPath $processingPath -Raw | ConvertFrom-Json
                $jobId = [string]$job.job_id
                $jobType = [string]$job.job_type
                if ([string]::IsNullOrWhiteSpace($jobId) -or [string]::IsNullOrWhiteSpace($jobType)) {
                    Write-Result -Identity $identity -JobId $jobFile.BaseName -JobType 'unknown' -Status 'FAIL' -Message 'Malformed job: job_id and job_type are required.' -IssueNumber $null | Out-Null
                } else {
                    Invoke-AllowlistedJob -Identity $identity -JobId $jobId -JobType $jobType -IssueNumber $null | Out-Null
                }
            } catch {
                Write-Result -Identity $identity -JobId $jobFile.BaseName -JobType 'unknown' -Status 'FAIL' -Message $_.Exception.Message -IssueNumber $null | Out-Null
                Write-WorkerLog "FAIL $($jobFile.BaseName) $($_.Exception.Message)"
            } finally {
                Remove-Item -LiteralPath $processingPath -Force -ErrorAction SilentlyContinue
            }
        }

        if ($githubReady) { Invoke-GitHubQueue -Identity $identity }
        Start-Sleep -Seconds $HeartbeatSeconds
    }
} finally {
    if ($lockStream) { $lockStream.Dispose() }
    Write-WorkerLog 'Worker stopped.'
}
