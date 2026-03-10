Write-Host ""
Write-Host "==============================="
Write-Host "910CPR Site Refresh Starting..."
Write-Host "==============================="
Write-Host ""

# Move to repo root
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

# Check Python
Write-Host "Checking Python..."
python --version

Write-Host ""
Write-Host "Step 1: Build schedule.json"
python scripts/build_schedule.py

Write-Host ""
Write-Host "Step 2: Build public_schedule.json"
python scripts/build_public_schedule_json.py

Write-Host ""
Write-Host "Step 3: Build index + sitemap"
python scripts/build_index_and_sitemap.py

Write-Host ""
Write-Host "==============================="
Write-Host "Site refresh complete."
Write-Host "==============================="
Write-Host ""