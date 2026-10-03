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

$taskAction = New-ScheduledTaskAction -Execute "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -Argument "-NoProfile -NonInteractive -WindowStyle Hidden -File `"$launcherPath`""
$timer = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5)
$logon = New-ScheduledTaskTrigger -AtLogOn -User ([Security.Principal.WindowsIdentity]::GetCurrent().Name)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 2)
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $taskName -Action $taskAction -Trigger @($timer,$logon) -Settings $settings -Principal $principal -Description 'Check public booking publication every five minutes; use existing local GitHub login to refresh before expiry.' -Force | Out-Null
Start-ScheduledTask -TaskName $taskName
[pscustomobject]@{TaskName=$taskName; InstallDirectory=$destination; StateFile=(Join-Path $stateDirectory 'health.json'); Requires='Computer awake with this user logged in; existing GitHub CLI login'} | ConvertTo-Json
