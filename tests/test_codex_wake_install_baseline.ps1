$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../ops/scripts/Test-CodexWakeInstallBaseline.ps1"
$root = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
New-Item -ItemType Directory $root | Out-Null
$source = Join-Path $root 'source.ps1'
$dest = Join-Path $root 'installed.ps1'
Set-Content $source 'source'
$files = @(@{Source=$source; Destination=$dest})
Assert-CodexWakeInstallBaseline $files
if (Test-Path $dest) { throw 'Preflight wrote missing destination' }
Copy-Item $source $dest
Assert-CodexWakeInstallBaseline $files
Set-Content $dest 'installed safeguard'
$before = (Get-FileHash $dest).Hash
$rejected = $false
try { Assert-CodexWakeInstallBaseline $files } catch {
    if ($_.Exception.Message -notlike '*install refused*') { throw }
    $rejected = $true
}
if (-not $rejected -or (Get-FileHash $dest).Hash -ne $before) { throw 'Drift not preserved' }
$rejected = $false
try { Assert-CodexWakeInstallBaseline @(@{Source="$root/missing"; Destination=$dest}) } catch { $rejected = $true }
if (-not $rejected) { throw 'Missing source accepted' }
# Full installer failure path: temporary LOCALAPPDATA only, never real installation.
$oldLocal = $env:LOCALAPPDATA
try {
    $env:LOCALAPPDATA = $root
    $installed = Join-Path $root '910CPR/CodexWake'
    New-Item -ItemType Directory -Path $installed -Force | Out-Null
    Set-Content "$installed/Invoke-CodexWake.ps1" 'throw "MUST NEVER EXECUTE"'
    Set-Content "$installed/state.json" 'preserve-state'
    $snapshot = (Get-FileHash "$installed/Invoke-CodexWake.ps1").Hash
    $rejected = $false
    try { & "$PSScriptRoot/../ops/scripts/Install-CodexWake.ps1" -SeedCurrentTask 297 } catch {
        if ($_.Exception.Message -notlike '*install refused*') { throw }
        $rejected = $true
    }
    if (-not $rejected) { throw 'Installer did not reject drift' }
    if ((Get-FileHash "$installed/Invoke-CodexWake.ps1").Hash -ne $snapshot) { throw 'Installer overwrote script' }
    if ((Get-Content "$installed/state.json" -Raw).Trim() -ne 'preserve-state') { throw 'Installer seeded state' }
    if (Test-Path "$installed/Start-CodexWakeLoop.ps1") { throw 'Installer partially copied loop' }
} finally { $env:LOCALAPPDATA = $oldLocal }
# Both files must be checked; loop-only drift also blocks installation.
Set-Content $dest 'loop drift'
$rejected = $false
try { Assert-CodexWakeInstallBaseline @(@{Source=$source;Destination="$root/new.ps1"}, @{Source=$source;Destination=$dest}) } catch { $rejected = $true }
if (-not $rejected -or (Test-Path "$root/new.ps1")) { throw 'Second-file drift accepted or wrote files' }
Write-Output 'PASS: 6 baseline/install checks; no launcher/task/process invoked'
Write-Output "Temporary fixtures retained: $root"
