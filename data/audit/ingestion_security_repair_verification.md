# Historical ingestion/compliance security repair

Status: applied to production and verified on 2026-09-01. No history was imported, no historical location was created, Hx-Builder behavior was not changed, and no application code was deployed.

## Disposition of the seven findings

| Relation | Purpose / current consumers | Browser required | Production disposition |
|---|---|---:|---|
| `ingest_jobs` | Internal source-document work queue; `landerware-ingest-ai` and backend worker use service role | No | RLS enabled; zero `anon`/`authenticated` grants; no browser policies |
| `ingest_facts` | Proposed extracted facts associated with an ingest job | No | RLS enabled; zero browser grants; no browser policies |
| `ingest_review_queue` | Human-review work generated from ingest facts | No current production browser consumer found | RLS enabled; zero browser grants; no browser policies |
| `compliance_requirement_sources` | Provenance catalog for compliance rules | No | RLS enabled; zero browser grants; no browser policies |
| `compliance_requirements` | Canonical compliance rule definitions | No direct browser access | RLS enabled; zero browser grants; no browser policies |
| `session_compliance_requirements` | Per-session compliance state/evidence; populated and updated through backend/trigger paths | No direct browser access | RLS enabled; zero browser grants; no browser policies |
| `historical_registration_import_rows` | Legacy staging rows used only by the historical registration batch RPC | No | RLS enabled; zero browser grants; no browser policies |

The dependent `ingest_operational_dashboard` and `session_compliance_summary` views also had their browser grants removed so view ownership cannot indirectly re-expose protected data. Existing service-role grants were preserved.

## Privileged function review

`public.import_historical_registration_batch(jsonb)` remains owned by `postgres` and remains `SECURITY DEFINER` for its staging-table write contract. Its search path is now exactly `pg_catalog`; all application relations in its body are explicitly `public`-qualified. `PUBLIC`, `anon`, and `authenticated` execution were revoked, while `service_role` execution was preserved. An empty-batch probe under `service_role` returned 0 staged/matched/unmatched inside a rolled-back transaction.

The function only writes `historical_registration_import_rows` and associates an existing `class_sessions.id`; it does not create people, sessions, registrations, completions, credentials, lifecycle assertions, or inventory events. Browser roles can no longer call it. No repository or production Edge Function caller of this RPC was found.

Two adjacent compliance mutation helpers were also closed: `populate_session_compliance_requirements(uuid)` is service-only, and the trigger-only functions `trg_seed_session_compliance()` and `release_archive_when_compliant()` are no longer browser-executable. All use `search_path=pg_catalog` after the repair.

## Validation

- Production migrations: `20260901113852 secure_ingestion_compliance_surfaces`; `20260901114113 secure_compliance_trigger_helpers`.
- Each change set passed two independent rolled-back production transactions before application.
- Authority counts stayed at 36 locations, 365 class sessions, and 33 registrations.
- Full-row SHA-256 hashes stayed unchanged: locations `f586218dc954f7a07d76245a76851814215ff7ce418d51aaeac3ef1c9cafb44e`; class sessions `8fecc7847e3775887759d1e7f20224b5bc01da2c93395df547bc22e25579bd49`; registrations `93dd889acefd6a1f756968c828b3c310a99206b566fd6a8ea66faaf288ca69c9`.
- Historical staging rows, ingest facts, inventory events, participant completions, and participant credentials remain 0.
- Public site and classes page returned HTTP 200 and the classes page retained class/registration content. The public registration Edge Function remained reachable without an application deployment.
- Local contract suite: 24 tests passed (lightweight direct runner; installed Python environments did not include pytest).
- Full 8,199-record Hx dry run: deterministic hash `db2599897fc7de26021d0a7cffc1bf6a1e3906fe3121c5aa55de6f5df9e05527`; independent runs equal; replay added 0 operations and 0 assertions; unexplained mismatches 0.

Supabase's security advisor no longer reports the seven tables as RLS-disabled and no longer reports the historical registration RPC as anonymously executable. It correctly reports the seven service-only tables as “RLS enabled, no policy”; that is the intended fail-closed design, not a missing browser policy. Other pre-existing advisor findings outside this repair remain separately reviewable.

## Caller inventory note

The deployed legacy `historical-class-import` Edge Function does not call the reviewed registration RPC or any of the seven tables. It is a separate, header-secret-protected legacy authority importer and was not changed because this task explicitly prohibited application deployment. Its existence should be handled in a separate endpoint-retirement review before any future historical import work.
