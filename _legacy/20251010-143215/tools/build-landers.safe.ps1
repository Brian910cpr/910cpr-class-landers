<# tools/Build-Landers.Safe.ps1 #>
[CmdletBinding()]
param(
  [string] $Root = ".\docs",
  [string] $GTM  = "GTM-K58Z4XD",
  [switch] $DryRun,
  [int] $MaxFiles = 5000,
  [switch] $GitCommit,
  [string] $CommitMessage = "Safe build: GTM inject + instructor lander"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# initialize re-entry flag under StrictMode
if (-not (Get-Variable -Name __BUILD_RUNNING -Scope Script -ErrorAction SilentlyContinue)) { $script:__BUILD_RUNNING = $false }
if ($script:__BUILD_RUNNING) { Write-Error "Build already running (re-entry guard)."; exit 1 }
$script:__BUILD_RUNNING = $true


function Get-TargetHtml {
  param([string]$Base)
  Get-ChildItem -Path $Base -Recurse -File -Include *.html -ErrorAction SilentlyContinue |
    Where-Object {
      # Avoid typical recursion traps / huge dirs
      $_.FullName -notmatch '\\(node_modules|\.git|dist)\\'
    } |
    Select-Object -First $MaxFiles
}

function Inject-GTM {
  param([string]$Path, [string]$GtmId)

  $t = Get-Content $Path -Raw -ErrorAction Stop

  # Already has GTM? bail.
  if ($t -match [regex]::Escape($GtmId) -or $t -match 'googletagmanager\.com/gtm\.js') {
    return $false
  }

  $headSnippet = @"
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});
var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;
j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);})
(window,document,'script','dataLayer','$GtmId');</script>
<!-- End Google Tag Manager -->
"@

  $bodySnippet = @"
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=$GtmId"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
"@

  $out = $t

  # Insert into <head> (once), safely before </head>
  if ($out -match '(?is)</head>') {
    $out = [regex]::Replace($out, '(?is)</head>', ($headSnippet + "`r`n</head>"), 1)
  } else {
    # Fallback: prepend to file
    $out = $headSnippet + "`r`n" + $out
  }

  # Insert noscript right after <body...>
  if ($out -match '(?is)<body[^>]*>') {
    $out = [regex]::Replace($out, '(?is)(<body[^>]*>)', ('$1' + "`r`n" + $bodySnippet), 1)
  } else {
    $out = $out + "`r`n" + $bodySnippet
  }

  if ($DryRun) {
    Write-Host "[DRY] GTM -> $Path"
    return $true
  } else {
    Set-Content -Path $Path -Value $out -Encoding UTF8
    Write-Host "GTM injected: $Path"
    return $true
  }
}

function Ensure-InstructorLander {
  param([string]$Base)
  $dir = Join-Path $Base 'instructor'
  $idx = Join-Path $dir 'index.html'
  if (-not (Test-Path $idx)) {
@"
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Instructor Programs — AHA Heartsaver, BLS, ACLS, PALS</title>
<link rel="stylesheet" href="../assets/lander.css" />
</head>
<body>
<header class="site-header">
  <nav class="chips">
    <a href="../medical/index.html">Medical Professionals</a>
    <a href="../workplaces/index.html">Workplaces</a>
    <a href="../industry/index.html">Industry & Construction</a>
    <a href="../caregivers/index.html">Child & Senior Care</a>
    <a href="../uscg-dan/index.html">USCG / DAN</a>
    <a href="../parents/index.html">Parents & Families</a>
  </nav>
</header>

<main class="container">
  <h1>Instructor Certification Programs</h1>
  <p>Become an instructor: Heartsaver, BLS, ACLS, PALS. This page aggregates prerequisites, alignment, monitoring, and how to schedule your instructor course day.</p>

  <section class="grid">
    <a class="card" href="#aha-instructor">AHA Instructor Pathway</a>
    <a class="card" href="#heartsaver">Heartsaver Instructor</a>
    <a class="card" href="#bls">BLS Instructor</a>
    <a class="card" href="#acls">ACLS Instructor</a>
    <a class="card" href="#pals">PALS Instructor</a>
  </section>

  <article id="aha-instructor">
    <h2>AHA Instructor Pathway</h2>
    <ol>
      <li>Hold current provider certification.</li>
      <li>Complete AHA Instructor Essentials online module.</li>
      <li>Attend an instructor course with us.</li>
      <li>Complete monitoring to finalize status.</li>
    </ol>
    <p>Questions? Email <a href="mailto:info@910cpr.com">info@910cpr.com</a>.</p>
  </article>
</main>

<footer class="site-footer">
  <p>&copy; 910 CPR</p>
</footer>
</body>
</html>
"@ | ForEach-Object {
      if ($DryRun) {
        Write-Host "[DRY] create $idx"
      } else {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Set-Content -Path $idx -Value $_ -Encoding UTF8
        Write-Host "Created: $idx"
      }
    }
  }
}

try {
  # 1) Guard: resolve and validate root
  $Root = (Resolve-Path $Root).Path
  Write-Host "Root: $Root"

  # 2) Instructor lander scaffold (once)
  Ensure-InstructorLander -Base $Root

  # 3) GTM injection (bounded set)
  $files = Get-TargetHtml -Base $Root
  Write-Host ("Scanning {0} HTML files (max {1})..." -f $files.Count, $MaxFiles)

  $changed = 0
  foreach ($f in $files) {
    $ok = Inject-GTM -Path $f.FullName -GtmId $GTM
    if ($ok) { $changed++ }
  }

  Write-Host ("Done. Modified {0} file(s)." -f $changed)

  if ($GitCommit -and -not $DryRun -and $changed -gt 0) {
    git add --all $Root
    git commit -m $CommitMessage
    git push
  }
}
finally {
  $script:__BUILD_RUNNING = $false
}
