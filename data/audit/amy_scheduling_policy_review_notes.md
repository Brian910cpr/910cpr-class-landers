# Amy Scheduling Policy Review Notes

Generated: 2026-06-28T10:35:00

## Addressed Findings

1. Date/source verification: added `amy_availability_source_trace` with source calendar key, event IDs, titles, raw/UTC/local timestamps, grouped window, preferred anchor start, and grouping rule.
2. Amy identity mapping: proposed policy now applies to `instructor_4180671442`, `amy`, and `a___arnold`; dynamic candidates use `instructor_4180671442`.
3. Candidate timestamp resolution: added `resolved_amy_candidate_rows` with timing/course/window/instructor/location/scheduler consumption and violation flags.
4. Standing versus dated config: proposed `data/config/instructor_scheduling_policy.json` standing policy is separate from calendar-derived window records.
5. Existing public non-dynamic Amy records: added `existing_public_non_dynamic_amy_table` and markdown table.
6. Remote main changed: added `remote_main_change_report`; no pull/reset/merge/deploy was run.

## Production Check Evidence

Checked `https://www.910cpr.com/data/schedule_future.json`. HTTP `200`. Matches origin/main `0a2e0d`: `True`. Matches `f8db04`: `False`.

## Test Decision

No code or scripts were changed. Per request, tests are only required if code/scripts changed. The prior validation remains `137 tests OK`.
