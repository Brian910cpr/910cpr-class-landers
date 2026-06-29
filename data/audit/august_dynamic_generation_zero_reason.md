# August Dynamic Generation Zero Reason

Active dynamic generation produces zero August offers because its selected availability source is a nonempty live snapshot that has no August availability blocks.

- Dynamic availability source: `live_availability_snapshot`
- Dynamic availability reason: `valid_live_available_blocks_found`
- Live snapshot range: 2026-06-21 to 2026-07-04
- Seed simulation range: 2026-08-03 to 2026-09-14

Checked causes:

- Live snapshot stale or not refreshed: likely. Runtime snapshots stop at July 4.
- Live snapshot horizon too short: yes for August visibility.
- Current date/window cutoff: not the dynamic offer date filter; the upstream snapshot lacks August rows.
- Timezone conversion: not the first break.
- Source file mismatch: yes. Seed simulation uses report-only base-horizon windows; active generation uses live snapshot blocks.
- Occupancy/course duration/location/course/instructor filters: downstream, not reached for August.
- Course Master gates: downstream, not reached for August.
