# BLS Initial native registration launch

## Implemented

- Per-student BLS manual choices: eBook ($17.49), physical manual with an official AHA direct-purchase link, or an existing current copy (default).
- Per-student First Aid choices: in-person ($50), online ($60), or none (default).
- Reserved image areas for each product choice.
- Per-student company Billing Code selection after three characters, with an optional first-student "same for all" control.
- Company codes are limited to AssistedCare, Breakthrough Autism, and the three Maxim company codes. They create a $0 customer checkout and retain the amount for the company's month-end invoice view; generic distributed codes are not exposed.
- Confirmation email includes the official AHA manual link when a physical manual or an existing copy is selected.
- Only BLS Initial real seated sessions route to `/register/?session=...`. Renewal, HeartCode, and appointment-generated BLS times remain on Enrollware.

## Live database and function work

- Applied and recorded migrations `20260930030000` and `20260930050000` directly through the authenticated Supabase management connection.
- Verified the live BLS catalog, per-student billing columns, and corporate invoice view.
- Deployed the `public-registration` Edge Function.

## Validation

- `python -m unittest tests/test_public_registration.py` — 10 passing.
- `node --check` on the registration page script — passing.
- `npx deno check supabase/functions/public-registration/index.ts` — passing.
- Verified `14501248` and `14135047` are the real BLS Initial seated sessions in the BLS availability data.

## Remaining deployment step

The browser page and BLS calendar route are committed on the launch branch and must be merged into `main` for GitHub Pages to publish them. The Edge Function and database changes are already live.

## Migration-history note

The remote Supabase history has many remote-only versions, so full `supabase db push` remains intentionally blocked. The two BLS migrations were applied directly, verified live, and recorded as applied; no blanket history repair was performed.
