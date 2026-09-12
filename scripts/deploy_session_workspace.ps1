param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{64}$')]
    [string]$ExpectedLiveSourceSha256,
    [string]$ProjectRef = 'wktwgcnwdvbebcobgyey'
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$sourcePath = Join-Path $repoRoot 'supabase/functions/session-workspace/index.ts'
$manifestPath = Join-Path $repoRoot 'supabase/functions/session-workspace/deployment.json'
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json

if ($manifest.function -ne 'session-workspace' -or $manifest.project_ref -ne $ProjectRef -or $manifest.verify_jwt -ne $false) {
    throw 'Deployment manifest does not preserve the reviewed session-workspace project/no-verify-jwt contract.'
}

$sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $sourcePath).Hash.ToLowerInvariant()
if ($sourceHash -ne $ExpectedLiveSourceSha256.ToLowerInvariant()) {
    throw "Source hash does not match independently established live hash. Local: $sourceHash"
}

$supabase = Get-Command supabase -ErrorAction SilentlyContinue
if (-not $supabase) { throw 'Supabase CLI was not found on PATH. Install/authenticate it before deployment.' }

Write-Host "Preflight passed for session-workspace source SHA-256 $sourceHash"
& $supabase.Source functions deploy session-workspace --project-ref $ProjectRef --no-verify-jwt
if ($LASTEXITCODE -ne 0) { throw "Supabase deployment failed with exit code $LASTEXITCODE" }
