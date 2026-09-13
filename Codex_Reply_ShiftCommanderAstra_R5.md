# ShiftCommander Astra R5 return receipt

- Dispatch: `SHIFTCOMMANDER_ASTRA_20260913_R1`, continuing after R4 as R5.
- Issue: https://github.com/Brian910cpr/910cpr-class-landers/issues/214
- Timestamp: 2026-09-13T10:05:00-04:00 (America/New_York).
- Work-item state: PR_OPEN checkpoint; full release BLOCKED. Issue #214 remains open.
- Evidence state: BUILT with synthetic local component/process proof. The operational system is not claimed PROVEN, MONITORED or HEALTHY.

## Exact work and review references

Target worktree: `E:\GitHub\shiftcommander_v2_codex_issue214_r5`.

Target branch: `codex/issue-214-auth-lifecycle-r5`.

Target commit: [`18ae1e6be8462b758f0d264a9f438de6ddcd6857`](https://github.com/Brian910cpr/shiftcommander_v2/commit/18ae1e6be8462b758f0d264a9f438de6ddcd6857).

Target draft PR: [ShiftCommander #7](https://github.com/Brian910cpr/shiftcommander_v2/pull/7), stacked on R4 draft PR #6 (`434d7b0650602a81263afb28ec39e464462f0331`), which is stacked on R3 draft PR #5. Readback verified the exact head, draft/open state and three-file scope. GitHub check-run list is empty; the test evidence below is local, not CI.

Primary report: [`docs/RELEASE_CHECKLIST_ISSUE214_R5.md`](https://github.com/Brian910cpr/shiftcommander_v2/blob/18ae1e6be8462b758f0d264a9f438de6ddcd6857/docs/RELEASE_CHECKLIST_ISSUE214_R5.md). It contains the defect, complete remaining release checklist, reproduction limits, exact commands, local log paths, recovery boundary and next review.

Exact intended target files:

1. [`server.py`](https://github.com/Brian910cpr/shiftcommander_v2/blob/18ae1e6be8462b758f0d264a9f438de6ddcd6857/server.py)
2. [`tests/smoke/test_durable_auth.py`](https://github.com/Brian910cpr/shiftcommander_v2/blob/18ae1e6be8462b758f0d264a9f438de6ddcd6857/tests/smoke/test_durable_auth.py)
3. `docs/RELEASE_CHECKLIST_ISSUE214_R5.md`

Courier worktree: `E:\GitHub\910cpr-class-landers_codex_issue214_receipt_r5`.

Courier branch: `codex/issue-214-shiftcommander-receipt-r5`, based on R4 courier `c2cf2e503b4aa931fd47d6c9dbc28dfdbfd82326`.

Only intended courier file: repository-root `Codex_Reply_ShiftCommanderAstra_R5.md`. The receipt references the separate substantive target commit above; its own commit is discoverable from the pushed courier branch and issue return comment. Filename checks found neither Reply nor Read R5 collisions in main or existing local/remote issue-214 courier branches. Prior receipts/acknowledgements were preserved; no Codex_Read marker was created or renamed.

## Root cause and work performed

R4's durable password-change route hashes exact text, but its login route trims surrounding whitespace. A successful password change can therefore prevent subsequent login with that same password. Shared-supervisor form login also fails; password reset silently trims the supplied temporary credential. Existing login/member HTML sends exact input values, so the defect is in the backend.

In the opt-in durable lane, login and reset now preserve exact password text. JSON password fields must be strings; null, boolean, numeric, list and object inputs return sanitized HTTP 400 before credential/session mutation. This covers login, reset, change and the compatibility alias. The legacy lane retains its existing input behavior. No new schema, dependency, staffing truth or browser asset was introduced.

This independently testable backend repair proceeds under the dispatch's safe-preparation instruction while preserving the explicit account/current-data and no-deploy gates. It does not activate durable authentication, change source authority or remove a production bypass.

## Validation

Final command results:

```text
python -B -m unittest discover -s tests/smoke -p test_durable_auth.py -v
Ran 48 tests in 78.888s
OK

Combined R3 regression suites (exact command in the target report)
Ran 58 tests in 31.016s
OK

Syntax OK: server.py
Syntax OK: tests/smoke/test_durable_auth.py
git diff --cached --check: exit 0
git diff 434d7b0650602a81263afb28ec39e464462f0331..HEAD --check: exit 0
```

Final aggregate: **106 passing test cases**, zero failures/errors/skips. This includes inherited scenarios; it is not 106 independent requirements. The 58 existing cases comprise serving auth 23, beta session 8, live-state store 12, and resolver legality/audit 15. Tests block external sources and isolate mutable files; no full test sweep, generator, frontend build or Worker rebuild ran.

Six new cases cover member password-change/login after module reload with spaces/tabs/nonbreaking spaces, rejected trimmed alternatives, shared-supervisor form login, exact reset hash plus old-session revocation, and malformed JSON leaving credentials/sessions unchanged. Before the repair, the three whitespace cases failed with five assertions, including two cascading failures after the first member lockout. An exploratory malformed-input run overlapped edits and is not presented as a separate controlled baseline. Both final suite runs completed successfully against the final source.

Local logs retained under `E:\GitHub\shiftcommander_v2_codex_issue214_r5\debug\auth_r5\`: `before_whitespace.log`, `before_nonstring.log` (exploratory), `after_whitespace.log`, `durable_final.log`, `r3_regressions.log`. These are ignored local diagnostics, intentionally not pushed. The target report preserves their exact meaning and final outcomes. No unrelated final test failure is known; unrun historical suites may still contain their previously documented problems.

## Persistence, recovery and monitoring evidence

The 48-case run re-executed the R4 synthetic Windows HTTP sequence: login -> own-availability save -> OS-process termination/restart -> saved readback -> SQLite backup -> logout -> credential-only restoration into a distinct store without old sessions -> old-token rejection -> fresh login/readback. Fixture processes stopped, and no persistent local URL remains running. The new whitespace scenario adds module-reload evidence, not a new OS-process scenario.

This does not prove real browser TLS/login, hosted D1 recovery, real staffing inputs, supervisor publication or view agreement. There is no verified last complete real-world availability-to-publication success. Latest local component proof is the final September 13, 2026 test run. Test cadence is per candidate change, not a recurring observer.

Malformed inputs return 400; R4 storage failures produce startup failure/503. These signals do not prove staffing freshness or complete publication health. No active end-to-end observer, observer heartbeat, monitored backup cadence or delivered escalation is established.

Recovery retains R4's documented boundary: preserve failed storage; privately validate/reconcile a consistent backup; initialize a new credential store without sessions; reconcile password changes since backup; prove staged login/write/restart before approved cutover. Do not blindly overwrite the serving database or remove `SC_AUTH_DB_PATH` as rollback. No recovery was performed on operational data.

## Exact blockers and next action

1. **Provider access:** prior Cloudflare Pages metadata read returned HTTP 401. Minimum Pages/Worker/binding metadata access is still unverified. No unchanged failing account-auth path was retried.
2. **Credential/storage authority:** no approved persistent disk/path, privately provisioned real credentials, signing material or verified inherited/deployed settings. R4's candidate requires those before activation. Current main's legacy auth remains a release blocker. Temporary-password `must_change_password` is written but not enforced as a restricted-session workflow; durable lifecycle audit, staged client behavior and hosted backup/rotation remain unfinished.
3. **Current staffing truth:** approved current ADR availability consent, demand, roster/certifications, unit-specific qualOp and calendar snapshot are missing/unreconciled. The last successful prior schedule evidence ended August 10, 2026. Seed/history is not authorization to schedule. ADR Calendar retains published-staffing authority.
4. **Complete release evidence:** real staged auth, lawful resolution, supervisor review/publication, matching member/supervisor/mobile/wallboard views, hosted restart/recovery and observer health remain unproven. Phone/SMS/email integration, sender identity, deduplication, ambiguity review and delivery/retry handling remain in the original release scope.

Prior evidence is preserved at target commits `286876e7d506bd127e14c2852f65c827815a8fa7:docs/RELEASE_EVIDENCE_ISSUE214_R2.json`, `bc483821ca011f668d6e080b2764eec38a1ed9bb:docs/RELEASE_CHECKLIST_ISSUE214_R3.md`, and `434d7b0650602a81263afb28ec39e464462f0331:docs/RELEASE_CHECKLIST_ISSUE214_R4.md`. Fresh GitHub fetch still shows main `67a3f88f1b54fa2ffbd285df7df969cea7837616`; that is not provider deployment or current service-health proof.

**ChatGPT next action:** review draft PR #7's three-file increment against R4, including the report and tests. Keep PR #5/#6/#7 draft/unmerged and #214 open. Coordinate restored provider metadata reads, approved private credential/persistent-storage configuration and current ADR input snapshot before staging activation. Then complete temporary-password lifecycle/client verification, hosted recovery and the availability-to-publication/view scenarios. This checkpoint is not a release or a later acknowledgement.

Account-level action is required for unavailable provider reads and private credential/storage setup; owner/staffing authority is required for the current approved inputs. No repeated broad confirmation request or new paid service was introduced. Queue sweep found no other open title with the exact `[CODEX]` marker besides #214; #116 remains the concurrency rule, and #171 is separate PDF work. No independent eligible backend dispatch was identified.

## Runtime, preservation and deployment state

Sanitized current local `turn_context`: `model=gpt-6-astra`, `2026-09-13T13:53:46Z`; installed `codex-cli 0.153.4`. This is local runtime evidence, not provider-side attestation. GitHub recorded [pickup](https://github.com/Brian910cpr/910cpr-class-landers/issues/214#issuecomment-5653714301) at `2026-09-13T13:56:54Z`.

R2's reusable `E:\GitHub\shiftcommander_v2_codex_issue214_r2\scripts\Start-AstraReview.ps1` was inspected and checked. At `2026-09-13T09:55:19.7635361-04:00`, `-CheckOnly` returned dispatcher lock held/inaccessible and `can_launch=false`. No second worker, lock/lease modification or machine-default change. After the legitimate lock/lease is released, it accepts `-RepoPath E:\GitHub\shiftcommander_v2_codex_issue214_r5` and selects Astra. The [official model documentation](https://learn.chatgpt.com/docs/models) and [CLI reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli) support the launch options; changing settings is not model evidence.

- **Persisted locally / changed in repo:** three intended target files; clean target worktree after commit.
- **Validated locally:** final 106 tests, two Python syntax checks and exact base-to-head diff/scope checks.
- **Pushed:** target commit and draft PR #7; this root receipt is the only intended courier addition and is to be verified by GitHub blob readback before exit.
- **Not merged / not deployed:** all release gates remain; no production writes, secret changes, calendar cutover, communications or service purchases.
- **Preserved:** original LanderWare dirty HTML/bytecode/untracked runtime state; original ShiftCommander calendar mirror, untracked code/data/backups and four unpublished commits; all prior worktrees/PRs. The new courier checkout also reports `docs/Earl/index.html` modified immediately after checkout, as in prior rounds; it remains unstaged/uncommitted. No unrelated cleanup occurred.
- **Intentionally local only:** ignored target `debug/auth_r5/` logs and existing unrelated dirty files. The retired `ops/handoff/next_task.md` was never used.
