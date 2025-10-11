<#
Build-Sessions.ps1
- Prefers newest sessions*.csv in .\data
- Fallback: search Downloads and repo for sessions*.csv (including "sessions (1).csv")
- Copies chosen CSV -> .\data\sessions.csv
- Runs build + sitemap
- Optional git commit

Usage:
  pwsh -File .\scripts\Build-Sessions.ps1
  pwsh -File .\scripts\Build-Sessions.ps1 -NoGitCommit
#>

param(
  [switch]$NoGitCommit
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

# 1) First preference: data\sessions*.csv
$dataDir = Join-Path $Repo 'data'
$newest = Get-NewestCsv -Roots @($dataDir)

# 2) Fallback: Downloads and repo
if (-not $newest) {
  $downloads = Join-Path $env:USERPROFILE 'Downloads'
  $newest = Get-NewestCsv -Roots @($downloads, $Repo)
}

# 3) If found, normalize to data\sessions.csv; if not, we still proceed (builder will warn/skip)
if ($newest) {
  Write-Host "Using CSV: $($newest.FullName)"
  New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
  Copy-Item -LiteralPath $newest.FullName -Destination (Join-Path $dataDir 'sessions.csv') -Force
} else {
  Write-Host "No sessions*.csv found. Builder will skip (pages remain as-is)."
}

# 4) Run builder & sitemap
$buildPy   = Join-Path $Repo "scripts\build_from_hovn.py"
$siteMapPy = Join-Path $Repo "scripts\make_sessions_sitemap.py"
if (-not (Test-Path $buildPy))   { throw "Missing $buildPy" }
if (-not (Test-Path $siteMapPy)) { throw "Missing $siteMapPy" }

Write-Host "`n== Build session pages =="
python $buildPy

Write-Host "`n== Build sitemap (future only) =="
python $siteMapPy

# 5) Quick report
$SessDir = Join-Path $Repo "docs\sessions"
$pages = @(Get-ChildItem $SessDir -Filter *.html -ErrorAction SilentlyContinue)
Write-Host ("`nPages on disk: {0}" -f $pages.Count)

# 6) Optional commit
if (-not $NoGitCommit) {
  $changed = (git status --porcelain)
  if ($changed) {
    git add .
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    git commit -m "Build sessions & sitemap ($stamp)"
    Write-Host "Committed changes."
  } else {
    Write-Host "No changes to commit."
  }
} else {
  Write-Host "Skipping git commit (NoGitCommit)."
}
