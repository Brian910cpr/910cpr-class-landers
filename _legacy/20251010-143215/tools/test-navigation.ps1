param(
  [string]$Root = ".\docs",
  [string]$OutDir = ".\nav-report"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ----- Helpers -----
function Resolve-InternalLink {
  param([string]$SourceFile, [string]$Href, [string]$Root)

  if($Href -match '^(?i)(mailto:|tel:|https?://|javascript:|#)'){ return $null }

  if($Href.StartsWith('/')){
    $rel = $Href.TrimStart('/').Replace('/',[IO.Path]::DirectorySeparatorChar)
    return (Join-Path (Resolve-Path $Root) $rel)
  } else {
    return (Join-Path (Split-Path -Parent $SourceFile) $Href)
  }
}

# Terms that SHOULD be links (per your spec) -> target landers
$TermMap = [ordered]@{
  'BLS'                    = '/bls/index.html'
  'ACLS'                   = '/acls/index.html'
  'PALS'                   = '/pals/index.html'
  'Heartsaver'             = '/hsi/index.html'
  'Medical Professionals'  = '/medical/index.html'
  'Workplaces'             = '/workplaces/index.html'
  'Industry'               = '/industry/index.html'
  'Caregivers'             = '/caregivers/index.html'
  'Parents'                = '/parents/index.html'
  'USCG'                   = '/uscg/index.html'
  'DAN'                    = '/uscg/index.html'
  'Instructor'             = '/instructor/index.html'
}

# ----- Scan -----
$files = Get-ChildItem $Root -Recurse -Include *.html -File
$links     = New-Object System.Collections.Generic.List[object]
$problems  = New-Object System.Collections.Generic.List[object]
$termsMiss = New-Object System.Collections.Generic.List[object]
$incoming  = @{} # resolvedTargetPath -> [list of sources]
$hovnSeen  = @{} # source -> bool
$trapPages = New-Object System.Collections.Generic.HashSet[string]
$mailIssues= New-Object System.Collections.Generic.List[object]

$reHref = '<a\s+[^>]*?href\s*=\s*["'']([^"''>]+)["'']' # basic & safe
$reAOpen= '<a\b[^>]*>'
$reAClose='</a>'

foreach($f in $files){
  $html = Get-Content $f.FullName -Raw

  # Page has any direct path to HOVN?
  $hovnSeen[$f.FullName] = [regex]::IsMatch($html, 'https?://(www\.)?hovn\.app', 'IgnoreCase')

  # Extract links
  $ms = [regex]::Matches($html, $reHref, 'IgnoreCase')
  $hasSessionsLink = $false
  $hasExternalHovn = $false

  foreach($m in $ms){
    $href = $m.Groups[1].Value.Trim()
    $type = 'internal'
    $exists = $null
    $resolved = $null

    if($href -match '^(?i)mailto:'){ $type='mailto' }
    elseif($href -match '^(?i)tel:'){ $type='tel' }
    elseif($href -match '^(?i)https?://'){ $type='external' }
    elseif($href -match '^(?i)javascript:'){ $type='javascript' }
    elseif($href -match '^(?i)#'){ $type='fragment' }

    if($type -eq 'internal'){
      $resolved = Resolve-InternalLink -SourceFile $f.FullName -Href $href -Root $Root
      if($resolved){
        $exists = Test-Path $resolved
        if($exists){
          if(-not $incoming.ContainsKey($resolved)){ $incoming[$resolved] = New-Object System.Collections.Generic.List[string] }
          $incoming[$resolved].Add($f.FullName) | Out-Null
        }
      } else {
        $exists = $false
      }
    }

    # quick markers for "trap" detection
    if($href -match 'https?://(www\.)?hovn\.app'){ $hasExternalHovn = $true }
    if($href -match '/sessions/|classes/session_'){ $hasSessionsLink = $true }

    $links.Add([pscustomobject]@{
      Source   = $f.FullName
      Href     = $href
      Type     = $type
      Exists   = $exists
      Resolved = $resolved
    }) | Out-Null

    # Problems: dead internal, stub, javascript
    if( ($type -eq 'internal' -and $exists -eq $false) -or
        ($type -eq 'javascript') -or
        ($href -eq '') -or ($href -eq '#') ){
      $problems.Add([pscustomobject]@{
        Source   = $f.FullName
        Href     = $href
        Type     = $type
        Resolved = $resolved
        Issue    = if($type -eq 'internal' -and $exists -eq $false) {'Missing target'} elseif($type -eq 'javascript'){'JS link'} else {'Stub (#/empty)'}
      }) | Out-Null
    }

    # Mailto hygiene: enforce info+tag@910cpr.com
    if($type -eq 'mailto'){
      # mailto:foo@bar?subject=...
      $addr = $href.Substring(7).Split('?')[0]
      $local,$domain = $addr.Split('@',2)
      $hasPlus = $local -match '\+'
      if($domain -ne '910cpr.com' -or -not $hasPlus){
        $suggestTag = (Split-Path $f.DirectoryName -Leaf)
        if([string]::IsNullOrWhiteSpace($suggestTag)){ $suggestTag = (Split-Path $f.FullName -Leaf).Replace('.html','') }
        $suggest = "mailto:info+$suggestTag@910cpr.com"
        $mailIssues.Add([pscustomobject]@{
          Page      = $f.FullName
          Found     = $addr
          Problem   = if($domain -ne '910cpr.com'){'Non-910cpr.com domain'} else {'Missing +tag'}
          Suggest   = $suggest
        }) | Out-Null
      }
    }
  }

  # Simple "trap" signal: no hovn + no session-ish links on this page
  if(-not $hasExternalHovn -and -not $hasSessionsLink){
    $trapPages.Add($f.FullName) | Out-Null
  }

  # Term linking coverage (term appears but not inside an <a>…</a>)
  foreach($kv in $TermMap.GetEnumerator()){
    $term = [regex]::Escape($kv.Key)
    $hasTerm = [regex]::IsMatch($html, $term, 'IgnoreCase')
    if($hasTerm){
      $anchorPat = "<a\b[^>]*>(?:(?!</a>).)*?$term(?:(?!</a>).)*?</a>"
      $linked = [regex]::IsMatch($html, $anchorPat, 'IgnoreCase')
      if(-not $linked){
        $termsMiss.Add([pscustomobject]@{
          Page = $f.FullName
          Term = $kv.Key
          ShouldLinkTo = $kv.Value
        }) | Out-Null
      }
    }
  }
}

# Orphans: internal HTML files with no incoming links (ignore root index)
$allHtml = $files.FullName
$rootIndex = (Resolve-Path (Join-Path $Root 'index.html')).Path
$orphans = $allHtml | Where-Object {
  $_ -ne $rootIndex -and -not $incoming.ContainsKey($_)
}

# ----- Output -----
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
$links     | Export-Csv (Join-Path $OutDir 'links.csv') -NoTypeInformation
$problems  | Export-Csv (Join-Path $OutDir 'problems.csv') -NoTypeInformation
$termsMiss | Export-Csv (Join-Path $OutDir 'terms_missing.csv') -NoTypeInformation
$mailIssues| Export-Csv (Join-Path $OutDir 'mailto_issues.csv') -NoTypeInformation
$orphans   | Set-Content (Join-Path $OutDir 'orphans.txt')
$trapPages | Set-Content (Join-Path $OutDir 'trap_suspects.txt')

Write-Host ("Links scanned: {0}" -f $links.Count)
Write-Host ("Problems: {0} -> {1}" -f $problems.Count, (Join-Path $OutDir 'problems.csv'))
Write-Host ("Terms missing anchors: {0} -> {1}" -f $termsMiss.Count, (Join-Path $OutDir 'terms_missing.csv'))
Write-Host ("Mailto issues: {0} -> {1}" -f $mailIssues.Count, (Join-Path $OutDir 'mailto_issues.csv'))
Write-Host ("Orphan HTML files: {0} -> {1}" -f $orphans.Count, (Join-Path $OutDir 'orphans.txt'))
Write-Host ("Trap-suspect pages: {0} -> {1}" -f $trapPages.Count, (Join-Path $OutDir 'trap_suspects.txt'))
