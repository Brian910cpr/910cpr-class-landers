# Issue 380 R5 — installer drift refusal

2026-10-12, America/New_York. Review in existing draft PR #381; no rollout.

## Change and evidence

R4 found unconditional replacement of installed-only safety behavior. `ops/scripts/Install-CodexWake.ps1` now checks both source/destination pairs with `ops/scripts/Test-CodexWakeInstallBaseline.ps1` before directory creation, copying, state seeding, task removal, startup changes or process launch. Missing sources, non-file destinations and differing SHA256 hashes throw. Error identifies path and both hashes. There is deliberately no force bypass. Fresh installs and identical files pass this preflight; this does not approve installation or reconcile source drift.

`tests/test_codex_wake_install_baseline.ps1` uses temporary local fixtures: absent destination, identical files, differing installed file preserved, missing source rejected, full installer rejects before copy/state seed, and second-file drift rejects. No installed script, task or process is invoked. Temporary fixtures are retained under OS Temp, outside Git. Test passed under pwsh and Windows PowerShell 5.1: `PASS: 6 baseline/install checks; no launcher/task/process invoked`. Parser checks of all three changed PowerShell files: zero errors. Existing node strip-types route/auth/reconciliation suite: 37 passed, zero failed. `git diff --check`: pass after removing extra EOF blank line.

## Scope and remaining gates

This is a safeguard-preserving prerequisite, not the requested full source reconciliation. Runtime selection is unchanged. Hash comparison is a preflight, not an atomic installer transaction: another process changing files after preflight is an unresolved rollout concern. Do not run installer while reconciling. Source baseline still lacks installed safeguards; authenticated typed intake, versioned atomic claim/skip audit, pre-mutation wiring, resolution/version/audit migration, private evidence and UI/history/counts remain unfinished. All six issue acceptance criteria remain open. No owner credential blocker; no Brian action required for review.

Evidence level: BUILT only; no end-to-end board resolution or installed worker skip proof. Expected safety window: every install and every future selection/mutation; failure: drift overwritten or resolved/blocked work launched. Observer/observer health for runtime reconciliation unproven. Recovery: preserve installed files/state, review drift and rollout separately. Owner is not an implemented monitoring substitute.

Original dirty checkout untouched. Worktree inherited Windows case-collision changes `docs/Earl/index.html` and `docs/Jackson/index.html`; neither staged. No generators, production data writes, installation, merge or deployment. #371 remains primary; #372 untouched. Open issue queue swept; other assignments retained, no unrelated deep stream started. Existing prior Python Maxim-auth failures not rerun; no Python changed.

Next engineering: reconcile all R4 installed-only safeguards into reviewed source and add fake-adapter no-launch tests; then authenticated typed transactional integration and actual pre-mutation proof. Review this guard before any installer use.
