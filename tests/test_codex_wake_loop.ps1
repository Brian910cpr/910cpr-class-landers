$ErrorActionPreference = 'Stop'
$source = (Resolve-Path "$PSScriptRoot/../ops/scripts/Start-CodexWakeLoop.ps1").Path
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('issue380-loop-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $fixture | Out-Null
@'
param($StateDirectory,$LoopProcessId,$WorkerProcessId=0)
"$WorkerProcessId" | Add-Content (Join-Path $StateDirectory 'calls.txt')
'@ | Set-Content (Join-Path $fixture 'Publish-CodexWakeHealth.ps1')
function Start-Process {
    param($FilePath,$ArgumentList,$WindowStyle,[switch]$PassThru)
    if ($WindowStyle -ne 'Hidden' -or $ArgumentList -notmatch '-NonInteractive') { throw 'Unsafe process arguments' }
    $process = [pscustomobject]@{ Id=12345; ExitCode=7; Calls=0 }
    $process | Add-Member ScriptMethod WaitForExit { param($milliseconds) $this.Calls++; return ($this.Calls -ge 2) }
    return $process
}
function Start-Sleep { param($Seconds) if ($Seconds -eq 60) { throw 'ISOLATED_STOP' } }
try { & $source -RepoPath $fixture -StateDirectory $fixture -InitialDelaySeconds 0 -IntervalMinutes 1; throw 'Loop unexpectedly returned' }
catch { if ($_.Exception.Message -ne 'ISOLATED_STOP') { throw } }
$calls = @(Get-Content (Join-Path $fixture 'calls.txt'))
if (($calls -join ',') -ne '12345,12345,0') { throw "Wrong work/idle publication sequence: $calls" }
if ((Get-Content (Join-Path $fixture 'loop.log') -Raw) -notmatch 'cycle_exit=7') { throw 'Worker failure not preserved' }
$lock = [IO.File]::Open((Join-Path $fixture 'loop.lock'), 'Open', 'ReadWrite', 'None')
$lock.Dispose()
Write-Output 'PASS: hidden fake process; work/idle publication; nonzero exit; lock released; no real process/network'
