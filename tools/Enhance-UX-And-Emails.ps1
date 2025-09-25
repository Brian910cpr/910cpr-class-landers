param(
  [string]$Root = ".\docs",
  [string]$HovnBase = "https://www.hovn.app/service-providers/910cpr/sessions",
  [string]$Domain   = "910cpr.com",
  [switch]$DryRun,
  [switch]$GitCommit,
  [string]$CommitMessage = "UX: add 'View more dates' controls + page-specific info+ email aliases"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function New-Dir([string]$p){
  if(-not (Test-Path $p)){ New-Item -ItemType Directory -Path $p | Out-Null }
}

function Get-Rel([string]$path, [string]$base){
  $full = (Resolve-Path $path).Path
  $b    = (Resolve-Path $base).Path
  return [IO.Path]::GetRelativePath($b, $full)
}

function Get-PageSlug([string]$filePath, [string]$root){
  $rel = Get-Rel $filePath $root
  $dir = Split-Path $rel -Parent
  $name = Split-Path $rel -Leaf
  $stem = [IO.Path]::GetFileNameWithoutExtension($name)

  if ($stem -ieq 'index') {
    if ([string]::IsNullOrWhiteSpace($dir) -or $dir -eq '.') { $slug = 'home' }
    else { $slug = (Split-Path $dir -Leaf) }
  } else {
    # e.g. classes/session_xxx.html -> classes-session_xxx
    $parent = [string]::IsNullOrWhiteSpace($dir) ? '' : ((Split-Path $dir -Leaf) + '-')
    $slug = $parent + $stem
  }

  # sanitize
  $slug = $slug -replace '[^a-zA-Z0-9]+','-'
  $slug = $slug.Trim('-').ToLowerInvariant()
  if([string]::IsNullOrWhiteSpace($slug)){ $slug = 'page' }
  return $slug
}

function Ensure-Assets([string]$root, [string]$hovnBase){
  $assets = Join-Path $root "assets"
  New-Dir $assets
  $cssPath = Join-Path $assets "ux.css"
  $jsPath  = Join-Path $assets "ux.js"

  $cssBlock = @"
/* BEGIN HOVN_VIEW_MORE_CSS */
.card .card-controls{display:flex;gap:.5rem;margin-top:.75rem;flex-wrap:wrap}
.card .card-controls .view-more,
.card .card-controls .close-card{padding:.5rem .75rem;border-radius:.5rem;text-decoration:none;border:1px solid currentColor;background:transparent;cursor:pointer;font:inherit}
.card .card-controls .view-more{display:inline-block}
@media (min-width:769px){.card .card-controls{display:none}}
/* END HOVN_VIEW_MORE_CSS */
"@

  $jsBlock = @"
// BEGIN HOVN_VIEW_MORE
(function(){
  window.HOVN_BASE = window.HOVN_BASE || '$hovnBase';
  function init(){
    var cards = document.querySelectorAll('.card[data-collapsible="1"]');
    cards.forEach(function(card){
      if(card.dataset.controlsInit === '1') return;
      card.dataset.controlsInit = '1';

      var hovn = card.getAttribute('data-hovn') || window.HOVN_BASE;

      var container = document.createElement('div');
      container.className = 'card-controls';

      var more = document.createElement('a');
      more.className = 'view-more';
      more.target = '_blank';
      more.rel = 'noopener';
      more.href = hovn;
      more.textContent = 'View more dates';

      var close = document.createElement('button');
      close.className = 'close-card';
      close.type = 'button';
      close.textContent = 'Close';

      close.addEventListener('click', function(){
        card.classList.remove('open');
      });

      container.appendChild(more);
      container.appendChild(close);

      var body = card.querySelector('.card-body') || card;
      body.appendChild(container);
    });
  }
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
// END HOVN_VIEW_MORE
"@

  if(Test-Path $cssPath){
    $css = Get-Content $cssPath -Raw
    if($css -notmatch 'BEGIN HOVN_VIEW_MORE_CSS'){
      if($script:DRY){ "[DRY] append CSS block -> $cssPath" } else {
        Add-Content -Path $cssPath -Value "`r`n$cssBlock"
        "Appended CSS block -> $cssPath"
      }
    }
  } else {
    if($script:DRY){ "[DRY] write $cssPath" } else {
      Set-Content -Path $cssPath -Encoding UTF8 -Value $cssBlock
      "Wrote $cssPath"
    }
  }

  if(Test-Path $jsPath){
    $js = Get-Content $jsPath -Raw
    if($js -notmatch 'BEGIN HOVN_VIEW_MORE'){
      if($script:DRY){ "[DRY] append JS block -> $jsPath" } else {
        Add-Content -Path $jsPath -Value "`r`n$jsBlock"
        "Appended JS block -> $jsPath"
      }
    }
  } else {
    if($script:DRY){ "[DRY] write $jsPath" } else {
      Set-Content -Path $jsPath -Encoding UTF8 -Value $jsBlock
      "Wrote $jsPath"
    }
  }
}

function Update-Emails-InFile([string]$filePath, [string]$domain, [string]$slug){
  $html = Get-Content $filePath -Raw
  $orig = $html

  $domEsc = [regex]::Escape($domain)
  $alias  = "info+$slug@$domain"

  # mailto: keep any query string (e.g., ?subject=)
  $mailtoPattern = "(?i)mailto:[\w\.\+\-]+@" + $domEsc + "(?<qs>\?[^\s""'>]*)?"
  $html = [regex]::Replace($html, $mailtoPattern, {
      param($m)
      "mailto:$alias" + $m.Groups['qs'].Value
  })

  # bare emails on page (only our domain)
  $emailPattern = "(?i)(?<![\w\.\+\-])[\w\.\+\-]+@" + $domEsc
  $html = [regex]::Replace($html, $emailPattern, $alias)

  if($html -ne $orig){
    if($script:DRY){
      "[DRY] emails -> $filePath  (alias: $alias)"
    } else {
      Copy-Item $filePath "$filePath.bak" -Force
      Set-Content $filePath $html -Encoding UTF8
      "emails updated: $filePath  (alias: $alias)"
      return $true
    }
  }
  return $false
}

# ---- main ----
$script:DRY = [bool]$DryRun
$rootFull = (Resolve-Path $Root).Path
"Root: $rootFull"

# 1) Ensure assets + JS controls
Ensure-Assets -root $rootFull -hovnBase $HovnBase | % { $_ | Out-Host }

# 2) Email rewrites
$changed = 0
$files = Get-ChildItem $rootFull -Recurse -Include *.html -File |
  Where-Object { $_.FullName -notmatch '\\(node_modules|\.git|dist|vendor)\\' }

foreach($f in $files){
  $slug = Get-PageSlug $f.FullName $rootFull
  if(Update-Emails-InFile -filePath $f.FullName -domain $Domain -slug $slug){
    $changed++
  }
}

"Done. Modified $changed file(s)."

if($GitCommit -and -not $DryRun -and $changed -ge 0){
  git add -A
  if([string]::IsNullOrWhiteSpace($CommitMessage)){ $CommitMessage = "Enhance UX + email aliasing" }
  git commit -m $CommitMessage | Out-Host
  git push | Out-Host
}
