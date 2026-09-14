# Issue 235: Deployment verification

- Timestamp: 2026-09-14 16:51 UTC
- Branch: `main`
- Pull request: `#236`
- Squash merge commit: `5d2c1d959dc76d152a6296bf9dc2c64fbd46870d`
- Work-item state: `VERIFIED` for public messaging and page continuity; `BUILT` for overnight inventory pending a fresh eligible production offer.

## Production verification

- Source-integrity and Cloudflare preflight checks passed before merge.
- Browser checks confirmed `/BLS`, `/ACLS`, `/PALS`, and `/HEARTSAVER` each display “Same-day eCards.”
- Browser checks confirmed each page displays the daytime/evening/overnight verified-availability message.
- All four pages retain their existing SEO title and selector shell.
- No additional funnel or registration click was introduced.

## Operational status

- The production policy now permits starts from `00:00` through `23:45` on the existing quarter-hour grid.
- No blocker logic was changed. Existing availability, occupancy, school/calendar, ADR/travel buffer, duration, lead-time, caps, and fail-closed checks still determine whether a time becomes public.
- A real overnight public offer has not yet been observed. The expanded-hour system therefore remains `BUILT`, not `PROVEN` or `HEALTHY`, until a fresh successful availability cycle finds and publishes a genuinely free overnight interval.

## Next evidence needed

Observe a fresh public availability cycle. If an overnight interval is actually free, verify the selector presents it with the correct course, location, duration, appointmentDayId, and unchanged Enrollware registration URL. If no overnight interval is free, the absence of an offer is correct behavior.
