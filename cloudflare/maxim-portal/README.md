# MAXIM portal backend

Build date: 2026-07-17
Status: Integration scaffold — not deployed

This Worker is the durable write/API layer for the MAXIM corporate portal and the LanderWare document inbox. It is intentionally isolated from the existing public scheduler until the shared authoritative availability service is exposed.

## Implemented

- D1 schema for people, corporate profiles, renewal cycles, registrations, `/go/` tokens, and audit events.
- Persistent scheduling-link creation, resolution, skip behavior, person history, and native corporate registration writes.
- Registration writes remain blocked unless an authoritative availability proof is supplied.
- Private MAXIM document ingest backed by R2.
- D1 document metadata with an explicit `unfiled` queue so dropped files cannot silently disappear.
- Admin-only upload/list/assignment endpoints protected by an `ADMIN_TOKEN` Worker secret.
- Recent-registration lookup for matching a dropped ATLAS document to the right person/class.
- Browser drag-and-drop inbox at `/admin/maxim-documents.html`, including a lightweight filename-based match suggestion.

## Intended document workflow

1. Create the completion document in ATLAS.
2. Download it in Chrome.
3. Switch to the MAXIM Document Inbox tab.
4. Drag the recent download directly into the large drop target.
5. The file is stored privately in R2 and appears in the Unfiled queue.
6. Assign it to the matching registration. The queue remains visibly incomplete until every file is assigned.

This deliberately preserves the existing Enrollware muscle-memory workflow rather than requiring a new filing process.

## Required before deployment

1. Create or identify the production D1 database and replace `REPLACE_WITH_D1_DATABASE_ID` in `wrangler.toml`.
2. Apply `schema.sql`, then `migrations/0002_document_inbox.sql`.
3. Create the private R2 bucket named `910cpr-landerware-documents` (or change the bucket name in `wrangler.toml`).
4. Set the Worker secret with `wrangler secret put ADMIN_TOKEN`. Never commit that token.
5. Bind the Worker routes for the API and `/go/*` paths.
6. Ensure `/admin/maxim-documents.html` reaches the Worker API on the same origin, or set `window.LANDERWARE_API_ORIGIN` before the page script executes.
7. Expose the authoritative LanderWare availability check as a callable endpoint or Worker service binding.
8. Replace the temporary `availabilityProof` contract with a server-side availability recheck before registration insert.
9. Wire `docs/corp/maxim.html` to the durable API and retain INTEGRATION status until end-to-end verification passes.
10. Replace the shared admin-token prompt with Cloudflare Access or equivalent identity-based admin authentication before sensitive production documents are used broadly.

## Document API

- `POST /api/admin/documents` — multipart upload; requires Bearer admin token.
- `GET /api/admin/documents?state=unfiled` — list the visible work queue.
- `GET /api/admin/registrations/recent?days=120` — matching candidates.
- `POST /api/admin/documents/:documentId/assign` — attach a document to a registration/person/class.

R2 objects are private. The browser is not given direct bucket access.

## Release rule

The corporate portal must not display LIVE until scheduling persistence and authoritative availability checks are verified. The document inbox must not be treated as production-ready until D1, R2, the Worker route, the migration, and admin authentication are deployed and tested end-to-end.
