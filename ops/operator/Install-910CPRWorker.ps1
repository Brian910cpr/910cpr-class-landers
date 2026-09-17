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
        worker_version = '0.2.0'
        enrolled_at_utc = (Get-Date).ToUniversalTime().ToString('o')
        capabilities = @('heartbeat.local','github.queue','github.receipt','job.selftest.ping','job.reject-unapproved','duplicate-suppression.local')
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

$identity | Add-Member -NotePropertyName worker_version -NotePropertyValue '0.2.0' -Force
$identity | Add-Member -NotePropertyName capabilities -NotePropertyValue @('heartbeat.local','github.queue','github.receipt','job.selftest.ping','job.reject-unapproved','duplicate-suppression.local') -Force
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

$process = Start-Process -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -ArgumentList @(
    '-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-WindowStyle','Hidden','-File',$runtimePath,
    '-StateDirectory',$workerDirectory,'-HeartbeatSeconds',$HeartbeatSeconds,'-RepoSlug',$RepoSlug
) -WindowStyle Hidden -PassThru

Start-Sleep -Seconds 2
$heartbeatPath = Join-Path $workerDirectory 'heartbeat.json'
$heartbeat = $null
if (Test-Path -LiteralPath $heartbeatPath) { $heartbeat = Get-Content -LiteralPath $heartbeatPath -Raw | ConvertFrom-Json }

[pscustomobject]@{
    WorkerName = $identity.worker_name
    WorkerId = $identity.worker_id
    Machine = $env:COMPUTERNAME
    Version = $identity.worker_version
    InstallDirectory = $workerDirectory
    StartupLauncher = $startupLauncher
    ProcessId = $process.Id
    HeartbeatState = if ($heartbeat) { $heartbeat.state } else { 'pending' }
    ControlPlane = $identity.control_plane
    ReadyForGitHubClaims = $githubReady
}
