# Marblism Rachel -> LanderWare intake investigation

Date: 2026-09-10
Status: locally implemented and tested; not connected, deployed, or production-enabled.

## Verified delivery capability

The authenticated 910CPR Marblism workspace exposes two completed-test-call outputs:

1. Rachel posts a natural-language completion summary in her Marblism chat.
2. `My Account -> Manage Notifications -> Email -> Call Summary` is enabled and described as “Call summaries from Rachel.” Rachel states this is a platform-standard email using the same Call Analysis and that she cannot customize the template.

No generic webhook, public API, Zapier, Make, Pipedream, download, export, or LanderWare/Enrollware connector was visible in the integration catalog or Rachel surfaces. The Calls page reported `0 calls` while two test-call summaries remained in chat. Therefore test calls are not entered into the Calls ledger and the Calls page cannot be treated as a complete source.

The only verified machine-routable transport is the standard email notification. The email's raw MIME/headers and exact structured format were not available in the Marblism UI, so a mail-parser bridge remains necessary and must be validated against a real received message before production connection.

## Visible completed test calls

Rachel line: `+1 910-716-8250`. Dedicated testing number: `+1 910-395-5193`.

- Initial BLS request: Leland, after 5:00 PM, before September 24; explicitly test and excluded from monthly call hours.
- Reschedule request at 9:18 PM on September 9, 2026: caller name “Brian Ness”; BLS class from Saturday, September 12 to Thursday, September 24 at 5:00 PM; follow-up promised only after team verification; explicitly test.

Available in the visible source: direction (inbound), caller name on one call, chat/message timestamp, test status/reason, natural-language summary, requested credential, requested location/window/deadline where spoken, and intended human-follow-up outcome.

Not exposed for these test calls: platform call ID, caller telephone number distinct from the known testing number, duration, full transcript, recording URL, structured extracted-answer object, call disposition code, email message ID, or raw email payload. The local fixture uses an explicitly synthetic test-only ID and nulls rather than inventing these values.

## Contract and mapping

The receiver accepts a normalized envelope from an email parser (or a future verified webhook):

```json
{
  "transport": "email_bridge",
  "call": {
    "external_call_id": "required stable Marblism call ID or stable email Message-ID",
    "direction": "inbound",
    "caller_phone": "+19105551212",
    "caller_name": "optional",
    "timestamp": "ISO-8601",
    "duration_seconds": null,
    "is_test": false,
    "test_number": "+19103955193",
    "summary": "platform Call Analysis",
    "transcript": null,
    "recording_url": null,
    "outcome": "human_follow_up_required",
    "extracted_answers": {
      "organization": null,
      "requested_credential": null,
      "deadline": null,
      "location": null,
      "flexibility": null,
      "preferred_windows": [],
      "alternate_windows": [],
      "group_size": null,
      "unresolved_questions": [],
      "escalation_flags": []
    }
  }
}
```

Unknowns remain null/empty. The bridge must not infer them from unrelated records.

## Durable destination

- `customers`: existing authoritative person/customer record; match by uniquely normalized caller phone only. Ambiguous or absent matches remain null.
- `phone_call_events`: immutable inbound event, full raw payload, transcript/recording reference, test flag, and matched customer link. This is necessary because no existing table represents telephony events.
- `phone_intakes`: structured scheduling/request interpretation and action-required state. This is not a registration and cannot schedule.
- `production_board_cards`: the existing operational queue receives one `NEW PHONE INTAKE` card for each non-test event.
- `production_board_activity`: existing audit trail records creation and links the call event, intake, external ID, and customer match.
- Organization is retained on the intake until a verified organization model is available; no organization record is auto-created.
- `maxim_registration_requests` is intentionally not used because it is customer-specific and represents registration state, not unverified telephone intent.

## Authentication and idempotency

Proposed endpoint: `POST /functions/v1/rachel-intake` with a high-entropy `x-rachel-intake-secret`, stored only as a Supabase function secret and in the mail bridge. The function hashes both values before constant-time comparison. Production should additionally restrict the bridge's outbound IP if its provider publishes stable ranges and rotate the secret on suspected disclosure.

Uniqueness is `(source, external_call_id)`. A transactional database function inserts the call event, intake, queue card, and audit row atomically. Retries return the original call event and never create another card; a partial downstream failure rolls the whole operation back. Operational events without a stable external ID are rejected. Preferred key order: Marblism call ID; otherwise RFC Message-ID from the one-email-per-call notification. Content hashes are unsuitable as primary IDs because summaries/templates can change.

## Test exclusion

An event is test when `is_test` is true or the normalized caller number equals the supplied dedicated test number. Test events are retained in `phone_call_events` for evidence and deduplication, then return `202 retained_test`; no `phone_intakes`, production-board card, scheduling, invoice, registration, or promise is created.

Before production, verify whether real Marblism email identifies test status directly. If it does not, the bridge must mark mail produced by the known testing workflow/number and quarantine uncertain messages instead of treating them as real.

## Missing information Rachel should collect

For training requests: exact credential and certifying body; initial/renewal/skills-only; deadline and why it matters; city/site and onsite-versus-office preference; time/date flexibility; preferred and alternate windows; group size; caller name, callback number, email, and organization; existing registration/class identifiers for changes; unresolved questions; and escalation reasons. Rachel must continue to say availability and policy require human verification.

## Privacy and recording risks

- Callers need legally appropriate recording/AI notice; consent rules vary by caller location.
- Transcripts and recordings may contain medical, payment, minor, employer, or other sensitive data. Do not collect card data or unnecessary health details.
- Recording URLs may be bearer links or expire. Store references only until access controls and retention are verified; never make them public or copy recordings by default.
- Limit service-role access, redact logs, define retention/deletion policy, and audit access.
- Email forwarding broadens the data path. Restrict the parser mailbox, validate sender/domain plus message authentication, and prevent arbitrary inbound email from becoming an intake.

## Implementation plan

1. Obtain one real standard Call Summary email with full headers and verify exact fields, Message-ID stability, sender authentication, test markers, and whether transcript/recording links exist.
2. Configure a dedicated inbound parser to allow only authenticated Marblism summary messages and map them to the normalized contract.
3. Apply the migration and deploy the Edge Function first to a non-production Supabase project with secrets.
4. Replay the checked-in test fixture and duplicate; verify one retained test event and zero operational cards.
5. Replay synthetic real/duplicate/ambiguous-customer cases; verify exactly one card per external ID and no scheduling-side tables touched.
6. Review privacy, consent, retention, recording-link authorization, alerting, and dead-letter/quarantine behavior.
7. Only after review, point the mail bridge at production. Never permit this endpoint to schedule, invoice, register, send messages, or promise availability.
