# Issue 334 — observer proof R27

Timestamp: 2026-10-12T07:46:00Z
Branch: codex/issue334-observer-proof-r27-current
Evidence commit: 8f33c45f062a8199177a7b02795e207f6c58b515
Work-item state: BLOCKED (independent recurring health); read-only checkpoint VERIFIED.
Persistent evidence: PROVEN local publication, AT RISK; not overall HEALTHY.

## Execution and findings
Read issue body and full comment history, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, proof standard and design ethos. Acknowledged actual execution on originating issue before implementation (comment 6119929941). No application implementation was necessary or authorized past the remaining credential gate.

Live audit at 2026-10-12T07:43:25.894256Z: all eight families evaluate 210/210 windows, zero failed windows and no coverage alerts. BLS 4086 offers/89 dates (4074 dynamic, 12 seated); Heartsaver 8509/88 (8505 dynamic, 4 seated). Both unexpired through 07:53:24.628935Z. October 14 Heartsaver retains 17:30 and 19:30 choices. BLS/Heartsaver public HTML GETs HTTP200. These are current feed and HTTP proofs; no fresh interactive browser walkthrough or uninterrupted sampling claim.

Last sampled successful end-to-end publication: admin 38218632627 followed by Pages 38218934482, completed/updated 07:40:06Z. Earlier admin 38218168871 / Pages 38218439456 also succeeded. Admin 38219102918 normally in progress at capture; no competing dispatch made.

Exact blockers: public booking observer has only two workflow_dispatch runs (38198348377 success; 38197805655 prior pre-repair failure), no natural schedule event despite configured five-minute cron. AVAILABILITY_WATCHDOG_HEALTH_URL repository-variable lookup returns HTTP404. Existing owner-recorded repository-restricted Actions read/write token/encrypted GITHUB_ACTIONS_TOKEN gate remains; no new credentials or scope changes supplied. No activation retry. CYBERPC awake/login/network dependency remains.

## Changed files and validation
Only these intended evidence files plus this receipt:
- data/audit/issue334_observer_r27_live.json
- data/audit/issue334_observer_r27_runs.json
- data/audit/issue334_observer_r27_observer.json
- data/audit/issue334_observer_r27_http.json
- Codex_Reply_Issue334_ObserverProof_20261012_R27.md

Locally validated: 4/4 tests via python -B -m unittest discover -s tests -p test_family_publication_coverage.py; audit-script AST syntax and JSON parsing passed; staged whitespace passed. Remote read-only live audit passed. No generator, dry-run release, merge or deployment performed. Evidence and receipt committed/pushed separately; branch tip is the receipt commit.

Original E:/GitHub/910cpr-class-landers dirty work preserved. Fetch failed on missing object 6e61cabca5981d1389e52c60d95424d9893bb50f / bad refs/remotes/origin/codex/group-training-experience. Isolated fresh clone used, no destructive repair. Windows case collisions leave docs/Earl/index.html and docs/Jackson/index.html dirty in fresh clone; excluded explicitly. Existing #372/#383/#387 assignments preserved; no duplicate PR or changes to those streams.

## Proof contract and next action
Expected outcome: fresh legal public offers remain selectable before expiry. Source freshness still caps effective lease; expiry, missing dynamic inventory or failed windows are failures. Observer: verify-public-booking-inventory.yml, five-minute cadence; observer health UNPROVEN because natural heartbeat absent. Independent watchdog observer skipped without health URL; no claim of independent monitoring. Existing local timer sustains proven publication but cannot remove machine dependency.

Queue swept across open issues and existing PR assignments; no safe independent unassigned narrow backend quick win identified without competing with gated streams. No empty repair or repeated activation attempted.

Keep #334 OPEN. Next: prove a natural scheduled observer heartbeat; resolve the existing secure cloud credential gate through approved encrypted provisioning, then verify cloud timer and configure health URL, prove its scheduled observer and recovery before removing CYBERPC dependency. Preserve #383 skills-edge compatibility. Brian/account action is limited to existing credential provisioning/approval; routine monitoring must not be assigned to Brian. Prior boundary misses remain authoritative; exact earlier screenshot outage duration remains unknown.
