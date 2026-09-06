# Group training funnel audit

Date: 2026-09-06

Branch: `codex/group-training-funnel`
Issue: https://github.com/Brian910cpr/910cpr-class-landers/issues/148

## Evidence and failure

- Production `https://www.910cpr.com/group-training.html` displayed a white active program panel with light text after later global theme rules conflicted with the older `.slug-panel-card` rules. The component originated in commit `b271151`; the later dark-theme cascade made the active card unreadable.
- The indexed hub privileged “Request on-site BLS” and offered four course tabs instead of an industry decision path.
- `docs/request_group_session.html` and `scripts/build_request_group_session.py` rendered `method="post" action="#"` without a submit handler. It created no email, request, organization, coordinator, or session record.
- Thirty-nine repository files contain an internal reference to `/group-training.html`; the homepage booking code, class-index routing, admin navigation, sitemap, and audits intentionally keep the route.
- GTM container `GTM-PQS8DCBH` was present and is preserved. Repository access does not include the private GA4 property or a GA4 Data API export, so historical views, users, sessions, entrances, exits, engagement, acquisition, and conversion totals were not invented.

## Recovered work

- Branch `origin/codex/group-training-experience` contains commits `909d92d4b49` and `6e61cabca59` for a training-day builder. It collected organization, program, logistics, and contact choices, but finished in an email draft and explicitly left availability pending.
- That branch also carried a broad unrelated generated-site rewrite, so it was not cherry-picked. The useful decision concepts were recovered as targeted files.
- The current selector artifacts at `docs/data/block-selector-availability/*.json` use `selector-resolved-availability.v1`. Their authority statement says they are generated server-side from occupancy, conflict, course-consumption, public-location, and public-offer rules. The browser does not recreate that conflict engine.
- Existing `free-time-offer-worker.js` recheck behavior is marked `scaffold_only` when it cannot perform a remote check. It is not sufficient evidence for an immediately confirmed traveling group session.
- Existing LanderWare migrations already define durable organizations, people, relationships, sessions, rosters, registrations, and activity events. This slice adds only the missing group-request/audit record and links it to those records.

## Implemented first slice

- Replaced the fragile shared-theme page with isolated, high-contrast `group-training.css` and a decision-first first viewport.
- Added eight organization paths, role-sensitive recommendations, five business programs, supported optional modules, full-address/headcount/logistics collection, pricing-factor explanation, and custom-date fallback.
- Candidate times are read only from authoritative selector artifacts, exclude seated-class inventory, and are labeled **Requested time requiring confirmation**. The edge function re-fetches the production artifact and rejects a stale candidate. It never returns a confirmed reservation.
- The edge function uses an idempotency key, creates a LanderWare organization and coordinator, creates a requested-confirmation session when a candidate exists, creates `landerware_group_requests`, and appends a system activity event.
- The legacy request URL is retained as a canonical, parameter-and-hash-preserving adapter.
- Added 12 substantive industry pages and five service-area pages through one generator. Each has distinct metadata, canonical, breadcrumbs, Service and Organization JSON-LD, visible FAQs, natural internal links, GTM, and scheduler context. No industry-city matrix was generated.
- Updated the sitemap artifact and its authoritative builder to admit only indexable, self-canonical group child pages.
- Events implemented without PII: `group_training_view`, `group_industry_selected`, `group_location_selected`, `group_program_recommended`, `group_program_selected`, `group_schedule_started`, `group_date_selected`, `group_request_submitted`. `group_session_reserved` is deliberately not fired because this slice does not confirm a reservation.

## Image repository inventory

| Page | Placement | Source | Delivered asset | Alt | Basis |
|---|---|---|---|---|---|
| Hub and all child pages | Site identity in header | `docs/images/logo.png` | same stable asset, 44 by 44 CSS display | empty because adjacent “910CPR” text names the link | Existing repository-owned site logo, visually inspected |

Visually inspected candidate assets included `nurse doing CPR.jpg`, `HS-PEDI-FA-CPR-AED.jpeg`, and `HS-BBP.jpeg`. They were not used because the repository contains no explicit public-approval or licensing manifest and the course marks should not be used as generic industry illustrations. The deliberate image-free article layout avoids false facilities and unverified people.

Missing authentic subjects: restaurant staff response, church volunteer/AED readiness, dental team practice, childcare manikin practice, workplace team training, aquatics response, and each travel market. Preferred deliverable is an authentic 910CPR photograph, landscape approximately 1600 by 900, with no students’ paperwork, screens, roster information, or other private data. Public ownership/consent must be recorded before use.

## Validation

- `node --check docs/assets/group-training.js`: pass.
- `node tests/group_training_funnel.test.cjs`: pass.
- `python -m unittest tests.test_group_training_public`: 5 tests, pass.
- Python source compilation for the three changed generators: pass. Generated bytecode was not retained.
- `git diff --check`: pass.
- Local browser: desktop page rendered with readable high-contrast cards; healthcare selection revealed the correct mixed-role warning, program selector, modules, and logistics fields. Keyboard-accessible native inputs and visible focus rules are present.
- Responsive CSS collapses form and authority layouts below 680px. The available in-app browser surface did not honor requested viewport emulation, so a true mobile screenshot and interactive 200% browser zoom remain a pre-merge manual check.
- GTM script and noscript are present exactly once per page. GTM Preview/GA4 DebugView requires access to the live container/property and is not claimed complete from source inspection.
- Edge function was source-validated, but Deno is not installed locally and the migration/function were not deployed. Durable creation integration testing requires a preview Supabase environment with the migration applied.

## Deferred deliberately

- Immediate reservation, travel-time computation for arbitrary customer addresses, instructor assignment, payment/invoice calculation, and market-specific minimums or travel charges.
- Coordinator roster entry/upload, participant self-service, attendance, materials/equipment workflow, cards, invoice handling, expirations, and renewal outreach.
- Industry-plus-location pages. Publish only when search demand and original local operational evidence justify each page.
- GA4 historical report from July 11, 2026. Required input: GA4 property access with page-path and event reporting, or exported exploration covering the requested dimensions and metrics.
- Approved, consented industry photography and optimized derivatives.

## Deployment and rollback

1. Review the PR and run a preview deployment.
2. Apply `20260906010000_group_training_requests.sql` to the preview Supabase project.
3. Deploy the `group-training` Edge Function with existing Supabase URL/service-role secrets.
4. Exercise idempotent submission and stale-candidate rejection against preview data.
5. Verify desktop, 390px mobile, 200% text, keyboard-only flow, GTM Preview, GA4 DebugView, JSON-LD, and every listed URL.
6. Deploy static files only after the backend is healthy. Verify live HTML, CSS/JS versions, sitemap, and request creation.
7. Roll back static files to the prior commit and undeploy the function if submission verification fails. The additive request table can remain safely; do not drop captured requests during rollback.

No merge or production deployment was performed.
