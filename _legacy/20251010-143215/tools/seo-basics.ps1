param(
  [string]$Root = ".\docs",
  [string]$BaseUrl = "https://910cpr.com",   # <- change to your live origin
  [switch]$Ping                                # ping Google/Bing after writing
)

$ErrorActionPreference = "Stop"

function Join-Url([string]$a,[string]$b){
  ($a.TrimEnd('/') + '/' + $b.TrimStart('/')).Replace('///','/').Replace('//','//')
}

# 1) Build sitemap.xml
$pages = Get-ChildItem $Root -Recurse -Include *.html -File |
  Where-Object { $_.FullName -notmatch '\.bak$' -and $_.FullName -notmatch '\\assets\\' }

[xml]$doc = New-Object System.Xml.XmlDocument
$decl = $doc.CreateXmlDeclaration("1.0","UTF-8",$null); $doc.AppendChild($decl) | Out-Null
$urlset = $doc.CreateElement("urlset")
$attr = $doc.CreateAttribute("xmlns"); $attr.Value = "http://www.sitemaps.org/schemas/sitemap/0.9"
$urlset.Attributes.Append($attr) | Out-Null

foreach($p in $pages){
  $rel = Resolve-Path $p.FullName | ForEach-Object { $_.Path.Substring((Resolve-Path $Root).Path.Length).TrimStart('\','/') }
  $loc = Join-Url $BaseUrl $rel.Replace('\','/')
  $url = $doc.CreateElement("url")
  $n1 = $doc.CreateElement("loc");     $n1.InnerText = $loc
  $n2 = $doc.CreateElement("lastmod"); $n2.InnerText = (Get-Item $p.FullName).LastWriteTimeUtc.ToString("yyyy-MM-ddTHH:mm:ssZ")
  $n3 = $doc.CreateElement("changefreq"); $n3.InnerText = "weekly"
  $n4 = $doc.CreateElement("priority");   $n4.InnerText = if($p.Name -ieq "index.html"){"0.9"}else{"0.6"}
  $url.AppendChild($n1) | Out-Null
  $url.AppendChild($n2) | Out-Null
  $url.AppendChild($n3) | Out-Null
  $url.AppendChild($n4) | Out-Null
  $urlset.AppendChild($url) | Out-Null
}
$doc.AppendChild($urlset) | Out-Null
$siteMapPath = Join-Path $Root "sitemap.xml"
$doc.Save($siteMapPath)
"Written: $siteMapPath"

# 2) Write robots.txt that points to sitemap
$robots = @"
User-agent: *
Allow: /

Sitemap: $(Join-Url $BaseUrl "sitemap.xml")
"@
Set-Content (Join-Path $Root "robots.txt") $robots -Encoding UTF8
"Written: $(Join-Path $Root "robots.txt")"

# 3) Optional: ping Google + Bing
if($Ping){
  $smap = [uri]::EscapeDataString((Join-Url $BaseUrl "sitemap.xml"))
  foreach($endpoint in @("https://www.google.com/ping?sitemap=$smap","https://www.bing.com/ping?sitemap=$smap")){
    try{
      $res = Invoke-WebRequest -UseBasicParsing -Uri $endpoint -Method GET -TimeoutSec 20
      "Pinged: $endpoint -> $($res.StatusCode)"
    } catch {
      "Ping failed: $endpoint -> $($_.Exception.Message)"
    }
  }
}
