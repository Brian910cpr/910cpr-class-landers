# Recheck Seed Worker Plan

Status: scaffold only. Not routed, not deployed, and not wired to public pages.

## Purpose

`POST /api/recheck-seed` will eventually perform a click-time live recheck for a selected dynamic appointment seed before sending a customer to an Enrollware deterministic appointment URL.

The endpoint is intentionally disabled in this scaffold. It must not redirect, fetch Enrollware, create appointments, or trust browser-submitted appointment URLs.

## Proposed Request Body

```json
{
  "seed_id": "seed_20260622_0830_209806",
  "source_offer_id": "offer_...",
  "date": "2026-06-22",
  "start_time": "08:30",
  "course_id": "209806",
  "instructor_person_id": "instructor_24057895173",
  "location": "NC - Wilmington: 4018 Shipyard Blvd",
  "appointment_url_preview": "https://www.enrollware.com/..."
}
```

## Eventual Responsibilities

1. Validate payload shape and reject missing or malformed seed data.
2. Recheck Google Calendar API for instructor availability.
3. Recheck blocking calendars, including DNS / Do Not Schedule calendars.
4. Recheck occupancy snapshot if a trusted current snapshot is available.
5. Rebuild the deterministic appointment URL server-side from trusted config.
6. Return JSON only:

```json
{
  "valid": true,
  "redirect_url": "https://www.enrollware.com/...",
  "reasons": ["calendar_available", "no_dns_block", "url_rebuilt_server_side"]
}
```

or:

```json
{
  "valid": false,
  "message": "That time is no longer available.",
  "reasons": ["dns_block_found"]
}
```

## Required Secrets / Config Before Enabling

- `GOOGLE_SERVICE_ACCOUNT_JSON` or equivalent Google Calendar auth.
- Calendar IDs for instructor availability and blocking calendars.
- Allowed origins for CORS.
- Appointment container config for deterministic URL rebuild.
- Course catalog / appointment eligibility source.
- Occupancy snapshot source and staleness policy.
- Audit log destination if customer clicks are recorded.

## Safety Rules

- Do not use `appointment_url_preview` as the redirect target.
- Do not fetch Enrollware during recheck.
- Do not create appointments or classes.
- Do not return redirects from this scaffold.
- Do not enable a route until live Google Calendar recheck and URL rebuild tests exist.
- Keep public buttons pointed at existing behavior until this endpoint is explicitly approved.

## Integration Plan

1. Keep `worker/src/recheckSeed.ts` disabled and unimported.
2. Add unit tests around payload validation and disabled behavior.
3. Add Google Calendar API client behind an interface with mock tests.
4. Add trusted appointment URL rebuild from server config.
5. Add stale-seed and stale-snapshot handling.
6. Add CORS/allowed-origin checks.
7. Wire route behind an explicit feature flag.
8. Only then consider public UI wiring.

## Manual Test Plan

When a TypeScript Worker toolchain exists:

1. Import `handleRecheckSeed` into the Worker router behind a disabled feature flag.
2. Send `GET /api/recheck-seed` and confirm `405`.
3. Send invalid JSON and confirm `400`.
4. Send missing seed fields and confirm `400`.
5. Send a complete seed while disabled and confirm `503` with `endpoint_disabled`.
6. Confirm no Enrollware network calls occur.
7. Confirm no redirect response occurs.
8. Confirm no appointment URL is accepted from the browser as trusted.

