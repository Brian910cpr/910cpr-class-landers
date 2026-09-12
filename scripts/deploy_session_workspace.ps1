param(
    [switch]$Deploy,
    [string]$ProjectRef = 'wktwgcnwdvbebcobgyey'
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$sourcePath = Join-Path $repoRoot 'supabase/functions/session-workspace/index.ts'
$manifestPath = Join-Path $repoRoot 'supabase/functions/session-workspace/deployment.json'
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json

if ($manifest.function -ne 'session-workspace' -or $manifest.project_ref -ne $ProjectRef -or $manifest.verify_jwt -ne $false) {
    throw 'Deployment manifest does not preserve the reviewed project/no-verify-jwt contract.'
}
if ($manifest.authorization_boundary -ne 'x-maxim-session' -or $manifest.live_source_match -ne $true) {
    throw 'Deployment manifest does not record the reviewed internal authorization boundary and live-source match.'
}

$sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $sourcePath).Hash.ToLowerInvariant()
$reviewedHash = [string]$manifest.live_source_sha256
if ($sourceHash -ne $reviewedHash) {
    throw "Source hash differs from the independently reviewed live source. Local: $sourceHash; reviewed live: $reviewedHash"
}

Write-Host "Preflight passed: local session-workspace source matches reviewed live SHA-256 $sourceHash"
if (-not $Deploy) {
    Write-Host 'Check-only mode; production was not deployed. Pass -Deploy only after review approval.'
    exit 0
}

$supabase = Get-Command supabase -ErrorAction SilentlyContinue
if (-not $supabase) { throw 'Supabase CLI was not found on PATH. Install/authenticate it before deployment.' }

& $supabase.Source functions deploy session-workspace --project-ref $ProjectRef --no-verify-jwt
if ($LASTEXITCODE -ne 0) { throw "Supabase deployment failed with exit code $LASTEXITCODE" }
