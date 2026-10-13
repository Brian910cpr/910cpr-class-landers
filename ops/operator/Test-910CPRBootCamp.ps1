[CmdletBinding()]
param()

# Read-only readiness evidence. Never enroll, launch workers, or inspect credentials.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$checks = @()
foreach ($name in @('Install-910CPRWorker.ps1', 'Start-910CPRWorker.ps1')) {
    $path = Join-Path $PSScriptRoot $name
    $valid = Test-Path -LiteralPath $path -PathType Leaf
    if ($valid) {
        $tokens = $null
        $parseErrors = $null
        [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$parseErrors) | Out-Null
        $valid = @($parseErrors).Count -eq 0
    }
    $checks += [pscustomobject]@{ check = $name; passed = $valid }
}
$checks += [pscustomobject]@{
    check = 'windows_powershell_runtime'
    passed = ($env:OS -eq 'Windows_NT' -and (Test-Path -LiteralPath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"))
}
$checks += [pscustomobject]@{
    check = 'startup_directory'
    passed = -not [string]::IsNullOrWhiteSpace([Environment]::GetFolderPath('Startup'))
}
$checks += [pscustomobject]@{
    check = 'github_cli_present_auth_not_checked'
    passed = [bool](Get-Command gh.exe -ErrorAction SilentlyContinue)
}

# These are reviewed implementation gates, not environment probes. Keep closed
# until replacement code AND the required durable proof have been reviewed.
$blockers = @(
    '#249: runtime uses ambient gh auth; generated credential.protected is not bound to a server identity.'
    '#249: GitHub comment claims are not atomic leases; ambiguous attempts and stranded processing files lack recovery.'
    '#252: local disabled.flag is not server credential revocation; remote observer health is unproven.'
    '#250/#254: clean second Windows installation and graduation evidence are required; this host check cannot prove isolation.'
)
[pscustomobject][ordered]@{
    schema_version = 1
    observed_at_utc = [DateTime]::UtcNow.ToString('o')
    evidence_level = 'BUILT'
    ready_for_clean_room_graduation = $false
    checks = $checks
    blockers = $blockers
    next_action = 'Implement and prove #249 credential binding and atomic attempt/recovery before clean enrollment. See OPERATOR_BOOT_CAMP_ROLLOUT.md.'
} | ConvertTo-Json -Depth 5
exit 1
