# Issue #371 — gated promised follow-up capture

Timestamp: 2026-10-13, UTC (receipt authored during this dispatch).
Branch: codex/issue371-taskui-20261013; existing PR #372 head feat/customer-learning-studio-20261010.
Substantive commit: 8fd58e47222ec63226f201fa9076cff43112c33a.
Base: 34ada8a24f8bab6b31f3a6a95ecfb858181e0af0.
Work-item state: IN_PROGRESS / PR_OPEN. Evidence: BUILT, validated locally with synthetic fixtures. Not deployed, not operationally PROVEN or MONITORED/HEALTHY.

## Execution and findings

Acknowledged actual execution on originating issue before implementation: https://github.com/Brian910cpr/910cpr-class-landers/issues/371#issuecomment-6154738796 . Continued existing Path A stream in isolated worktree E:/GitHub/910cpr-issue371-taskui-20261013. E: original checkout dirty work/broken references preserved; healthy existing repository supplied worktree. Existing assignments, launcher and monitors untouched. No third-party comments used as owner authority. Queue titles swept; no independent narrow change selected because this primary implementation was actionable and unrelated items have existing safety/dependency gates.

The previous task coordinator was unloaded. Studio now saves explicit promised follow-ups against a confirmed canonical case/interaction and reloads their stored state. No parallel task authority or Enrollware dependency added. Incumbent identity/history rationale remains docs/CUSTOMER_INTERACTION_STORAGE.md. Manual capture is a foundation/fallback, not completion of the owner's asynchronous extra-brain requirement.

## Exact changed files

- docs/admin/customer-interaction-studio.mjs — existing task coordinator integration, pending-task navigation/edit guards, same-envelope retry, terminal-conflict export, privacy clearing, paginated task recovery, fresh task lookup before call resume.
- docs/admin/customer-learning.html — default-off follow-up title/evidence/save/retry/stored-task controls; controller and module references versioned 20261013-followup1. Meta gate still disabled.
- tests/customer_interaction_studio_browser.py — synthetic task API fixtures and three new Chromium scenarios, including pagination through an empty first page.
- docs/CUSTOMER_INTERACTION_PATH_A_SAFETY.md — section “Default-off promised follow-up capture — 2026-10-13” contains full findings, transactional limitation, proof contract and next gates.
- This unique root Codex_Reply receipt (separate communication commit).

No generator, inventory, public class page, auth, CORS, schema migration, endpoint or infrastructure configuration changed. No local installation or NAS write. docs/Earl/index.html and docs/Jackson/index.html appear dirty due to existing Windows case-colliding tracked pages; preserved/excluded from staging. Original checkout unrelated work remains untouched. No intentional new untracked artifacts.

## Exact validation

PowerShell:

    $env:PGLITE_MODULE='file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js'
    $crmTests = @(Get-ChildItem tests/customer_interaction*.test.mjs | ForEach-Object FullName) + @('tests/admin_auth.test.mjs')
    node --experimental-strip-types --test @crmTests
    python tests/customer_interaction_studio_browser.py
    node --check docs/admin/customer-interaction-studio.mjs
    git diff --check
    git diff --cached --check

Node final output:

    1..61
    # tests 61
    # suites 0
    # pass 61
    # fail 0
    # cancelled 0
    # skipped 0
    # todo 0

Chromium final output:

    Ran 11 tests in 10.094s
    OK

Syntax/diff checks passed. Existing PGlite scratch dependency and installed Chromium reused; no dependencies installed. Browser/DOM tests prove default-disabled no requests, save/reload, atomic interrupt/recovery, task uncertain-save identical retry, conflict retention/export, lock privacy clearing, and task-read failure blocking resume. Existing Node task test composes coordinator/transport/actual handler/real local SQL RPC. New Chromium tests use synthetic API and owner-session fixtures; they do not prove genuine owner authorization, deployed Edge Runtime/PostgREST or production persistence. First browser run had one assertion reading visible text within collapsed details; corrected to text_content; final runs passed. No unrelated test failures found in the selected checks. Full output captured in local TEMP/issue371-taskui-node.txt, not committed as junk.

Supabase skill used. Current changelog, Data API security markdown, and November TLS cipher deprecation page fetched read-only via Invoke-WebRequest after web tool rejected markdown content type. No applicable custom-transport API change; no live database writes/metadata requests needed this increment.

## Safety boundaries and exact remaining blockers

Fresh task reads yield follow_up_due when pending/proposed/snoozed tasks exist and prevent a failed lookup from masquerading as no follow-up. HOWEVER task lookup and existing atomic two-interaction resume RPC remain separate transactions. Concurrent task creation/status changes between them are not fenced. This is an explicit production NO-GO condition, not a proven no-follow-up invariant. Add server-side task/resume consistency under shared locking before release.

Task completion/snooze controls and automatic saved-only NEXT remain unwired. Unconfirmed task fields exist only in memory; navigation guards do not guarantee recovery after process death. No automatic recognition/reminders, Gmail/Fieldy/Google Tasks, sends/refunds/reschedules/payments/eCards or policy promotion. Production Board stays read-only and is never marked complete.

Other existing production gates: usable backup/restore evidence and real owner-session UI/API/database save/reload/resume/conflict/recovery proof, followed by separate explicit rollout GO. Docker/WSL2/Synology installation is superseded for this milestone; do not request those prerequisites again. No merge, deployment, production migration/write, origin expansion or UI exposure authorized/performed. PR #372 remains draft.

## Proof/health contract

Expected on-demand outcome: saved owner obligation survives browser reload and remains pending when its call resumes. Last local synthetic proof: 2026-10-13, tests above. Genuine operational end-to-end proof: absent. Failure signals: uncertain/mismatched receipts, conflict, incomplete task pages, auth replacement, unconfirmed drafts. Local test runners observe regressions; no deployed CRM outcome observer or observer-health evidence exists. Recovery: identical request retry for uncertainty; retained envelope/draft export, fresh server review after terminal conflict. Brian must not be the routine monitoring layer. No HEALTHY claim.

## Next action

Continue existing #371/PR372 stream: implement and test transactional task/resume consistency fencing (including concurrent creation and disposition), then task status controls and saved-only NEXT, followed by genuine runtime/database recovery and backup/restore evidence. Review the four exact source/test/report paths above and substantive SHA. Keep gate disabled and PR draft/unmerged/undeployed. No owner/account action needed for safe local code/test continuation. A separate concrete rollout GO is required only after all safety evidence exists.

Push this receipt and intended changes to codex branch and existing PR372 head; verify receipt through GitHub contents API at final pushed SHA. Final pushed receipt SHA is reported on originating issue and dispatch response (avoids a self-referential commit hash).
