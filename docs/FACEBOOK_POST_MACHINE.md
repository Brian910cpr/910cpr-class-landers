# 910CPR Facebook Post Machine

The Facebook Post Machine is an internal control-center module for drafting, reviewing, copying, approving, and manually posting 910CPR Facebook Page content.

It does not publish to Facebook yet. Meta tokens are not exposed to the browser, and Meta API posting remains disabled.

## Modes

### Static GitHub Pages Mode

Use this when the dashboard is served from GitHub Pages with no backend.

- Reads `data/facebook_post_queue.json`.
- Displays draft cards.
- Allows `Copy Post` and `Copy Link`.
- Allows browser-local preview status for `Approve`, `Reject`, and `Mark Manually Posted`.
- Shows: `Static Mode: changes are local to this browser and not saved to repo.`

Static mode cannot write to repo JSON files. It is useful for manual posting, review, and copy/paste workflows.

### Admin Server Mode

Use this when a local or Render admin backend is running.

- Detects an admin API through `GET /api/facebook-post-machine/status`.
- Loads queue data through `GET /api/facebook-post-machine/queue`.
- Persists edits through `POST /api/facebook-post-machine/save`.
- Persists status changes through `POST /api/facebook-post-machine/status-update`.
- Creates drafts through `POST /api/facebook-post-machine/create`.
- Exports approved/manual-ready posts through `GET /api/facebook-post-machine/export-approved`.

Admin mode requires `ADMIN_TOKEN`. The token is sent from the dashboard as `X-Admin-Token` and must match the server environment variable. Do not commit real tokens.

## Local Admin Server

From the repo root:

```powershell
python -m pip install -r requirements.txt
$env:ADMIN_TOKEN="set-a-local-token"
python scripts\fb_post_machine_admin.py
```

Open:

```text
http://127.0.0.1:8011/docs/control-center/modules/facebook-post-machine.html
```

Enter the same admin token in the dashboard. Leave the Admin API base URL blank for same-origin local admin mode.

## Render Admin Mode

The repo includes `render.yaml`, `requirements.txt`, and `runtime.txt` for a Render web service.

Render start command:

```text
gunicorn scripts.fb_post_machine_admin:app --bind 0.0.0.0:$PORT
```

Set environment variables in the Render dashboard:

```text
ADMIN_TOKEN=<strong random token>
FB_POST_DRY_RUN=true
META_PAGE_ID=
META_PAGE_ACCESS_TOKEN=
```

Use the Render service URL as the dashboard Admin API base URL, for example:

```text
https://your-service.onrender.com
```

When the dashboard is served from GitHub Pages, browser requests go cross-origin to Render. The admin server sends CORS headers and requires `ADMIN_TOKEN` for protected endpoints.

### First Deploy Checklist

1. Create a Render Web Service from this repo.
2. Use the included `render.yaml` or set the start command to `gunicorn scripts.fb_post_machine_admin:app --bind 0.0.0.0:$PORT`.
3. Set `ADMIN_TOKEN` to a strong random value.
4. Set `FB_POST_DRY_RUN=true`.
5. Deploy the service.
6. Open `/api/facebook-post-machine/status` on the Render service URL.
7. Open the Facebook Post Machine dashboard.
8. Enter the Render service URL as the Admin API base URL.
9. Enter the same `ADMIN_TOKEN`.
10. Connect dashboard to Render API URL.

## Security Notes

- `ADMIN_TOKEN` is required for queue reads through the admin API and for all writes.
- Meta tokens stay server-side only.
- This version does not call Meta Graph API.
- Do not commit `.env` or real token values.

## Data Files

- `data/facebook_post_queue.json` - draft queue and persisted status.
- `data/facebook_post_history.json` - manual-post history records.
- `data/facebook_cadence_rules.json` - cadence defaults.
- `data/facebook_topic_rules.json` - reusable topic/audience rules.

## Current Workflow

1. Open the dashboard.
2. Use static mode for copy/paste only, or connect admin mode with a Render/local API URL and `ADMIN_TOKEN`.
3. Edit draft text and links in admin mode.
4. Save draft changes.
5. Approve, reject, or mark manually posted.
6. Export approved/manual-ready posts as Markdown when needed.

## Not Included Yet

- No Meta Page post publishing.
- No Facebook Events automation.
- No browser automation for Facebook.
- No committed secrets.
