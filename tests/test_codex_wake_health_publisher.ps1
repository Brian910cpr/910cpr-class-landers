$ErrorActionPreference = 'Stop'
$source = (Resolve-Path "$PSScriptRoot/../ops/scripts/Publish-CodexWakeHealth.ps1").Path
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('issue380-health-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $fixture | Out-Null
$global:healthCalls = 0
function gh {
    $global:healthCalls++
    $payload = $input | Out-String
    if ($payload -match 'PRIVATE_SENTINEL') { throw 'Private state escaped allowlist' }
    if ($args -notcontains 'repos/Brian910cpr/910cpr-class-landers/issues/comments/123') { throw 'Wrong target' }
    $global:LASTEXITCODE = 0
    if ($global:healthCalls -eq 2) { $global:LASTEXITCODE = 1 }
}
& $source -StateDirectory $fixture -LoopProcessId $PID
if ($global:healthCalls) { throw 'Missing configuration caused publication' }
'{"comment_id":"123"}' | Set-Content "$fixture/health-publish.json"
'{"worker_state":"idle","private":"PRIVATE_SENTINEL"}' | Set-Content "$fixture/state.json"
& $source -StateDirectory $fixture -LoopProcessId $PID
$before = Get-Content "$fixture/published-health.json" -Raw
if ($global:healthCalls -ne 1 -or $before -match 'PRIVATE_SENTINEL') { throw 'Publication/allowlist failed' }
& $source -StateDirectory $fixture -LoopProcessId $PID
if ((Get-Content "$fixture/published-health.json" -Raw) -ne $before) { throw 'Failed upload fabricated fresh success' }
if ((Get-Content "$fixture/loop.log" -Raw) -notmatch 'health publication failed') { throw 'Failure not recorded' }
'{"comment_id":"invalid"}' | Set-Content "$fixture/health-publish.json"
& $source -StateDirectory $fixture -LoopProcessId $PID
if ($global:healthCalls -ne 2) { throw 'Invalid configuration reached GitHub' }
Write-Output 'PASS: no-config skip; allowlisted success; upload failure retains last success; invalid target rejected; fake GitHub only'
