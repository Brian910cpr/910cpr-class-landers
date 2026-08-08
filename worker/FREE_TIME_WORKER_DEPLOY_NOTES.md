# Free-Time Offer Worker Deployment Notes

This Worker is safe confirmation-page scaffolding only. Enrollware creation is not wired, and the deployment config keeps creation disabled:

- `CREATION_ENABLED=false`
- `DRY_RUN=true`
- `ALLOW_PUBLIC_CREATION=false`

## DNS Requirement

`schedule.910cpr.com` must exist in Cloudflare DNS for the `910cpr.com` zone and must be proxied through Cloudflare. The Worker route is:

```text
schedule.910cpr.com/*
```

Keep `offer_click_target.enabled=false` in the static site until the Worker route is verified.

## Local Dev Test

```powershell
cd E:\GitHub\910cpr-class-landers
$env:OFFER_DATA_JSON = Get-Content -Raw .\docs\data\customer_facing_offers.json
$env:CREATION_ENABLED = "false"
$env:DRY_RUN = "true"
$env:ALLOW_PUBLIC_CREATION = "false"
npx wrangler dev --config wrangler.toml --local --port 8787
```

Expected local URL:

```text
http://127.0.0.1:8787/o/bls-renewal-wilmington-20260611-1245
```

Expected behavior:

- `GET /o/<offer_slug>` returns a confirmation page.
- `POST /open-registration` returns `501 Enrollware creation not wired`.
- No Enrollware class is created.

## Safe Deploy Command

Before deploying, verify the `free-time-offer-worker` has all of these production
bindings. The admin API deliberately fails closed when either authentication or
persistence is missing:

- Secret `HOT_SYNC_ADMIN_KEY`
- D1 database binding `HOT_SYNC_D1`, with `migrations/0001_admin_operations.sql` applied
- R2 bucket binding `LANDERWARE_INBOX`

The checked-in `wrangler.toml` does not contain resource IDs or secret values. Do
not guess them or create replacement storage during a routing repair. Add the
existing D1 and R2 resource identifiers to the deployment configuration (or
confirm they will be preserved by the deployment path) before deploying.

Run only after the binding check and explicit approval:

```powershell
cd E:\GitHub\910cpr-class-landers
npx wrangler deploy --config wrangler.toml
```

Expected deployed test URL:

```text
https://schedule.910cpr.com/o/bls-renewal-wilmington-20260611-1245
```

## Rollback

```powershell
npx wrangler rollback --name free-time-offer-worker
```

If needed, remove or disable the `schedule.910cpr.com/*` Worker route in Cloudflare after rollback.

## Storage Notes

Local testing may use `OFFER_DATA_JSON` from the shell. Do not commit `OFFER_DATA_JSON` or live offer data in Wrangler config. Production offer lookup should use trusted Worker-side storage such as KV, D1, R2, or current offer JSON loaded into a controlled binding.
