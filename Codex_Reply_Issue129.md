# Codex reply: Issue 129

- Assignment: GitHub issue #129, “Expand Add-on Workbench into database record browser”
- Timestamp: 2026-09-11 12:45 EDT (UTC-04:00)
- Branch: `codex/issue-129-record-browser-inventory`
- Substantive commit: `d54e3731582ee168d0671b03c92cd317e5dc5c72`
- Pull request: https://github.com/Brian910cpr/910cpr-class-landers/pull/186
- Issue inventory comment: https://github.com/Brian910cpr/910cpr-class-landers/issues/129#issuecomment-5637667979
- Work-item state: `PR_OPEN` (pre-implementation inventory gate complete; browser implementation remains separately scoped)

## Findings

Issue #136 is the completed dependency for canonical silo ownership and the Session Bundle boundary. The repository has three distinct durable persistence families—Supabase/Postgres, HOT_SYNC D1, and Maxim portal D1—plus authoritative/source files, reviewed configuration, runtime/state intermediates, generated public/admin projections, audit/debug evidence, and derived HTML outputs. A record browser must preserve those boundaries and display authority/provenance explicitly.

The Add-on Catalog Workbench is currently only a Beta placeholder in `docs/admin/toolbox.js`. No corresponding app source, schema, local checkout, or Brian910cpr GitHub repository was available. Current add-on information is limited to JSON embedded in registration profiles/catalogs and selected option/order records. Product dimensions, weights, vendor SKU versus 910CPR SKU, and compatibility/exclusion rules are not canonically modeled and must not be guessed.

Some database tables referenced by runtime code do not have authoritative DDL in this repository. These include base Supabase tables such as `class_sessions`, `customers`, and `registrations`, NHCSO/instructor/email tables, and the offer-worker `customer_facing_offers` table. They must be marked unavailable until authorized schema introspection is performed.

## Work performed

- Read the complete issue #129 body and comments.
- Read `AGENTS.md` and `CODEX_HANDOFF_PROTOCOL.md` from current `origin/main` before task changes.
- Reused the completed issue #136 inventory rather than creating a competing silo model.
- Enumerated tracked data files, migrations, SQL table definitions, Supabase table calls, and Worker D1 queries.
- Classified what is safe to display, owner-only, aggregate/redacted, or never display.
- Proposed a fixed-layout, read-only information architecture with source rail, collection index, dense record grid, stable inspector, relationship view, provenance, and unavailable/error states.
- Posted the full inventory and architecture to issue #129 before any implementation.
- Opened PR #186 with only the inventory report.

## Exact files changed

- `data/audit/issue_129_record_browser_inventory.md`
- `Codex_Reply_Issue129.md`

No application code, generated public page, database schema, or production data was changed.

## Tests and checks

- `git diff --check`: passed after removing Markdown trailing-space line breaks.
- Tracked schema/data inventory: completed locally with `git ls-files` and `rg`.
- GitHub issue #129 read and inventory comment posted successfully.
- GitHub issue #136 dependency and its completed owner comment reviewed.
- Branch push: successful.
- PR creation: successful.

No generator or build was appropriate for this research-only gate. No database connection or production write was attempted.

## Known unrelated state

The isolated worktree showed `docs/Earl/index.html` modified immediately after creation from `origin/main`, consistent with the repository's known case-collision/worktree behavior. It was not edited, staged, or committed. The original checkout's unrelated dirty files were preserved untouched.

## Deployment status

- Persisted locally: yes
- Changed in repository branch: yes
- Validated locally: yes, proportionate research/document checks
- Pushed: yes
- PR open: yes, #186
- Merged: no
- Deployed: not applicable; no public/runtime behavior changed

## Remaining risks and blockers

- Add-on Workbench source/schema unavailable, blocking a truthful SKU/product-specific layout.
- Missing authoritative DDL blocks safe layouts for referenced base tables until authenticated introspection is available.
- Owner authentication/hosting boundary, retention rules, export permission, and audit requirements need explicit implementation decisions.
- Sensitive records require server-side DTO allowlists and redaction; direct browser database access or arbitrary SQL/file browsing is unsafe.

## Recommended next action for ChatGPT

Review and merge PR #186 as the issue's required pre-implementation inventory. Then ask Brian to identify or recover the Add-on Workbench repository/data source and choose the owner-authenticated hosting boundary. Scope the first implementation PR to the static read-only catalog shell plus allowlisted schema/count adapters for one Supabase environment and HOT_SYNC D1; do not include editing, arbitrary SQL, bulk export, or sensitive raw-record passthrough.

## User/account action required

Yes. Brian or the supervisor must provide the missing Add-on Workbench source/data location and approve the authentication/hosting boundary before product/add-on or sensitive-record implementation. PR #186 also requires normal review/merge action.
