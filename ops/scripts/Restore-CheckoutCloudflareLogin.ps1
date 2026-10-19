# Run interactively only: opens Cloudflare consent, never deploys or sends.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$python=Get-Command python -ErrorAction Stop
$npx=Get-Command npx.cmd -ErrorAction Stop
$configPath=Join-Path $env:APPDATA 'xdg.config/.wrangler/config/default.toml'
$scopeReader=@'
import json,sys,tomllib
try:
    with open(sys.argv[1],'rb') as stream:
        values=tomllib.load(stream).get('scopes')
    if not isinstance(values,list) or not values or not all(isinstance(s,str) for s in values):
        raise ValueError()
    print(json.dumps(values))
except Exception:
    print('Cannot read existing Cloudflare scope metadata.',file=sys.stderr)
    sys.exit(1)
'@
$scopeJson=& $python.Source -c $scopeReader $configPath
if($LASTEXITCODE -ne 0){throw 'Existing scope metadata unavailable; no login attempted.'}
# offline_access is appended by Wrangler itself. Retain existing scopes.
$scopes=@(@($scopeJson | ConvertFrom-Json) | Where-Object {$_ -ne 'offline_access'})
if('email_sending:write' -notin $scopes){$scopes+= 'email_sending:write'}
$priorToken=$env:CLOUDFLARE_API_TOKEN
try {
    # This process and its children only; never remove the saved environment token.
    Remove-Item Env:CLOUDFLARE_API_TOKEN -ErrorAction SilentlyContinue
    Write-Host 'Approve the existing 910CPR account. Adding Email Sending; no deploy or send will run.'
    & $npx.Source --yes wrangler@4.151.1 login --scopes @scopes
    if($LASTEXITCODE -ne 0){throw 'Cloudflare browser authorization did not complete.'}
    & $npx.Source --yes wrangler@4.151.1 whoami
    if($LASTEXITCODE -ne 0){throw 'Cloudflare account verification failed.'}
} finally {
    if($null -eq $priorToken){Remove-Item Env:CLOUDFLARE_API_TOKEN -ErrorAction SilentlyContinue}
    else {$env:CLOUDFLARE_API_TOKEN=$priorToken}
}
