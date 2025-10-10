param(
  [Parameter(Mandatory=$true)]
  [string]$RepoRoot,
  [switch]$DryRun
)

# --- Resolve and prepare ---
$RepoRoot = (Resolve-Path $RepoRoot).Path
if (-not (Test-Path $RepoRoot)) { throw "Repo root not found: $RepoRoot" }

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LegacyRoot = Join-Path $RepoRoot "_legacy\$stamp"
$LogPath = Join-Path $RepoRoot ("_legacy\archive-" + $stamp + ".log")
if (-not (Test-Path (Split-Path $LogPath))) { New-Item -ItemType Directory -Path (Split-Path $LogPath) -Force | Out-Null }

# --- Keep lists ---
$KeepFilesRoot = @("CNAME",".nojekyll","robots.txt","sitemap.xml",".gitignore","README.md")
$KeepFiles     = @(
  "data\sessions.csv",
  "data\courses.csv",
  "data\locations.csv",
  "scripts\build_from_hovn.py",
  "docs\index.html"
)
$KeepDirs      = @("docs\courses","docs\images","data\seo")

function To-Rel([string]$path) {
  $rp = (Resolve-Path $path).Path
  return ($rp.Substring($RepoRoot.Length).TrimStart('\')).ToLowerInvariant()
}

$KeepFilesFull = New-Object System.Collections.Generic.HashSet[string]
foreach ($f in $KeepFiles) {
  $full = Join-Path $RepoRoot $f
  if (Test-Path $full) { [void]$KeepFilesFull.Add((To-Rel $full)) }
}
$KeepFilesRootFull = New-Object System.Collections.Generic.HashSet[string]
foreach ($f in $KeepFilesRoot) {
  $full = Join-Path $RepoRoot $f
  if (Test-Path $full) { [void]$KeepFilesRootFull.Add((To-Rel $full)) }
}
$KeepDirPrefixes = $KeepDirs | ForEach-Object { $_.TrimEnd('\').ToLowerInvariant() }

function Is-Kept([string]$relPath) {
  $rel = $relPath.ToLowerInvariant().Trim('\')
  if ($KeepFilesFull.Contains($rel)) { return $true }
  if ($KeepFilesRootFull.Contains($rel)) { return $true }
  foreach ($k in $KeepDirPrefixes) {
    if ($rel.StartsWith($k)) { return $true }
  }
  return $false
}

# --- Logging setup ---
"Archive started: $(Get-Date -Format s)" | Out-File -FilePath $LogPath
"Repo: $RepoRoot" | Out-File -FilePath $LogPath -Append
"Legacy target: $LegacyRoot`n" | Out-File -FilePath $LogPath -Append
if (-not $DryRun) { New-Item -ItemType Directory -Path $LegacyRoot -Force | Out-Null }

# --- Move everything not in keep list ---
$All = Get-ChildItem -LiteralPath $RepoRoot -Recurse -Force |
  Where-Object { $_.FullName -notlike "*\_legacy\*" -and $_.FullName -notlike "*\.git\*" }

$Files = $All | Where-Object { -not $_.PSIsContainer }
$Dirs  = $All | Where-Object { $_.PSIsContainer } | Sort-Object FullName -Descending
$Moved = 0

foreach ($file in $Files) {
  $rel = To-Rel $file.FullName
  if (-not (Is-Kept $rel)) {
    $dest = Join-Path $LegacyRoot $rel
    $destDir = Split-Path $dest
    if (-not $DryRun) {
      if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
      Move-Item -LiteralPath $file.FullName -Destination $dest -Force
    }
    "[FILE] $rel -> _legacy\$stamp\$rel" | Out-File -FilePath $LogPath -Append
    $Moved++
  }
}

foreach ($dir in $Dirs) {
  $rel = To-Rel $dir.FullName
  if ([string]::IsNullOrWhiteSpace($rel)) { continue }
  if (-not (Is-Kept $rel)) {
    if (-not (Get-ChildItem -LiteralPath $dir.FullName -Force -Recurse |
              Where-Object { $_.FullName -notlike "*\_legacy\*" })) {
      $dest = Join-Path $LegacyRoot $rel
      $destParent = Split-Path $dest
      if (-not $DryRun) {
        if (-not (Test-Path $destParent)) { New-Item -ItemType Directory -Path $destParent -Force | Out-Null }
        Move-Item -LiteralPath $dir.FullName -Destination $dest -Force
      }
      "[DIR ] $rel -> _legacy\$stamp\$rel" | Out-File -FilePath $LogPath -Append
      $Moved++
    }
  }
}

"`nMoved items: $Moved`nArchive complete: $(Get-Date -Format s)" | Out-File -FilePath $LogPath -Append
Write-Host "Done. Moved items: $Moved"
Write-Host "Log: $LogPath"
if ($DryRun) { Write-Host "DryRun mode: no changes made." }
