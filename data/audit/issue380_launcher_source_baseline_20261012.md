# Issue 380 R6 — tracked launcher safeguard baseline

2026-10-12T06:49:00-04:00. Existing draft PR #381; no rollout.

## Scope and provenance

Reconciled `ops/scripts/Invoke-CodexWake.ps1` to the installed launcher inspected in R3/R4. Source and observed installed SHA256: DB81F14C5894B614FBD34FC6C9E2DDA4E24C9D3F8B5A17D70DFFE1918F7AB168. Only executable source was copied, never state/logs/credentials. This preserves local heartbeat, fetch-independent preflight, paginated owner-authored issue intake, explicit issue/no fallback, manual hold, retry backoff, session/final evidence, GitHub receipt lookup, post-run watermark and failure cleanup. It does not authorize issue comments or convert prose to commands. This prerequisite adds no Enrollware dependency.

The tracked loop was deliberately not replaced: installed loop additionally invokes a health publisher and process supervision whose source/installation dependencies require separate review. Installer R5 still refuses differing loop files. Do not install this branch. No installed file/state/process/task was changed or invoked.

## Validation

`pwsh -NoProfile -File tests/test_codex_wake_no_launch.ps1` and `powershell -NoProfile -File tests/test_codex_wake_no_launch.ps1`: each PASS, 5 isolated paths. Child processes invoke repository source with fake git/gh/Codex commands and temporary state, never installed launcher or real network. Checked check-only, manual hold, retry, active lease, explicit unauthorized/missing issue without fallback. Owner filtering excludes fake outsider P0; no run artifacts or started/failed status. Fixtures remain in OS Temp outside repository.

`pwsh -NoProfile -File tests/test_codex_wake_install_baseline.ps1`: PASS, 6 checks.
`node --experimental-strip-types --test tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/owner_access.test.mjs`: 37/37 passed.
PowerShell parser: both changed source/test files zero errors. `git diff --check`: pass.
No generators, database writes or builds. Existing unrelated Python Maxim-auth failures not rerun; no Python changed.

## Limits and next engineering

BUILT only. All six issue acceptance criteria remain open. This preserves observed safeguards rather than asserting they are sufficient: updatedAt eligibility, preferred task before P0, elapsed lease, ProofOnly hold bypass, and receipt lookup not tied to an atomic canonical claim remain known limitations. Receipt verification is handoff evidence, never business completion. Authenticated typed intake/versioned transactional claim/skip audit and actual pre-side-effect wiring remain unimplemented. Resolution/version/audit migration, private evidence and UI/history/counts still unfinished. No credential blocker or Brian action required; these are engineering gates.

Next: reconcile loop/publisher dependencies without installation; then fake-adapter no-launch/pre-mutation tests and reviewed canonical integration. Preserve #266 separate operator dispatcher boundary. Keep #381 draft; no merge/deploy authorization. #371 remains primary; #372 untouched.

Proof contract: expected outcome is resolved/unchanged-blocked work skipped at every selection and mutation with durable audit. No successful runtime end-to-end proof yet; observer/observer health unintegrated. Failure is blocked/resolved work launching or stale claims mutating. Recovery: preserve runtime evidence/state, approved hold, reconcile authoritative state, retry only after cleared gates. Brian is not an implemented routine monitor.

Queue swept via open issue list; existing assignments retained, no competing deep stream started. Original checkout untouched. Inherited worktree case-collision changes docs/Earl/index.html and docs/Jackson/index.html excluded from commits. Exact intended files: ops/scripts/Invoke-CodexWake.ps1; tests/test_codex_wake_no_launch.ps1; this report; unique root R6 reply.
