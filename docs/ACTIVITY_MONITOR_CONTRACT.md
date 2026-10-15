# Activity Monitor phase 1 preparation (#373)

BUILT only: pure server-side envelope constructor and local tests. No producers,
storage, API, polling, lights, or live integrations are enabled. P1 #371 / draft
PR #372 remains the primary stream. UI integration waits for its proven foundation.

## Design and authority

The operating problem is visibility into actual authorized operations without
inventing AI activity. The existing repository uses audit/provenance and explicit
operation state; reuse that mature separation between operational truth and its
display. No Enrollware training capability is replaced here. Native observability
supports independence without adding an Enrollware dependency. The activity event
owns telemetry only; cases, registrations and task records remain authoritative.

`scripts/activity_event_contract.mjs` defines version 1. Fields: schema_version,
event_id (opaque UUID), correlation_id (opaque UUID per operation attempt), source,
operation_type (server registry key), timestamp (UTC ISO with milliseconds), status,
duration_ms, visibility (owner/staff), safe_summary (fixed status text).
Use distinct event IDs for start/completion; preserve correlation. Retry attempts
receive new correlation IDs; transport replay preserves the original event ID.
Queued/in_flight/retry duration is null; success/blocked/error duration is a
nonnegative safe integer measured by the producer's monotonic clock. Producer
timestamps are server-side; never trust browser supplied lifecycle events.

Idle is a derived presentation state, not an event. A source enumeration is not
evidence of connection: only an explicitly instrumented server operation may
register a producer. The module has no default operation registry and accepts no
customer text, arbitrary error messages, URLs, credentials, or freeform summaries.
The registry must be static server-owned code; dynamic/customer-derived keys would
defeat this boundary. Opaque IDs must never encode external/customer identifiers.
Actionable error codes/recovery hints need a reviewed fixed catalog before adding
them; raw exception text must stay outside telemetry.

## Next backend slice (not implemented)

After coordination with P1, wrap one existing owner-authorized read-only operation:
emit start and success/error around its actual execution, without changing its
result or adding blocking telemetry failures. No network request per event in the
critical path. Use a bounded asynchronous sink; cap queue and drop with aggregate
loss counters rather than delaying registration/payment/scheduling.

Storage/transport gate: reuse existing backend owner authentication, reject
unauthorized reads/writes before telemetry access, isolate owner events from staff
with server-side authorization (never browser filtering). No public event endpoint.
Enforce deduplication on event_id and order on server receipt sequence. Initial
proposed retention: maximum 24 hours and 1,000 events per owner, whichever is less;
cleanup must be proven before enabling persistent producers. This is a proposal,
not an installed retention policy. Do not store private operational payloads.

Poll only an authenticated, visible, enabled dashboard; stop on hide/sign-out and
back off on failures. Return server time, last observation, instrumented sources,
connection state and loss counts separately from events. Freshness/connection must
never be inferred from an empty list or an old success. Unknown/missing integrations
stay disconnected; stale in-flight operations become unknown, not success.

## Proof and monitoring gate

Expected useful proof: one real owner request -> sanitized start/terminal events
in owner transport -> corresponding accessible light/log. No such proof exists
yet; tests are local fixtures, never live events. Test auth isolation, duplicates,
failure/drop behavior, retention and performance before connection; then verify
light/dark, reduced motion, keyboard, screen reader, hide/collapse and log escaping.

Proposed freshness window: 60 seconds for active polling; producer timeout must be
operation-specific. Observer: backend operational health plus dashboard freshness;
observer health requires its own current heartbeat and independent stale detector.
Neither exists for this feature yet. Recovery: disable flag, inspect sanitized sink
health, repair auth/producer, re-prove a real request. Escalate only account access
or business-policy decisions to Brian; he must not routinely monitor this strip.
No HEALTHY/MONITORED claim until the end-to-end observer and its own health are
proven. UI and remaining acceptance criteria are dependency-gated, not completed.

Validation: `node --check scripts/activity_event_contract.mjs` and
`node --test tests/activity_event_contract.test.mjs`.
