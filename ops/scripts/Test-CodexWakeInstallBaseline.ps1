function Assert-CodexWakeInstallBaseline {
    [CmdletBinding()]
    param([Parameter(Mandatory)][object[]]$Files)

    # Review drift before any install/state/startup mutation. Never silently remove
    # installed-only receipt, hold, retry or intake safeguards.
    foreach ($file in $Files) {
        if (-not (Test-Path -LiteralPath $file.Source -PathType Leaf)) {
            throw "Missing Codex Wake source: $($file.Source)"
        }
        if (Test-Path -LiteralPath $file.Destination) {
            if (-not (Test-Path -LiteralPath $file.Destination -PathType Leaf)) {
                throw "Invalid Codex Wake destination: $($file.Destination)"
            }
            $sourceHash = (Get-FileHash -LiteralPath $file.Source -Algorithm SHA256).Hash
            $installedHash = (Get-FileHash -LiteralPath $file.Destination -Algorithm SHA256).Hash
            if ($sourceHash -ne $installedHash) {
                throw "Codex Wake install refused: installed script differs: $($file.Destination). Reconcile safeguards and review rollout before replacement. Source SHA256=$sourceHash Installed SHA256=$installedHash"
            }
        }
    }
}
