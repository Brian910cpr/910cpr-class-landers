# Maxim Hot_sync Direct Registration MVP

Generated: 2026-07-28

## Summary

This branch fixes the Maxim class-date display path and adds a direct Maxim registration MVP that writes to Hot_sync/Supabase after validating the chosen slot against the existing 910CPR resolved availability. It does not create a separate calendar, does not make the Maxim UI independently decide sellability, and does not send real emails.

## Timezone Audit And Fix

The Maxim page previously rendered class timestamps in the browser from raw timestamp values. That can display the wrong wall time when legacy/imported values were stored as if Eastern wall time were UTC. The API now returns `classDateDisplay`, a display-ready class-time label.

Display priority is now:

1. `status_detail` registered wall-time label, when present.
2. Direct Hot_sync `class_date` plus `start_time`, when present.
3. Raw timestamp formatted in America/New_York as a last fallback.

The page uses `classDateDisplay` first and only falls back to its own Eastern timestamp formatter when no API display label exists.

The direct registration path still uses `easternTimestamp(date, startTime)`, so a selected 9:15 AM Eastern class is stored as the correct UTC instant.

## Direct Registration Path

The Maxim portal already validates schedule choices through `canonicalCourseSlot()` against `/data/block-selector-availability/{bls,heartsaver}.json`. This MVP preserves that resolver as the source of truth.

Flow:

1. Maxim user selects an employee, course, location, date, and start time.
2. Edge Function revalidates the exact canonical slot.
3. Edge Function writes `maxim_registration_requests` through `maxim_replace_registration`.
4. Registration is marked with `registration_source = maxim_portal_hot_sync`.
5. Course date, start time, timezone, and source booking URL are stored for audit.
6. Simulated student/internal email payloads are stored and returned.

The Maxim registration path no longer requires an Enrollware registration URL. `registration_url` is written as `null` for direct Hot_sync registrations. Any canonical Enrollware/source URL remains only in `source_booking_url` for audit context.

## Simulated Emails

No Gmail, Postmark, or other mail provider is called. The Edge Function builds two JSON email payloads:

- `maxim_student_registration_confirmation`
- `maxim_internal_registration_notice`

Both include `sendMode: simulated`. They are persisted in `simulated_email_payloads` and returned in the registration response for review.

## Data Model

New migration:

`supabase/migrations/20260728093000_maxim_hotsync_direct_registration_simulated_emails.sql`

Adds:

- `registration_source`
- `source_booking_url`
- `class_date`
- `start_time`
- `timezone`
- `simulated_email_payloads`
- `simulated_email_created_at`

## Standing Order Scope

For this project, a narrow standing order is accepted for simulated Gmail-style/email outputs and reports only. I will not send, archive, label, modify, or otherwise act on Gmail or real email delivery without explicit per-action approval.

## Validation

Passed:

- `python -m unittest tests.test_maxim_corporate_portal`
- `node -e "...parse docs/corp/maxim.html inline scripts..."`
- `python -m scripts.public_offer_integrity_audit`

Full discovery attempted:

- `python -m unittest discover -s tests`

Result: not clean in this worktree. Failures were caused by missing ignored/generated runtime artifacts such as `data/runtime/audit_previews/dynamic_offers_preview.json` and `data/sessions_current.json`, plus existing unrelated public-generation baseline expectations. The targeted Maxim tests passed and public offer integrity remained `Audit failed: False`.

## Deployment Status

Not deployed.

## Deploy Readiness

Not ready to deploy until the Supabase migration and Edge Function changes are reviewed and explicitly approved for production deployment.
