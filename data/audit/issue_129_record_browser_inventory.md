# Issue #129 database record browser inventory and information architecture

Inventory date: 2026-09-11 (America/New_York)

Repository baseline: `origin/main` at `2bd414c871c`

Scope: pre-implementation inventory and owner-facing information architecture only

## Executive finding

The repository already has enough durable schemas and generated projections to support a useful read-only record browser, but it does not have one database or one uniform source of truth. It has three distinct persistence families—Supabase/Postgres, Cloudflare D1, and checked-in/local files—plus public/admin projections and audit evidence. The browser must preserve those boundaries, identify the source and authority of every record, and never imply that a generated JSON file is the canonical enterprise record.

Issue #136 is the completed dependency for canonical silo ownership and Session Bundle references. This issue should reuse that work rather than create a competing catalog. The separate “Add-on Catalog Workbench” is currently only a Beta placeholder in `docs/admin/toolbox.js`; no add-on application, schema, local checkout, or GitHub repository was available during this inventory. The only current add-on data found in this repository is JSON embedded in registration/catalog records (`landerware_registration_profiles.addons`, `landerware_registration_catalog.addons`, registration selections, and retail order selections).

## Existing stores and safe display boundary

| Store / source | Classification | Important records | Safe default display | Restricted or redacted |
|---|---|---|---|---|
| Supabase/Postgres migrations in `supabase/migrations/` | Durable operational database | organizations, people, identities, courses, sessions, rosters, registrations, requirements, memberships, documents, credentials, messages, completions, production-board records, registration catalogs/profiles, public orders, retail orders | schema, table/field metadata, counts, IDs, statuses, timestamps, source/provenance, non-sensitive course/product data, relationship links | names/contact data only behind owner auth; document contents/URLs, message bodies, token hashes, checkout/payment identifiers, and integration secrets hidden by default |
| Cloudflare HOT_SYNC D1 via `worker/migrations/` | Durable operational database | hot-sync sessions, inbox-file metadata, class students, payment receipts, admin and offer-worker audit logs | session operational fields, file metadata, counts, statuses, timestamps, non-sensitive audit summaries | student/contact fields, raw input/notes, payment references/comments, storage keys, audit payload JSON require owner auth and field-level redaction |
| Maxim portal D1 via `cloudflare/maxim-portal/schema.sql` | Durable, separate corporate portal database | people, corporate profiles, renewal cycles, registrations, go tokens, portal events | organization/session/renewal statuses, stable IDs, dates, aggregate counts | email/phone, roster data, token hashes, eCard/billing references, event payloads restricted; never show raw token material |
| `data/Class Report.xlsx`, raw Enrollware exports, private runtime snapshots | Authoritative external input or private source snapshot depending on file | classes, course catalog, students, source IDs | file metadata, import time, row count, column names, redacted preview, provenance | unrestricted raw student/customer rows, email, phone, balances, private notes |
| `data/config/`, `data/inventory/`, `data/content/` | Reviewed configuration and operational policy; authority varies by file | Course Master candidate, people/instructor catalogs, mappings, visibility, resources, availability policies | record fields with explicit authority/review status and source trace | personal contact fields and private calendar/source identifiers restricted |
| `data/sessions_current.json`, `data/runtime/`, `data/state/` | Intermediate/runtime/state | normalized sessions, snapshots, manifests, build state | freshness, producer, schema version, counts, IDs, status and relationship summaries | private calendar event details, participant data, and raw payloads restricted |
| `docs/data/schedule_future.json` and `docs/data/admin*.json` | Generated projections | authoritative public inventory contract and sanitized admin projections | public fields, build metadata, counts, provenance links | never present projection records as durable source rows; retain admin authentication |
| `data/audit/` and `debug/` | Generated audit/debug evidence | build health, conflicts, rejection reasons, trace reports | report name, producer, generated time, summary/counts, redacted structured inspection | raw HTML, source payloads, contact data, calendar IDs, and accidental secrets must not be blindly rendered |
| Generated HTML and sitemap families | Derived public outputs | class/course/location pages, index, sitemap | path, build/page IDs, hashes, source record links | no arbitrary raw-file viewer; HTML source should be escaped and size limited if later enabled |

## Concrete database table families

### Supabase / LanderWare

- Identity and organizations: `landerware_people`, `landerware_person_identities`, `landerware_organizations`, `landerware_person_organizations`.
- Catalog and rules: `landerware_courses`, `landerware_registration_profiles`, `landerware_registration_catalog`, `landerware_confirmation_templates`.
- Sessions and participation: `landerware_sessions`, `landerware_rosters`, `landerware_registrations`, `landerware_roster_memberships`, `landerware_registration_requirements`, `landerware_certification_requirements`, `landerware_completions`.
- Documents and communications: `landerware_documents`, `landerware_credentials`, `landerware_messages`, `landerware_disclosure_versions`, `landerware_document_submission_tokens`, `landerware_self_service_tokens`, `landerware_activity_events`.
- Commerce: `landerware_public_session_inventory`, `landerware_public_orders`, `landerware_public_order_students`, `landerware_retail_orders`.
- Intake/work queue: `public_registration_intents`.
- Production board: `production_board_cards`, `production_board_thoughts`, `production_board_activity`.
- Secret storage: `landerware_integration_secrets`—inventory its existence only; never expose values, ciphertext, nonces, tags, or provider secrets in this browser.

Some functions also reference older/base tables such as `class_sessions`, `customers`, `registrations`, NHCSO tables, instructor qualifications, session requirements, card processing, and transactional email outbox. Their authoritative DDL is not present in the checked-in migration set. They must appear as `schema_definition: unavailable` until introspected through an authorized backend; their shape must not be guessed from query code.

### Cloudflare D1

- HOT_SYNC/admin: `hot_sync_sessions`, `inbox_files`, `class_students`, `financial_payment_receipts`, `admin_audit_log`, `offer_worker_audit_log`.
- Maxim portal: `people`, `corporate_profiles`, `renewal_cycles`, `registrations`, `go_tokens`, `portal_events`.
- The offer worker also references `customer_facing_offers`; its DDL was not found in the repository and must be marked unavailable rather than inferred.

## Authority labels the UI must show

Every collection and record should carry one visible label:

- **Authoritative input**: external/source file used as operational input, such as Class Report, with source-system caveats.
- **Durable operational**: database row intended to survive builds and own operational history.
- **Reviewed configuration**: policy/catalog record whose authority is explicitly enabled or still gated.
- **Runtime intermediate**: replaceable working data used between pipeline stages.
- **Generated projection**: sanitized or public representation derived from other records.
- **Audit/debug evidence**: rebuildable trace or report, useful for explanation but not operational truth.
- **Derived output**: rendered pages, manifests, or sitemap.
- **Unknown/unavailable**: referenced store whose schema or current state was not available to this checkout.

`docs/data/schedule_future.json` remains the authoritative **public inventory contract**, but it is a generated projection and is not the authoritative owner of people, registrations, billing, or enterprise session history. Course Master must continue to display its explicit `authoritative` gate rather than being promoted silently.

## Proposed information architecture

### 1. Sources rail

A fixed left rail groups sources by persistence family, then by authority label:

1. Supabase / LanderWare
2. HOT_SYNC D1
3. Maxim portal D1
4. Source files and reviewed configuration
5. Runtime and state
6. Generated public/admin projections
7. Audit/debug evidence
8. Derived outputs

Each source entry shows environment, freshness/last observed time, availability state, collection count, and sensitivity tier. Missing credentials or unavailable schema should produce a clear unavailable state, not an empty table.

### 2. Collection index

The middle-left pane lists tables/files/collections with stable columns: name, authority, record count, primary key, updated/generated time, producer, and sensitivity. Filters should include authority, source system, domain/silo, freshness, and “needs attention.”

### 3. Dense record grid

The center pane uses a fixed-layout, keyboard-friendly grid. Columns remain stable while stepping between records. Default compact banks:

- identity: internal ID, source ID, external/vendor ID;
- status: lifecycle, visibility, active/listed, review/authority gate;
- measures: price/currency, capacity/counts, dimensions/weight where a future product schema supplies them;
- time: created, updated, imported/generated, start/end;
- provenance: source system, source file/table, source record ID, observed/imported time.

No product dimensions, weights, 910CPR SKU, vendor SKU, or compatibility fields currently have a canonical schema in this repository. The UI should omit those banks or display “not modeled,” never fabricate empty authoritative fields.

### 4. Record inspector

The right pane holds predictable sections: Identity, Status, Core fields, Relationships, Provenance, Conflicts/missing evidence, and Audit history. Long text and JSON open in an escaped, size-limited pop-out with formatted/raw toggle and copy controls. Secret-marked fields are omitted at the API layer, not merely hidden with CSS.

### 5. Relationship view

Relationship links should use declared foreign keys or explicit source references. Initial useful paths are:

- organization → people → registrations;
- course/profile/catalog → sessions → registrations → roster memberships/completions;
- registration → requirements → documents/credentials/messages;
- session → public inventory/order → order students;
- production card → thoughts/activity;
- HOT_SYNC session → class students/audit events by explicit record/class ID;
- generated projection record → source IDs/provenance, without reverse-writing.

Vendor SKU ↔ 910CPR SKU and product/add-on compatibility/exclusion views remain blocked on a canonical product/add-on model. Current `addons` and `selected_options` JSON can be inspected read-only, but should not be normalized by inference.

## Access and redaction policy

Use an authenticated server-side adapter with an explicit collection/field allowlist. Do not connect browser JavaScript directly to service-role Supabase or D1 credentials, and do not expose arbitrary SQL or arbitrary repository-path reads.

- Public-safe: course names/IDs already public, public session IDs/statuses/times/locations, non-sensitive policy names, schema metadata, counts, hashes, and generated timestamps.
- Owner-only but displayable: names and contact data needed for operations, rosters, internal notes, billing status/amounts, document metadata, message delivery state. Apply least privilege and audit reads where appropriate.
- Aggregate/redact by default: student/customer lists, emails, phones, employee IDs, calendar event details/IDs, financial references, message bodies, raw input, JSON payloads, storage keys, eCard identifiers, checkout/payment identifiers.
- Never display: service-role keys, OAuth credentials, private tokens, token hashes, recovery/self-service tokens, integration secret ciphertext/nonce/tag, webhook secrets, or unrestricted document contents.

Downloads and bulk export should be a separate later scope with authorization, explicit field sets, audit logging, and row limits. Editing remains out of scope.

## Recommended implementation slices

1. **Read-only catalog shell:** static 1980s fixed-layout UI plus a versioned source registry; use fixtures only. No database credentials and no writes.
2. **Schema/count adapters:** owner-authenticated endpoints returning allowlisted schema metadata, freshness, and counts for one Supabase environment and HOT_SYNC D1. Prove absence/error states.
3. **Low-risk records:** course/catalog/profile/config and public session projection records, with provenance and relationship navigation.
4. **Sensitive operational records:** owner-only session/registration/person views using explicit DTOs, redaction tests, access logs, and no raw-table passthrough.
5. **Product/add-on model:** only after locating/recovering the Add-on Workbench source and approving canonical SKU, compatibility, exclusion, dimensions, weight, and provenance fields.
6. **Long JSON/audit inspection:** curated allowlist, escaping, truncation, download restrictions, and sensitive-field scanning.

The first implementation PR should stop after slices 1–2 and prove one narrow end-to-end read-only path. It should not implement editing, direct SQL, unrestricted file browsing, or bulk export.

## Blockers and open questions

- The Add-on Catalog Workbench source/database is not present in this repository, in the available local GitHub checkout list, or in Brian910cpr repositories returned by GitHub. Its schema and data ownership cannot yet be inventoried.
- Authoritative DDL for referenced base Supabase tables (`class_sessions`, `customers`, `registrations`, and NHCSO/instructor/email tables) and `customer_facing_offers` was not found here. Authorized schema introspection is required before implementing their record layouts.
- The intended owner authentication boundary and hosting surface for cross-store inspection require an explicit implementation decision.
- Retention, export permission, and audit requirements for customer, payment, message, and document metadata are not yet specified.
- Add-on/SKU compatibility and exclusion rules are not canonically modeled. Current JSON blobs are evidence, not a complete normalized product model.

## Validation performed

- Read full GitHub issue #129 and its comments (none at inventory time).
- Read repository `AGENTS.md` and `CODEX_HANDOFF_PROTOCOL.md` from current `origin/main`.
- Reused completed issue #136 and `data/audit/data_inventory_issue_136.md` as the dependency baseline.
- Enumerated tracked database/data files and all checked-in `CREATE TABLE` statements across Supabase, worker D1, and Maxim portal schemas.
- Traced Supabase `.from(...)` calls and Worker D1 `prepare(...)` usage to identify referenced schemas missing from checked-in DDL.
- Inspected the ADMIN Toolbox Add-on Catalog entry and current add-on fields in registration/checkout migrations.
- No generator, database query, production write, deployment, or application-code change was performed.
