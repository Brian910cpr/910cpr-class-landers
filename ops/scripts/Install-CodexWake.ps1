[CmdletBinding()]
param(
    [string]$RepoPath = 'E:\GitHub\910cpr-class-landers',
    [string]$TaskName = '910CPR Codex Wake',
    [int]$SeedCurrentTask = 0,
    [switch]$NoStart
)

$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'Invoke-CodexWake.ps1'
$loopSource = Join-Path $PSScriptRoot 'Start-CodexWakeLoop.ps1'
$installDirectory = Join-Path $env:LOCALAPPDATA '910CPR\CodexWake'
$installedScript = Join-Path $installDirectory 'Invoke-CodexWake.ps1'
$installedLoop = Join-Path $installDirectory 'Start-CodexWakeLoop.ps1'
New-Item -ItemType Directory -Force -Path $installDirectory | Out-Null
Copy-Item -LiteralPath $source -Destination $installedScript -Force
Copy-Item -LiteralPath $loopSource -Destination $installedLoop -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Publish-CodexWakeHealth.ps1') -Destination (Join-Path $installDirectory 'Publish-CodexWakeHealth.ps1') -Force

if ($SeedCurrentTask -gt 0) {
    $stateFile = Join-Path $installDirectory 'state.json'
    $state = if (Test-Path -LiteralPath $stateFile) { Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
    $state | Add-Member -NotePropertyName preferred_task -NotePropertyValue $SeedCurrentTask -Force
    $state | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $stateFile -Encoding utf8
}

Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
$startupDirectory = [Environment]::GetFolderPath('Startup')
$startupLauncher = Join-Path $startupDirectory '910CPR Codex Wake.cmd'
$launcherText = "@echo off`r`nstart `"`" /min `"$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe`" -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$installedLoop`" -RepoPath `"$RepoPath`" -StateDirectory `"$installDirectory`"`r`n"
Set-Content -LiteralPath $startupLauncher -Value $launcherText -Encoding ascii

& $installedScript -RepoPath $RepoPath -CheckOnly
if ($NoStart) { return }
$process = Start-Process -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -ArgumentList "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$installedLoop`" -RepoPath `"$RepoPath`" -StateDirectory `"$installDirectory`"" -WindowStyle Hidden -PassThru
[pscustomobject]@{ Name = $TaskName; Type = 'Windows Startup background loop'; State = 'Started'; ProcessId = $process.Id; StartupLauncher = $startupLauncher; Script = $installedLoop }
