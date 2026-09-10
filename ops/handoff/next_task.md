# Next Codex Task

Status: READY - P0

## P0: Close the ChatGPT <-> Codex loop permanently

The repo handoff files already exist, but the system is incomplete if Codex only reads them when Brian manually opens Codex.

Your FIRST task is to install/repair a durable CyberPC-side dispatcher so Codex checks this repository on a regular cadence without Brian having to launch or prompt it manually.

### Required behavior

1. On CyberPC, determine whether any existing watcher, Windows Scheduled Task, service, startup task, or Codex automation already polls this repo. Do not create a duplicate if one exists. Repair the existing mechanism if present.
2. If no durable watcher exists, create one using the simplest reliable Windows-native mechanism available on CyberPC.
3. The watcher must periodically:
   - `git fetch` / update the local `E:\GitHub\910cpr-class-landers` working copy safely.
   - inspect `ops/handoff/next_task.md` and the LanderWare Production Board work queue.
   - start/continue Codex work only when there is actionable work.
   - avoid overlapping duplicate Codex runs with a lock/lease.
   - write heartbeat/status data into `ops/handoff/` so ChatGPT can tell whether the worker is alive, when it last checked, what it is doing, and why it stopped.
   - write completed work summaries/results back into the existing handoff files and commit/push them.
   - continue consuming eligible Production Board work until it reaches a genuine Brian decision, blocked credential/account action, unsafe ambiguity, or empty queue.
4. The watcher cadence should be modest and credit-conscious, not constant. Prefer roughly every 15 minutes unless an existing architecture has a better established cadence.
5. A failure on one production item must not kill the entire worker. Record the failure, mark/escalate the item appropriately, and continue with unrelated eligible work.
6. Do not let Cloudflare/GitHub deployment noise permanently stop the queue. Deduplicate repeated failures by root cause and keep processing work that is not blocked by that root cause.
7. Add a visible heartbeat file, suggested path: `ops/handoff/codex_heartbeat.json`, containing at minimum:
   - `last_check_at`
   - `worker_state` (`idle`, `working`, `blocked`, `error`)
   - `current_task`
   - `last_completed_task`
   - `last_commit`
   - `next_check_due`
   - `blocked_reason` when applicable
8. Add installation/repair documentation and an idempotent setup script in `ops/scripts/` so this mechanism can be recreated without Brian manually reconstructing it.
9. Verify the watcher is actually installed/enabled on CyberPC and performs at least one successful repo check before calling P0 complete.

### Acceptance test for P0

P0 is NOT complete merely because scripts exist in GitHub. It is complete only when CyberPC has an enabled recurring mechanism and a heartbeat proves it has checked the repo automatically.

## P1: Columbus County 2025 EMS protocol ZIP

After P0 is verified working, execute GitHub Issue #171 completely:

Source:
https://www.columbusco.org/2025-ems-protocols

- Use CyberPC/browser automation to collect every individual 2025 EMS protocol PDF from the live page.
- Preserve the original PDFs unchanged.
- Verify the actual live count rather than assuming 89.
- Create `MANIFEST.txt` with source URL, retrieval date, final count, filenames, and original URLs.
- Build the ZIP.
- Publish it at exactly:
  `https://www.910cpr.com/cc2025ems.zip`
- Verify HTTP 200, valid ZIP, and final PDF count.
- Report the deployed commit/PR and verified public URL.

## P2: Resume autonomous Production Board consumption

Once P0 and P1 are complete, continue working eligible LanderWare Production Board items autonomously according to priority and dependencies. The Production Board is a work queue, not a passive backlog. Do not require Brian to manually restart Codex between ordinary items.

## Required Codex write-back

- Write summary to: `ops/handoff/latest_codex_report.md`
- Write validation output to: `ops/handoff/latest_validation_run.txt`
- Write git status/log to: `ops/handoff/latest_git_status.txt`
- Write a short ChatGPT bundle to: `ops/handoff/latest_chatgpt_bundle.md`
- Update the heartbeat/status file during each run.
- Do not require Brian to paste giant logs.
- Do not broaden unrelated scope.
- Stop for Brian only when a real decision/credential/account-level action is necessary.
