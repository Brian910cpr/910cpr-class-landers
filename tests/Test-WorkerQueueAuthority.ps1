# Local regression tests: no GitHub requests, worker processes, or installed state.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$source = Join-Path $PSScriptRoot '../ops/operator/Start-910CPRWorker.ps1'
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $source), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
# Load actual function definitions without starting the infinite worker loop.
foreach ($node in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $false)) {
    . ([scriptblock]::Create($node.Extent.Text))
}
function Test-GitHubReady { return $true }
function Write-WorkerLog { param([string]$Message) }
function Write-Heartbeat { param($Identity,$State,$Detail) }
$RepoSlug = 'Brian910cpr/910cpr-class-landers'
$identity = [pscustomobject]@{ worker_id = 'test-id'; worker_name = 'TEST-02' }
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('worker-authority-' + [guid]::NewGuid())
$resultPath = $testRoot
New-Item -ItemType Directory -Path $testRoot | Out-Null
$script:mutations = @()
$script:jobAuthor = 'Brian910cpr'
$script:comments = @()
$script:jobType = 'selftest.ping'
$script:jobId = 'authority-001'
function gh {
    $global:LASTEXITCODE = 0
    switch ($args[1]) {
        'list' { return (ConvertTo-Json -InputObject @(@{ number=1; title="[WORKER] TEST-02 $script:jobType $script:jobId" })) }
        'view' { return (@{ author=$script:jobAuthor; comments=$script:comments } | ConvertTo-Json -Depth 8) }
        'comment' { $script:mutations += 'comment'; return }
        'close' { $script:mutations += 'close'; return }
        default { throw "Unexpected mock GitHub operation: $args" }
    }
}
function Assert-True { param([bool]$Condition,[string]$Message) if (-not $Condition) { throw $Message } }
$passed = 0
foreach ($author in @(@{login='untrusted-contributor'}, $null)) {
    $script:jobAuthor = $author
    Invoke-GitHubQueue -Identity $identity
    Assert-True ($script:mutations.Count -eq 0) 'Unauthorized/null author must not claim, receipt, or close.'
    Assert-True (-not (Test-Path (Get-ResultPath $script:jobId))) 'Unauthorized job executed.'
    $passed++
}
$script:jobAuthor = @{login='Brian910cpr'}
$marker = '910CPR_WORKER_RESULT worker_id=test-id job_id=authority-001 status=PASS'
$script:comments = @(@{author=@{login='untrusted-contributor'};body=$marker})
Invoke-GitHubQueue -Identity $identity
$resultFile = Get-ResultPath $script:jobId
Assert-True ((Get-Content $resultFile -Raw | ConvertFrom-Json).status -eq 'PASS') 'Forged receipt suppressed authorized job.'
Assert-True ($script:mutations.Count -eq 3) 'Authorized job must claim, receipt, and close.'
$passed++
$hashBefore = (Get-FileHash $resultFile).Hash
$script:mutations = @()
Invoke-GitHubQueue -Identity $identity
Assert-True ((Get-FileHash $resultFile).Hash -eq $hashBefore) 'Completed local result was overwritten.'
Assert-True ($script:mutations.Count -eq 2) 'Existing result should be receipted without another claim.'
$passed++
$script:mutations = @()
$script:comments = @(@{author=@{login='brian910cpr'};body=$marker})
Invoke-GitHubQueue -Identity $identity
Assert-True ($script:mutations.Count -eq 0) 'Authentic owner receipt must suppress a duplicate.'
$passed++
$script:comments = @()
$script:jobId = 'authority-reject-002'
$script:jobType = 'unapproved.shell'
Invoke-GitHubQueue -Identity $identity
Assert-True ((Get-Content (Get-ResultPath $script:jobId) -Raw | ConvertFrom-Json).status -eq 'REJECTED') 'Unapproved job must remain rejected.'
$passed++
Write-Output "PASS: $passed worker queue authority/result regression cases; no network or installed worker changes."
Write-Output "Fixture evidence retained outside Git: $testRoot"
