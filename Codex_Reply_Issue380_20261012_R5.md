# Issue 380 — R5 installer safeguard prerequisite

Timestamp: 2026-10-12 America/New_York.
State: PR_OPEN / IN_PROGRESS. Persistent evidence: BUILT only.
Local branch: codex/issue380-r5-20261012.
Pushed review branch: codex/issue380-manual-resolution-20261011; existing draft PR https://github.com/Brian910cpr/910cpr-class-landers/pull/381.
Substantive commit: a8c146e8e5f9364378600a44d31cc99e881f66c8. Receipt commit is the subsequent pushed tip (discoverable in GitHub).

Execution acknowledged on originating issue before implementation. Full issue and comments, AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design and proof standards read. Latest owner direction retains #381 draft and asks safeguard-preserving source reconciliation; this is its narrow installer prerequisite, not full completion.

Root cause: installer unconditionally overwrote scripts containing installed-only safeguards. Added hash preflight of both files before all installer mutations; differing or invalid destinations and missing sources fail closed. No force bypass. No installed runtime or state was altered.

Exact intentional changed files:
- ops/scripts/Install-CodexWake.ps1
- ops/scripts/Test-CodexWakeInstallBaseline.ps1
- tests/test_codex_wake_install_baseline.ps1
- data/audit/issue380_installer_drift_guard_20261012.md
- Codex_Reply_Issue380_20261012_R5.md

Primary report: data/audit/issue380_installer_drift_guard_20261012.md. Prior preservation matrix: data/audit/issue380_launcher_safeguard_reconciliation_20261012.md. Review installer/helper/test together. No JSON contract changes.

Validation, processed locally:
- pwsh -NoProfile -File tests/test_codex_wake_install_baseline.ps1: PASS, six checks.
- Windows PowerShell 5.1 -NoProfile -File tests/test_codex_wake_install_baseline.ps1: PASS, six checks.
- Both report: PASS: 6 baseline/install checks; no launcher/task/process invoked.
- node --experimental-strip-types --test tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/owner_access.test.mjs: 37 tests, 37 pass, 0 fail.
- Parser.ParseFile of three PowerShell files: zero syntax errors.
- git diff --check and staged diff check: pass.
- Prior Python obsolete Maxim-auth failures not rerun; unrelated.

Deployment: locally persisted/validated, committed and pushed for draft review only. No installation, production mutation, merge or deployment. PR #372 untouched; #371 primary preserved. Original E:/GitHub/910cpr-class-landers dirty work untouched. In isolated worktree, inherited Windows case-collision docs/Earl/index.html and docs/Jackson/index.html remain unstaged. Temporary test fixtures retained outside repository under OS Temp; no intentional untracked repository files.

Exact outstanding engineering gates: installed/tracked source safeguard reconciliation; isolated fake-adapter no-launch/pre-mutation proof; authenticated canonical typed intake; transactional versioned atomic claim/skip audit; worker-safe adapter and actual pre-side-effect integration; resolution/version/audit migration, private evidence path, UI/history/counts and concurrency/upload/browser proof. No owner credential blocker. All six issue acceptance criteria remain open. Guard preflight is not atomic with replacement and does not approve installer execution.

No real end-to-end board resolution/worker skip proof yet. Cadence: each selection/mutation (install preflight on installer invocation). Failure: drift overwritten, blocked/resolved work launched, stale claims executing. Observer/observer health remain unintegrated/unproven. Recovery: preserve state, reconcile safeguards and canonical data before reviewed rollout. Brian must not become routine observer.

Next ChatGPT action: review substantive commit and exact report/test paths, retain draft/unmerged/undeployed status, continue full safeguard source reconciliation and typed atomic integration. No user/account action required. Open issue queue swept; other assignments preserved, no conflicting independent deep stream begun.
