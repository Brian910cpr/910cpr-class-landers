# Issue 380 R4 — installed/tracked safeguard reconciliation

Observed 2026-10-12 (America/New_York). Read-only diagnostic; no runtime changes.
Base: f168d6363c1a9619d3753c9192e81e728e8bbac1. Review: draft PR #381.

## Exact inputs

- Tracked `ops/scripts/Invoke-CodexWake.ps1`, SHA256 9B5DC9D634FD65143952D9634203C1E0BFCB77DB2221CFC0837E70EAF8A96B0F.
- Installed `C:/Users/ten77/AppData/Local/910CPR/CodexWake/Invoke-CodexWake.ps1`, SHA256 DB81F14C5894B614FBD34FC6C9E2DDA4E24C9D3F8B5A17D70DFFE1918F7AB168.
- These match R3 observations. `git diff --no-index -- ops/scripts/Invoke-CodexWake.ps1 C:/Users/ten77/AppData/Local/910CPR/CodexWake/Invoke-CodexWake.ps1` inspected in full. Exit 1 means differences, not a runtime failure.
- `ops/scripts/Install-CodexWake.ps1:15` unconditionally copies tracked script with Force. `ops/scripts/Start-CodexWakeLoop.ps1:13` consumes the installed script. Do not run the installer from this baseline.

## Preservation matrix

| Concern | Tracked | Installed | Required reconciliation |
| --- | --- | --- | --- |
| Heartbeat | retired ops/handoff path | local state directory | Preserve local-only path |
| Repository preflight | fetch/prune | rev-parse only | Preserve independence from damaged checkout/fetch |
| Queue | search limited to 100, no author | paginated API, owner issue author | Preserve pagination/owner restriction; comments are not authority |
| Explicit issue | absent | IssueNumber; no fallback | Preserve no-fallback behavior |
| Manual hold | absent | manual-hold.json | Preserve; ProofOnly bypass needs separate diagnostic-only review |
| Failure retry | absent | one-hour retry_after | Preserve bounded backoff |
| Session evidence | exit status only | JSON events/thread/final response | Preserve, never equate exit zero with receipt |
| Durable receipt | absent | GitHub Contents lookup at reported SHA | Preserve; receipt proves handoff, not task resolution |
| Watermark | pre-run updatedAt | post-run updatedAt | Preserve loop prevention, replace lifecycle eligibility separately |
| Error state | can leave current_task set | clears current_task | Preserve cleanup without erasing diagnostic evidence |
| Proof mode | absent | explicit no-edit/no-receipt diagnostic prompt | Keep distinct from implementation and claims |
| Priority | preferred before sorted P0 | same plus explicit issue | Defect remains: authenticated P0 must outrank ordinary preference |
| Blocker/resolution | updatedAt only | updatedAt only | Neither enforces canonical typed reconciliation |
| Lease | elapsed time only | elapsed time only | Neither is versioned atomic card claim |

## Integration boundary and exact remaining gates

Issue #266 explicitly requires a separate `ops/operator` dispatcher; do not turn Codex Wake into that dispatcher. Codex Wake is model-session intake; worker claim/execution is a separate surface. A selector fix alone cannot protect an external side effect.

Before runtime replacement, prepare a reviewed source baseline preserving every installed-only safeguard above. Do not copy installed state, run logs, private evidence or credentials into Git. Add isolated process tests that invoke neither Codex nor installed scripts, with fake GitHub/canonical adapters.

The integration adapter remains unimplemented: authenticated typed card/job identity, canonical resolution and version, explicit blocker reconciliation, source evidence, worker-safe allowlist and owner priority; transactional compare-and-swap claim/skip audit and idempotency; second reconciliation at the actual job mutation boundary. Boolean `authoritative:true` from an arbitrary caller is not authentication. GitHub issue author filtering does not authenticate all comments. No issue prose may become shell commands.

Required no-launch proof: unchanged blocked #297 stays skipped despite comment updatedAt changes; changed source signature alone cannot clear blocker; #371 remains ordinary P1 priority and new authenticated P0 wins; unavailable canonical service fails closed; resolution after selection stops before mutation; stale/duplicate claims cannot mutate; held/retry/lease states retain safeguards. Receipt-only runs must not count as business completion.

This is engineering work remaining, not an owner-credential blocker. Production mutations/merge/deploy remain separately gated by issue #380. No rollout requested here. Transactional resolution/private evidence/UI/history/counts remain unfinished; all six acceptance criteria open. No Brian action required for review.

## Local validation and proof limits

`node --experimental-strip-types --test tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/owner_access.test.mjs`: 37 tests, 37 pass, 0 fail.
Installed script parsed using PowerShell Language.Parser.ParseFile: zero syntax errors; never executed. No generators or SQL ran.
Existing R2 baseline Python tests had three obsolete Maxim-auth assertions; not rerun or changed here.

Evidence level stays BUILT for existing advisory contracts. No end-to-end owner resolution/evidence/worker-skip proof. Expected window every selection and mutation; failure is blocked/resolved work launched or stale claims executing. Observer and observer health remain unintegrated/unproven; runtime health cannot be claimed. Recovery: preserve state and use approved hold controls, reconcile canonical state, then retry only after explicit gate clearance. Owner must not become routine observer.

Queue swept via GitHub open issue list. #371 primary and all other assignments preserved; no independent backend edit selected without reading its complete gates. Original E:/GitHub/910cpr-class-landers dirt untouched; new worktree case-collision docs/Earl/index.html and docs/Jackson/index.html excluded explicitly.
