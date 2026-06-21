# Recheck Seed Worker Test Plan

No Worker TypeScript test tooling currently exists in this repo. This file is the manual test plan until a Worker test harness is introduced.

## Current Scaffold State

- `worker/src/recheckSeed.ts` is not imported by `worker/free-time-offer-worker.js`.
- No route is registered in `wrangler.toml`.
- No public page calls this endpoint.
- `RECHECK_SEED_ENABLED` defaults to disabled unless future wiring explicitly sets it to `true`.

## Manual Tests Before Route Wiring

1. Add a temporary local-only import of `handleRecheckSeed` behind a disabled route.
2. Send `GET /api/recheck-seed`.
   - Expected: `405`, `method_not_allowed`.
3. Send `POST /api/recheck-seed` with invalid JSON.
   - Expected: `400`, `invalid_json`.
4. Send `POST /api/recheck-seed` with `{}`.
   - Expected: `400`, missing field reasons.
5. Send a complete seed payload with `RECHECK_SEED_ENABLED` unset.
   - Expected: `503`, `endpoint_disabled`.
6. Confirm the response is JSON and `cache-control: no-store`.
7. Confirm the Worker does not fetch Enrollware.
8. Confirm the Worker does not redirect.
9. Confirm the Worker does not use `appointment_url_preview` as a trusted redirect target.

## Required Automated Tests Later

- Payload validation.
- CORS/allowed origin handling.
- Google Calendar availability recheck mock.
- Blocking calendar recheck mock.
- Occupancy overlap mock.
- Deterministic appointment URL rebuild from trusted config.
- Disabled route behavior.
- No redirect until all checks pass.

