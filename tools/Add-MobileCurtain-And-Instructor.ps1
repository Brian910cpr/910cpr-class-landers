[CmdletBinding()]
param(
  [string]$Root = ".\docs",
  [switch]$DryRun,
  [switch]$GitCommit,
  [string]$CommitMessage = "UX: mobile curtain + AHA instructor row + assets injection (fixed regex)"
)

function Write-Change([string]$msg){ Write-Host $msg }

$cssPath = Join-Path $Root "assets\ux.css"
$jsPath  = Join-Path $Root "assets\ux.js"

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

# ensure assets
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

# helpers
function Get-Rel([string]$fromDir, [string]$toPath){
  # Compute a relative path WITHOUT requiring the target to exist
  $fromFull = [IO.Path]::GetFullPath($fromDir)
  $toFull = $toPath
  try { $toFull = [IO.Path]::GetFullPath($toPath) } catch { }
  try {
    return [IO.Path]::GetRelativePath($fromFull, $toFull).Replace('\','/')
  } catch {
    if($toFull.StartsWith($fromFull, [StringComparison]::OrdinalIgnoreCase)){
      return $toFull.Substring($fromFull.Length).TrimStart('\','/').Replace('\','/')
    }
    return $toPath.Replace('\','/')
  }
}

function Inject-Assets([string]$filePath, [string]$html){
  $dir     = Split-Path -Parent $filePath
  $cssRel  = Get-Rel $dir (Join-Path $Root 'assets\ux.css')
  $jsRel   = Get-Rel $dir (Join-Path $Root 'assets\ux.js')
  if($html -match '(?is)assets/ux\.css' -and $html -match '(?is)assets/ux\.js'){ return $html }
  $headInsert = "`r`n<link rel=""stylesheet"" href=""$cssRel"">`r`n<script defer src=""$jsRel""></script>`r`n"
  if($html -match '(?is)</head>'){
    $html = $html -replace '(?is)</head>', ($headInsert + '</head>')
  } else {
    $html = $headInsert + $html
  }
  return $html
}

function Mark-Home-Collapsible([string]$relPath, [string]$html){
  # homepage only (docs/index.html)
  if($relPath -ne 'index.html'){ return $html }
  if($html -match 'data-collapsible="1"'){ return $html }
  $pattern = '(?is)<(div|article|section|figure)([^>]*\bclass="[^"]*\bcard\b[^"]*"[^>]*)>'
  $replacement = '<$1$2 data-collapsible="1">'
  return ($html -replace $pattern, $replacement)
}

function Add-Instructor-Block([string]$relPath, [string]$html){
  # only HSI lander
  if($relPath -ne 'hsi/index.html'){ return $html }
  if($html -match 'id="instructor-cards"'){ return $html }
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

# process files
$rootFull = [IO.Path]::GetFullPath($Root)
$indexes = Get-ChildItem $Root -Recurse -Filter index.html -File | Sort-Object FullName
$modified = @()

foreach($f in $indexes){
  $html0 = Get-Content $f.FullName -Raw
  $fileFull = [IO.Path]::GetFullPath($f.FullName)
  $rel = [IO.Path]::GetRelativePath($rootFull, $fileFull).Replace('\','/').ToLowerInvariant()

  $html1 = Inject-Assets $f.FullName $html0
  $html1 = Mark-Home-Collapsible $rel $html1
  $html1 = Add-Instructor-Block $rel $html1

  if($html1 -ne $html0){
    if($DryRun){
      Write-Change ("[DRY] Enhanced: " + $f.FullName)
    } else {
      $bak = "$($f.FullName).bak"
      if(-not (Test-Path $bak)){ Set-Content $bak $html0 -Encoding UTF8 }
      Set-Content $f.FullName $html1 -Encoding UTF8
      Write-Change ("Enhanced: " + $f.FullName)
      $modified += $f.FullName
    }
  }
}

if(-not $DryRun){
  Write-Host ("Done. Modified {0} file(s)." -f $modified.Count)
  if($GitCommit){
    git add -A
    git commit -m $CommitMessage
    git push
  }
} else {
  Write-Host "Preview complete. No files written."
}
