# MAXIM portal backend

Build date: 2026-07-16
Status: Integration backend path implemented locally — not deployed

This Worker is the durable write/API layer for the MAXIM corporate portal. It is intentionally isolated from the existing public scheduler until the shared authoritative availability service is exposed.

## What is implemented in this scaffold

- D1 schema for people, corporate profiles, renewal cycles, registrations, `/go/` tokens, and audit events.
- One wildcard `/go/*` Worker route design; no per-token Cloudflare routes.
- Persistent scheduling-link creation and reuse for an active renewal cycle.
- Token resolution with active/consumed/expired/revoked state handling.
- Persistent Skip behavior that revokes active scheduling links but preserves history.
- Person history endpoint.
- Native corporate registration write endpoint with server-side authoritative availability recheck.
- Active duplicate registration protection for the same person, corporate customer, and credential family.
- Move support that supersedes the prior active registration only when the replacement write succeeds.
- Course/delivery mapping for BLS Initial/Renewal/HeartCode and Heartsaver Total In-Person/Online+Skills.

## Required before deployment

1. Create or identify the production D1 database and replace `REPLACE_WITH_D1_DATABASE_ID` in `wrangler.toml`.
2. Apply `schema.sql` to the D1 database.
3. Bind the Worker route(s) for `910cpr.com/go/*` and the API path used by the portal.
4. Confirm the production authoritative LanderWare availability source URL or Worker service binding. The current Worker can recheck `PUBLIC_ORIGIN/data/schedule_future.json` or an injected availability binding.
5. Wire production routes to this Worker and verify writes against the real D1 database.
6. Add authentication/authorization for MAXIM staff portal writes before production use.

## Release rule

The portal must not display LIVE until:

- exact delivery-method availability is live;
- final confirmation rechecks authoritative availability server-side in deployed production;
- Send Link persists and resolves after reload;
- Skip persists after reload;
- View History reads real records;
- Schedule for Them writes a real registration in deployed production D1;
- employee `/go/` self-service writes a real registration;
- resulting registration appears in the MAXIM Registered view;
- Move supersedes the prior active registration without deleting history;
- tests cover duplicate/expired/revoked/stale-slot cases.
