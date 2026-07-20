# August Dynamic Generation Zero Reason

Active dynamic generation no longer produces zero August offers. RRULE expansion now gives the live snapshot August availability blocks, and dynamic generation evaluates August offers from that source.

- Dynamic availability source: `live_availability_snapshot`
- Dynamic availability reason: `valid_live_available_blocks_found`
- Live snapshot range: 2026-07-14 to 2026-11-11
- Seed simulation range: 2026-08-03 to 2026-09-14

Checked causes:

- Live snapshot stale or not refreshed: no after RRULE expansion
- Live snapshot horizon too short: no for current August audit range
- Current date/window cutoff: not the dynamic offer date filter; the upstream snapshot lacks August rows.
- Timezone conversion: not the first break.
- Source file mismatch: resolved. Both paths now expose August rows before downstream gates.
- Occupancy/course duration/location/course/instructor filters: downstream.
- Course Master gates: downstream.
