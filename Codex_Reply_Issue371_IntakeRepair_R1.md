# Issue #371 — P0 intake diagnostic and first CRM storage increment

- Timestamp: 2026-10-10, America/New_York (UTC-04:00).
- Branch: `feat/customer-learning-studio-20261010`; existing draft PR #372.
- Substantive commit: `07382b725e85cc71f34930cf38540a92cdd65caf`.
- Work-item state: IN_PROGRESS / PR_OPEN. No production merge or CRM deployment.
- Intake evidence state: PROVEN for one real detection-to-execution cycle; sustained independent monitoring remains unproven.
- CRM evidence state: BUILT, validated locally; not CONNECTED to the browser or deployed.

## Findings: facts, inference and limits

The executable intake already existed in `ops/scripts/Invoke-CodexWake.ps1`, `Start-CodexWakeLoop.ps1`, and `Install-CodexWake.ps1`. Installed copies live in `%LOCALAPPDATA%\910CPR\CodexWake`. The current user's Startup file `910CPR Codex Wake.cmd` launches that loop every logon; the loop polls every 15 minutes and invokes `codex exec` against authorized `[CODEX]` issues.

At investigation time there was no running Codex Wake loop, no registered Codex Wake scheduled task, and its last check was `2026-09-15T17:45:06.4300366-04:00`. Its last recorded execution was #214, failed at `2026-09-15T16:29:55.1044057-04:00`. The log explicitly contained `You've hit your usage limit` and an unrelated Cloudflare MCP OAuth startup error. These are historical failures, not evidence of current exhaustion. The October 10 real proof succeeded with existing credentials. The precise event that terminated the old loop is not established by its logs.

The Startup launcher still pointed at `E:\GitHub\910cpr-class-landers`, recorded as corrupted in #255. The clean sibling was also divergent/dirty (ahead 10, behind 264 at inspection), so neither checkout was reset, cleaned or repurposed. The repaired launcher points at the separate existing-PR checkout `D:\Users\ten77\Documents\2020 -_ 2025 & Enrollware\910cpr-customer-interaction-studio`.

All 16 repository GitHub Actions workflows were active but none launched Codex intake. Repository hooks list was empty. Local Codex automations contained only the paused #157/#297 monitor. The running CYBERPC-01 worker accepts typed `[WORKER]` jobs, not `[CODEX]` implementation instructions; its allowlist was preserved. Owner confirmed that enabled ChatGPT Scheduled Tasks “910CPR Delta Watch” and “910CPR Deep Stability Review” are supervisors, not launchers. Neither was changed or duplicated.

## Repairs persisted locally and changed in repo

- Reused the existing launcher and Startup registration; preserved all 16 prior `completed_issue_updates` entries and existing assignment history. Selected #371 as the preferred primary continuation.
- Queue discovery no longer waits on a broad Git fetch from the damaged checkout. It paginates open issues and filters the literal title prefix and `Brian910cpr` author.
- Heartbeat now writes local runtime state, never the retired `ops/handoff/` mailbox.
- Loop cycles run in child PowerShell processes. Cycle exit/failure cannot directly exit the persistent supervisor.
- The exclusive worker lock covers execution. Manual sessions can hold automatic dispatch with `manual-hold.json`; this diagnostic used that hold while editing.
- Failed runs release stale task state and back off one hour. Actual session ID, JSONL events and final response are retained. Normal runs must name a receipt and commit resolvable through GitHub before they are marked processed.
- Installer preserves assignment state when selecting a preferred task and quotes paths containing spaces. Original installed scripts, state and Startup entry were backed up under the existing local state directory before replacement.

## Real end-to-end proof

Command, from the existing PR checkout:

```powershell
& .\ops\scripts\Invoke-CodexWake.ps1 -RepoPath (Get-Location).Path -IssueNumber 371 -ProofOnly
```

Result: exit 0, `last_launch_status=proof_completed`, actual session `01a127a2-d6b7-7411-977b-fb746dafefde`. The session fetched #371, verified the owner, read repository instructions, posted its bounded acknowledgment, and returned the correct existing PR and next storage milestone. It did not edit implementation or consume #371's processed watermark. This was a real Codex inference/execution session, not a mock or comment-only test.

Durable compact evidence: `data/audit/issue371_intake_proof.json`, including event types, final response and raw local event path. Acknowledgment: https://github.com/Brian910cpr/910cpr-class-landers/issues/371#issuecomment-6102175393 . Original local JSONL and final response remain in `%LOCALAPPDATA%\910CPR\CodexWake`.

Repaired persistent loop PID 27964 started `2026-10-10T17:10:32.6593590-04:00`; its first check returned zero at `2026-10-10T17:10:37.1735316-04:00`. A manual implementation hold was correctly observed. Startup is installed for future logons. The hold is removed when this session yields, so the next ordinary loop check can continue #371.

## CRM continuation

Read-only live Supabase schema discovery succeeded for project `wktwgcnwdvbebcobgyey`; no customer interaction/case/task tables existed. The new additive migration reuses canonical `landerware_people` with nullable verified linkage, distinct cases/interactions/follow-up tasks, immutable save receipts, server-derived actor provenance, idempotency and optimistic versions. Tables deny direct anon/authenticated access; the service-role RPC is SECURITY INVOKER. The Edge Function requires the existing revocable owner browser session and denies corporate/legacy automation credentials.

The existing UI and read-only Production Board attention integration are preserved. No new CRM UI, scheduler, person catalog, external task sync, autonomous customer action or production data mutation was introduced.

## Changed files / review targets

1. `ops/scripts/Install-CodexWake.ps1`
2. `ops/scripts/Invoke-CodexWake.ps1`
3. `ops/scripts/Start-CodexWakeLoop.ps1`
4. `ops/scripts/README_CODEX_WAKE.md`
5. `data/audit/issue371_intake_proof.json`
6. `docs/CUSTOMER_INTERACTION_STORAGE.md`
7. `supabase/migrations/20261010210607_customer_interaction_storage.sql`
8. `supabase/functions/customer-interactions/handler.ts`
9. `supabase/functions/customer-interactions/index.ts`
10. `tests/codex_wake.test.mjs`
11. `tests/customer_interactions.test.mjs`
12. `tests/customer_interactions_sql.test.mjs`
13. This immutable receipt.

## Validation and exact meaningful results

- PowerShell parser: PASS for all three launcher scripts.
- `node --test tests/codex_wake.test.mjs`: tests 4, pass 4, fail 0.
- `node --experimental-strip-types --test tests/customer_interactions.test.mjs tests/customer_interactions_sql.test.mjs`: tests 10, pass 10, fail 0. PGlite 0.3.14 was scratch-installed outside the repo; actual SQL/functions/grants ran locally. Coverage includes save/reload, many interactions per case, paused/resumed state, original note history, retry dedup, changed-payload conflict, stale tab writes, source dedup, failed-write rollback, private table/RPC access and append-only audit grants.
- `node --experimental-strip-types --test tests/admin_auth.test.mjs`: tests 10, pass 10, fail 0.
- `deno check supabase/functions/customer-interactions/index.ts`: PASS using the cached local Deno binary.
- Real CLI intake proof: exit 0 and actual session/ack/final response, as above.
- No broad generator, public-site rebuild, merge or production deployment was run.

## Remaining boundaries, health contract and owner actions

Expected cadence: 15 minutes while CyberPC is awake and the Windows user session is running. Last full intake proof: October 10, session above. Staleness: local check older than 30 minutes, absent loop process, persistent manual hold, or failed run. Observer: loop state and local logs; existing ChatGPT supervisors remain the intended escalation layer, but their ability to read current local health is not proven. Therefore **not MONITORED or HEALTHY**, and not an always-on cloud service. A crash/logoff/sleep boundary remains; logon Startup restores execution. Recovery is inspect active assignments/locks, then restart this same installed loop. Do not install a competing scheduler.

No owner authorization or credential action is required for the currently proven local execution path. If a future run reports login failure, sign in locally with `codex login` or `gh auth login` according to the exact failing tool; never put a token in GitHub. Current proof succeeded, so do not ask Brian to reauthorize Cloudflare merely because the September log mentioned it.

Account-side follow-up: the two existing ChatGPT watchers need an independently verifiable launcher-health signal before claiming unattended service is monitored. Their settings/access are outside this session's verified surface. Do not create duplicates or assert that their monitoring works.

CRM is not complete: follow-up task endpoints, atomic interrupt/new-call transitions, UI autosave/error/retry/conflict handling, retention/deletion policy, isolated preview origin/auth, and remote preview validation remain. The browser is still a clearly labeled tab-local prototype. No production Supabase migration or Edge Function deployment occurred. Preview setup/readiness must precede any deployment; do not merge draft PR #372 without authorization.

Next concrete action for ChatGPT/Codex: review the above code/schema/tests in PR #372, then continue that same PR with task and interrupt transaction APIs and existing UI integration. Read the originating issue again before returning; the launcher's post-run watermark can otherwise include owner comments arriving during execution. Preserve all other assignments.

Unrelated files intentionally unstaged: `docs/Earl/index.html`, `docs/Jackson/index.html` (present immediately after checkout; origin unknown, not part of this assignment). `supabase/.temp/cli-latest` is a CLI-generated local artifact intentionally untracked. Scratch test dependency/runtime files remain outside the repo. No cleanup/reset was performed.
