$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$StaticPort = 8000
$AdminPort = 5057
$InventoryUrl = "http://localhost:$StaticPort/docs/control-center/modules/inventory-control.html"

function Test-PortActive {
  param([int]$Port)
  return [bool](Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1)
}

function Get-ChromePath {
  $candidates = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
  )
  foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path $candidate)) {
      return $candidate
    }
  }
  return $null
}

if (Test-PortActive -Port $StaticPort) {
  Write-Host "Static server already running on http://localhost:$StaticPort"
} else {
  Start-Process -FilePath "python" `
    -ArgumentList @("-m", "http.server", "$StaticPort") `
    -WorkingDirectory $RepoRoot `
    -WindowStyle Hidden | Out-Null
  Start-Sleep -Seconds 1
  Write-Host "Static server running on http://localhost:$StaticPort"
}

if (Test-PortActive -Port $AdminPort) {
  Write-Host "Admin server already running on http://127.0.0.1:$AdminPort"
} else {
  Start-Process -FilePath "python" `
    -ArgumentList @("scripts\inventory_control_admin_server.py") `
    -WorkingDirectory $RepoRoot `
    -WindowStyle Hidden | Out-Null
  Start-Sleep -Seconds 2
  Write-Host "Admin server running on http://127.0.0.1:$AdminPort"
}

Write-Host "Opening Inventory Control"
$chrome = Get-ChromePath
if ($chrome) {
  Start-Process -FilePath $chrome -ArgumentList @($InventoryUrl) | Out-Null
} else {
  Start-Process $InventoryUrl | Out-Null
}
