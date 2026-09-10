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

## P1: Backend stabilization gate

Do not begin customer-facing expansion or the Columbus County ZIP task while the backend failure queue below is unresolved. Work these incidents in order, deduplicating repeated deployment noise by root cause.

### 1. Issue #172 - public refresh can publish with broken links

Execute GitHub Issue #172 completely before moving on.

Required outcome:
- reproduce and capture all current BROKEN rows from `scripts.audit_sitewide_links`;
- fix the underlying generator/static-source causes rather than suppressing findings;
- make canonical public publication fail closed when BROKEN > 0;
- preserve CSV and Markdown audit output as GitHub Actions artifacts even on a strict audit failure;
- add a regression test proving an intentionally missing internal target blocks strict publication;
- verify `Broken: 0`, public validation green, and GitHub Pages green before closing #172.

### 2. Issue #164 - persistent Cloudflare Pages instant failure

After #172, resume GitHub Issue #164. GitHub Pages is healthy on the same commits where Cloudflare Pages instant-fails, so do not treat duplicate Cloudflare check failures as separate incidents.

Use CyberPC/browser access if available to open the failed Cloudflare production deployment and capture the first actual Cloudflare error line/error code. Continue repository-side diagnosis and repair from evidence, not guesses. If Cloudflare authentication, account permission, or an IP-restricted token genuinely blocks access, record the exact blocked action and required account-level setting for Brian rather than a generic "check Cloudflare" request.

Required outcome: smallest reversible fix, then Cloudflare Pages and GitHub Pages green on the same commit, or a precise documented Brian-only account action if that is the true blocker.

### 3. Issue #167 - Windows case-collision cleanup

Then execute GitHub Issue #167 to eliminate tracked case-only path collisions without breaking legacy uppercase URLs, canonical routing, redirects, or SEO behavior. Verify Windows checkout/build cleanliness and public-route compatibility.

### Backend gate acceptance

Do not advance to customer-facing work until:
- source-integrity checks are green;
- real scheduled admin/public refreshes remain healthy;
- canonical public refresh is fail-closed on broken internal navigation and currently reports `Broken: 0`;
- GitHub Pages is green;
- Cloudflare #164 is either repaired and green or is stopped on one precise Brian-only account action that has been written back to the handoff;
- #167 no longer leaves Windows-hosted automation vulnerable to case-only path collisions.

## P2: Columbus County 2025 EMS protocol ZIP

Only after the backend stabilization gate above is satisfied, execute GitHub Issue #171 completely:

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

## P3: Resume autonomous Production Board consumption

Once P0, P1, and P2 are complete, continue working eligible LanderWare Production Board items autonomously according to priority and dependencies. The Production Board is a work queue, not a passive backlog. Do not require Brian to manually restart Codex between ordinary items.

## Required Codex write-back

- Write summary to: `ops/handoff/latest_codex_report.md`
- Write validation output to: `ops/handoff/latest_validation_run.txt`
- Write git status/log to: `ops/handoff/latest_git_status.txt`
- Write a short ChatGPT bundle to: `ops/handoff/latest_chatgpt_bundle.md`
- Update the heartbeat/status file during each run.
- Do not require Brian to paste giant logs.
- Do not broaden unrelated scope.
- Stop for Brian only when a real decision/credential/account-level action is necessary.
