# Issue #255 — CYBERPC-01 bounded control-plane proof

- Timestamp: 2026-10-11T00:00:00Z (America/New_York: 2026-10-10 20:00 EDT).
- Branch: codex/issue255-controlplane-20261010.
- Source commit: bb29a3a46dfd902c5c70c1c6c80f67f5b57bf8cb. Receipt commit: discoverable as branch tip; this file cannot contain its own commit hash.
- Work-item state: VERIFIED for the bounded operational proof; receipt is submitted on a review branch, not merged.
- Persistent evidence: PROVEN historical round-trip, currently CONNECTED; MONITORED/HEALTHY not established.
- Owner/account action required: none for #255.

## Findings and work

Read full #255 including owner comments, parent #254, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Acknowledged execution before installation:
https://github.com/Brian910cpr/910cpr-class-landers/issues/255#issuecomment-6103537889

Fetched current main using the clean sibling repository, preserving its dirty branch. Created isolated worktree E:/GitHub/910cpr-issue255-20261010 from origin/main. The original corrupted E:/GitHub/910cpr-class-landers was inspected read-only and never reset/repaired. No existing assignments, PRs, or customer-facing code were changed. Draft PR #372 was not merged or deployed.

The exact job was already executed in #259. Creating another job or deleting its result would violate exactly-once intent, so reused the existing job and evidence. Installed current main worker v0.2.3 (already installed; newer than requested v0.2.0) without ForceReenroll. Installer restarted only this worker, not Windows. Identity retained: 4f966f81-b645-467c-a0e0-7073cfb28b86.

Exact operational commands (PowerShell, from isolated worktree):

```powershell
git fetch origin main
git worktree add -b codex/issue255-controlplane-20261010 E:/GitHub/910cpr-issue255-20261010 origin/main
powershell -ExecutionPolicy Bypass -File ./ops/operator/Install-910CPRWorker.ps1 -WorkerName 'CYBERPC-01'
gh issue view 259 --repo Brian910cpr/910cpr-class-landers --json title,body,state,comments,closedAt
$workerDir = "$env:LOCALAPPDATA/910CPR/Worker/CYBERPC-01"
Get-Content "$workerDir/identity.json"
Get-Content "$workerDir/heartbeat.json"
Get-Content "$workerDir/diagnostic.json"
Get-Content "$workerDir/results/cyberpc-roundtrip-001.json"
Get-FileHash "$workerDir/results/cyberpc-roundtrip-001.json"
(Select-String -Path "$workerDir/worker.log" -Pattern 'PASS cyberpc-roundtrip-001 selftest.ping').Count
```

Installer output:

```text
WorkerName           : CYBERPC-01
WorkerId             : 4f966f81-b645-467c-a0e0-7073cfb28b86
Machine              : CYBERPC
Version              : 0.2.3
ProcessId            : 38596
HeartbeatState       : idle
ControlPlane         : GITHUB_ISSUES_BOUNDED_V1
ReadyForGitHubClaims : True
```

Fresh heartbeat observed_at_utc=2026-10-10T23:59:49.7213559Z, process_id=38596, detail="Runtime healthy; GitHub control plane connected; waiting for an allowlisted job." The quoted runtime message is component output, not a claim of system HEALTHY. Diagnostic at 2026-10-10T23:59:50.6535359Z: phase=idle, detail="GitHub queue poll completed.", last_error="".

## Durable round-trip evidence

Job: https://github.com/Brian910cpr/910cpr-class-landers/issues/259
Title: [WORKER] CYBERPC-01 selftest.ping cyberpc-roundtrip-001
State: CLOSED, closedAt=2026-09-18T10:34:59Z.

Claim: https://github.com/Brian910cpr/910cpr-class-landers/issues/259#issuecomment-5728785455
Result: https://github.com/Brian910cpr/910cpr-class-landers/issues/259#issuecomment-5728785598
Both authored by Brian910cpr; no third-party comment used as authority.

```text
910CPR_WORKER_RESULT worker_id=4f966f81-b645-467c-a0e0-7073cfb28b86 job_id=cyberpc-roundtrip-001 status=PASS completed_at_utc=2026-09-18T10:34:58.7303045Z
```

Local file: C:/Users/ten77/AppData/Local/910CPR/Worker/CYBERPC-01/results/cyberpc-roundtrip-001.json

```json
{"worker_id":"4f966f81-b645-467c-a0e0-7073cfb28b86","worker_name":"CYBERPC-01","job_id":"cyberpc-roundtrip-001","job_type":"selftest.ping","status":"PASS","github_issue":259,"completed_at_utc":"2026-09-18T10:34:58.7303045Z"}
```

Before/after worker restart SHA256: 31F79E1D9D53AFA03337CCA18D775A64FF4A3DDEBC257359417BFF4904CA7D4F.
PASS log count remained 1. GitHub has one claim and one result, with no new receipt after restart. This proves no reexecution of the closed completed job; it does not claim a reopened-job duplicate injection test.

## Validation and scope

- Windows PowerShell parser: installer and runtime syntax PASS (zero parse errors).
- Installer readiness, preserved identity, fresh matching PID heartbeat, completed GitHub queue poll: PASS.
- Historical result identity/status/issue match: PASS.
- Restart result immutability and single PASS/receipt: PASS.
- No generator, broad rebuild, application changes, arbitrary shell job, reenrollment, reboot, merge, or public deployment.
- Only intended repository file: Codex_Reply_CyberPCControlPlane_R1.md.
- Unrelated dirty files in fresh checkout preserved: docs/Earl/index.html, docs/Jackson/index.html, four tracked scripts/__pycache__ files. Original checkout dirty files also preserved.
- Isolated worktree acquired unrelated modifications to docs/Earl/index.html and docs/Jackson/index.html despite no command in this assignment editing them. Their origin is unverified; explicitly excluded from staging and left uncommitted. No cleanup performed.
- No intentionally created untracked artifacts beyond the receipt before commit.

## Proof contract, limitations, and next action

Expected outcome: owner job -> worker claim -> allowlisted execution -> local result -> GitHub PASS receipt -> closed issue. Last successful full proof: 2026-09-18T10:34:58.7303045Z, #259. Current connectivity/restart verified 2026-10-10T23:59:50Z. Worker polls nominally every 60 seconds plus API time. Missing/stale heartbeat, degraded diagnostic, absent result/receipt, or non-PASS result indicates failure. Local diagnostic and heartbeat are available but independently observed monitor/observer health was not established; therefore do not call this system MONITORED or HEALTHY. Historical log has intermittent network/TLS failures, most recently 2026-10-09T22:56:14Z; current poll succeeded.

Recovery: inspect identity/heartbeat/diagnostic/log at the stated local directory, verify gh authentication, rerun installer without ForceReenroll only if needed. Escalate only actual account authentication or Windows permission failures. No such blocker occurred here. Routine unattended monitoring remains unproven and must not be assigned implicitly to Brian.

Queue swept; existing backend authority fix and fleet gates are already in PR #374 for #254. Reused its findings; did not duplicate that implementation or start another deep stream. Parent #254 requires a second clean Windows environment, independent jobs, and revocation proof; this receipt does not complete it. PR #374's owner-authority hardening is not merged and was not installed from an unmerged branch.

Recommended ChatGPT action: review this receipt and #259; acknowledge the bounded #255 proof without rerunning cyberpc-roundtrip-001. Preserve #254/PR #374 as the existing fleet workstream and separately decide its review/release. Receipt is locally persisted and pushed on the named branch; no merge or deployment claimed.
