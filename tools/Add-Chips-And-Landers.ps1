[CmdletBinding()]
param(
  [string] $Root = ".\docs",
  [switch] $DryRun,
  [switch] $GitCommit,
  [string] $CommitMessage = "Add header chips to all landers + create missing landers"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function New-FileIfMissing {
  param([string]$Path, [string]$Content)
  if (Test-Path $Path) { return $false }
  if ($DryRun) { Write-Host "[DRY] create $Path"; return $true }
  New-Item -ItemType Directory -Force -Path ([System.IO.Path]::GetDirectoryName($Path)) | Out-Null
  Set-Content -Path $Path -Encoding UTF8 -Value $Content
  Write-Host "Created: $Path"
  return $true
}

$chipsHtml = @'
<!-- audience chips -->
<nav class="chipbar" aria-label="Audience shortcuts">
  <a class="chip" href="/medical/index.html">Medical Professionals</a>
  <a class="chip" href="/workplaces/index.html">Workplaces (OSHA-Acceptable)</a>
  <a class="chip" href="/industry/index.html">Industry & Construction</a>
  <a class="chip" href="/caregivers/index.html">Child &amp; Senior Care</a>
  <a class="chip" href="/uscg/index.html">USCG / DAN (Maritime &amp; Diving)</a>
  <a class="chip" href="/parents/index.html">Parents &amp; Families</a>
</nav>
<style>
  .chipbar{display:flex;gap:.5rem;flex-wrap:wrap;margin:1rem 0}
  .chip{padding:.5rem .75rem;border-radius:999px;border:1px solid var(--border,#e5e7eb);text-decoration:none}
  @media (prefers-color-scheme: dark){
    .chip{border-color:#374151}
  }
</style>
'@

# Pages that should have chips (top-level index + any */index.html)
$targets = @(Join-Path $Root "index.html")
$targets += Get-ChildItem -Path $Root -Directory | ForEach-Object { Join-Path $_.FullName "index.html" }
$targets = $targets | Where-Object { Test-Path $_ }

# Add chips if missing
$modified = 0
foreach($file in $targets){
  $html = Get-Content $file -Raw
  if ($html -match 'class="chipbar"'){ continue }

  $injected = $false
  $t2 = $html

  if ($t2 -match '(?is)(<main[^>]*>)'){
    $t2 = [regex]::Replace($t2, '(?is)(<main[^>]*>)', ('$1' + "`r`n" + $chipsHtml), 1)
    $injected = $true
  } elseif ($t2 -match '(?is)(<header[^>]*>)'){
    $t2 = [regex]::Replace($t2, '(?is)(</header>)', ($chipsHtml + '`r`n$1'), 1)
    $injected = $true
  } elseif ($t2 -match '(?is)(<body[^>]*>)'){
    $t2 = [regex]::Replace($t2, '(?is)(<body[^>]*>)', ('$1' + "`r`n" + $chipsHtml), 1)
    $injected = $true
  } else {
    $t2 = $chipsHtml + "`r`n" + $t2
    $injected = $true
  }

  if ($injected -and $t2 -ne $html){
    if ($DryRun) { Write-Host "[DRY] chips -> $file" }
    else {
      Copy-Item $file "$file.bak" -Force
      Set-Content $file $t2 -Encoding UTF8
      Write-Host "chips injected: $file"
    }
    $modified++
  }
}

# Create missing landers (simple, standalone stubs; your GTM injector can enhance later)
$landers = @(
  @{ slug="medical";    title="Medical Professionals";    h1="BLS for Healthcare Providers"; },
  @{ slug="workplaces"; title="Workplaces (OSHA-Acceptable)"; h1="CPR/AED & First Aid for Workplaces"; },
  @{ slug="industry";   title="Industry & Construction";  h1="CPR/AED & First Aid for Industrial Sites"; },
  @{ slug="parents";    title="Parents & Families";       h1="CPR & First Aid for Parents and Families"; },
  @{ slug="uscg";       title="USCG / DAN (Maritime & Diving)"; h1="Maritime & Diving CPR / First Aid"; }
)

$tpl = @'
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{TITLE}} • 910CPR</title>
<meta name="description" content="{{DESC}}">
<link rel="stylesheet" href="/assets/site.css">
</head>
<body>
<header class="container">
  <h1 class="title">{{H1}}</h1>
  <p class="subtle">{{DESC}}</p>
</header>

<main class="container">
  <!-- chips injected here by Add-Chips-And-Landers.ps1 if not present -->
  <section class="cards">
    <a class="card" href="/bls/index.html">
      <h2>BLS Certification</h2>
      <p>For healthcare providers. AHA, ARC, or HSI options. In-person or blended.</p>
    </a>
    <a class="card" href="/firstaid/index.html">
      <h2>First Aid / CPR / AED</h2>
      <p>OSHA-acceptable training for staff and teams. Classroom or blended.</p>
    </a>
    <a class="card" href="/instructor/index.html">
      <h2>Instructor Pathways</h2>
      <p>Heartsaver, BLS, ACLS, PALS (AHA). Become an instructor.</p>
    </a>
  </section>

  <section aria-labelledby="more">
    <h2 id="more">More</h2>
    <ul>
      <li><a href="/caregivers/index.html">Child &amp; Senior Care</a></li>
      <li><a href="/parents/index.html">Parents &amp; Families</a></li>
      <li><a href="/uscg/index.html">USCG / DAN (Maritime &amp; Diving)</a></li>
    </ul>
  </section>
</main>

<footer class="container">
  <p class="subtle">© 910CPR</p>
</footer>
</body>
</html>
'@

$created = 0
foreach($l in $landers){
  $dir = Join-Path $Root $l.slug
  $path = Join-Path $dir "index.html"
  $desc = switch ($l.slug) {
    "medical"    { "American Heart Association BLS for Healthcare Providers—initial, renewal, and blended (HeartCode)." }
    "workplaces" { "OSHA-acceptable CPR/AED & First Aid training for employees, supervisors, and safety teams." }
    "industry"   { "Industrial and construction-ready CPR/AED & First Aid solutions for sites and contractors." }
    "parents"    { "CPR and First Aid courses designed for families, babysitters, and caregivers at home." }
    "uscg"       { "USCG and DAN curricula for maritime and diving environments; CPR/AED & First Aid tailored to water operations." }
    default      { "CPR/AED & First Aid training and certifications with classroom and blended options." }
  }
  $html = $tpl.Replace("{{TITLE}}",$l.title).Replace("{{H1}}",$l.h1).Replace("{{DESC}}",$desc)
  if (New-FileIfMissing -Path $path -Content $html){ $created++ }
}

Write-Host "Done. Modified $modified file(s). Created $created new lander(s)."

if ($GitCommit -and -not $DryRun){
  git add -A | Out-Null
  git commit -m $CommitMessage
  git push
}
