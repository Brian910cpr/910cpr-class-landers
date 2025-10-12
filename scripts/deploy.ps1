# deploy.ps1
param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$BuildOutDir
)
# Example:
# .\deploy.ps1 -RepoRoot "D:\Users\ten77\Documents\GitHub\910cpr-class-landers" -BuildOutDir "D:\Work\sales-fliers-out"

$ErrorActionPreference = "Stop"

$docsFliers = Join-Path $RepoRoot "docs\fliers"
New-Item -ItemType Directory -Force -Path $docsFliers | Out-Null

Copy-Item -Path (Join-Path $BuildOutDir "fliers\*.html") -Destination $docsFliers -Force
Copy-Item -Path (Join-Path $BuildOutDir "image-sales-fliers-wishlist.txt") -Destination (Join-Path $RepoRoot "docs\") -Force

Set-Location $RepoRoot
git pull
git add docs\fliers\*.html docs\image-sales-fliers-wishlist.txt
git commit -m "Add per-session sales flier landers + image wishlist"
git push
