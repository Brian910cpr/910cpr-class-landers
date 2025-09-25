param(
  [string]$Root = ".\docs",
  [switch]$DryRun,
  [switch]$GitCommit,
  [string]$CommitMessage = "Normalize headers (chipbar kept, unified hero H1)"
)

$ErrorActionPreference = "Stop"

function Get-H1Text {
  param([string]$html)
  if($html -match '(?is)<h1[^>]*>(.*?)</h1>'){
    return (($matches[1] -replace '<[^>]+>','') -replace '\s+',' ').Trim()
  }
  if($html -match '(?is)<title[^>]*>(.*?)</title>'){
    return (($matches[1] -replace '\s+',' ') -replace '<[^>]+>','').Trim()
  }
  return "CPR, First Aid & BLS"
}

function Normalize-File {
  param([string]$filePath)

  $orig = Get-Content $filePath -Raw
  $html = $orig

  # split at <body>
  if($html -notmatch '(?is)<body[^>]*>'){
    return $false
  }
  $bodyStart = $matches[0]
  $preBody   = $html.Substring(0, $matches.Index + $matches.Length)
  $bodyRest  = $html.Substring($matches.Index + $matches.Length)

  # find first <main> or <section> to separate header-ish area
  $preEndIdx = $null
  foreach($tag in @('<main','<section')){
    $i = $bodyRest.IndexOf($tag, [StringComparison]::OrdinalIgnoreCase)
    if($i -ge 0){ $preEndIdx = $i; break }
  }
  if($null -eq $preEndIdx){ $preEndIdx = $bodyRest.Length }

  $pre  = $bodyRest.Substring(0,$preEndIdx)
  $rest = $bodyRest.Substring($preEndIdx)

  $h1 = Get-H1Text $html

  # remove any existing H1s in the header region
  $preNoH1 = [regex]::Replace($pre,'(?is)<h1\b[^>]*>.*?</h1>','')

  # build a single uniform hero block (keeps chipbar if it’s already there)
  $hero = @"
<header class="site-hero">
  <div class="container hero-container">
    <h1 class="page-title">$h1</h1>
  </div>
</header>
"@

  # try to inject hero right AFTER chipbar if present; else prepend to pre
  $injected = $false
  $chipIdx  = $preNoH1.IndexOf('chipbar', [StringComparison]::OrdinalIgnoreCase)
  if($chipIdx -ge 0){
    # drop hero after the closing tag that contains chipbar (best-effort)
    $navClose = $preNoH1.IndexOf('</nav>', $chipIdx, [StringComparison]::OrdinalIgnoreCase)
    if($navClose -ge 0){
      $navClose += 6
      $preNorm = $preNoH1.Insert($navClose, "`r`n$hero`r`n")
      $injected = $true
    }
  }
  if(-not $injected){
    $preNorm = $hero + "`r`n" + $preNoH1
  }

  # ensure there is a <main> wrapper; if not, wrap $rest
  if($rest -notmatch '(?is)<main\b'){
    $rest = "<main>`r`n$rest`r`n</main>"
  }

  # put it back together
  $new = $preBody + $preNorm + $rest

  if($new -ne $orig){
    if($DryRun){
      "Would normalize: $filePath"
      return $true
    } else {
      if(-not (Test-Path "$filePath.bak")){ Set-Content "$filePath.bak" $orig -Encoding UTF8 }
      Set-Content $filePath $new -Encoding UTF8
      "Normalized: $filePath"
      return $true
    }
  }
  return $false
}

$files = Get-ChildItem $Root -Recurse -Filter index.html |
  Where-Object { $_.FullName -notmatch '\.bak$' }

$changed = 0
foreach($f in $files){ if(Normalize-File $f.FullName){ $changed++ } }

"Done. Modified $changed file(s)."

if($GitCommit -and -not $DryRun -and $changed -gt 0){
  git add -A
  git commit -m $CommitMessage
  git push
}
