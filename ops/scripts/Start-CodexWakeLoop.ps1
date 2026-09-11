[CmdletBinding()]
param(
    [string]$RepoPath = 'E:\GitHub\910cpr-class-landers',
    [string]$StateDirectory = "$env:LOCALAPPDATA\910CPR\CodexWake",
    [int]$IntervalMinutes = 15,
    [int]$InitialDelaySeconds = 20
)

$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $StateDirectory | Out-Null
$loopLockPath = Join-Path $StateDirectory 'loop.lock'
$loopLogPath = Join-Path $StateDirectory 'loop.log'
$worker = Join-Path $StateDirectory 'Invoke-CodexWake.ps1'

try {
    $loopLock = [System.IO.File]::Open($loopLockPath, 'OpenOrCreate', 'ReadWrite', 'None')
} catch {
    exit 0
}

try {
    "$(Get-Date -Format o) startup loop active; pid=$PID" | Add-Content -LiteralPath $loopLogPath
    Start-Sleep -Seconds $InitialDelaySeconds
    while ($true) {
        & $worker -RepoPath $RepoPath -StateDirectory $StateDirectory
        "$(Get-Date -Format o) cycle_exit=$LASTEXITCODE; next_minutes=$IntervalMinutes" | Add-Content -LiteralPath $loopLogPath
        Start-Sleep -Seconds ($IntervalMinutes * 60)
    }
} finally {
    $loopLock.Dispose()
}
