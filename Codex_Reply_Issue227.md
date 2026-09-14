# Codex reply: Issue 227, Sites first release

Timestamp: 2026-09-14T04:00:39Z
Assignment: https://github.com/Brian910cpr/910cpr-class-landers/issues/227
Work-item state: IN_PROGRESS (first Sites slice DEPLOYED)
Evidence level: BUILT; public source reads CONNECTED during development. Full operational workflow not PROVEN, MONITORED or HEALTHY.
Branch: main in the Sites source repository; this receipt is on LanderWare main.
Sites source commit: f02400fd26ead001a61bc715aee73ee8b47f94f7
Inspected LanderWare commit: e69b1846f3bb346b564f21960cee523ceccf6f86

## Published artifact

https://landerware-operations.butternutsquash.chatgpt.site

Owner-private Sites project: appgprj_6aa76dae73a08191a3540fc096352628
Version: 1
Deployment: appgdep_6aa77151f7f08191b83393e3ec1dae10; native status succeeded 2026-09-14T04:00:39.430737Z.
Source repository: https://git.chatgpt-team.site/eebe4103-0db4-4f16-97db-505d0f5428b3/appgprj_6aa76dae73a08191a3540fc096352628.git

## Implemented

- Source-dated public listings with seven-day calendar/list toggle, family and text filters, Eastern dates, and detail panels.
- Enrollware admin class/participant links for numeric external IDs, using the owner's requested admin URL shape.
- Existing NOW, registry, all-classes/roster and production-board links; no duplicate business records.
- Private customer course comparison preview at /courses with 15 existing options across BLS, ACLS, PALS and Heartsaver. It continues to existing 910cpr.com course/registration routes and does not invent prices or seats.
- Read-only GitHub work queue (latest 30 matching open instructions within latest 100 issues), five-minute cache, no simulated agent messages or worker-heartbeat claims.
- Feature-detected read-only WebMCP listing tool. Browser WebMCP validation unavailable under current preview permissions; user did not request WebMCP as a release gate.

Auth-sensitive records remain in the existing LanderWare screens. This Site does not contain owner credentials or private participant payloads. It has no authenticated roster, eCard count, finance, registration writer or scheduler integration yet.

## Verification

Build passed. TypeScript noEmit passed. Behavioral checks passed: duplicate, past, canceled and malformed listing exclusion; Eastern day boundaries including winter; unsafe-link rejection; old/unknown timestamp detection. Source public schedule returned HTTP 200 with 25 rows and generated_at 2026-09-11T14:45:44.530461-04:00. NOW page returned HTTP 200. Owner-dashboard endpoint returned 401 without owner authorization, as expected. No browser QA requested/performed; Sites hosting guidance disallows automatic browser QA in this execution profile.

Source and archive were pushed/packaged from the exact stated commit before saving version 1; native deployment status succeeded. This is deployment proof, not the full schedule/booking/fulfillment business proof.

## Files

Sites project: app/page.tsx, app/workspace.tsx, app/api/overview/route.ts, app/courses/page.tsx, app/courses/finder.tsx, app/globals.css, app/layout.tsx, lib/data.ts, lib/catalog.json, public/favicon.svg, README.md, .openai/hosting.json and retained starter/tooling/component files. LanderWare application code was not changed; this repository change is the receipt only.

## Findings and concrete next work

1. Existing /admin/now.html and ops/owner-dashboard/README.md already implement the private NOW monitor under issue 216. Reuse the canonical owner-session path. docs/admin/admin-auth.js now uses owner sessions; legacy Worker access remains separate. Establish a supported authenticated connection before displaying private data in Sites; do not copy a guessed key, bypass auth, or count unavailable sources as zero.
2. Public course pages already have titles, descriptions, canonical URLs and static introductory text. Their course-option list starts as empty HTML and is populated by JavaScript. The generator scripts/build_bls_block_schedule_pilot.py render_html() owns this markup. Next targeted SEO/accessibility improvement: render the existing course-option descriptions and usable navigation in initial HTML, preserving current interactive selection and scheduling logic; extend tests and verify the four actual public routes. Do not rebuild availability or tens of thousands of landers for a markup change.
3. The public schedule source date is September 11. First-slice UI labels it explicitly; it is not the full authoritative private calendar. Investigate source freshness and reconciliation through existing workstreams, rather than adding another feed truth.
4. Scheduler repositories discovered: Brian910cpr/shiftcommander_v2, Brian910cpr/shift-commander (private, Base44 README), and Brian910cpr/adr-fr-scheduler-web. Verify latest deployment lineage before edits. Keep the owner's full availability, company needs, employee preferences, coverage/conflict resolution, publishing and phone/SMS scope in issue 227.
5. The Sites customer preview is private and noindexed. Production SEO, customer checkout and scheduler code have NOT changed. No claim of ranking improvement or released scheduler is made.

## Persistent proof contract

Expected outcome: open workspace -> see source-dated listing -> inspect -> open canonical destination. Refresh every 60 seconds while visible; GitHub cached five minutes. Failure/staleness: read error or >2 minutes since successful read; public source timestamp >24 hours or missing is visibly warned. This threshold is a UI freshness warning, not a business scheduling rule. Observer is the open browser tab; no independent observer configured. Last successful source proof is the HTTP read above; authenticated browser end-to-end proof is outstanding.

Recovery: retry bounded reads; inspect upstream source generation; use original tools while unavailable; roll back Sites version if necessary. No canonical data migrated, so existing Google Workspace recovery architecture remains unchanged. No account-level user action requested for this first release. Further authenticated connection requires supported owner access, not new shared passwords. Issue 227 preserves the complete owner instruction; its existence is not proof a background agent is running.
