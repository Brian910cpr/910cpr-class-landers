# RRULE Expansion Fix Report

Status: implemented and regenerated locally. No deploy was performed.

## What Changed

`scripts/export_calendar_snapshots.py::parse_ics_events` now expands bounded RRULE/RDATE instances inside the requested snapshot range, preserves duration, supports UNTIL/COUNT/BYDAY/INTERVAL through python-dateutil, applies EXDATE, and suppresses generated occurrences when a RECURRENCE-ID override exists.

## Before / After

- Live snapshot range before: 2026-06-29 to 2026-08-28
- Live snapshot range after: 2026-06-29 to 2026-08-28
- August live availability blocks before: 29
- August live availability blocks after: 29
- August dynamic BLS offers before: 0
- August dynamic BLS offers after: 6666
- August selected seeds before: 0
- August selected seeds after: 2

## Safety Gates

Expanded recurrence creates availability candidates only. Downstream occupancy checks, duration/buffer checks, public sellable filtering, Course Master-related suppression, appointmentDayId/courseId URL preview, UNKNOWN course suppression, and public offer integrity remain separate downstream gates.

## Render Scope

No public page/render build was run for this RRULE fix branch. The task was kept to snapshot, dynamic, public-filter, seed, URL-preview, and audit generation.
