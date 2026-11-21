# Issue 371 — completed follow-up restart checkpoint

Timestamp: 2026-10-11T11:42:00-04:00 (America/New_York)
Branch: codex/issue371-restart-followup-20261011
Existing draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/372
Substantive commit: 75cbd10651d05d5c7feaec5a95d31e31fede5d28
State: IN_PROGRESS / PR_OPEN; local Supabase integration BLOCKED.
Evidence level: BUILT, with locally validated synthetic SQL restart behavior.

## Execution and findings

Read full issue body/comments, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Acknowledged actual execution before implementation: https://github.com/Brian910cpr/910cpr-class-landers/issues/371#issuecomment-6110699488 . Continued existing PR head b86adc9d89f485a50c35e7b0ee52fdcb6187d388 in isolated named worktree E:/GitHub/910cpr-issue371-restart-followup-20261011. No new deep implementation stream, launcher, assignment changes or monitor changes.

Owner gate remains explicit: privileged Docker Desktop/WSL2 prerequisites and required reboot need approval; approved Synology UNC destination/security expectations have not been provided. Current Get-Command docker returned no executable, common C:/Program Files/Docker/Docker/resources/bin/docker.exe returned False, and wsl --status returned exit 1 stating Windows Subsystem for Linux is not installed. No installation, privileged operation, NAS write, production migration, origin expansion, paid staging project, merge or deployment attempted. Prior NAS/path findings reused; no arbitrary path guessed.

## Safe backend progress and exact changed files

- tests/customer_interaction_restart.test.mjs: added disk-backed synthetic completed-task restart test against the three existing CRM migrations. Lost-response create/completion retries preserve their immutable receipts without resetting current completion; actor conflicts, stale versions and duplicate source import are rejected. Completion/provenance and two-event audit survive reopen; no pending task remains. anon/authenticated cannot read task/audit or invoke mutation RPC.
- docs/CUSTOMER_INTERACTION_LOCAL_STAGING.md: documented this evidence and delayed historical-response boundary.
- Codex_Reply_Issue371_TaskRestart_20261011_R1.md: this unique required repository-root receipt.

No application/schema/auth/UI changes. This advances regression evidence for native LanderWare-owned task lifecycle without adding an Enrollware dependency or alternative task catalog. Browser interpretation of old receipts remains unproven and must refresh current authoritative state.

## Exact validation

Cached scratch dependency reused (no install or production dependency): @electric-sql/pglite 0.3.14 at C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js.

```powershell
$env:PGLITE_MODULE='file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js'
node --check tests/customer_interaction_restart.test.mjs
node --experimental-strip-types --test tests/customer_interactions.test.mjs tests/customer_interactions_sql.test.mjs tests/customer_interruptions_sql.test.mjs tests/customer_interaction_pagination.test.mjs tests/customer_interaction_restart.test.mjs tests/admin_auth.test.mjs
git diff --check
```

Output: tests 37; suites 0; pass 37; fail 0; cancelled 0; skipped 0; todo 0; duration_ms 11440.1041. Node syntax and diff checks passed. Synthetic temporary database removed by test finally blocks. No remote database/API/browser proof, power-loss or concurrent-process proof is claimed.

## Persistence/deployment and unrelated work

Changes persisted locally and committed. This receipt and substantive changes are intended for push to the named codex branch and existing PR372 branch with normal fast-forward push only; final issue checkpoint records actual pushed SHA. PR372 remains draft/unmerged/undeployed. No generated builders ran. Windows case-collision docs/Earl/index.html and docs/Jackson/index.html appear modified in the new worktree and were excluded. Original E: dirty files, caches/temp artifacts and broken-reference checkout preserved. No Codex_Read file manufactured. No ops/handoff/next_task.md use.

Queue sweep inspected open issue titles; existing P0 assignments remain preserved. No independently verified narrow backend quick win was identified outside this CRM test, so no competing assignment was claimed.

## Persistent proof contract and exact next step

Expected result: owner-approved follow-up disposition survives reload and retry without duplicate/reopened work. Cadence: on-demand per save. Last successful bounded SQL proof: this run at 2026-10-11 approximately 11:41 Eastern, 37-test output above. Full owner-session -> browser -> API -> persisted storage -> reload/resume proof has never been established. Failure: denied/failed write, version conflict, missing receipt or mismatch with current record. Operational CRM observer and observer health are not yet established; no MONITORED/HEALTHY claim. Existing launcher supervision is untouched and not re-audited here.

Recovery: retain pending request/draft; retry identical request after transient failure; reload/reconcile current versions after conflict or historical response; never automatically overwrite current state. Escalation: privileged runtime installation/reboot and NAS folder/security approval require Brian. Ordinary backend repairs remain Codex work.

Next: obtain explicit owner prerequisite approval on #371 and approved Synology UNC destination without secrets; then provision localhost-only synthetic isolated Supabase/auth/Edge environment and validate current migrations before connecting the feature-flagged Studio UI. Keep production unchanged. ChatGPT should review the two changed paths and this receipt, preserve the existing #371/#372 stream, and surface the exact owner gate instead of repeating cloud-preview authorization requests. No routine CRM health checking should be assigned to Brian.
