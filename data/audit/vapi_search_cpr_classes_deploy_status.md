# Vapi Search CPR Classes Deploy Status

Status: deployed and verified.

Branch: `codex/vapi-search-cpr-classes-api`

Implementation commits:

- `83f13f2eb7c Add Vapi CPR class search Worker endpoint`
- `71c20762609 Document Vapi endpoint deploy blocker`
- `390e356b348 Use custom domain for voice search Worker`

## Endpoint

Primary endpoint:

- `https://schedule.910cpr.com/voice/search-cpr-classes`

Fallback Worker URL:

- `https://free-time-offer-worker.brian-9ac.workers.dev/voice/search-cpr-classes`

Worker version deployed:

- `79c78076-339d-4cb7-8c30-c2d8208e2fb5`

Deployment ID:

- `76c66589-abba-4155-9fc6-13dc932e0c93`

Deploy method:

- `wrangler deploy`

Route/domain:

- `schedule.910cpr.com` as a Cloudflare Worker Custom Domain.

## Authentication

Bearer authentication is enabled with Cloudflare Worker secret:

- `VOICE_SEARCH_BEARER_TOKEN`

The token was generated locally and piped directly into Wrangler. It was not committed and was not pasted into chat.

Local copy for Brian/Vapi handoff:

- `C:\Users\ten77\.910cpr-secrets\voice_search_bearer_token.txt`

## Source

The Worker reads the published generated resolver snapshots:

- `https://www.910cpr.com/data/block-selector-availability/bls.json`
- `https://www.910cpr.com/data/block-selector-availability/acls.json`
- `https://www.910cpr.com/data/block-selector-availability/pals.json`
- `https://www.910cpr.com/data/block-selector-availability/heartsaver.json`
- `https://www.910cpr.com/data/block-selector-availability/arc.json`
- `https://www.910cpr.com/data/block-selector-availability/hsi.json`

Observed source `generatedAt`:

- `2026-07-24T23:34:58.664477`

Maximum data staleness:

- Time since the most recent successful resolver/build plus static-site deployment and CDN propagation.

## Verification

Local tests:

- `node --test worker/tests/voiceSearchCprClasses.test.mjs`: passed
- `python -m unittest tests.test_voice_search_cpr_classes`: passed
- `wrangler deploy --dry-run --outdir .wrangler-dry-run`: passed before production deploy

Production checks:

- Authenticated BLS August query on `workers.dev`: passed
- Authenticated BLS August query on `schedule.910cpr.com`: passed using Cloudflare DNS resolution
- Missing bearer token: returned `401` with `error.code = unauthorized`
- Invalid date format: returned structured `400` with `error.code = invalid_parameters`
- Response scan: no `registration_url`, `registrationUrl`, or `appointmentUrl` fields returned

Verified query:

```text
GET /voice/search-cpr-classes?program=BLS&date_from=2026-08-01&date_to=2026-08-31&limit=3
Authorization: Bearer [redacted]
```

Observed response summary:

- `generated_at`: `2026-07-24T23:34:58.664477`
- `total_matching`: `1388`
- `returned`: `3`
- `has_more`: `true`

First observed offer:

```json
{
  "offer_id": "bls-hsi-20260801-0800-wilmington-shipyard-blvd-463743-brian-do-not-schedule-inverse-gap-11",
  "course_id": 463743,
  "appointment_day_id": "260711",
  "program": "BLS",
  "course_type": null,
  "delivery_method": "In Person",
  "date": "2026-08-01",
  "start_time": "08:00",
  "display_time": "8:00 AM",
  "display_date": "Saturday, August 1, 2026",
  "location": "Wilmington - Shipyard Blvd",
  "seats_available": null,
  "price": null,
  "currency": "USD",
  "registration_status": "open"
}
```

## DNS Note

`schedule.910cpr.com` resolved through Cloudflare DNS (`1.1.1.1`) during verification. The local OS resolver still had a temporary negative cache immediately after domain creation, so the custom-domain verification used `curl --resolve` against Cloudflare’s returned IP.

## Schema Mismatches

- `price`: unavailable in generated snapshots; API returns `null`.
- `seats_available`: unavailable in generated snapshots; API returns `null`.
- `appointment_day_id`: present for generated appointment rows; `null` for seated Enrollware rows.
