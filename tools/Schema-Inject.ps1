param(
  [string]$Root = ".\docs",
  [string]$BaseUrl = "https://910cpr.com",
  [string]$PeriscopeJson = ".\docs\periscope_full.json",
  [int]$MaxInstancesPerCourse = 10,
  [switch]$Force,
  [switch]$DryRun,
  [switch]$GitCommit,
  [string]$CommitMessage = "SEO: add JSON-LD Course + Event markup"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Read-Json($path){
  if(-not (Test-Path $path)){ return @() }
  try { Get-Content $path -Raw | ConvertFrom-Json } catch { @() }
}

function Save-File($path, [string]$content, [switch]$MakeBak){
  if($DryRun){ "[DRY] write $path"; return $false }
  if($MakeBak -and (Test-Path $path)){ Copy-Item $path "$path.bak" -Force }
  $dir = Split-Path $path -Parent
  if(-not (Test-Path $dir)){ New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  Set-Content -Path $path -Encoding UTF8 -Value $content
  return $true
}

function Insert-JsonLd([string]$htmlPath, [string]$jsonText, [string]$marker, [switch]$Force){
  $html = Get-Content $htmlPath -Raw
  if(-not $Force -and $html -like "*$marker*"){ return $false } # already present (simple fast check)

  $scriptTag = "<script type=""application/ld+json"">$jsonText</script>"

  $new = $null
  if($html -match '(?is)</head>'){
    $new = [regex]::Replace($html, '(?is)</head>', ($scriptTag + "`r`n</head>"), 1)
  } elseif($html -match '(?is)</body>'){
    $new = [regex]::Replace($html, '(?is)</body>', ($scriptTag + "`r`n</body>"), 1)
  } else {
    $new = $html + "`r`n" + $scriptTag + "`r`n"
  }

  if($DryRun){ "[DRY] inject -> $htmlPath"; return $false }
  Copy-Item $htmlPath "$htmlPath.bak" -Force
  Set-Content $htmlPath -Encoding UTF8 -Value $new
  return $true
}

# ------- Load sessions (Periscope)
$sessions = Read-Json $PeriscopeJson
if(-not $sessions -or $sessions.Count -eq 0){
  Write-Host "WARN: No sessions found at $PeriscopeJson. Event/CourseInstance will be empty."
}
# Build lookup by session id (from tail of hovn url)
$byId = @{}
foreach($s in $sessions){
  try{
    if($s.url -match '/sessions/([^/?#]+)'){
      $byId[$Matches[1]] = $s
    }
  } catch {}
}

function CityToRegion($city){
  # All current locations are NC
  return "NC"
}

function Make-Place($city){
@{
  "@type" = "Place"
  "name"  = "910 CPR – $city"
  "address" = @{
    "@type" = "PostalAddress"
    "addressLocality" = $city
    "addressRegion"   = (CityToRegion $city)
    "addressCountry"  = "US"
  }
}
}

function Make-Event($s, $pageUrl){
  $city = if($s.city){ $s.city } else { "Wilmington" }
  $ev = @{
    "@context" = "https://schema.org"
    "@type"    = "Event"
    "name"     = $s.title
    "startDate"= $s.start
    "eventStatus" = "https://schema.org/EventScheduled"
    "eventAttendanceMode" = "https://schema.org/OfflineEventAttendanceMode"
    "location" = (Make-Place $city)
    "organizer" = @{
      "@type" = "Organization"
      "name"  = "910 CPR"
      "url"   = $BaseUrl
    }
    "offers" = @(@{
      "@type" = "Offer"
      "url"   = $s.url
      "availability" = "https://schema.org/InStock"
    })
    "url" = $pageUrl
  }
  return $ev
}

function CourseKeyFromTitle($t){
  if($t -match '(?i)\bACLS\b'){ return "acls" }
  if($t -match '(?i)\bPALS\b'){ return "pals" }
  if($t -match '(?i)\bBLS\b'){  return "bls"  }
  return $null
}

function CourseMeta($key){
  switch($key){
    "bls"  { @{ name="BLS Provider (AHA)"; slug="bls";  desc="American Heart Association Basic Life Support (BLS) Provider course for healthcare professionals: high-quality CPR for adults, children, and infants, AED use, team dynamics, and choking relief."; } }
    "acls" { @{ name="ACLS Provider (AHA)"; slug="acls"; desc="Advanced Cardiovascular Life Support (ACLS) for healthcare providers: recognition and management of cardiac arrest, acute coronary syndromes, stroke, and team-based resuscitation."; } }
    "pals" { @{ name="PALS Provider (AHA)"; slug="pals"; desc="Pediatric Advanced Life Support (PALS) for healthcare providers: recognition and management of pediatric respiratory and circulatory emergencies and cardiac arrest."; } }
    default { $null }
  }
}

function Make-Course($key, $pageUrl, $instances){
  $meta = CourseMeta $key
  if(-not $meta){ return $null }
  $inst = @()
  foreach($s in $instances | Select-Object -First $MaxInstancesPerCourse){
    $mode = if($s.title -match '(?i)heartcode|blended'){ "Blended" } elseif($s.title -match '(?i)renewal'){ "InPerson (Renewal)" } else { "InPerson" }
    $inst += @{
      "@type"   = "CourseInstance"
      "name"    = $s.title
      "startDate" = $s.start
      "location"  = (Make-Place ($s.city ? $s.city : "Wilmington"))
      "courseMode"= $mode
      "url"       = $s.url
    }
  }
  return @{
    "@context" = "https://schema.org"
    "@type"    = "Course"
    "name"     = $meta.name
    "description" = $meta.desc
    "provider" = @{
      "@type" = "Organization"
      "name"  = "910 CPR"
      "sameAs"= $BaseUrl
    }
    "url" = $pageUrl
    "hasCourseInstance" = $inst
  }
}

# ------- 1) Inject Event JSON-LD into each session page
$modified = 0
$sessionFiles = Get-ChildItem -Path (Join-Path $Root "classes") -Filter "session_*.html" -File -ErrorAction SilentlyContinue
foreach($f in $sessionFiles){
  $name = [IO.Path]::GetFileNameWithoutExtension($f.Name)
  $id = $null
  if($name -match '^session_([^_]+)'){ $id = $Matches[1] }
  if(-not $id -or -not $byId.ContainsKey($id)){ continue }
  $s = $byId[$id]
  $pageUrl = "$BaseUrl/classes/$($f.Name)"
  $ev = Make-Event $s $pageUrl
  $json = ($ev | ConvertTo-Json -Depth 10 -Compress)
  if(Insert-JsonLd -htmlPath $f.FullName -jsonText $json -marker '"@type":"Event"' -Force:$Force){
    "Event JSON-LD -> $($f.FullName)"
    $modified++
  }
}

# ------- 2) Inject Course JSON-LD into BLS/ACLS/PALS landers
$courseKeys = @("bls","acls","pals")
foreach($key in $courseKeys){
  $meta = CourseMeta $key
  if(-not $meta){ continue }
  $lander = Join-Path $Root "$($meta.slug)\index.html"
  if(-not (Test-Path $lander)){ continue }
  $pageUrl = "$BaseUrl/$($meta.slug)/"
  $courseSessions = @()
  foreach($s in $sessions){
    $ck = CourseKeyFromTitle ($s.title)
    if($ck -eq $key){ $courseSessions += $s }
  }
  $course = Make-Course $key $pageUrl $courseSessions
  if($course){
    $json = ($course | ConvertTo-Json -Depth 12 -Compress)
    if(Insert-JsonLd -htmlPath $lander -jsonText $json -marker '"@type":"Course"' -Force:$Force){
      "Course JSON-LD ($key) -> $lander"
      $modified++
    }
  }
}

# ------- 3) Organization JSON-LD on homepage (once)
$home = Join-Path $Root "index.html"
if(Test-Path $home){
  $org = @{
    "@context"="https://schema.org"
    "@type"="Organization"
    "name"="910 CPR"
    "url"=$BaseUrl
    "logo"="$BaseUrl/assets/og-card.png"
    "sameAs"=@()
  }
  $orgJson = ($org | ConvertTo-Json -Depth 10 -Compress)
  if(Insert-JsonLd -htmlPath $home -jsonText $orgJson -marker '"@type":"Organization"' -Force:$Force){
    "Organization JSON-LD -> $home"
    $modified++
  }
}

if($modified -gt 0){
  "Done. Modified $modified file(s)."
} else {
  "No changes (existing JSON-LD present or no matching pages)."
}

if($GitCommit -and -not $DryRun -and $modified -gt 0){
  git add -A
  git commit -m $CommitMessage
  git push
}
