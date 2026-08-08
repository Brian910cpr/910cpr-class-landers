# Travel Calendar Event Materialization Handoff

## Status

- Branch: `codex/travel-calendar-events`
- Locally implemented and tested.
- Worker write gate remains disabled: `TRAVEL_EVENT_SYNC_ENABLED=false`.
- Guarded Worker deployed as Cloudflare version `0d2ae4c7-3f15-4248-8aea-e9707d0f8208` with `TRAVEL_EVENT_SYNC_ENABLED=false`.
- No Google Calendar events were created, updated, or deleted.

## Behavior

`POST /internal/travel-events/sync` accepts an authenticated recognized calendar-event change. For a timed event with an address it:

1. Calculates Shipyard-to-event and event-to-Shipyard driving routes once.
2. Applies an optional named-place minimum and route margin.
3. Creates or updates two deterministic, visible `TRAVEL — ...` Google Calendar events.
4. Links each generated event to the source event with private extended properties.
5. Deletes both generated travel events when the source event is deleted.
6. Ignores generated travel events to prevent recursive generation.
7. Uses a configured visible fallback duration when routing is unavailable.

The selector's prior implicit `apply_travel_time_rule` expansion was removed. Calendar occupancy now consumes stated event intervals only; explicit travel events provide the travel occupancy.

## Important rollout gate

Do not deploy the selector change before the Worker is configured and existing future off-site events have been backfilled with visible travel events. Removing implicit buffers first would temporarily expose extra public availability.

Required configuration/secrets:

- `TRAVEL_EVENT_SYNC_ENABLED=true` only after verification
- `TRAVEL_SYNC_WEBHOOK_SECRET`
- `TRAVEL_CALENDAR_ID` (recommended: Brian's existing DoNotSchedule calendar so current ICS ingestion sees the events)
- `GOOGLE_ROUTES_API_KEY`
- Google Calendar OAuth: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`
- Optional base address, fallback, margin, and named minimum JSON settings

The calendar ID, webhook secret, Routes API key, OAuth client ID, OAuth client secret, and OAuth refresh token are now installed as Cloudflare Worker secrets. Their values are not committed.

The upstream recognizer that sends complete create/move/address-change/delete payloads to the internal endpoint still needs to be connected. Native Google Calendar push notifications identify a changed resource but do not themselves contain the complete event record.

## Changed files

- `worker/travel-calendar-events.js`
- `worker/travel-calendar-events.test.mjs`
- `worker/free-time-offer-worker.js`
- `worker/.dev.vars.example`
- `wrangler.toml`
- `scripts/block_start_time_selector.py`
- `tests/test_block_start_time_selector.py`
- `.github/workflows/refresh-admin-availability.yml`

## Validation

```text
python -m py_compile scripts/block_start_time_selector.py tests/test_block_start_time_selector.py
PASS

python -m unittest \
  tests.test_block_start_time_selector.BlockStartTimeSelectorTests.test_offsite_events_are_not_silently_expanded_with_travel_time \
  tests.test_block_start_time_selector.BlockStartTimeSelectorTests.test_visible_travel_calendar_event_blocks_only_its_stated_interval \
  tests.test_block_start_time_selector.BlockStartTimeSelectorTests.test_travel_buffer_blocks_brian_but_not_shipyard_room_for_another_instructor
Ran 3 tests: OK

node --experimental-default-type=module --check worker/travel-calendar-events.js
PASS

node --experimental-default-type=module --check worker/free-time-offer-worker.js
PASS

node --experimental-default-type=module --test worker/travel-calendar-events.test.mjs
7 tests passed, 0 failed

wrangler deploy --dry-run --keep-vars --config wrangler.toml
PASS

Guarded production endpoint check
HTTP 503: {"status":"disabled","writesPerformed":false}

git diff --check
PASS
```

## Open operational questions

1. Confirm the destination calendar. Using Brian's existing DoNotSchedule calendar avoids adding a new ICS source and instructor mapping.
2. Decide what component recognizes Google event changes and calls the Worker endpoint.
3. Confirm Google Calendar write scope and Routes API billing/key restrictions.
4. Backfill future off-site events before enabling the selector change.
