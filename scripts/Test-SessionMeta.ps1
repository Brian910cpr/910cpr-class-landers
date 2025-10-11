# scripts\Test-SessionMeta.ps1
<#
Audits docs\sessions\*.html for:
- robots meta (index vs noindex)
- "This class has passed." banner
Usage:
  pwsh -File .\scripts\Test-SessionMeta.ps1
#>

$ErrorActionPreference = "Stop"
$Repo   = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$SessDir = Join-Path $Repo "docs\sessions"
if (-not (Test-Path $SessDir)) { throw "Missing $SessDir" }

function Get-DateFromName([string]$name) {
  if ($name -match '^(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})-') {
    $d = Get-Date ("$($Matches[1]) $($Matches[2]):$($Matches[3])")
    return $d
  }
  return $null
}

$now = Get-Date
$files = Get-ChildItem $SessDir -Filter *.html
$report = foreach ($f in $files) {
  $dt = Get-DateFromName $f.Name
  $isFuture = $false
  if ($dt) { $isFuture = $dt -ge $now.AddMinutes(-1) }
  $html = Get-Content -LiteralPath $f.FullName -Raw
  $robots = if ($html -match '<meta\s+name=["'']robots["'']\s+content=["'']([^"'']+)["'']') { $Matches[1] } else { "" }
  $hasBanner = ($html -match 'This class has passed.')
  [pscustomobject]@{ File=$f.Name; Date=$dt; Future=$isFuture; Robots=$robots; PassedBanner=$hasBanner }
}

$future  = $report | Where-Object { $_.Future -eq $true }
$past    = $report | Where-Object { $_.Future -eq $false -and $_.Date -ne $null }
$futureWrong = $future | Where-Object { $_.Robots -notmatch 'index,follow' }
$pastWrong   = $past   | Where-Object { $_.Robots -notmatch 'noindex,follow' -or $_.PassedBanner -ne $true }

Write-Host ("Total: {0} | Future: {1} | Past: {2}" -f $report.Count, $future.Count, $past.Count)
Write-Host ("Future with wrong robots: {0}" -f $futureWrong.Count)
Write-Host ("Past missing noindex or banner: {0}" -f $pastWrong.Count)

$futureWrong | Select-Object -First 5 | Format-Table -AutoSize
$pastWrong   | Select-Object -First 5 | Format-Table -AutoSize
