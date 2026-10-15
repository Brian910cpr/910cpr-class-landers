# Issue 335 readiness checkpoint — 2026-10-14

State: IN_PROGRESS; activation BLOCKED. This is a read-only backend preflight, not the requested availability program.

## Authority and preserved work

Read issue #335 body and both Brian910cpr owner comments in full; acknowledged execution at https://github.com/Brian910cpr/910cpr-class-landers/issues/335#issuecomment-6182223300 before implementation. Read repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md, LANDERWARE_PROOF_AND_HEALTH_STANDARD.md and docs/CODEX_INSTRUCTIONS.md. Examined #334, #351 and concurrency rule #116. No third-party comment was treated as owner authorization.

Original E:/GitHub/910cpr-class-landers worktree is dirty on codex/durable-session-participant-linking and was preserved. New isolated worktree: E:/GitHub/910cpr-issue335-20261014; branch codex/issue335-availability-20261014, base 8e08de5ca5eb2525bf578bd7ace77971d39efd5b. This worktree shows tracked docs/Earl/index.html and docs/Jackson/index.html modifications after checkout, before edits; neither was edited/staged by this assignment. No resets or cleanup. No existing PR matching 335 was found. Existing PRs #393/#383/#387/#382 own overlapping production scheduling/checkout work; do not fork their implementation or merge their drafts. #372 remains untouched, unmerged, undeployed.

## Incumbent and canonical boundary

The issue documents the incumbent workaround: empty Enrollware class occurrences represent Amy's availability. Existing data/inventory/instructor_availability.json explicitly describes prototype blocks, while data/config/instructors.json declares explicit-calendar availability. Preserve the business distinction between instructor availability, an offered course, a committed class, a registration and a paid seat. Replacing empty session templates with native availability moves toward independence only when intake, conflicts, payment and the customer surface are proven. No new parallel catalog or speculative Enrollware occurrence was created here.

## Reproducible findings

Run `python -m scripts.audit_instructor_intake_qualification --instructor amy` (stdout only; no generated files). Intended exit is 2 when review gates remain. PowerShell shell wrapper reported nonzero; Python's explicit return is 2.

Actual reasons:

- exact_course_qualifications_unreviewed
- certification_expiry_unreviewed
- profile_and_qualification_family_mismatch

Exact source references:

- data/config/instructors.json: instructors[instructor_key=amy].allowed_course_groups = ACLS, PALS, BLS.
- data/config/instructor_catalog.json: instructors[instructor_id=amy].can_teach_course_ids = []; can_teach_course_families = ACLS, PALS; expiration_date = UNKNOWN.
- Same qualification record's certifications[0] claims HSI_INSTRUCTOR and notes that **Brian** confirmed he is an HSI Instructor. This is conflicting provenance, not proof of Amy's credential. Do not silently fix it or infer exact eligibility.
- supabase/functions/landerware-calendar/index.ts: accepts LANDERWARE_ICAL_TOKEN only; fetches all landerware_sessions and registration counts; no instructor-scoped token binding. It is unsuitable to share with Amy. Negative lifecycle filtering and a fallback 60-minute end do not prove booked/committed-only instructor calendar semantics.
- scripts/anchor_state.py: existing canonical demand/explicit commitment promotion must be reused. Do not treat a prototype availability row as an Anchor.
- data/config/anchor_schedule_policy.json: open_day_excluded_families currently includes ACLS/PALS. This is an existing-policy observation, not permission to change public suppression globally; reconcile with #351 and active #383 before native intake activation.
- Repository path search for scan/paperwork/watcher identifies scripts/ew_schedule_watcher.py (schedule ingestion) and an instructor intake prototype, no evidenced 4018 scanner watcher. This search does not prove a worker is absent from another machine. Scanner share path, machine identity/access and worker heartbeat remain undiscovered; no folder polling or private scan reads occurred.

The new tool is conservative and read-only. Even STATIC_CHECKS_PASSED always returns can_publish=false. It does not validate current credential authenticity, exact identity mapping, expired dates, durations, course mapping, or operational eligibility; it is a prerequisite review detector, not a production validator.

## Full request retained / next gates

| Requirement | Current checkpoint / next evidence |
| --- | --- |
| Durable native availability intake | Not implemented here. Bind reviewed canonical instructor/course/location identities and versioned submission provenance; keep windows separate from sessions. |
| Paid 14:00 PALS Renewal Anchor | Not proven. Reuse #387 payment transaction boundary and existing canonical demand. Race/replay tests must prove one anchor and atomic conflicts before public mutation. |
| Remove competing ACLS Initial/Renewal and PALS Initial | Not changed. Coordinate #383/#351; fixture and final HTML must show collapse scoped to Amy/resources/time. |
| Skills barnacles, including 13:00 | Not proven. Require reviewed consumption duration, setup/cleanup and instructor/resource checks; no guessed durations. |
| Legacy migration / Oct21 Nicholas, Oct22 Amy stale proof | Not changed. Obtain current private canonical roster proof and commitment provenance. Preserve registrations/history; stale uncertainty must not erase Brian date-wide. |
| Refresh and live customer proof | Not proven; #334/#393 remain active. No publication generator run or customer links changed. |
| Instructor communications | Not implemented. Queue only accepted availability and actual booking/change/cancel/reminder/roster events with durable delivery/retry proof, not speculative offer notices. |
| Instructor iCalendar | BLOCKED for sharing current owner feed. Build separately scoped instructor credential with exact identity binding; use committed classes only and minimal fields; prove add/change/cancel in an actual subscribed calendar. |
| 4018 scan intake | BLOCKED on scanner source discovery/access. Reuse Session Workspace document lifecycle, hash deduplication, explicit ambiguous/unmatched queue and attachment confirmation; prove watcher plus observer heartbeat. |

## Validation and operational proof

- `python -m unittest tests.test_audit_instructor_intake_qualification`: 6 tests passed, covering family-only qualification, duplicate/missing identity, unknown expiry, family mismatch, nonmutation and non-authorizing success.
- AST syntax parse: 2 files passed without writing pycache.
- `git diff --check`: passed.
- No public builder or generator, schema migration, production write, payment, notification, merge or deployment.
- Evidence level: BUILT for the read-only audit only. Native instructor availability program is not CONNECTED/PROVEN/MONITORED/HEALTHY.
- Last useful end-to-end proof: none for the requested program. Synthetic audit tests are not operational proof.
- Expected success: accepted availability -> qualified offer -> paid seat/atomic Anchor -> correct public collapse -> instructor notification/calendar -> paperwork attached with traceable provenance.
- Expected cadence: payment/availability/change event processing plus refresh SLA must be set and proven alongside #334; no timing values invented here.
- Failure/staleness: missing intake acknowledgement, unreconciled payment, stale publication, undelivered notifications, missing calendar change/cancel, unmatched scan or stale watcher.
- Observer and observer health: not established for the composed program. Existing production components require current proof; Brian is not an acceptable routine observer.
- Recovery: first reconcile Amy's canonical identity/qualification evidence; continue backend intake/transaction work against isolated fixtures while production activation stays gated; discover scan source using authorized infrastructure records. Retain external provenance/history and Enrollware fallback until native proof.
- Escalation: qualification facts and scanner source/access require owner/account evidence if not discoverable in authorized sources. No secret should be posted in an issue or receipt.

## Queue safety

Swept open CODEX issues and open PRs. Existing independent backend work (#240/#380/#371/#219) already has assigned draft streams and review gates; this dispatch does not take them over. The safe independent progress during activation gating was the local read-only qualification audit. No second deep implementation stream was launched.
