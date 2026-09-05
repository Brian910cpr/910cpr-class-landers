# Canonical silo ownership map

## Identifier rules

- Canonical export IDs are opaque, type-prefixed and deterministic from `(object kind, source system, immutable source ID)`.
- Every imported object retains one or more `{source_system, source_id}` references. Source IDs are never repurposed as cross-system IDs.
- Cross-silo links use IDs (`session_id`, `person_id`, `organization_id`, assignment IDs), not embedded copies of whole records.
- If the source lacks an immutable ID, import must create and durably persist one before later exports; mutable names/times are not safe identities.

## Ownership and relationships

| Silo | Owns | References | Does not own |
|---|---|---|---|
| Person / Customer | human identity and contact channels | organization/profile, registrations, documents | instructor credentials, session status, invoice state |
| Organization / Client | legal/customer account identity and organization-level billing defaults | people, sessions, billing accounts | a venue address copied from one session |
| Session / Class | scheduled occurrence, course ref, time, status, location snapshot, visibility and occupancy policy | organization, course, instructor assignments, registrations | participant contact data, full instructor record, payment ledger |
| Registration / Participant | relationship between a person and a session, registration/completion state | person, session, billing/document refs | canonical session time or person identity |
| Instructor | instructor role, credentials and scheduler eligibility | person | person contact truth, session assignment |
| Instructor Assignment | instructor-to-session role and certainty | instructor, session | instructor credential truth |
| Requirements | course/session/participant requirements and satisfaction state | course/session/registration/document | course marketing copy |
| Documents | document identity, kind, lifecycle and storage pointer | person/registration/session | binary duplication inside unrelated JSON |
| Communications | message/event identity, channel, direction, timestamps and related-object refs | person/organization/session/registration | operational truth inferred from prose unless promoted with provenance |
| Billing | charges, invoices, payer/account and reconciliation state | organization/person/registration/session | registration or session status |
| Inventory | resources, availability windows and occupancy observations | sessions, instructors, locations | canonical session record |
| Audit / Provenance | source observation, source IDs, import/export run, transforms, conflicts | any canonical object | replacement values chosen silently |

## Conflict and uncertainty policy

Conflicting source facts are emitted as conflict records containing the object/field, candidate values, source references and unresolved/resolved status. Unknown ownership or absent evidence remains `null` or a `missing_dependencies` item. Generated projections may cache display fields for inspection, but those fields remain non-authoritative and must include provenance.

## Transient versus durable

- Durable: LanderWare session rows, Enrollware source records, reviewed person/course catalogs, D1 portal rows and persisted source identifiers.
- Snapshots: HOT_SYNC, Enrollware student snapshot and calendar snapshots. These are point-in-time transport forms of durable/external records.
- Generated projections: `sessions_current`, `schedule_future`, admin schedule, hub/debug/audit JSON, pages and the Session Bundle itself.
- The Session Bundle is a portable, inspectable backup/interop envelope. Re-import must reconcile source references and conflicts; it must never overwrite production truth merely because the JSON is clean.
