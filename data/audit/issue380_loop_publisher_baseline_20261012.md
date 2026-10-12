# Issue 380 R7 — loop and publisher source reconciliation

2026-10-12, America/New_York. Existing draft PR #381. BUILT / validated locally only.

## Findings and changes

Read installed executable source only; did not read health configuration, credentials, state or run contents. Observed installed SHA256: Start-CodexWakeLoop.ps1 15CAB9CBF60746F03840F6920AFFFBD8F6DE2E4BA53C48AB619B0B3738B7CE59; Publish-CodexWakeHealth.ps1 59A252AFC8896DE8A83C20B8D8A7EC520C81005DF43A327CC7DD4E7F90724025.

Reconciled tracked loop to that source: hidden child worker isolates exit from supervisor, periodic health publication during work and idle, exit-code logging and finally lock release. Added observed publisher as tracked source: no configuration means no publication; explicit field allowlist; numeric comment target; failed publication logs locally and retains last successful published signal. Installer now includes publisher in baseline preflight and copy set, before any mutations. No configuration copied or invented; no publisher called against GitHub. No installation authorized by this increment.

Exact files: ops/scripts/Start-CodexWakeLoop.ps1; ops/scripts/Publish-CodexWakeHealth.ps1; ops/scripts/Install-CodexWake.ps1; tests/test_codex_wake_loop.ps1; tests/test_codex_wake_health_publisher.ps1; this report; unique root R7 receipt.

## Local proof

Both pwsh and Windows PowerShell 5.1: test_codex_wake_loop.ps1 PASS (hidden fake process; two working publications and one idle publication; nonzero exit logged; exclusive lock released). No actual child worker, installed script or network invoked. Both shells: test_codex_wake_health_publisher.ps1 PASS (no-config skip; allowlist; failed publication retains last success; invalid target never reaches fake GitHub). Both shells: test_codex_wake_install_baseline.ps1 PASS, six checks. PowerShell parser on all CodexWake source and tests: zero errors. git diff --check PASS. Node dispatch_reconciliation, production_execution_check, owner_access: 37 tests, 37 pass, zero fail.

Fixtures retained only in OS Temp. No generators/builds/database writes. Existing unrelated Python Maxim-auth baseline failures not rerun; no Python changed.

## Limits / next gate

All six acceptance criteria remain open. No canonical typed authenticated intake/versioned atomic claim/skip audit or actual pre-mutation wiring exists yet. No resolution/private evidence/UI/history implementation. Publisher proves launcher liveness only, not business completion; allowlisted state values still originate from local launcher state. External GitHub/auth hangs, publisher timeout and supervisor observer health remain unproven. Installer matching source is not rollout authorization. Future runtime changes must preserve #266 separate operator-worker boundary and add fake-adapter blocked/resolved/stale claim tests before rollout review.

Persistent proof contract: expected outcome is blocked/resolved tasks skipped before launch and every side effect with durable audit; cadence every selection/mutation; no successful runtime end-to-end proof yet. Failure is blocked/resolved launch or stale mutation. Observer/observer health remain unintegrated for that outcome. Recovery preserves evidence/state, reconciles canonical state and uses approved hold; account escalation only if proven necessary. No Brian action now; engineering gates remain, no credential blocker.

Queue swept, existing assignments retained; #371 primary, #372 untouched. Original checkout unchanged. Worktree inherited Windows case-collision dirt docs/Earl/index.html and docs/Jackson/index.html excluded. No merge/deployment/runtime/state/task/process change. Next: review source dependency baseline, then authenticated canonical atomic adapter and pre-mutation proof; keep #381 draft.
