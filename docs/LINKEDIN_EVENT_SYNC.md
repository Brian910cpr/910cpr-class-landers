# LinkedIn Event Sync

This interface publishes real, seated public classes from
`docs/data/schedule_future.json` as LinkedIn Page Events. Dynamic appointment
possibilities are intentionally excluded.

## Safety model

- Dry-run is the default.
- Only future, active, open, directly bookable sessions at configured public
  location prefixes are eligible.
- A configured address must match before an Event can be planned.
- `promoted_session_ids` can include a deliberately promoted future session,
  but it does not bypass the public-address requirement.
- State is written after every successful API change to prevent duplicates.

## Dry-run

```powershell
python scripts/linkedin_event_sync.py --output debug/linkedin_event_plan.json
```

Review `eligible_count`, every event payload, and the skipped reasons before a
live run.

## Required LinkedIn configuration

After LinkedIn approves the developer application:

1. Add the 910CPR organization URN to `data/linkedin_event_sync.json` or set
   `LINKEDIN_ORGANIZATION_URN`.
2. Upload/approve the course cover asset and add its asset URN to the config or
   set `LINKEDIN_EVENT_BACKGROUND_IMAGE_URN`.
3. Store the OAuth token outside the repository as `LINKEDIN_ACCESS_TOKEN`.
4. The token must include `rw_events` and the organization posting permission
   granted with the approved Event Management/Community Management products.

## Live synchronization

```powershell
$env:LINKEDIN_ACCESS_TOKEN = "..."
python scripts/linkedin_event_sync.py --apply
```

Never commit access tokens. Live execution is intentionally unavailable until
LinkedIn approves the app and the required organization scopes are granted.

## GitHub Actions

The `LinkedIn Event Sync` workflow is manual-only during rollout. Its defaults
are safe: dry-run with at most one changed Event when apply is enabled. Review
the uploaded audit report and the resulting LinkedIn Event before increasing
the batch size.

Repository secrets:

- `LINKEDIN_ACCESS_TOKEN` (fallback; current access token)
- `LINKEDIN_REFRESH_TOKEN`
- `LINKEDIN_CLIENT_ID`
- `LINKEDIN_CLIENT_SECRET`
- `LINKEDIN_ORGANIZATION_URN`
- `LINKEDIN_EVENT_BACKGROUND_IMAGE_URN` (optional)
