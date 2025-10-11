<#
Nightly-Refresh.ps1
- git pull --rebase
- Build-Sessions (no Now override)
- commit + push (only if changes)

Schedule in Windows Task Scheduler daily.
#>

$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Set-Location $Repo

git pull --rebase

pwsh -File (Join-Path $Repo "scripts\Build-Sessions.ps1")

# Build-Sessions already commits; push if ahead
$ahead = (git status -sb) -match '\[ahead '
if ($ahead) {
  git push
}
