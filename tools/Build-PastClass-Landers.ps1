Param(
  [string]$Root = "D:\Users\ten77\Documents\GitHub\910cpr-class-landers\docs",
  [string]$EnrollwareCsv = "D:\Users\ten77\Documents\GitHub\910cpr-class-landers\data\Enrollware_Courses_with_HOVN_Matches.csv",
  [string]$HovnCoursesCsv = "D:\Users\ten77\Documents\GitHub\910cpr-class-landers\data\course-offerings (6).csv",
  [string]$CourseExportPath = "D:\Users\ten77\Documents\GitHub\910cpr-class-landers\data\course-export (26).xlsx",
  [string]$UpcomingSessionsCsv = ""
)

function Ensure-Dir($Path) {
  if (-not (Test-Path $Path)) { New-Item -Path $Path -ItemType Directory | Out-Null }
}

function Slugify([string]$text) {
  if (-not $text) { return "" }
  $s = $text -replace '[^\p{L}\p{Nd}\s\-]+',''
  $s = $s -replace '\s+','-' | ForEach-Object { $_.Trim('-') }
  return $s.ToLower()
}

function SeoDateToken([datetime]$dt) { $dt.ToString("yyyy-MM-dd_HHmm") }
function HtmlEscape($s) { if ($null -eq $s) { return "" }; return ($s -replace '&','&amp;' -replace '<','&lt;' -replace '>','&gt;' -replace '"','&quot;' -replace "'","&#39;") }

$ApprovedLocations = @(
  '325 Sound Rd','111 S Wright St','115-3 Hinton Ave','4018 Shipyard Blvd','809 Gum Branch Rd','4902 Merlot Ct'
)

function Normalize-DisplayLocation($venue, $city, $state) {
  $full = @($venue, $city, $state) -join ', '
  if ([string]::IsNullOrWhiteSpace($venue)) { return ($city, $state) -join ', ' }
  foreach ($allow in $ApprovedLocations) {
    if ($venue -like "*$allow*") { return $full }
  }
  return ($city, $state) -join ', '
}

function Render-ChipsHtml($label, $hovnLink) {
  $l = HtmlEscape($label)
  $u = HtmlEscape($hovnLink)
  @"
<div class="chips">
  <a class="chip" href="$u">All $l Sessions</a>
  <a class="chip" href="/index.html#courses">All Courses</a>
  <a class="chip" href="/past-classes.html">Past Classes</a>
  <a class="chip" href="/locations.html">Locations</a>
</div>
"@
}

function Render-FloatingPhoneHtml() {
@"
<a class="float-call" href="tel:+19103955193" aria-label="Call 910 CPR">Call 910 CPR</a>
"@
}

function Render-JsonLd($providerName, $courseName, $courseDesc, $startIso, $endIso, $displayLocation, $courseUrl, $imageUrl) {
  $json = @{
    "@context"="https://schema.org";"@type"="Course";
    "name"=$courseName;"description"=$courseDesc;
    "provider"=@{"@type"="Organization";"name"=$providerName;"url"="https://www.910cpr.com/";"telephone"="+1-910-395-5193"};
    "hasCourseInstance"=@(@{"@type"="Event";"name"="$courseName (Past Session)";"eventStatus"="https://schema.org/EventCancelled";"eventAttendanceMode"="https://schema.org/OfflineEventAttendanceMode";"startDate"=$startIso;"endDate"=$endIso;"location"=@{"@type"="Place";"name"=$displayLocation};"image"=$imageUrl;"url"=$courseUrl})
  } | ConvertTo-Json -Depth 6 -Compress
  return "<script type=""application/ld+json"">$json</script>"
}

$BaseCss = @"
:root{--bg1:#ffffff;--bg2:#eef7ff;--border:#e5e7eb;--accent:#0369a1;--accent2:#0ea5e9;}
*{box-sizing:border-box} body{margin:0;font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif;line-height:1.5;background:linear-gradient(180deg,var(--bg1),var(--bg2));color:#0f172a}
.container{max-width:1080px;margin:0 auto;padding:16px}
.banner{background:#fee2e2;border:1px solid #fecaca;padding:10px;border-radius:10px;margin:12px 0;color:#7f1d1d}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}
.chip{padding:6px 10px;border:1px solid var(--border);border-radius:999px;text-decoration:none;color:#0f172a;background:#fff}
.btn{display:inline-block;padding:10px 14px;border-radius:10px;background:var(--accent);color:#fff;text-decoration:none}
.float-call{position:fixed;right:12px;bottom:12px;padding:12px 14px;border-radius:999px;background:var(--accent2);color:#fff;text-decoration:none;font-weight:700;box-shadow:0 4px 10px rgba(0,0,0,.18)}
img.responsive{max-width:100%;height:auto;display:block}
"@

function Resolve-Image($courseLabel) {
  $byLabel="/images/"+(Slugify $courseLabel)+".jpg"
  $fallback="/images/910cpr_wave.png"
  return $byLabel,$fallback
}

$enroll = Import-Csv -Path $EnrollwareCsv
$hovnCourses = Import-Csv -Path $HovnCoursesCsv
$hovnByLabel = @{}
foreach ($c in $hovnCourses) {
  $key=($c.label ?? "").Trim()
  if ($key) { $hovnByLabel[$key]=$c }
}

$OutDir=Join-Path $Root "past"; Ensure-Dir $OutDir
$counter=0
foreach ($row in $enroll) {
  try { $start=[datetime]$row.start } catch { continue }
  $ewTitle=($row.course_title).Trim()
  $courseLabel=if ($row.hovn_match) { $row.hovn_match } else { $ewTitle }
  $city=($row.city??"").Trim(); $venue=($row.venue??"").Trim(); $state="NC"
  $displayLoc=Normalize-DisplayLocation $venue $city $state
  $hovnLink=if ($hovnByLabel.ContainsKey($courseLabel)) { $hovnByLabel[$courseLabel].link } else { "" }
  $datePretty=$start.ToString("dddd, MMMM d, yyyy h:mm tt")
  $pageTitle="$courseLabel — $datePretty — $displayLoc"
  $token=SeoDateToken $start; $fileSlug=Slugify $courseLabel; $citySlug=if ($city){Slugify $city}else{"nc"}
  $fileName="$token`_$fileSlug`_$citySlug.html"; $outPath=Join-Path $OutDir $fileName
  $img,$imgFallback=Resolve-Image $courseLabel
  $jsonLd=Render-JsonLd "910 CPR" $courseLabel "Past session record" $start.ToString("s") $start.AddHours(1).ToString("s") $displayLoc $hovnLink $img
  $chips=Render-ChipsHtml $courseLabel $hovnLink
  $floatPhone=Render-FloatingPhoneHtml
  $html=@"
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>$([HtmlEscape]$pageTitle) | 910 CPR</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>$BaseCss</style>
$jsonLd
</head>
<body>
<div class="container">
  $chips
  <div class="banner"><strong>PAST CLASS:</strong> $datePretty at $displayLoc. <a href="$hovnLink">See current $courseLabel dates</a>.</div>
  <h1>$courseLabel</h1>
  <p>$datePretty — $displayLoc</p>
  <a class="btn" href="$hovnLink">See Current Schedule</a>
  <img class="responsive" src="$img" onerror="this.src='$imgFallback';" alt="$courseLabel training in $displayLoc">
</div>
$floatPhone
</body></html>
"@
  Set-Content -LiteralPath $outPath -Value $html -Encoding UTF8
  $counter++
}
Write-Host "Done. Generated $counter past class landers in: $OutDir" -ForegroundColor Green
