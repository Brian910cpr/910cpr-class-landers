# Issue 380 R7 receipt

Timestamp: 2026-10-12 America/New_York.
Branch: codex/issue380-r7-20261012; pushed to existing PR #381 head codex/issue380-manual-resolution-20261011.
Substantive commit: 70e599ba9ad1dcea3bfb3acbb623e431cb4d09e9.
State: PR_OPEN / IN_PROGRESS. Evidence: BUILT, validated locally only.

Reconciled observed installed loop/publisher executable source into repository and installer baseline guard. Isolated fake process/GitHub tests cover work/idle supervision, failed worker exit, lock release, field allowlist, missing/invalid config and failed publication. No installed source/state/process/task changed. No production writes, installation, merge or deployment. PR #381 remains draft; #371/#372 preserved.

Exact changes and findings: data/audit/issue380_loop_publisher_baseline_20261012.md (full report); ops/scripts/Start-CodexWakeLoop.ps1; ops/scripts/Publish-CodexWakeHealth.ps1; ops/scripts/Install-CodexWake.ps1; tests/test_codex_wake_loop.ps1; tests/test_codex_wake_health_publisher.ps1; this receipt.

Validation: loop and publisher suites pass on PowerShell 7 and Windows PowerShell 5.1; six installer checks pass on both; 37/37 Node route/auth/reconciliation tests pass; PowerShell parser zero errors; diff check passes. Existing unrelated Python Maxim-auth failures not rerun. Temp fixtures outside repo. Inherited docs/Earl/index.html and docs/Jackson/index.html case-collision dirt excluded; original checkout dirty work untouched.

Remaining engineering gates: authenticated canonical intake and versioned atomic claim/skip audit, real pre-mutation integration; resolution/private evidence/UI/history/counts. All six acceptance criteria remain open. No credential blocker. Last end-to-end proof: none for actual resolution/worker skip. Expected cadence every selection/mutation; failure blocked/resolved launch or stale mutation; observer and observer health unintegrated. Recovery preserve state/evidence, reconcile canonical truth, approved hold; owner must not be routine monitor. Source-baseline tests do not establish operational health.

Recommended next action: review six-file source/report increment, retain draft/unmerged/undeployed status, implement isolated canonical adapter and pre-mutation proof before rollout. No Brian/account action required now. Queue scanned; existing assignments retained.
