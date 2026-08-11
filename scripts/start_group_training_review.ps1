[CmdletBinding()]
param(
    [ValidateRange(1024, 65535)]
    [int]$Port = 8765,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$docsRoot = Join-Path $repoRoot 'docs'
$landingPage = Join-Path $docsRoot 'group-training.html'
$requestPage = Join-Path $docsRoot 'request_group_session.html'

foreach ($requiredFile in @($landingPage, $requestPage)) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "Missing review page: $requiredFile"
    }
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $commonPythonPaths = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'),
        'C:\Python312\python.exe',
        'C:\Python313\python.exe'
    )
    $pythonPath = $commonPythonPaths | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
    if (-not $pythonPath) {
        throw 'Python was not found on PATH or in the common installation locations checked.'
    }
} else {
    $pythonPath = $python.Source
}

$existingListener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if (-not $existingListener) {
    $serverArguments = "-m http.server $Port --directory `"$docsRoot`""
    $process = Start-Process -FilePath $pythonPath `
        -ArgumentList $serverArguments `
        -WorkingDirectory $repoRoot `
        -WindowStyle Hidden `
        -PassThru
    Start-Sleep -Milliseconds 700
    if ($process.HasExited) {
        throw "The review server exited before it could listen on port $Port."
    }
}

$landingUrl = "http://127.0.0.1:$Port/group-training.html"
$requestUrl = "http://127.0.0.1:$Port/request_group_session.html"

if (-not $NoBrowser) {
    Start-Process $landingUrl
    Start-Process $requestUrl
}

Write-Output '910CPR group-training review server is available.'
Write-Output "Landing page: $landingUrl"
Write-Output "Request page: $requestUrl"
Write-Output 'The server uses the current branch docs directory without modifying rendered files.'
