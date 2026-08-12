[CmdletBinding()]
param(
    [ValidateSet('status', 'inventory', 'push', 'pull', 'verify')]
    [string]$Operation = 'status',
    [string]$ManifestPath = (Join-Path $PSScriptRoot '..\data\migration\google_drive_transfer_manifest.json'),
    [string[]]$EntryId,
    [string]$DriveRoot = $env:LANDERWARE_DRIVE_ROOT,
    [switch]$Execute
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$StateRoot = if ($env:LANDERWARE_TRANSFER_STATE_ROOT) {
    $env:LANDERWARE_TRANSFER_STATE_ROOT
} elseif ($env:LOCALAPPDATA) {
    Join-Path $env:LOCALAPPDATA 'LanderWare\DriveTransfer'
} else {
    Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'LanderWare\DriveTransfer'
}
$LogRoot = Join-Path $StateRoot 'logs'
$ConfigPath = Join-Path $StateRoot 'config.json'
$script:LogPath = $null

# The Dockmaster kept two ledgers: one for cargo promised, and one for cargo actually aboard.
# He never let a penciled promise become a departure order without the owner's mark.

function Write-TransferLog {
    param([string]$Level, [string]$Message)
    if (-not $script:LogPath) {
        New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
        $script:LogPath = Join-Path $LogRoot ("drive-transfer-{0:yyyyMMdd-HHmmss}-{1}.log" -f (Get-Date), $PID)
    }
    $line = '{0:o} [{1}] {2}' -f (Get-Date), $Level.ToUpperInvariant(), $Message
    Add-Content -LiteralPath $script:LogPath -Value $line -Encoding utf8
    Write-Host $line
}
function Get-ConfiguredDriveRoot {
    if ($DriveRoot) { return $DriveRoot }
    if (Test-Path -LiteralPath $ConfigPath -PathType Leaf) {
        $config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
        if ($config.drive_root) { return [string]$config.drive_root }
    }
    return $null
}

function Assert-SafeRelativePath {
    param([Parameter(Mandatory)][string]$Path, [string]$Label)
    if ([IO.Path]::IsPathRooted($Path) -or $Path -match '(^|[\\/])\.\.([\\/]|$)') {
        throw "$Label must be a repository/Drive-relative path without '..': $Path"
    }
    $normalized = $Path.Replace('\', '/').Trim('/')
    $blocked = @(
        '(^|/)\.git(/|$)',
        '(^|/)\.env($|\.)',
        '(^|/)(credentials?|secrets?|tokens?)(/|$|\.)',
        '(^|/)(browser profiles?|auth(entication)?)(/|$)'
    )
    foreach ($pattern in $blocked) {
        if ($normalized -match $pattern) { throw "$Label is blocked by the safety policy: $Path" }
    }
    return $normalized
}

function Get-ManifestEntries {
    $resolved = (Resolve-Path -LiteralPath $ManifestPath).Path
    $manifest = Get-Content -LiteralPath $resolved -Raw | ConvertFrom-Json
    if ($manifest.schema_version -ne 1) { throw "Unsupported manifest schema_version: $($manifest.schema_version)" }
    $entries = @($manifest.entries)
    if ($EntryId) { $entries = @($entries | Where-Object { $EntryId -contains $_.id }) }
    if ($EntryId -and $entries.Count -ne $EntryId.Count) { throw 'One or more requested EntryId values were not found.' }
    return $entries
}

function Get-ExpandedFiles {
    param([Parameter(Mandatory)][string]$Root, [Parameter(Mandatory)][string]$RelativePath)
    $base = Join-Path $Root $RelativePath
    if (-not (Test-Path -LiteralPath $base)) { return @() }
    $item = Get-Item -LiteralPath $base -Force
    if (-not $item.PSIsContainer) {
        return ,([pscustomobject]@{ FullName = $item.FullName; Relative = $RelativePath.Replace('\', '/') })
    }
    return @(Get-ChildItem -LiteralPath $item.FullName -File -Recurse -Force | ForEach-Object {
        $child = $_.FullName.Substring($item.FullName.Length).TrimStart('\', '/')
        [pscustomobject]@{ FullName = $_.FullName; Relative = (Join-Path $RelativePath $child).Replace('\', '/') }
    })
}

function Get-HashValue { param([string]$Path) (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }

function Invoke-CopyEntry {
    param([object]$Entry, [ValidateSet('push', 'pull')][string]$Direction)
    if ($Entry.approval_status -ne 'approved') { throw "Entry '$($Entry.id)' is '$($Entry.approval_status)'; only approved entries may transfer." }
    $sourceRel = Assert-SafeRelativePath ([string]$Entry.source_path) 'source_path'
    $driveRel = Assert-SafeRelativePath ([string]$Entry.proposed_drive_destination) 'proposed_drive_destination'
    $drive = Get-ConfiguredDriveRoot
    if (-not $drive -or -not (Test-Path -LiteralPath $drive -PathType Container)) { throw 'Drive root is unavailable. Set LANDERWARE_DRIVE_ROOT or the external config drive_root.' }

    if ($Direction -eq 'push') { $sourceRoot = $RepoRoot; $sourceBase = $sourceRel; $destinationRoot = $drive; $destinationBase = $driveRel }
    else { $sourceRoot = $drive; $sourceBase = $driveRel; $destinationRoot = $RepoRoot; $destinationBase = $sourceRel }

    $files = Get-ExpandedFiles $sourceRoot $sourceBase
    if ($files.Count -eq 0) { throw "Source is missing or empty for entry '$($Entry.id)'." }
    foreach ($file in $files) {
        $suffix = if ($file.Relative -eq $sourceBase) { '' } else { $file.Relative.Substring($sourceBase.Length).TrimStart('/') }
        $destinationRel = if ($suffix) { (Join-Path $destinationBase $suffix).Replace('\', '/') } else { $destinationBase }
        [void](Assert-SafeRelativePath $destinationRel 'resolved destination')
        $destination = Join-Path $destinationRoot $destinationRel
        $sourceInfo = Get-Item -LiteralPath $file.FullName
        if (Test-Path -LiteralPath $destination -PathType Leaf) {
            $destinationInfo = Get-Item -LiteralPath $destination
            if ($destinationInfo.LastWriteTimeUtc -gt $sourceInfo.LastWriteTimeUtc) { throw "Destination is newer; refusing overwrite: $destination" }
            if ($destinationInfo.Length -eq $sourceInfo.Length -and (Get-HashValue $destination) -eq (Get-HashValue $file.FullName)) {
                Write-TransferLog INFO "SKIP identical: $($file.FullName) -> $destination"
                continue
            }
        }
        if (-not $Execute) { Write-TransferLog DRYRUN "COPY $($file.FullName) -> $destination"; continue }
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $destination
        $copied = Get-Item -LiteralPath $destination
        if ($copied.Length -ne $sourceInfo.Length -or (Get-HashValue $destination) -ne (Get-HashValue $file.FullName)) {
            throw "Post-copy verification failed: $destination"
        }
        Write-TransferLog INFO "COPIED+VERIFIED $($file.FullName) -> $destination"
    }
}

function Invoke-VerifyEntry {
    param([object]$Entry)
    $sourceRel = Assert-SafeRelativePath ([string]$Entry.source_path) 'source_path'
    $driveRel = Assert-SafeRelativePath ([string]$Entry.proposed_drive_destination) 'proposed_drive_destination'
    $drive = Get-ConfiguredDriveRoot
    if (-not $drive -or -not (Test-Path -LiteralPath $drive -PathType Container)) { throw 'Drive root is unavailable.' }
    $files = Get-ExpandedFiles $RepoRoot $sourceRel
    foreach ($file in $files) {
        $suffix = if ($file.Relative -eq $sourceRel) { '' } else { $file.Relative.Substring($sourceRel.Length).TrimStart('/') }
        $destinationRel = if ($suffix) { Join-Path $driveRel $suffix } else { $driveRel }
        $destination = Join-Path $drive $destinationRel
        if (-not (Test-Path -LiteralPath $destination -PathType Leaf)) { Write-TransferLog ERROR "MISSING $destination"; continue }
        $sourceInfo = Get-Item -LiteralPath $file.FullName
        $destinationInfo = Get-Item -LiteralPath $destination
        $ok = $sourceInfo.Length -eq $destinationInfo.Length -and (Get-HashValue $file.FullName) -eq (Get-HashValue $destination)
        Write-TransferLog ($(if ($ok) { 'INFO' } else { 'ERROR' })) "VERIFY=$ok $($file.FullName) <-> $destination"
    }
}

try {
    Write-TransferLog INFO "operation=$Operation execute=$([bool]$Execute) repo=$RepoRoot manifest=$ManifestPath"
    $drive = Get-ConfiguredDriveRoot
    if ($Operation -eq 'status') {
        $status = [pscustomobject]@{
            drive_root = $drive
            drive_available = [bool]($drive -and (Test-Path -LiteralPath $drive -PathType Container))
            config_path = $ConfigPath
            config_exists = Test-Path -LiteralPath $ConfigPath -PathType Leaf
            manifest_exists = Test-Path -LiteralPath $ManifestPath -PathType Leaf
            default_mode = 'dry-run'
            log_path = $script:LogPath
        }
        $status | Format-List
        exit $(if ($status.drive_available) { 0 } else { 2 })
    }

    $entries = Get-ManifestEntries
    if ($Operation -eq 'inventory') {
        $entries | ForEach-Object {
            $safe = Assert-SafeRelativePath ([string]$_.source_path) 'source_path'
            $files = Get-ExpandedFiles $RepoRoot $safe
            [pscustomobject]@{ id=$_.id; approval_status=$_.approval_status; files=$files.Count; actual_bytes=[int64](($files | ForEach-Object { (Get-Item -LiteralPath $_.FullName).Length } | Measure-Object -Sum).Sum); source_path=$safe; proposed_drive_destination=$_.proposed_drive_destination }
        } | Format-Table -AutoSize
    } elseif ($Operation -in @('push', 'pull')) {
        foreach ($entry in $entries) { Invoke-CopyEntry $entry $Operation }
    } elseif ($Operation -eq 'verify') {
        foreach ($entry in $entries) { Invoke-VerifyEntry $entry }
    }
} catch {
    Write-TransferLog ERROR $_.Exception.Message
    exit 1
}
