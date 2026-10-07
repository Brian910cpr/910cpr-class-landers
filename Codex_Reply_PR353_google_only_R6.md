# PR353 Google-only instructor availability

Owner instruction: accept instructor availability only from Google Calendar, explicit or exception/inverse. Both generic offer selection and public-page selection now require google_calendar or inverse_google_calendar source types. Legacy instructor_availability.json fallback disabled. Missing/invalid/empty Google data produces no available windows, never manual free time. Existing approved inverse-source restrictions, coverage freshness, qualification checks and booking/occupancy preservation remain.

32 targeted Google-only, bounded coverage, publication and customer-render pipeline tests passed. Syntax validated. Old generic tests which explicitly expect legacy fallback describe retired behavior and require corresponding fixture updates; no claim that all repository tests were run/passed. New regressions directly prove rejection of manual/unknown sources and absence of legacy fallback. No generators or booking mutations.

Public activation not performed; existing review hold remains respected. Exact-head supported real-source probe dispatched following push, pending. Prior explicit coverage probe37623927050 succeeded.
