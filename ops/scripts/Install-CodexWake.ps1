[CmdletBinding()]
param(
    [string]$RepoPath = 'E:\GitHub\910cpr-class-landers',
    [string]$TaskName = '910CPR Codex Wake',
    [int]$SeedCurrentTask = 0
)

$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'Invoke-CodexWake.ps1'
$installDirectory = Join-Path $env:LOCALAPPDATA '910CPR\CodexWake'
$installedScript = Join-Path $installDirectory 'Invoke-CodexWake.ps1'
New-Item -ItemType Directory -Force -Path $installDirectory | Out-Null
Copy-Item -LiteralPath $source -Destination $installedScript -Force

if ($SeedCurrentTask -gt 0) {
    @{
        current_task = $SeedCurrentTask
        last_dispatch_at = (Get-Date).ToString('o')
        worker_state = 'working'
        blocked_reason = $null
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $installDirectory 'state.json') -Encoding utf8
}

$powerShell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$arguments = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$installedScript`" -RepoPath `"$RepoPath`""
$action = New-ScheduledTaskAction -Execute $powerShell -Argument $arguments
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 15)
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 8) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Checks the durable 910CPR [CODEX] GitHub queue and dispatches one guarded Codex worker.' -Force | Out-Null

& $installedScript -RepoPath $RepoPath -CheckOnly
Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName,State,@{Name='Script';Expression={$installedScript}}
