# Canonical participant source map

Generated for issue #150 on 2026-09-06.

## Authoritative path

`class_sessions.id` → `registrations.class_session_id` → `registrations.customer_id` → `customers.id` → Canonical Session Workspace → Dashboard / Admin Port.

Active registration statuses are `registered`, `confirmed`, and `completed`. `canceled`, `no_show`, `rescheduled`, and removed relationships are excluded from the active roster while their records remain preserved. `people` is instructor/staff identity and is never used for participant identity.

## Source classification

| Source | Ingestion | Storage / projection | Classification | Operational treatment |
|---|---|---|---|---|
| Public LanderWare registration | `register_participant` / registration functions | `customers`, `registrations`, `class_sessions` | CANONICAL | Count and roster source |
| Historical Enrollware bridge | historical staging/promotion functions | canonical tables plus historical import/provenance rows | RECONCILIATION INPUT | Display only after canonical promotion |
| Gmail Enrollware notices | manual/recovery reconciliation | canonical sessions/registrations when resolved | RECONCILIATION INPUT | Evidence only; no frontend dependency |
| `data/enrollware_student_snapshot.json` | `scripts/import_enrollware_student_report.py` | formerly overlaid onto `sessions_current.json` and `admin_schedule.json` | LEGACY/FALLBACK | Retained as evidence; removed from operational builds |
| `data/sessions_current.json` | Enrollware iCal normalization | static schedule projection | RECONCILIATION / SCHEDULING INPUT | Session discovery only; participant fields are unavailable |
| `docs/data/admin_schedule.json` | `scripts/publish_admin_schedule.py` | Dashboard schedule projection | PROJECTION | Participant count/roster explicitly unknown until live canonical resolution |
| R2 `private/session-bundles/*.json` | `scripts/build_session_bundle.py` | former Admin Port response | DEAD/OBSOLETE FOR ROSTERS | Replaced by live Canonical Session Workspace |
| D1 `class_students` | legacy Dashboard manual student intake | `landerware-hot-sync` D1 | LEGACY/RECONCILIATION | Not consumed by canonical count or roster surfaces |
| `historical_student_count`, `source_seats` | historical source aggregates | `class_sessions` provenance fields | RECONCILIATION INPUT | May describe source evidence; never overrides registrations |
| Anchor seat overrides / `students_count_raw` | static scheduling scripts | capacity projections | LEGACY/FALLBACK | Not consumed by participant UI |

## Before-repair production finding

- The static admin projection contained 39 future rows and represented every missing participant value as `0`.
- Production contained 7 future operational durable Sessions: 5 with active registrations, 2 with true canonical zero registrations.
- Three durable sessions with registrations overlapped static schedule rows that displayed `0`.
- Four durable Sessions were absent from the static projection.
- The static HOT_SYNC projection contained a duplicate same-time record pair.

## Repair boundary

The static schedule remains useful for external schedule discovery and availability. It now publishes `participant_count: null`, `count_available: false`, `roster_available: false`, and `count_source: canonical_session_workspace_required`. Once authenticated, both operational screens use the protected Canonical Session Workspace response, whose count and roster are derived only from active `registrations` joined to `customers`.
