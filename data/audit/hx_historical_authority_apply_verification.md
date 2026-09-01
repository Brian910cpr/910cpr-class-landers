# Historical Authority Migration Apply Verification

The reviewed migration and its append-only audit correction were applied to production. No historical candidate locations, historical sessions, registrations, lifecycle assertions, or application code were deployed or imported.

## Production integrity

- Locations: **36 before / 36 after**
- Class sessions: **365 before / 365 after**
- Registrations: **33 before / 33 after**
- Legacy-content hashes for all three tables: **unchanged**
- Other captured authority-table counts: **unchanged**
- New historical location candidates: **0**
- Location-status audit events: **28** expected transition events

The 28 pre-existing locations referenced only by historical sessions are now `historical_only`. The other 8 retain `active` behavior. No historical-only location is public or referenced by an operational session.

New locations default to `inactive`. Operational sessions continue to require instructor, end time, and complete consumption-window data. Closed, non-public sessions with `record_scope = historical` may retain source-supported null instructor/end values. The future Unknown Historical Instructor substitution trigger and function are absent.

The audit table has RLS enabled, zero browser grants, zero `service_role` update/delete/truncate grants, and database triggers rejecting update, delete, and truncate.

## Complete Hx-Builder dry run

- Source records: **8,199**
- Fully canonicalized sessions: **3,439**
- Sessions accepted under the historical unknown-field contract: **3,570**
- Remaining unresolved locations: **421**
- Remaining ambiguous course rows: **17**
- Remaining identity conflicts: **27**
- Independent runs: **identical**
- Replay additional operations/assertions: **0 / 0**
- Unexplained mismatches: **0**
- Deterministic hash: `db2599897fc7de26021d0a7cffc1bf6a1e3906fe3121c5aa55de6f5df9e05527`

Supabase security advisors continue to report pre-existing findings outside this migration, including seven public tables without RLS and an anonymous-callable historical registration import function. This migration did not introduce or change those objects.
