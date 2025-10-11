<#
Build-Sessions.ps1
- Prefers newest sessions*.csv in .\data (fallback: Downloads + repo)
- Copies to .\data\sessions.csv
- Runs: build_from_hovn.py (with optional --now), make_sessions_sitemap.py, make_course_hubs.py
- Optional commit/push

Usage:
  pwsh -File .\scripts\Build-Sessions.ps1
  pwsh -File .\scripts\Build-Sessions.ps1 -Now "2025-10-12 12:00" -NoGitCommit
  pwsh -File .\scripts\Build-Sessions.ps1 -Push
#>

param(
  [string]$Now,
  [switch]$NoGitCommit,
  [switch]$Push
)

$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Set-Location $Repo

function Get-NewestCsv {
  param([string[]]$Roots)
  $patterns = @('sessions*.csv','Sessions*.csv')
  $files = @()
  foreach ($root in $Roots) {
    foreach ($pat in $patterns) {
      $files += Get-ChildItem -Path $root -Filter $pat -Recurse -ErrorAction SilentlyContinue
    }
  }
  $files = $files | Where-Object { -not $_.PSIsContainer } | Sort-Object LastWriteTime -Descending
  if ($files) { return $files[0] }
  return $null
}

# 1) Locate CSV (prefer data)
$dataDir = Join-Path $Repo 'data'
$newest = Get-NewestCsv -Roots @($dataDir)
if (-not $newest) {
  $downloads = Join-Path $env:USERPROFILE 'Downloads'
  $newest = Get-NewestCsv -Roots @($downloads, $Repo)
}
if ($newest) {
  Write-Host "Using CSV: $($newest.FullName)"
  New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
  Copy-Item -LiteralPath $newest.FullName -Destination (Join-Path $dataDir 'sessions.csv') -Force
} else {
  Write-Host "No sessions*.csv found. Builder will skip (pages remain as-is)."
}

# 2) Paths
$buildPy   = Join-Path $Repo "scripts\build_from_hovn.py"
$siteMapPy = Join-Path $Repo "scripts\make_sessions_sitemap.py"
$coursesPy = Join-Path $Repo "scripts\make_course_hubs.py"
foreach ($p in @($buildPy,$siteMapPy,$coursesPy)) { if (-not (Test-Path $p)) { throw "Missing $p" } }

# 3) Build: pages (+json), sitemap, hubs
Write-Host "`n== Build session pages (and sessions.json) =="
$nowArg = @()
if ($Now) { $nowArg = @("--now", $Now) }
python $buildPy @nowArg

Write-Host "`n== Build sitemap (future only) =="
python $siteMapPy

Write-Host "`n== Build course hubs =="
python $coursesPy

# 4) Report
$SessDir = Join-Path $Repo "docs\sessions"
$pages = @(Get-ChildItem $SessDir -Filter *.html -ErrorAction SilentlyContinue)
Write-Host ("`nPages on disk: {0}" -f $pages.Count)

# 5) Commit / push
if (-not $NoGitCommit) {
  $changed = (git status --porcelain)
  if ($changed) {
    git add .
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    git commit -m "Build: sessions + sitemap + hubs ($stamp)"
    Write-Host "Committed changes."
  } else {
    Write-Host "No changes to commit."
  }
} else {
  Write-Host "Skipping git commit (NoGitCommit)."
}

if ($Push) {
  git push
  Write-Host "Pushed to origin."
}
