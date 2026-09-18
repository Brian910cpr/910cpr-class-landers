[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]{1,62}$')]
    [string]$WorkerName,

    [string]$InstallRoot = "$env:LOCALAPPDATA\910CPR\Worker",

    [int]$HeartbeatSeconds = 60,

    [string]$RepoSlug = 'Brian910cpr/910cpr-class-landers',

    [switch]$ForceReenroll
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$runtimeSource = Join-Path $PSScriptRoot 'Start-910CPRWorker.ps1'
if (-not (Test-Path -LiteralPath $runtimeSource)) { throw "Runtime script missing: $runtimeSource" }

$workerDirectory = Join-Path $InstallRoot $WorkerName
$identityPath = Join-Path $workerDirectory 'identity.json'
$runtimePath = Join-Path $workerDirectory 'Start-910CPRWorker.ps1'
$credentialPath = Join-Path $workerDirectory 'credential.protected'
$inboxPath = Join-Path $workerDirectory 'inbox'
$resultPath = Join-Path $workerDirectory 'results'
$heartbeatPath = Join-Path $workerDirectory 'heartbeat.json'
$logPath = Join-Path $workerDirectory 'worker.log'
$startupDirectory = [Environment]::GetFolderPath('Startup')
$startupLauncher = Join-Path $startupDirectory ("910CPR Worker - {0}.cmd" -f $WorkerName)

New-Item -ItemType Directory -Force -Path $workerDirectory, $inboxPath, $resultPath | Out-Null

$existingIdentity = $null
if (Test-Path -LiteralPath $identityPath) {
    $existingIdentity = Get-Content -LiteralPath $identityPath -Raw | ConvertFrom-Json
    if ($existingIdentity.worker_name -ne $WorkerName) { throw "Existing identity name does not match requested worker name. Use a different InstallRoot or inspect $identityPath." }
}

if ($existingIdentity -and -not $ForceReenroll) {
    $identity = $existingIdentity
} else {
    if ($existingIdentity -and $ForceReenroll) {
        $backupName = 'identity.{0}.bak.json' -f (Get-Date -Format 'yyyyMMdd-HHmmss')
        Copy-Item -LiteralPath $identityPath -Destination (Join-Path $workerDirectory $backupName)
    }
    $identity = [pscustomobject][ordered]@{
        schema_version = 1
        worker_id = [guid]::NewGuid().ToString()
        worker_name = $WorkerName
        machine_name = $env:COMPUTERNAME
        enrolled_user = [Environment]::UserName
        worker_version = '0.2.2'
        enrolled_at_utc = (Get-Date).ToUniversalTime().ToString('o')
        capabilities = @('heartbeat.local','github.queue','github.receipt','job.selftest.ping','job.site.healthcheck','job.reject-unapproved','duplicate-suppression.local')
        control_plane = 'GITHUB_ISSUES_BOUNDED_V1'
        repository = $RepoSlug
    }

    $randomBytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($randomBytes) } finally { $rng.Dispose() }
    $seed = [Convert]::ToBase64String($randomBytes)
    $secure = ConvertTo-SecureString -String $seed -AsPlainText -Force
    $secure | ConvertFrom-SecureString | Set-Content -LiteralPath $credentialPath -Encoding ascii
    [Array]::Clear($randomBytes,0,$randomBytes.Length)
    $seed = $null
    $secure = $null
}

$gh = Get-Command gh.exe -ErrorAction SilentlyContinue
$githubReady = $false
if ($gh) {
    & $gh.Source auth status -h github.com *> $null
    $githubReady = ($LASTEXITCODE -eq 0)
}

$identity | Add-Member -NotePropertyName worker_version -NotePropertyValue '0.2.2' -Force
$identity | Add-Member -NotePropertyName capabilities -NotePropertyValue @('heartbeat.local','github.queue','github.receipt','job.selftest.ping','job.site.healthcheck','job.reject-unapproved','duplicate-suppression.local') -Force
$identity | Add-Member -NotePropertyName control_plane -NotePropertyValue $(if ($githubReady) { 'GITHUB_ISSUES_BOUNDED_V1' } else { 'LOCAL_ONLY_GITHUB_AUTH_MISSING' }) -Force
$identity | Add-Member -NotePropertyName repository -NotePropertyValue $RepoSlug -Force
$identity | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $identityPath -Encoding utf8

Copy-Item -LiteralPath $runtimeSource -Destination $runtimePath -Force

$launcher = @"
@echo off
start "" /min "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "$runtimePath" -StateDirectory "$workerDirectory" -HeartbeatSeconds $HeartbeatSeconds -RepoSlug "$RepoSlug"
"@
Set-Content -LiteralPath $startupLauncher -Value $launcher -Encoding ascii

Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*Start-910CPRWorker.ps1*" -and $_.CommandLine -like "*$workerDirectory*" } |
    ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch { } }

# Heartbeats are ephemeral readiness evidence. Remove any prior heartbeat before
# launching so the installer cannot mistake an old worker's state for the new process.
Remove-Item -LiteralPath $heartbeatPath -Force -ErrorAction SilentlyContinue
$launchStartedUtc = (Get-Date).ToUniversalTime()

$process = Start-Process -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -ArgumentList @(
    '-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-WindowStyle','Hidden','-File',$runtimePath,
    '-StateDirectory',$workerDirectory,'-HeartbeatSeconds',$HeartbeatSeconds,'-RepoSlug',$RepoSlug
) -WindowStyle Hidden -PassThru

$heartbeat = $null
$heartbeatDeadline = (Get-Date).AddSeconds(15)
do {
    $process.Refresh()
    if ($process.HasExited) { break }

    if (Test-Path -LiteralPath $heartbeatPath) {
        try {
            $candidate = Get-Content -LiteralPath $heartbeatPath -Raw | ConvertFrom-Json
            $observedUtc = ([DateTimeOffset]::Parse([string]$candidate.observed_at_utc)).UtcDateTime
            if (([int]$candidate.process_id -eq $process.Id) -and ($observedUtc -ge $launchStartedUtc)) {
                $heartbeat = $candidate
                break
            }
        } catch {
            # The runtime may still be replacing the heartbeat file. Retry until deadline.
        }
    }
    Start-Sleep -Milliseconds 500
} while ((Get-Date) -lt $heartbeatDeadline)

if (-not $heartbeat) {
    $tail = @()
    if (Test-Path -LiteralPath $logPath) {
        $tail = @(Get-Content -LiteralPath $logPath -Tail 12 -ErrorAction SilentlyContinue)
    }
    $detail = if ($process.HasExited) { "Worker process exited with code $($process.ExitCode) before publishing a fresh heartbeat." } else { 'Worker process did not publish a fresh matching heartbeat within 15 seconds.' }
    if ($tail.Count -gt 0) { $detail += " Recent worker.log:`n$($tail -join [Environment]::NewLine)" }
    throw $detail
}

[pscustomobject]@{
    WorkerName = $identity.worker_name
    WorkerId = $identity.worker_id
    Machine = $env:COMPUTERNAME
    Version = $identity.worker_version
    InstallDirectory = $workerDirectory
    StartupLauncher = $startupLauncher
    ProcessId = $process.Id
    HeartbeatState = $heartbeat.state
    ControlPlane = $heartbeat.control_plane
    ReadyForGitHubClaims = ($githubReady -and $heartbeat.control_plane -eq 'GITHUB_ISSUES_BOUNDED_V1')
}
