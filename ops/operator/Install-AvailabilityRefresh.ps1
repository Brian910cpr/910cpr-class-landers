[CmdletBinding()]
param([string]$InstallRoot = "$env:LOCALAPPDATA\910CPR\AvailabilityRefresh")

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$taskName = '910CPR Availability Refresh'
$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$nodePath = (Get-Command node.exe -ErrorAction Stop).Source
$ghPath = (Get-Command gh.exe -ErrorAction Stop).Source
& $ghPath auth status --hostname github.com *> $null
if ($LASTEXITCODE -ne 0) { throw 'Existing GitHub CLI login is unavailable.' }

$destination = [IO.Path]::GetFullPath($InstallRoot)
$workerDirectory = Join-Path $destination 'worker'
$operatorDirectory = Join-Path $destination 'ops\operator'
$stateDirectory = Join-Path $destination 'state'
New-Item -ItemType Directory -Force -Path $workerDirectory,$operatorDirectory,$stateDirectory | Out-Null
Copy-Item -LiteralPath (Join-Path $repoRoot 'worker\availability-refresh-watchdog.mjs') -Destination $workerDirectory -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Run-AvailabilityRefresh.mjs') -Destination $operatorDirectory -Force
$runner = Join-Path $operatorDirectory 'Run-AvailabilityRefresh.mjs'
$launcherPath = Join-Path $destination 'Run-AvailabilityRefresh.ps1'
$qNode = $nodePath.Replace("'", "''")
$qRunner = $runner.Replace("'", "''")
$qState = $stateDirectory.Replace("'", "''")
$qGh = $ghPath.Replace("'", "''")
@"
& '$qNode' '$qRunner' '$qState' '$qGh'
exit `$LASTEXITCODE
"@ | Set-Content -LiteralPath $launcherPath -Encoding UTF8

# Use the same PowerShell host that successfully runs this installer. Windows
# PowerShell 5.1 may have a different effective script policy than PowerShell 7.
# Do not weaken machine/user execution policy to make the scheduled task run.
$shellPath = (Get-Process -Id $PID).Path
$taskCommand = "& '$qNode' '$qRunner' '$qState' '$qGh'; exit `$LASTEXITCODE"
$taskAction = New-ScheduledTaskAction -Execute $shellPath -Argument "-NoProfile -NonInteractive -WindowStyle Hidden -Command `"$taskCommand`""
$timer = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5)
$logon = New-ScheduledTaskTrigger -AtLogOn -User ([Security.Principal.WindowsIdentity]::GetCurrent().Name)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 2)
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$previousTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
$previousXml = if ($previousTask) { Export-ScheduledTask -TaskName $taskName } else { $null }
Register-ScheduledTask -TaskName $taskName -Action $taskAction -Trigger @($timer,$logon) -Settings $settings -Principal $principal -Description 'Check public booking publication every five minutes; use existing local GitHub login to refresh before expiry.' -Force | Out-Null
$started = [DateTimeOffset]::UtcNow
Start-ScheduledTask -TaskName $taskName
$healthPath = Join-Path $stateDirectory 'health.json'
$observed = $null
do {
    if (Test-Path -LiteralPath $healthPath) {
        try {
            $candidate = Get-Content -LiteralPath $healthPath -Raw | ConvertFrom-Json
            if ([DateTimeOffset]::Parse($candidate.checkedAt) -ge $started) { $observed = $candidate; break }
        } catch { }
    }
    Start-Sleep -Milliseconds 500
} while ([DateTimeOffset]::UtcNow -lt $started.AddSeconds(15))
if (-not $observed) {
    if ($previousXml) { Register-ScheduledTask -TaskName $taskName -Xml $previousXml -Force | Out-Null }
    else { Disable-ScheduledTask -TaskName $taskName | Out-Null }
    throw 'Scheduled process did not produce a fresh observation. Prior task restored when available. If the native task cannot see an app-private LocalAppData path, use -InstallRoot on a shared physical drive.'
}
[pscustomobject]@{TaskName=$taskName; InstallDirectory=$destination; StateFile=$healthPath; CheckedAt=$observed.checkedAt; Action=$observed.action; Requires='Computer awake with this user logged in; existing GitHub CLI login'} | ConvertTo-Json
