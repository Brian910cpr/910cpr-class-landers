# Marblism Rachel → LanderWare phone intake audit

Date: 2026-09-09

## Verified delivery capability

The authenticated Rachel workspace exposes completed calls only through Rachel → Calls and Rachel chat. The Calls list supports search, filters, playback, and a details modal. No webhook, API, JSON action, export/download, structured email setting, Zapier, Make, or Pipedream control is exposed. The organization integration catalog also has no such connector.

Marblism's current help center states that there is no public API and it is not on the roadmap. Its integrations article says Zapier is “coming soon.” Rachel's help articles document saving calls with summaries and recordings in the Calls tab and returning recording URLs through chat. They do not document a completed-call webhook or export.

Therefore there is no verified production transport to connect. The local receiver in this branch is an authenticated staging contract for a future supported webhook or a separately built, reviewed notification adapter.

## Actual source records

Three completed test calls dated September 7 were inspected. Each exposes caller number, Test Call badge, duration, sentiment, date, prose summary, transcript, and an opaque CloudFront WAV URL. None exposes a provider call ID, exact start/end timestamp, structured extracted answers, explicit transfer result, explicit booking result, or signature/authentication metadata.

| Call | Duration | Outcome | Extractable facts | Missing |
|---|---:|---|---|---|
| Location complaint | 169s | Negative; caller hung up | AHA BLS, initial, Tuesday, service-area discussion | Name, exact Tuesday, callback preference, stable call ID, timestamps |
| Nursing-school deadline | 128s | Positive | Brian, AHA BLS, initial, due Friday, evenings next week except Wednesday, Jacksonville/Wilmington | Callback/email, exact dates, stable call ID, timestamps |
| Holly Ridge request | 67s | Neutral | Brian, callback number, BLS, Holly Ridge, September 15 | Certifying body, initial/renewal, alternate windows, stable call ID, timestamps |

The exact caller number and recording URLs are deliberately omitted from this repository report. The committed fixture is sanitized.

## Durable model mapping

- Call event: new generic `landerware_phone_call_events`; it is the immutable ingestion fact and dedupe boundary, not a Rachel leads table.
- Caller/person match: existing `landerware_people` and `landerware_person_identities`, matched by normalized phone. The receiver does not invent or auto-create a person.
- Customer/organization: existing `landerware_organizations`, exact normalized-name match only. The receiver does not auto-create one.
- Scheduling request/action required: new generic `landerware_service_requests`, titled `NEW PHONE INTAKE` with `action_required` status. It is intentionally not a registration or session.
- Transcript: retained on the source call event with the raw normalized payload and SHA-256 request hash.
- Recording: existing `landerware_documents` stores a protected external recording reference; the call event links to it.
- Audit history: existing `landerware_activity_events`, with event type `new_phone_intake_received` for real calls only.
- Test calls: retained in `landerware_phone_call_events`; no service request or activity event is created.

## Adjusted contract

The prior contract is retained with these additions: `schema_version`, `external_call_id_kind`, precise call timestamps when available, outcome/transfer/booking status, flexibility, unresolved questions, and ingestion provenance. `external_call_id` is mandatory at the receiver. Because Marblism's UI exposes no call ID, a notification adapter must use a documented provider ID. A mailbox message ID may be accepted only with `external_call_id_kind=notification_message_id` and must remain a provisional dedupe mechanism.

## Authentication and idempotency

`POST /functions/v1/rachel-phone-intake` is server-to-server only. It requires key ID, Unix timestamp, nonce, and HMAC-SHA256 over `timestamp.nonce.raw_body`. The timestamp window is five minutes; used nonces are persisted and rejected on replay; the database also has a unique `(source, external_call_id)` constraint and a transaction advisory lock. Secrets are supplied only at deployment through `RACHEL_INTAKE_KEYS`; none are committed. A later deployment must explicitly configure this function to bypass Supabase JWT verification because this endpoint authenticates with its own HMAC; that production setting was not added or deployed here.

## Missing information Rachel must collect

Name, callback number, email when follow-up is expected, organization, exact credential wording, certifying body, initial/renewal/skills status, explicit required-by date including year, service type, group size, city/ZIP and travel radius, preferred date/time window, alternate windows, flexibility, follow-up channel, and a confirmed read-back. Platform metadata still needed from Marblism: immutable call ID, exact timestamps, test/billable status, transfer result, booking result, recording retention, and recording authorization/expiry.

## Privacy and recording risks

The recording URLs observed are opaque CloudFront paths without visible expiry parameters. That is not proof of durable or user-bound authorization; treat them as bearer-sensitive. Do not place them in ordinary logs. Keep call tables service-role-only, minimize transcript retention, document consent/recording law obligations, and obtain Marblism's retention and access-control terms before production use.

## Implementation state

Implemented locally on `codex/rachel-phone-intake`:

- `supabase/functions/rachel-phone-intake/index.ts`
- `supabase/functions/_shared/rachel-phone-intake-core.mjs`
- `supabase/migrations/20260909120000_receptionist_phone_intakes.sql`
- `tests/fixtures/marblism_rachel_test_call.json`
- `tests/rachel_phone_intake.test.mjs`

No migration was applied, no function was deployed, and no production system was connected.
