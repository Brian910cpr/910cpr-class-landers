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
$publisher = Join-Path $StateDirectory 'Publish-CodexWakeHealth.ps1'

try {
    $loopLock = [System.IO.File]::Open($loopLockPath, 'OpenOrCreate', 'ReadWrite', 'None')
} catch {
    exit 0
}

try {
    "$(Get-Date -Format o) startup loop active; pid=$PID" | Add-Content -LiteralPath $loopLogPath
    Start-Sleep -Seconds $InitialDelaySeconds
    while ($true) {
        # Isolate exit/native-command failures from the persistent supervisor.
        $arguments = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$worker`" -RepoPath `"$RepoPath`" -StateDirectory `"$StateDirectory`""
        $cycle = Start-Process -FilePath (Get-Process -Id $PID).Path -ArgumentList $arguments -WindowStyle Hidden -PassThru
        do {
            if (Test-Path -LiteralPath $publisher) { & $publisher -StateDirectory $StateDirectory -LoopProcessId $PID -WorkerProcessId $cycle.Id }
        } while (-not $cycle.WaitForExit(60000))
        "$(Get-Date -Format o) cycle_exit=$($cycle.ExitCode); next_minutes=$IntervalMinutes" | Add-Content -LiteralPath $loopLogPath
        # Same supervisor, no second timer/service: publish during both work and idle.
        for ($minute = 0; $minute -lt $IntervalMinutes; $minute++) {
            if (Test-Path -LiteralPath $publisher) { & $publisher -StateDirectory $StateDirectory -LoopProcessId $PID }
            Start-Sleep -Seconds 60
        }
    }
} finally {
    $loopLock.Dispose()
}
