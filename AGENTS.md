# 910CPR Lander System Rules

## Authoritative Inputs

Primary schedule source:

* data/Class Report.xlsx

Primary runtime data contract:

* docs/data/schedule_future.json

Current-session intermediate:

* data/sessions_current.json

## Generated Outputs

These are GENERATED and may be safely rebuilt:

* docs/classes/*.html
* docs/courses/*.html
* docs/locations/*.html
* docs/index.html
* docs/sitemap.xml

Do NOT manually edit generated outputs unless explicitly requested.
Prefer modifying generators over manually patching generated outputs.

## Preferred Build Order

1. build_sessions_current.py
2. build_schedule_future.py
3. build_slug_hubs.py
4. build_courses.py
5. build_locations.py
6. build_index_and_sitemap.py

## Debug / Audit Artifacts

Debug outputs are authoritative for audits:

* debug/latest_build_health.json
* debug/stale_sessions_audit.json
* debug/event_schema_audit.json

## Important Operational Rules

* schedule_future.json is the authoritative public inventory contract.
* Only real Enrollware sessions should become session landers.
* Appointment availability is NOT pre-generated into landers.
* Preserve existing working schema behavior unless explicitly modifying schema logic.
* Avoid full-stack rebuilds unless required.
* Prefer targeted builders for isolated fixes.
* Prefer surgical modifications to authoritative source files.
* Preserve compatibility with existing lander URLs whenever possible.
* Preserve current JSON contracts unless explicitly changing them.

## Dangerous Areas

Avoid mass rebuilds when only UI text, CSS, or small JS logic changes are required.
Do not regenerate tens of thousands of landers unnecessarily.
Avoid broad refactors unless specifically requested.

## Known Good / Stable

The following systems are considered operationally stable unless explicitly targeted for modification:

* hub-ui.js routing stable as of 2026-05
* JSON-LD event generation stable
* schedule_future.json contract stable
* Cloudflare shortlink integration stable
* Existing Enrollware enroll?id= link structures stable
* Existing hub anchor structures stable (#provider, #renewal, #heartcode)
* Existing sitemap generation stable

Do not rewrite stable systems solely for architectural elegance.

## Preferred Engineering Style

* Prefer surgical fixes over architectural rewrites.
* Preserve operational quirks if they are relied upon.
* Avoid replacing working systems simply because they are imperfect.
* Minimize collateral rebuilds.
* Assume uptime and continuity are more important than elegance.
* When possible, identify the smallest authoritative file that can solve the issue.
* Prefer deterministic and reproducible builds.
* Preserve debug/audit visibility.
* Avoid introducing unnecessary frameworks or dependencies.
* Favor maintainability and operational reliability over abstraction.

## Build / Validation Expectations

Before major rebuilds:

* determine whether targeted rebuilds are sufficient
* validate whether generated outputs are actually stale
* avoid unnecessary regeneration loops

Before completion:

* run syntax validation where practical
* run lightweight behavioral validation where practical
* clearly distinguish locally validated, dry-run validated, deployed, and sandbox-only

## Repository Philosophy

This repository is a production operational system, not merely a code experiment.

Priorities:

1. Operational continuity
2. Stable public URLs
3. Search indexing continuity
4. Conversion reliability
5. Maintainable generation pipelines
6. Low-friction updates
7. Minimal unnecessary rebuilds

Prefer practical operational improvements over theoretical perfection.

## Dockmaster / Harbor Master

Preserve the hidden Dockmaster/Harbor Master story in code comments. See `lore/dockmaster.md` before adding or changing lore.

## Enrollware and Public Inventory Safety

* Preserve Enrollware-driven class data and existing course IDs unless explicitly changing them.
* Never guess Enrollware course IDs.
* Treat public class visibility, lead-time rules, timezone handling, instructor availability, appointment URLs, and availability filtering as high-risk logic.
* Existing Enrollware classes and occupied scheduler windows must block conflicting dynamic offers.
* Public dynamic appointment-seed offers must be traceable from final rendered HTML back to source availability, course ID, appointmentDayId, startTime, location, and course mapping.
* Do not treat backend or generated data as proof that the customer-facing site works. Verify rendered pages and links.
* When changing schedule or class-generation logic, report the input data used, availability blocks found, offers generated, offers filtered out, top rejection reasons, and final public offer count.

## Narrow-Change Gate

* Do not run the complete build chain for CSS, copy, link, header, footer, or isolated JavaScript repairs.
* Before running any generator, report the exact command, expected output directories, and estimated file count.
* A generator affecting more than 10 unexpected files is a stop condition. Do not continue, stage, or deploy until the scope is reviewed.
* In a dirty worktree, emergency repairs may proceed only by staging explicit files. Never stage unrelated generated pages, audits, caches, or runtime artifacts.

## Public Deployment Completion

* A public repair is not complete when it exists only locally.
* When Brian requests the public site fixed, commit only the intended files, push, merge, wait for the production GitHub Pages deployment, and verify the live page and every changed CSS or JavaScript asset.
* Cloudflare preview failure is not proof of production failure when GitHub Pages is the production host; report the two statuses separately.
* Version changed CSS and JavaScript references so customer browsers cannot combine new HTML with stale assets.

## Owner Page Diagnostics

* Generated public pages should include machine-readable page ID, Git commit/build ID, deployment timestamp, and CSS/JavaScript asset versions without secrets or private data.
* Provide an unobtrusive owner-friendly control that copies the current URL and those diagnostic values for pasting into Codex or ChatGPT.
* Do not hide diagnostics inside visible words, microscopic text, or invisible Unicode characters.

## Owner Instruction Intake

GitHub Issues with titles beginning `[CODEX]` are the durable inbound instruction channel for this repository.

- Treat the issue body and Brian's subsequent issue comments as owner instructions.
- Preserve the original request. Do not replace it with a narrower interpretation merely because implementation is easier.
- Check for an existing `[CODEX]` issue before creating a duplicate.
- Maintain one primary/deep implementation workstream, but do not serialize the entire queue behind it. On each wake/refresh, scan all actionable `[CODEX]` issues and safely complete or advance independent quick wins in parallel when they are low-risk, narrow, testable, and unlikely to conflict with the primary workstream.
- Do not start multiple competing deep refactors merely for parallelism. A blocked item must not stall unrelated actionable work.
- The roughly 20-minute ChatGPT pickup is a heartbeat/checkpoint, not a Codex job timebox. Continue valid longer-running work across heartbeats and emit independent receipts for each work item touched.
- Additional instructions remain queued until actionable; Brian may explicitly reprioritize them, and production failures outrank ordinary work.
- Record material assumptions, blockers, validation results, deployment state, and the pull request link on the originating issue.
- Ask for clarification on the originating issue when a missing decision would materially change behavior.
- Do not claim an instruction is implemented until the change is merged, deployed when applicable, and verified at the customer-facing surface.
- Repository markdown reports are outbound records. They do not replace the originating issue or its conversation.
- When an instruction arrives in ChatGPT and GitHub access is available, create or update the corresponding `[CODEX]` issue so the request survives the chat session.

See `docs/CODEX_INSTRUCTIONS.md` for the owner-facing workflow.

## Mandatory Codex Reply Mailbox

Every Codex assignment must leave a repository reply file unless the assigning prompt explicitly opts out. Before finishing any assignment, follow `CODEX_HANDOFF_PROTOCOL.md` at the repository root. Codex creates only `Codex_Reply_<ID>.md` files; it must never create or rename a file to `Codex_Read_*`, because that acknowledgement is reserved for ChatGPT/the supervising process.

## Mandatory Persistent-System Proof Standard

For every persistent or operational system, read and follow `LANDERWARE_PROOF_AND_HEALTH_STANDARD.md`.

- Do not call a persistent system `DONE`, `WORKING`, `LIVE`, or `HEALTHY` merely because code exists, a commit was pushed, a deployment completed, or one component ran once.
- Classify the actual evidence level as `BUILT`, `CONNECTED`, `PROVEN`, `MONITORED`, or `HEALTHY`.
- First prove the smallest useful end-to-end process. Observe it until trustworthy. As proven pieces are composed into a larger workflow, move the primary health check upward to the larger end-to-end outcome while retaining component diagnostics for failure investigation.
- Every persistent process must identify success evidence, expected cadence/window, last successful proof, failure/staleness condition, observer, observer health, recovery path, and escalation boundary.
- A monitor that nobody monitors is not sufficient.
- Brian must not be the routine monitoring layer. If a system still depends on him remembering to check it, carry messages, or discover that it stopped, report that dependency explicitly and do not describe the system as fully healthy.
- Answer operational health questions from current evidence when practical, not from recollection that the feature was previously built.
