param(
  [Parameter(Mandatory=$true)]
  [string]$RepoRoot
)

$RepoRoot = (Resolve-Path $RepoRoot).Path
if (-not (Test-Path $RepoRoot)) { throw "Repo root not found: $RepoRoot" }

function Ensure-Dir($path) {
  if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path -Force | Out-Null }
}

$dirs = @(
  "data","data\seo","docs","docs\courses",
  "docs\images","docs\sessions","scripts"
)
foreach ($d in $dirs) { Ensure-Dir (Join-Path $RepoRoot $d) }

$gitkeepTargets = @(
  "data\seo\.gitkeep",
  "docs\courses\.gitkeep",
  "docs\images\.gitkeep",
  "docs\sessions\.gitkeep"
)
foreach ($gk in $gitkeepTargets) {
  $full = Join-Path $RepoRoot $gk
  if (-not (Test-Path $full)) { New-Item -ItemType File -Path $full -Force | Out-Null }
}

$seedFiles = @{
  "data\sessions.csv"  = "session_id,course_id,title,start_datetime,end_datetime,city,state,location_name,enroll_url,status`r`n"
  "data\courses.csv"   = "course_id,course_slug,course_name,provider,price,duration_minutes,image_relpath,description_html_file`r`n"
  "data\locations.csv" = "city,state,county,region_type,display_name`r`n"
}
foreach ($kvp in $seedFiles.GetEnumerator()) {
  $full = Join-Path $RepoRoot $kvp.Key
  if (-not (Test-Path $full)) { Set-Content -Path $full -Value $kvp.Value -Encoding UTF8 }
}

$indexPath = Join-Path $RepoRoot "docs\index.html"
if (-not (Test-Path $indexPath)) {
@"
<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <title>910CPR — Classes</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <style>
    body{font-family:system-ui,Arial,sans-serif;margin:0;
      background:linear-gradient(180deg,#fff,#eef6ff);}
    header{padding:28px 16px;}
    h1{margin:0 0 8px;}
    .wrap{max-width:1080px;margin:0 auto;padding:0 16px 32px;}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;}
    a.card{display:block;padding:14px;border-radius:16px;background:#fff;
      box-shadow:0 6px 24px rgba(0,0,0,0.06);text-decoration:none;color:#111;}
    a.card:hover{box-shadow:0 10px 28px rgba(0,0,0,0.09);}
    small{color:#4a5568;}
  </style>
</head>
<body>
<header class='wrap'>
  <h1>910CPR Classes</h1>
  <p>Live schedule powered by HOVN.</p>
  <p><a href='https://www.hovn.app/910cpr/schedule'>
     https://www.hovn.app/910cpr/schedule</a></p>
</header>
<main class='wrap'>
  <div class='grid'>
    <a class='card' href='/courses/aha-bls-provider/'><strong>BLS Provider</strong><br><small>Healthcare professionals</small></a>
    <a class='card' href='/courses/aha-acls-provider/'><strong>ACLS</strong><br><small>Advanced hospital providers</small></a>
    <a class='card' href='/courses/aha-pals-provider/'><strong>PALS</strong><br><small>Pediatric focus</small></a>
    <a class='card' href='/courses/aha-heartsaver-first-aid-cpr-aed/'><strong>Heartsaver FA/CPR/AED</strong><br><small>Workplace & community</small></a>
  </div>
</main>
</body>
</html>
"@ | Set-Content -Path $indexPath -Encoding UTF8
}

Write-Host "Skeleton ensured under: $RepoRoot"
