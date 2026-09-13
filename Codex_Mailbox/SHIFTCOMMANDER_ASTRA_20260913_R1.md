# Owner dispatch: ShiftCommander Astra release work

- Dispatch ID: SHIFTCOMMANDER_ASTRA_20260913_R1
- Owner instruction: Brian explicitly asked ChatGPT to deliver this through the existing GitHub handshake instead of making him copy/paste it to PC Codex.
- Transport repository: Brian910cpr/910cpr-class-landers, because the installed CyberPC wake worker polls its open [CODEX] issues.
- Implementation repository: Brian910cpr/shiftcommander_v2.
- Target local checkout: E:\GitHub\shiftcommander_v2.
- Requested model: gpt-6-astra. Verify actual runtime model before claiming an Astra review.

## Dispatch routing and receipts

Use this repository only for the existing dispatch/receipt transport. All ShiftCommander product code, operational data, and implementation PRs belong in the ShiftCommander repository and follow its AGENTS.md and confirmed scheduling rules. Do not implement EMS staffing inside LanderWare or import LanderWare class rules into it.

The worker may initially launch in E:\GitHub\910cpr-class-landers with its default model. Read the full originating issue, this handoff, and the target repository instructions, then continue the assignment in the target checkout with Astra through supported model controls. Verify installed client support and account availability. Do not merely add the word Astra to a prompt or report a configuration change as model-switch proof. Preserve permissions and account controls.

Honor the existing single-worker dispatcher lock/lease and any newer owner concurrency rules, including issue #116. Advance this as a coherent assigned workstream; do not create competing launches or change the machine-wide model default for unrelated tasks. Do not stop an active legitimate task without saving its state. If Astra/target access is blocked, complete safe inventory and return the precise blocker through this handshake; do not silently substitute another model for the requested review.

Post a pickup acknowledgement on the originating [CODEX] issue with dispatch ID, timestamp, target checkout/branch, active model if observable, and first action. Keep substantial progress and blockers on that issue. After the first meaningful review/fix checkpoint, push a unique root Codex_Reply_ShiftCommanderAstra_R1.md to the transport repository, referencing target-repository branch, exact commits/PRs, tests, actual model evidence, and next action. Subsequent receipts use R2, R3, etc., after checking collisions. A transport receipt may contain links and non-sensitive operational summaries only. Never create Codex_Read_*; acknowledgement belongs to ChatGPT. Keep the task open until the requested release state is evidenced, or explicitly report BLOCKED. Do not revive the retired ops/handoff/next_task.md channel.

The owner is not the courier. Use the established GitHub loop for instructions, questions, status, and receipts. Do not require him to re-paste this file into a PC session when the supported local launch path is available.

---

# ShiftCommander: PC development and Astra release review

Resume and finish my existing ShiftCommander / Shift Supervisor system for ADR-FR. The goal is a dependable release that receives member availability and produces an explainable schedule that meets company staffing requirements while honoring member preferences wherever possible. Member trust matters. Work toward a usable release, with evidence that the complete workflow works.

1. Establish the correct local project.

   Start at `E:\GitHub\shiftcommander_v2`, associated with `Brian910cpr/shiftcommander_v2`. Verify this path and remote on this PC. If the folder has moved, locate the existing checkout before cloning. Keep ShiftCommander separate from LanderWare, 910CPR, and Enrollware.

   Inspect `git status`, branches, worktrees, recent commits, remotes, and unfinished Git operations before changing anything. Preserve uncommitted code, availability, calendar mirrors, backups, and operational data. A previous checkpoint used `codex/base44-worker-consolidation` and a separate `shiftcommander_v2_main_deploy` worktree. Treat these as leads to verify. Compare current local work with GitHub and preserve work that has not been pushed. Do not reset or replace the checkout to make it clean.

2. Arrange an actual Astra review.

   Use `gpt-6-astra` for the fresh assessment, difficult corrections, and final release review. Inspect the installed Codex version and available model controls. Configure a project-specific launch command or supported setting so future ShiftCommander review runs select Astra automatically. The documented CLI launch command is `codex -m gpt-6-astra`.

   Verify the active model from runtime/session information where available. Changing a configuration file does not prove that the current session switched models. If the current session cannot switch, save the handoff and give me the exact launch or picker action needed. Do not describe another model's work as an Astra review. If Astra is unavailable to this installation/account, state the precise blocker and continue useful preparation. Use Astra as the development/review model; adding an AI dependency to the scheduling application requires a separate product reason.

3. Recover the complete requirements and challenge previous conclusions.

   Read `AGENTS.md`, `docs/PROJECT_BOUNDARIES.md`, `docs/CONFIRMED_SCHEDULING_RULES.md`, `RULES.md`, `DATA_CONTRACT.md`, the migration and overlay documents, and existing handoff/audit reports. Examine the actual frontend, Worker, resolver, persistence, tests, and deployment configuration. Verify old claims against current behavior. Preserve proven behavior while investigating defects and unfinished features.

   Build one concise release checklist showing each requirement, its implementation location, evidence, and remaining blocker. Earlier checkpoints reported development authentication and deployment gaps; establish whether those gaps still exist. Identify expired rollout dates and stale configuration, including the August 31, 2026 display transition.

4. Establish trustworthy data flow.

   Map member identities, qualifications, per-unit driver permissions, availability, staffing demand, assignments, locks, and audit records to their actual sources and write paths. Reconcile local JSON, `data-seed/`, D1 overlays, Google Calendar imports, and static fallbacks. Prevent silent data loss, duplicate assignments, and stale schedules appearing current.

   Preserve ADR Google Calendar's existing published-staffing authority during this work. Verify the documented integration and publication rules before proposing a cutover. Keep Quick Test Mode separate from Real Mode. Never infer a remote database or deployment target from its name alone.

5. Enforce the established staffing rules.

   Use the confirmed rules for the 0600–1800 / 1800–0600 shifts, 2-2-3 backbone, partial coverage, unit demand, ALS coverage, certifications, unit-specific `qualOp`, hours, overtime, preferences, fairness, publishing, locks, and swaps. Keep scoring and validation server-side.

   Preserve Preferred, Available, Do Not, and Blank availability states. Blank means do not schedule automatically, including FT baseline assignments. Historical availability is suggestion data only. Reserve members volunteer through explicit availability. A driver license alone does not establish qualification to drive a particular unit.

   Respect hard constraints and protected assignments. Preserve valid published assignments, minimize reassignment, and explain exclusions. When demand cannot be met legally, keep required seats visibly OPEN and explain the shortage. Never hide the unmet demand or silently relax a hard rule.

6. Deliver the complete core workflow.

   Members must be able to authenticate, save and revise availability, see their shifts and the full schedule, see who is working now, and use the approved open-shift, release, and swap workflows. Supervisors must be able to define staffing demand, review shortages and explanations, make protected overrides, manage publication, and inspect changes. Supervisor, member, mobile, and wallboard views must agree on the same authoritative schedule.

   Verify real authentication, member/supervisor authorization, write validation, persistence after restart, audit history, export, backup, and recovery. Member accounts must only edit their own permitted data. Development authentication and misleading save confirmations are release blockers.

7. Preserve phone, SMS, and email intake in the product scope.

   Inventory the intended and existing connections. Where connected, normalize incoming availability and requests into the same validated workflow, retaining sender identity, timestamps, source records, and duplicate protection. Ambiguous messages need clarification or review before changing availability or assignments. Account for delivery failures and retries. Identify missing access or provider decisions explicitly. Establish the dependable core workflow first, then complete the agreed integrations without losing them from the release checklist.

8. Make the system usable on this PC.

   Provide a verified local development setup and simple Windows start/stop commands or launchers, with exact local URLs. Check package scripts and project instructions before selecting install, migration, test, and startup commands. Document required services and configuration. Prove the app starts again and retains saved data. Keep secrets and operational member records out of public artifacts.

9. Verify the release with meaningful scenarios.

   Test the full availability → resolver → supervisor review → publication path in a controlled environment, including refresh/restart persistence. Cover blank availability, partial and overnight shifts, conflicting assignments, missing driver qualifications, unavailable ALS coverage, locked assignments, overtime boundaries, swaps, duplicate submissions, unauthorized edits, stale-source failures, and backup restoration. Validate timezone and daylight-saving behavior. Confirm the existing audit artifacts still generate and explanations match the decisions.

   Report each result separately as locally tested, staging tested, deployed, or unverified. A passing build alone is not release evidence.

10. Continue implementation and maintain a verifiable handoff.

    Make reversible development decisions and targeted fixes without repeatedly asking permission. Use the existing GitHub handoff convention where present. Record the task, branch, commit, tests, remaining blockers, and next action. Push reviewable changes and open a PR under existing authorization and access controls. Verify that handoffs were received and results returned before claiming the bilateral loop works. A file on GitHub does not itself wake a sleeping PC.

    Ask focused questions when an answer changes staffing policy, release scope, paid services, production authority, or another genuine owner decision. Complete independent work while awaiting answers. Honor existing authorization for deployment and communications; prepare a concrete release candidate before any remaining approval request.

    Begin with a brief verified status and the first release blocker, then work through the checklist. Finish with the working local URLs and launch commands, code/PR references, test evidence, deployment state, recovery instructions, and any exact decision still needed from me.

Model-control reference: [Official OpenAI model selection documentation](https://learn.chatgpt.com/docs/models). Model availability depends on the client, sign-in method, account access, and rollout.
