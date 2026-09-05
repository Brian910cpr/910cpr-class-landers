# Data inventory for issue #136

## Scope and method

This is a repository inventory, not a production-data rewrite. It traces checked-in durable inputs, private/runtime integration points, generated JSON projections, and known database schemas. Generated JSON remains an export or view; it is not promoted to canonical truth.

## Authoritative or durable domains found

| Domain | Current durable owner/evidence | IDs and notable fields | Main producers | Main consumers |
|---|---|---|---|---|
| Session / Class | LanderWare `class_sessions` via the private HOT_SYNC snapshot; Enrollware/Class Report for absorbed sessions | durable UUID or Enrollware class/session ID; status, start/end, course, location, instructor | external Supabase/LanderWare; `scripts/fetch_hot_sync_snapshot.py`; `scripts/build_sessions_current.py` | `scripts/publish_admin_schedule.py`, `scripts/generate_dynamic_offers.py`, `scripts/free_time_scheduler.py`, `scripts/block_start_time_selector.py` |
| Registration / Participant | Enrollware student snapshot and Maxim portal `registrations` table | registration ID, person ID, class ID, starts-at, status, eCard/billing refs | `scripts/import_enrollware_student_report.py`; Maxim worker API | admin schedule, portal history, participant/document workflows |
| Person / Customer | `data/config/people_catalog.json`; Maxim `people` table; raw Enrollware student exports | person/instructor IDs, names, contact fields, source metadata | catalog imports, portal writes, Enrollware exports | staffing, portal, registration matching |
| Organization / Client | session `client_name`; corporate profile/renewal rows | organization name/code, billing account | HOT_SYNC/manual intake; Maxim portal | session display, billing/renewal flow |
| Instructor | `people_catalog.json` and `instructor_catalog.json` | person ID, source instructor ID, credentials, scheduler flags | instructor/people catalog import scripts | schedule builders, availability, assignment validation |
| Course / Requirements | `data/config/course_master.json` plus reviewed policy/config files | course key, Enrollware ID, duration, eligibility, credential and scheduling requirements | Course Master import/review pipeline | session normalization, public offers, scheduler |
| Documents | Maxim registration fields and NHCSO document/eCard controls | eCard number/URL, document metadata, registration/person refs | portal/admin flows | participant history and completion handling |
| Billing | Maxim `registrations`, `renewal_cycles`, `corporate_profiles`; Stripe reference script | billing account/batch and Stripe invoice IDs | portal/API and reconciliation work | corporate renewal/registration history |
| Communications | `go_tokens`, `portal_events`, Facebook queues/history, LinkedIn event state | token/event/message IDs and actor/payload metadata | portal, social automation scripts | audit/history and outbound workflows |
| Inventory | `data/inventory/*.json`, calendar snapshots, durable sessions | appointment containers, resource/time occupancy, selected seeds | calendar/export and offer builders | scheduler, selector, public offer generation |
| Audit / Provenance | `data/audit/*`, `data/runtime/*`, `debug/*`, source metadata embedded in catalogs | source file/system/ID, generated-at, counts, warnings, reconciliation decisions | virtually every builder/importer | operator review and regression tests |

## Important generated JSON/feed boundaries

| Path/family | Classification | Creation/consumption finding |
|---|---|---|
| `data/sessions_current.json` | current-session intermediate | Built by `build_sessions_current.py`; feeds `build_schedule_future.py`, admin schedule, availability and offer tools. Not sufficient for unabsorbed durable HOT_SYNC sessions alone. |
| `docs/data/schedule_future.json` | authoritative public inventory projection, not enterprise truth | Built from `sessions_current`; consumed by page/hub builders and schedulers. Cancelled sessions are intentionally absent from public availability. |
| `data/private/runtime/hot_sync_snapshot.json` | private runtime snapshot of durable LanderWare records | Fetched by `fetch_hot_sync_snapshot.py`; consumed by `publish_admin_schedule.py`. Absence must fail closed for occupancy-sensitive work. |
| `docs/data/admin_schedule.json` | generated sanitized combined occupancy | Produced by `publish_admin_schedule.py` from Enrollware plus HOT_SYNC plus optional student snapshot. |
| `data/state/session_manifest.json` | large generated reconciliation/manifest state | Contains normalized source keys and historical session projections; useful evidence, not a replacement for durable session records. |
| `data/enrollware_student_snapshot.json` | generated private registration snapshot | Produced by `import_enrollware_student_report.py`; applied to Enrollware-derived admin sessions. |
| `data/config/course_master.json` | reviewed catalog candidate | Rich course truth with an explicit `authoritative` gate; must not become authoritative until unresolved fields are reviewed. |
| `data/config/people_catalog.json` | persisted people/instructor catalog | Contains source IDs and provenance, but duplicates instructor-specific catalog/config shapes. |
| `data/runtime/calendar_snapshots/*.json` | transient availability evidence | Calendar extracts used by availability builders; not session truth. |
| `data/audit/*.json`, `data/runtime/*.json`, `debug/*.json` | generated audit/runtime outputs | Rebuildable diagnostic evidence. Many files duplicate session/course/location fields for traceability and presentation. |
| `cloudflare/maxim-portal/schema.sql` | D1 durable schema | Defines people, corporate profiles, renewal cycles, registrations, tokens and portal events. This is D1, not Supabase, and must be mapped rather than conflated with LanderWare tables. |

## Duplicated or conflicting fields

- Session time/status/course/location/instructor appear in Class Report/Enrollware, HOT_SYNC, `sessions_current`, `schedule_future`, admin schedule, session manifest and multiple audit feeds. Only source-linked normalization can explain disagreements.
- `id`, `record_id`, `session_id`, `class_id`, and `enrollware_class_id` are used in overlapping contexts. They must be retained as source references, not collapsed into one guessed identifier.
- Course identity appears as IDs, keys, cleaned titles and raw HTML-rich names. Course Master should own canonical course meaning after its authority gate passes.
- Instructor identity appears as display names, Enrollware instructor IDs and person IDs. Assignment certainty is sometimes unknown; a blank name is not permission to assume Brian.
- Client/organization and location are frequently conflated in schedule records. The Session Bundle keeps organization references separate from location snapshots.
- Registration counts in schedule projections can mean unknown, stale snapshot, or confirmed zero. The export must record missing registration evidence explicitly.

## September 19 finding

`tests/test_canonical_schedule_hot_sync.py` is the checked-in adversarial evidence added by PR #131. It records scheduled sessions at Hendersonville Family Dental (09:00–11:00) and Little Leaps (11:00–14:00), plus a cancelled 14:00–16:00 Hendersonville-related record. Scheduled records reserve Brian and their locations; the cancelled record remains historically relevant but does not reserve availability. The test has no participant rows, canonical course IDs, or original message timestamps, so the bundle flags those dependencies instead of inventing them.

Canonical people/organization identity is a separate reconciliation concern from source-observation identity. The export's `identity_aliases` carries exact, previously persisted mappings from multiple source references to one canonical entity ID; the exporter performs no fuzzy matching.
