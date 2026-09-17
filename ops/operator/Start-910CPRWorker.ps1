[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$StateDirectory,

    [int]$HeartbeatSeconds = 60
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$identityPath = Join-Path $StateDirectory 'identity.json'
$heartbeatPath = Join-Path $StateDirectory 'heartbeat.json'
$inboxPath = Join-Path $StateDirectory 'inbox'
$resultPath = Join-Path $StateDirectory 'results'
$disabledPath = Join-Path $StateDirectory 'disabled.flag'
$lockPath = Join-Path $StateDirectory 'worker.lock'
$logPath = Join-Path $StateDirectory 'worker.log'

function Write-WorkerLog {
    param([string]$Message)
    $stamp = (Get-Date).ToUniversalTime().ToString('o')
    Add-Content -LiteralPath $logPath -Value "$stamp $Message" -Encoding utf8
}

function Write-Heartbeat {
    param(
        [object]$Identity,
        [string]$State,
        [string]$Detail
    )

    [ordered]@{
        schema_version = 1
        worker_id = $Identity.worker_id
        worker_name = $Identity.worker_name
        machine_name = $env:COMPUTERNAME
        process_id = $PID
        worker_version = $Identity.worker_version
        state = $State
        detail = $Detail
        observed_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $heartbeatPath -Encoding utf8
}

function Write-Result {
    param(
        [object]$Identity,
        [string]$JobId,
        [string]$JobType,
        [string]$Status,
        [string]$Message
    )

    $safeJobId = ($JobId -replace '[^A-Za-z0-9_.-]', '_')
    $path = Join-Path $resultPath "$safeJobId.json"
    [ordered]@{
        schema_version = 1
        worker_id = $Identity.worker_id
        worker_name = $Identity.worker_name
        job_id = $JobId
        job_type = $JobType
        status = $Status
        message = $Message
        completed_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $path -Encoding utf8
}

New-Item -ItemType Directory -Force -Path $StateDirectory, $inboxPath, $resultPath | Out-Null

if (-not (Test-Path -LiteralPath $identityPath)) {
    throw "Worker identity missing: $identityPath"
}

$identity = Get-Content -LiteralPath $identityPath -Raw | ConvertFrom-Json
if (-not $identity.worker_id -or -not $identity.worker_name) {
    throw 'Worker identity is invalid.'
}

$lockStream = $null
try {
    $lockStream = [System.IO.File]::Open($lockPath, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
} catch {
    Write-WorkerLog 'Another worker runtime already owns the local lock; exiting.'
    exit 0
}

try {
    Write-WorkerLog "Worker starting: $($identity.worker_name) / $($identity.worker_id)"

    while ($true) {
        if (Test-Path -LiteralPath $disabledPath) {
            Write-Heartbeat -Identity $identity -State 'disabled' -Detail 'Local revocation flag present; no jobs will be claimed.'
            Start-Sleep -Seconds $HeartbeatSeconds
            continue
        }

        Write-Heartbeat -Identity $identity -State 'idle' -Detail 'Local runtime healthy; waiting for an allowlisted job.'

        $jobs = @(Get-ChildItem -LiteralPath $inboxPath -Filter '*.json' -File -ErrorAction SilentlyContinue | Sort-Object Name)
        foreach ($jobFile in $jobs) {
            $processingPath = "$($jobFile.FullName).processing"
            try {
                Move-Item -LiteralPath $jobFile.FullName -Destination $processingPath -ErrorAction Stop
            } catch {
                continue
            }

            try {
                $job = Get-Content -LiteralPath $processingPath -Raw | ConvertFrom-Json
                $jobId = [string]$job.job_id
                $jobType = [string]$job.job_type

                if ([string]::IsNullOrWhiteSpace($jobId) -or [string]::IsNullOrWhiteSpace($jobType)) {
                    Write-Result -Identity $identity -JobId $jobFile.BaseName -JobType 'unknown' -Status 'FAIL' -Message 'Malformed job: job_id and job_type are required.'
                    Write-WorkerLog "Rejected malformed job file: $($jobFile.Name)"
                    continue
                }

                $existingResult = Join-Path $resultPath (($jobId -replace '[^A-Za-z0-9_.-]', '_') + '.json')
                if (Test-Path -LiteralPath $existingResult) {
                    Write-WorkerLog "Duplicate job suppressed: $jobId"
                    continue
                }

                switch ($jobType) {
                    'selftest.ping' {
                        Write-Heartbeat -Identity $identity -State 'working' -Detail "Executing allowlisted self-test job $jobId"
                        Write-Result -Identity $identity -JobId $jobId -JobType $jobType -Status 'PASS' -Message 'Worker accepted and executed the allowlisted self-test exactly once.'
                        Write-WorkerLog "PASS $jobId $jobType"
                    }
                    default {
                        Write-Result -Identity $identity -JobId $jobId -JobType $jobType -Status 'REJECTED' -Message 'Job type is not allowlisted by this worker version.'
                        Write-WorkerLog "REJECTED $jobId $jobType"
                    }
                }
            } catch {
                $fallbackId = $jobFile.BaseName
                Write-Result -Identity $identity -JobId $fallbackId -JobType 'unknown' -Status 'FAIL' -Message $_.Exception.Message
                Write-WorkerLog "FAIL $fallbackId $($_.Exception.Message)"
            } finally {
                Remove-Item -LiteralPath $processingPath -Force -ErrorAction SilentlyContinue
            }
        }

        Start-Sleep -Seconds $HeartbeatSeconds
    }
} finally {
    if ($lockStream) {
        $lockStream.Dispose()
    }
    Write-WorkerLog 'Worker stopped.'
}
