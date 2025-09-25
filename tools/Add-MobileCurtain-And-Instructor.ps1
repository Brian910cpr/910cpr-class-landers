[CmdletBinding()]
param(
  [string]$Root = ".\docs",
  [switch]$DryRun,
  [switch]$GitCommit,
  [string]$CommitMessage = "UX: mobile curtain + AHA instructor row + assets injection (fixed)"
)

function Write-Change([string]$msg){ Write-Host $msg }

# --- asset targets ---
$cssPath = Join-Path $Root "assets\ux.css"
$jsPath  = Join-Path $Root "assets\ux.js"

# --- asset contents (double-quoted here-strings so they don't collide with outer writers) ---
$cssContent = @"
/* --- UX curtain / collapsible cards (mobile-first) --- */
.card[data-collapsible="1"] { overflow: hidden; transition: max-height .25s ease; }
.card[data-collapsible="1"] .card-details { display: block; }
.card[data-collapsible="1"]:not(.open) .card-details { display: none; }

@media (max-width: 768px) {
  .card[data-collapsible="1"] { border-radius: 12px; }
  .card[data-collapsible="1"] .card-header { cursor: pointer; }
}
"@

$jsContent = @"
(function(){
  function ready(fn){ if(document.readyState!="loading"){ fn(); } else { document.addEventListener("DOMContentLoaded",fn); } }
  ready(function(){
    // Collapsible behavior
    var cards = document.querySelectorAll("[data-collapsible='1']");
    cards.forEach(function(card){
      if(card.classList.contains("collapsible-ready")) return;
      card.classList.add("collapsible-ready");

      var header = card.querySelector(".card-header, h2, h3, .title") || card;
      if(header){ header.style.cursor="pointer"; header.addEventListener("click", function(){ card.classList.toggle("open"); }); }

      // default state: open on desktop, closed on mobile
      if (window.matchMedia("(max-width: 768px)").matches) { card.classList.remove("open"); }
      else { card.classList.add("open"); }
    });
  });
})();
"@

Write-Host "Root: $(Resolve-Path $Root)"

# --- ensure assets directory / files ---
$assetsDir = Join-Path $Root "assets"
if($DryRun){
  if(-not (Test-Path $cssPath)){ Write-Change "[DRY] write $cssPath" }
  if(-not (Test-Path $jsPath)){  Write-Change "[DRY] write $jsPath" }
}else{
  New-Item -ItemType Directory -Path $assetsDir -Force | Out-Null
  if( -not (Test-Path $cssPath) -or (Get-Content $cssPath -Raw) -ne $cssContent ){
    Set-Content $cssPath $cssContent -Encoding UTF8
    Write-Change "Wrote $cssPath"
  }
  if( -not (Test-Path $jsPath) -or (Get-Content $jsPath -Raw) -ne $jsContent ){
    Set-Content $jsPath $jsContent -Encoding UTF8
    Write-Change "Wrote $jsPath"
  }
}

# --- gather lander index pages ---
$indexes = Get-ChildItem $Root -Recurse -Filter index.html -File | Sort-Object FullName

# robust relative path helper (works on pwsh 7+; falls back for Windows PowerShell)
function Get-Rel([string]$fromDir, [string]$toPath){
  try {
    return [IO.Path]::GetRelativePath($fromDir, $toPath).Replace('\','/')
  } catch {
    $uriFrom = New-Object System.Uri((Resolve-Path $fromDir))
    $uriTo   = New-Object System.Uri((Resolve-Path $toPath))
    return $uriFrom.MakeRelativeUri($uriTo).ToString()
  }
}

# helper: inject <link> and <script> once
function Inject-Assets([string]$filePath, [string]$html){
  $dir     = Split-Path -Parent $filePath
  $cssRel  = Get-Rel $dir (Join-Path $Root 'assets\ux.css')
  $jsRel   = Get-Rel $dir (Join-Path $Root 'assets\ux.js')

  if($html -match '(?is)assets/ux\.css' -and $html -match '(?is)assets/ux\.js'){ return $html } # already linked

  $headInsert = "`r`n<link rel=""stylesheet"" href=""$cssRel"">`r`n<script defer src=""$jsRel""></script>`r`n"
  if($html -match '(?is)</head>'){
    # safe single -replace
    $html = $html -replace '(?is)</head>', ($headInsert + '</head>')
  } else {
    $html = $headInsert + $html
  }
  return $html
}

# helper: mark homepage cards collapsible (only once)
function Mark-Home-Collapsible([string]$filePath, [string]$html){
  if($filePath -notmatch '[\\/]\Qdocs\E[\\/]index\.html$'){ return $html } # homepage only
  if($html -match 'data-collapsible="1"'){ return $html }                  # already marked
  # Add data-collapsible="1" to any element whose class contains 'card'
  $pattern = '(?is)<(div|article|section|figure)([^>]*\bclass="[^"]*\bcard\b[^"]*"[^>]*)>'
  $replacement = '<$1$2 data-collapsible="1">'
  return ($html -replace $pattern, $replacement)
}

# helper: append AHA Instructor card block to HSI lander (once)
function Add-Instructor-Block([string]$filePath, [string]$html){
  # only for HSI lander
  if($filePath -notmatch '[\\/]\Qdocs\E[\\/]hsi[\\/]index\.html$'){ return $html }
  if($html -match 'id="instructor-cards"'){ return $html } # already present

  $block = @"
<section id="instructor-cards" class="section wide">
  <h2 class="title">Become an AHA Instructor</h2>
  <div class="grid">
    <a class="card" href="/instructor/index.html#heartsaver">
      <div class="card-header"><h3>Heartsaver Instructor</h3></div>
      <div class="card-details">
        <p>Teach CPR, AED, and First Aid (AHA Heartsaver). Train workplaces and the public.</p>
      </div>
    </a>
    <a class="card" href="/instructor/index.html#bls">
      <div class="card-header"><h3>BLS Instructor</h3></div>
      <div class="card-details">
        <p>Train healthcare providers in Basic Life Support skills and team-based resuscitation.</p>
      </div>
    </a>
    <a class="card" href="/instructor/index.html#acls">
      <div class="card-header"><h3>ACLS Instructor</h3></div>
      <div class="card-details">
        <p>Teach adult cardiac arrest & peri-arrest management for advanced providers.</p>
      </div>
    </a>
    <a class="card" href="/instructor/index.html#pals">
      <div class="card-header"><h3>PALS Instructor</h3></div>
      <div class="card-details">
        <p>Teach pediatric resuscitation to providers in emergency and acute care settings.</p>
      </div>
    </a>
  </div>
</section>
"@

  if($html -match '(?is)</main>'){
    $html = $html -replace '(?is)</main>', ("  $block`r`n</main>")
  } else {
    $html = $html + "`r`n" + $block
  }
  return $html
}

$modified = @()
foreach($f in $indexes){
  $html0 = Get-Content $f.FullName -Raw

  $html1 = Inject-Assets $f.FullName $html0
  $html1 = Mark-Home-Collapsible $f.FullName $html1
  $html1 = Add-Instructor-Block $f.FullName $html1

  if($html1 -ne $html0){
    if($DryRun){
      Write-Change ("[DRY] Enhanced: " + $f.FullName)
    } else {
      # backup once per run if not already created this run
      $bak = "$($f.FullName).bak"
      if(-not (Test-Path $bak)){ Set-Content $bak $html0 -Encoding UTF8 }
      Set-Content $f.FullName $html1 -Encoding UTF8
      Write-Change ("Enhanced: " + $f.FullName)
      $modified += $f.FullName
    }
  }
}

if(-not $DryRun){
  if($modified.Count -eq 0){ Write-Host "Done. Modified 0 file(s)." }
  else                     { Write-Host ("Done. Modified {0} file(s)." -f $modified.Count) }
  if($GitCommit){
    git add -A
    git commit -m $CommitMessage
    git push
  }
} else {
  Write-Host "Preview complete. No files written."
}
