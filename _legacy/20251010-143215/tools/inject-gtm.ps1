[CmdletBinding(SupportsShouldProcess=$true)]
param(
  [string]$Root = ".\docs",
  [Parameter(Mandatory)] [string]$GTM,     # e.g. GTM-K58Z4XD
  [switch]$InjectConsent = $true,
  [switch]$InjectEvents  = $true,
  [switch]$ReplacePlaceholders = $true,    # GTM placeholders only
  [switch]$Backup,
  [switch]$Zip,
  [string]$EventScriptPath = ".\docs\assets\gtm-events.js",
  [string]$ZipOut = ".\site.zip"
)

function Get-TargetHtml {
  Get-ChildItem -Path $Root -Recurse -Include *.html,*.htm -File |
    Where-Object { $_.FullName -notmatch '\\(node_modules|\.git|dist|vendor|\.cache)\\' }
}
function Get-TargetJs {
  Get-ChildItem -Path $Root -Recurse -Include *.js -File |
    Where-Object { $_.FullName -notmatch '\\(node_modules|\.git|dist|vendor|\.cache)\\' }
}
function Save-TextFile {
  param([System.IO.FileInfo]$File, [string]$Content)
  if ($Backup) {
    $bak = "$($File.FullName).bak"
    if (-not (Test-Path $bak)) { Copy-Item -LiteralPath $File.FullName -Destination $bak -ErrorAction SilentlyContinue }
  }
  if ($PSCmdlet.ShouldProcess($File.FullName, "Write updated content")) {
    Set-Content -LiteralPath $File.FullName -Value $Content -Encoding UTF8
  }
}

# --- Snippets ---
$headGtm = @"
<!-- Google Tag Manager -->
<script>
(function(w,d,s,l,i){w[l]=w[l]||[];
 w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});
 var f=d.getElementsByTagName(s)[0], j=d.createElement(s), dl=l!='dataLayer'?'&l='+l:'';
 j.async=true; j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;
 f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','$GTM');
</script>
<!-- End Google Tag Manager -->
"@

$bodyGtm = @"
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=$GTM"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
"@

$consent = @"
<!-- Consent Mode defaults -->
<script>
window.dataLayer = window.dataLayer || [];
window.dataLayer.push({
  event: 'default_consent',
  analytics_storage: 'granted',
  ad_storage: 'denied',
  ad_user_data: 'denied',
  ad_personalization: 'denied'
});
</script>
"@

$eventsJs = @"
window.dataLayer = window.dataLayer || [];
function dl(event, props){ try{ dataLayer.push(Object.assign({event}, props||{})); }catch(e){} }

document.addEventListener('DOMContentLoaded', function () {
  var sessionLinks = Array.prototype.slice.call(document.querySelectorAll('a[href*=""\/sessions\/""]')).slice(0, 15);
  if (sessionLinks.length) {
    var items = sessionLinks.map(function(a){
      var m = (a.href||'').match(/\/sessions\/([a-z0-9]+)/i);
      return {
        item_id:   (m && m[1]) || null,
        item_name: ((a.dataset && (a.dataset.title||'')) || a.title || a.textContent || '').trim().slice(0,100),
        item_list_name: 'Periscope Sessions',
        item_category: (a.dataset && a.dataset.course) || null,
        location_id: (a.dataset && a.dataset.city) || null
      };
    });
    dl('view_item_list', { items: items });
  }

  document.addEventListener('click', function(e){
    var el = e.target.closest && e.target.closest('a,button');
    if (!el) return;

    if (el.dataset && el.dataset.event) {
      var payload = {};
      for (var k in el.dataset) if (k !== 'event') payload[k] = el.dataset[k];
      payload.link_text = (el.innerText||'').trim().slice(0,80);
      payload.link_url  = el.href || null;
      dl(el.dataset.event, payload);
      return;
    }

    if (el.matches && el.matches('a[href*=""\/sessions\/""]')) {
      var m = (el.href||'').match(/\/sessions\/([a-z0-9]+)/i);
      dl('select_item', {
        item_id: (m && m[1]) || null,
        item_name: ((el.dataset && (el.dataset.title||'')) || el.title || el.textContent || '').trim().slice(0,100),
        item_list_name: 'Periscope Sessions',
        link_url: el.href
      });
      dl('book_click', { link_url: el.href });
      return;
    }

    if (el.matches && el.matches('a[href^=""tel:""]'))   { dl('click_phone', { link_url: el.href }); return; }
    if (el.matches && el.matches('a[href^=""mailto:""]')){ dl('click_email', { link_url: el.href }); return; }
  });

  var searchForm = document.querySelector('form[id*=""search""], form[action*=""search""]');
  if (searchForm) {
    searchForm.addEventListener('submit', function(){
      var qInput = searchForm.querySelector('input[name=""q""], input[type=""search""]');
      var q = (qInput && qInput.value) || '';
      dl('search', { search_term: (q||'').toString().slice(0,100) });
    });
  }
});
"@

# Ensure events helper if requested
if ($InjectEvents) {
  $eventsFile = Resolve-Path -LiteralPath $EventScriptPath -ErrorAction SilentlyContinue
  if (-not $eventsFile) {
    $target = $EventScriptPath
    $dir = Split-Path -Parent $target
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if ($PSCmdlet.ShouldProcess($target, "Write gtm-events.js")) {
      Set-Content -LiteralPath $target -Value $eventsJs -Encoding UTF8
    }
  }
}

$changes = 0

# HTML injection
foreach ($f in Get-TargetHtml) {
  $t = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8
  $orig = $t

  if ($InjectConsent -and ($t -notmatch 'default_consent' -and $t -notmatch 'analytics_storage')) {
    if ($t -match '(?is)</head>') { $t = [regex]::Replace($t, '(?is)</head>', ($consent + "`r`n</head>"), 1) }
    else { $t = $consent + "`r`n" + $t }
  }

  if ($t -notmatch [regex]::Escape($GTM) -and $t -notmatch 'googletagmanager\.com/gtm\.js') {
    if ($t -match '(?is)</head>') { $t = [regex]::Replace($t, '(?is)</head>', ($headGtm + "`r`n</head>"), 1) }
    else { $t = $headGtm + "`r`n" + $t }
    if ($t -match '(?is)<body[^>]*>') { $t = [regex]::Replace($t, '(?is)(<body[^>]*>)', ('$1' + "`r`n" + $bodyGtm), 1) }
    else { $t = $t + "`r`n" + $bodyGtm }
  }

  if ($InjectEvents -and ($t -notmatch [regex]::Escape('/assets/gtm-events.js'))) {
    if ($t -match '(?is)</body>') { $t = [regex]::Replace($t, '(?is)</body>', ("<script src=""/assets/gtm-events.js"" defer></script>`r`n</body>"), 1) }
    else { $t = $t + "`r`n" + '<script src="/assets/gtm-events.js" defer></script>' }
  }

  if ($ReplacePlaceholders) {
    $t = $t `
      -replace [regex]::Escape('GTM-XXXXXXX'), $GTM `
      -replace [regex]::Escape('GTM_PLACEHOLDER'), $GTM `
      -replace [regex]::Escape('GT-XXXXXXX'), $GTM
  }

  if ($t -ne $orig) { Save-TextFile -File $f -Content $t; $changes++; Write-Host "Updated $($f.FullName)" }
}

# JS placeholder replacement (GTM tokens only)
if ($ReplacePlaceholders) {
  foreach ($f in Get-TargetJs) {
    $t = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8
    $orig = $t
    $t = $t `
      -replace [regex]::Escape('GTM-XXXXXXX'), $GTM `
      -replace [regex]::Escape('GTM_PLACEHOLDER'), $GTM `
      -replace [regex]::Escape('GT-XXXXXXX'), $GTM
    if ($t -ne $orig) { Save-TextFile -File $f -Content $t; $changes++; Write-Host "Updated $($f.FullName)" }
  }
}

# ZIP (optional)
if ($Zip) {
  $zipDir = Split-Path -Parent $ZipOut
  if ($zipDir -and -not (Test-Path $zipDir)) { New-Item -ItemType Directory -Path $zipDir -Force | Out-Null }
  if ($PSCmdlet.ShouldProcess($ZipOut, "Create ZIP of $Root")) {
    if (Test-Path $ZipOut) { Remove-Item -LiteralPath $ZipOut -Force }
    Compress-Archive -Path (Join-Path $Root '*') -DestinationPath $ZipOut -Force
    Write-Host "ZIP created: $ZipOut"
  }
}

Write-Host "Done. Files changed: $changes"
exit 0
