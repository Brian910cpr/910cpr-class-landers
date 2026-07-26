# Vapi Search CPR Classes Deploy Status

Status: blocked before production deployment.

Branch: `codex/vapi-search-cpr-classes-api`

Implementation commit: `83f13f2eb7c Add Vapi CPR class search Worker endpoint`

## Implemented

- Added `GET /voice/search-cpr-classes` to the existing Cloudflare Worker.
- Requires `Authorization: Bearer <secret>` using `VOICE_SEARCH_BEARER_TOKEN`.
- Reads generated block-selector availability snapshots from `https://www.910cpr.com/data/block-selector-availability`.
- Supports optional filters: `program`, `course_type`, `delivery_method`, `date`, `date_from`, `date_to`, `daypart`, `location`, and `limit`.
- Returns structured JSON errors for invalid parameters.
- Does not return registration URLs.
- Does not decide sellability independently; it only adapts rows already marked `publicSelectable=true` in generated resolver output.

## Source

Production source files:

- `bls.json`
- `acls.json`
- `pals.json`
- `heartsaver.json`
- `arc.json`
- `hsi.json`

Observed generated timestamp from current published/local snapshots:

- `2026-07-24T23:34:58.664477`

Maximum data staleness:

- Time since the most recent successful resolver/build plus static-site deployment and CDN propagation.

## Local Verification

Passed:

- `node --test worker/tests/voiceSearchCprClasses.test.mjs`
- `python -m unittest tests.test_voice_search_cpr_classes`
- `wrangler deploy --dry-run --outdir .wrangler-dry-run`

Local real-source handler check:

- Authenticated request status: `200`
- Example query: `/voice/search-cpr-classes?program=BLS&date_from=2026-08-01&date_to=2026-08-31&limit=3`
- `total_matching`: `1388`
- `returned`: `3`
- `has_more`: `true`
- Unauthenticated request status: `401`

## Deployment Blocker

Wrangler Cloudflare API authentication is blocked in this environment.

Commands attempted:

- `wrangler secret list`
- `wrangler whoami`

Observed Cloudflare errors:

- `Authentication error [code: 10000]` when listing Worker secrets.
- `Cannot use the access token from location: 2600:1702:6bf0:940:5546:34ca:6688:8b6 [code: 9109]` when checking account access.

Because secret management is blocked, `VOICE_SEARCH_BEARER_TOKEN` could not be safely stored as a Cloudflare Worker secret, and production deployment was not performed.

## Schema Mismatches

- `price`: unavailable in the generated snapshots; API returns `null`.
- `seats_available`: unavailable in the generated snapshots; API returns `null`.
- `appointment_day_id`: present for generated appointment rows; `null` for seated Enrollware rows.

## Next Step

Use a Cloudflare API token that is valid from this location, or run the following from an approved environment:

1. Set `VOICE_SEARCH_BEARER_TOKEN` as a Worker secret.
2. Deploy the Worker.
3. Verify `https://schedule.910cpr.com/voice/search-cpr-classes`.

Do not paste the bearer token into chat or commit it to the repository.
