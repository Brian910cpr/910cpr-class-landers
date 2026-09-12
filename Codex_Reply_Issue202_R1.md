# Codex Reply — Issue #202 R1

- Assignment: GitHub issue #202, backend repository/source parity stabilization
- Timestamp: 2026-09-12T13:47:50-04:00
- Branch: `codex/issue-202-session-workspace-parity`
- Implementation head commit: `eb97be79cc3243c7b0d2f9c486ccf36189ad2795` (receipt is committed separately per `CODEX_HANDOFF_PROTOCOL.md`)
- Pull request: #207 — https://github.com/Brian910cpr/910cpr-class-landers/pull/207
- Work-item state: `PR_OPEN`
- Persistent-system evidence state: `BUILT` for the restored canonical source/deployment guard; the existing production endpoint remains independently `PROVEN` only to the anonymous boundary evidence recorded in PR #201.

## Findings and provenance

Facts:

- Current `main` did not contain `supabase/functions/session-workspace/index.ts`.
- The durable reference branch `origin/codex/schedule-integrity-stop-bleeding` contains the original endpoint and later schema-reconciled commits. Only backend runtime/projection artifacts were used; no dashboard, public UI, schedule, or generated-page changes were restored.
- Restored runtime provenance is `origin/codex/schedule-integrity-stop-bleeding@7f9788de55a`, where the endpoint had been reconciled to current-main canonical `class_sessions`, `registrations`, and `customers` tables.
- The exact deployment commit named in PR #201, `a8d44b79a7c92a0e95572279e75e0bdde9776caf`, remains unresolvable as a Git object in the current clone/ref set.
- Authenticated Supabase CLI metadata inspection found production `session-workspace` version 2 active with `verify_jwt: false` and bundle SHA-256 `7dd29aed182e3fe1880993adb44f2cbf869c05cc11eee9f1501408a7205d11fb`.
- An authenticated `supabase functions download` exported the deployed source without printing secrets or response data. Its file SHA-256 is `5253d0e8018705635ab9fc670e7d910d77a2bc1ce71b7217af731127277a7796`.
- The exported production source uses the older `landerware_sessions`, `landerware_registrations`, and related `landerware_*` tables. The restored repository source uses current-main canonical tables and therefore is not an exact source match.
- Both live and restored sources preserve the internal `x-maxim-session` authorization gate for detail and an anonymous-safe summary path.

Inference:

- Redeploying the restored canonical implementation would be a behavior/schema change, not a no-op parity redeploy. Issue #202 R1 explicitly prohibits that production action.

## Work performed and exact files

- `.github/workflows/verify-session-workspace-parity.yml` — CI for Node compatibility contracts and Deno projection tests.
- `scripts/deploy_session_workspace.ps1` — repository-owned deploy path pinned to the production project and `--no-verify-jwt`; requires an independently established matching live source SHA-256 before invoking the CLI.
- `supabase/functions/session-workspace/index.ts` — restored backend-only runtime using the current-main canonical participant/session model and internal detail authorization.
- `supabase/functions/session-workspace/projection.ts` — isolated committed-lifecycle projection contract.
- `supabase/functions/session-workspace/projection.test.ts` — lifecycle and truthful-count projection tests.
- `supabase/functions/session-workspace/deployment.json` — non-secret deployment contract and live parity evidence.
- `tests/fixtures/production_session_workspace_schema.json` — captured canonical production schema contract from the durable reference branch.
- `tests/session_workspace_contract.test.cjs` — compatibility, privacy-boundary, unknown-count, canonical-table, schema, and deployment-gate checks.
- `Codex_Reply_Issue202_R1.md` — this required durable receipt.

No generator ran and no generated/public pages were intentionally changed.

## Tests and checks

- `node --test tests/session_workspace_contract.test.cjs` — PASS, 6 passed / 0 failed.
- `npx -y deno test supabase/functions/session-workspace/projection.test.ts` — PASS, 2 passed / 0 failed.
- `npx -y deno check supabase/functions/session-workspace/index.ts` — PASS.
- `pwsh -NoProfile -File scripts/deploy_session_workspace.ps1 -ExpectedLiveSourceSha256 ('0' * 64)` — expected negative-path PASS: refused the mismatched hash before Supabase CLI invocation.
- `git diff --check` — PASS.
- Supabase metadata/source export — PASS; version/config and exact mismatch recorded above.

## Deployment and operational status

- Local validation: completed.
- Branch push: completed.
- PR: open, not merged.
- Production deployment status: **not deployed**.
- Reason: independently exported live source does not exactly match the canonical repository implementation, so the permitted no-op parity redeploy condition is false.
- Production was not mutated by this work.
- Last successful production boundary proof: the PR #201 receipt records anonymous summary success, unknown count preservation, and unauthorized resolve without participant detail after the 2026-09-11 deployment. R1 did not repeat private/live body probes because no deployment occurred.
- Monitoring: no new production monitor was added; this PR adds repository CI/preflight drift visibility. The live endpoint's ongoing health is outside the proof reached by this non-deployed R1.

## Known unrelated state

- The original checkout's unrelated dirty work was preserved and never staged.
- The isolated Windows worktree shows `docs/earl/index.html` modified because the repository tracks a case-colliding `docs/Earl/index.html` path. It was not staged, committed, or pushed.

## Remaining blocker and next safe action

The reviewed production endpoint and current canonical schema implementation are semantically divergent. Review PR #207 and choose one of two explicit follow-ups: (1) approve a separately scoped migration/redeployment of `session-workspace` to canonical tables with live compatibility probes, or (2) first restore the byte-exact exported live source as the canonical runtime and defer canonical-table migration. Do not deploy the R1 branch as a no-op.

User/account-level action required: PR review and the architectural choice above. No credential intervention is currently required; authenticated read-only Supabase inspection succeeded.
