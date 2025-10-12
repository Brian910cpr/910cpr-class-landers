param(
  [switch]$Headless = $false
)

$ErrorActionPreference = 'Stop'

# Resolve repo root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Repo = Resolve-Path (Join-Path $ScriptDir "..") | Select-Object -ExpandProperty Path
Set-Location $Repo
Write-Host "Repo: $Repo"

function Get-PySpec {
  # Prefer Python 3.12, then 3.11
  try { & py -3.12 -c "import sys;print(sys.version)" *> $null; return "-3.12" } catch {}
  try { & py -3.11 -c "import sys;print(sys.version)" *> $null; return "-3.11" } catch {}
  throw "No suitable Python found. Install Python 3.12 (or 3.11), then re-run:
  winget install --id Python.Python.3.12 -e"
}

$pySpec = Get-PySpec

# If a venv exists but was made with a different base version, replace it
$Venv = Join-Path $Repo ".venv"
$PyExe = Join-Path $Venv "Scripts\python.exe"
$NeedNewVenv = $true
if (Test-Path $PyExe) {
  try {
    $v = & $PyExe -c "import sys;print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ($pySpec -eq "-3.$v") { $NeedNewVenv = $false }
  } catch {}
}

if ($NeedNewVenv) {
  if (Test-Path $Venv) {
    Write-Host "Removing previous venv (to switch Python version cleanly)..."
    Remove-Item -Recurse -Force $Venv
  }
  Write-Host "Creating virtualenv with Python $pySpec..."
  & py $pySpec -m venv .venv
}

$Pip = Join-Path $Venv "Scripts\pip.exe"
$Py  = $PyExe

# Deps (Playwright 1.47 has wheel support for 3.12/3.11 and Windows)
& $Py -m pip install --upgrade pip
& $Py -m pip install playwright==1.47.0
& $Py -m playwright install chromium

# Headless toggle env var consumed by the Python checker
if ($Headless) { $env:PW_HEADLESS = "1" } else { Remove-Item Env:\PW_HEADLESS -ErrorAction SilentlyContinue }

# Run the quickcheck (headed the first time so you can log in)
$Checker = Join-Path $Repo "tools\quickcheck_export_hovn.py"
& $Py $Checker
