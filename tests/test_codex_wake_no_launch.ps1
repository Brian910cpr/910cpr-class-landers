param([string]$PowerShell = (Get-Process -Id $PID).Path)
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path "$PSScriptRoot/../ops/scripts/Invoke-CodexWake.ps1").Path
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('issue380-no-launch-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $fixture | Out-Null
$wrapper = Join-Path $fixture 'wrapper.ps1'
@'
param($Source,$State,$Mode)
$ErrorActionPreference = 'Stop'
function git { $global:LASTEXITCODE=0; if ($args -contains '--is-inside-work-tree') { 'true' } else { 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' } }
function gh {
    $global:LASTEXITCODE=0
    if ($args[0] -ne 'api' -or $args -notcontains '--paginate') { throw 'Unexpected GitHub call' }
    '{"number":371,"title":"[CODEX] P1 CRM","author":"Brian910cpr","updatedAt":"2026-10-12T00:00:00Z"}'
    '{"number":999,"title":"[CODEX] P0 outsider","author":"outsider","updatedAt":"2026-10-12T00:00:00Z"}'
}
function codex.exe { throw 'FAIL: launcher reached' }
$parameters=@{RepoPath=$State; StateDirectory=$State}
if ($Mode -eq 'check') { $parameters.CheckOnly=$true }
if ($Mode -eq 'missing') { $parameters.IssueNumber=999 }
& $Source @parameters
'@ | Set-Content -LiteralPath $wrapper
foreach ($mode in @('check','hold','retry','lease','missing')) {
    $state = Join-Path $fixture $mode
    New-Item -ItemType Directory -Path $state | Out-Null
    $seed = @{}
    if ($mode -eq 'hold') { '{}' | Set-Content (Join-Path $state 'manual-hold.json') }
    if ($mode -eq 'retry') { $seed.retry_after=(Get-Date).AddHours(1).ToString('o') }
    if ($mode -eq 'lease') { $seed.current_task=371; $seed.last_dispatch_at=(Get-Date).ToString('o') }
    $seed | ConvertTo-Json | Set-Content (Join-Path $state 'state.json')
    & $PowerShell -NoProfile -NonInteractive -File $wrapper $source $state $mode
    if ($LASTEXITCODE -ne 0) { throw "$mode failed: child exit $LASTEXITCODE" }
    $result=Get-Content (Join-Path $state 'heartbeat.json') -Raw | ConvertFrom-Json
    if ($result.last_launch_status -eq 'started' -or $result.last_launch_status -eq 'failed') { throw "$mode launched or failed" }
    if ($result.queue_count -ne 1 -and $mode -ne 'retry') { throw "$mode owner filtering failed" }
    $expected=@{check='check_only'; hold='manual_workstream_hold'; lease='active_dispatch_lease'; missing='queue_empty'}
    if ($expected.ContainsKey($mode) -and $result.blocked_reason -ne $expected[$mode]) { throw "$mode wrong reason" }
    if (Get-ChildItem $state -Filter 'run-*') { throw "$mode created execution artifacts" }
}
Write-Output 'PASS: 5 isolated no-launch paths; fake git/gh only; no runtime state touched'
