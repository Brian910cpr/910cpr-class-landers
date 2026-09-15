# Requirement inquiry Edge Function

Public server-side relay for the “My employer or school gave me exact wording”
panel. The function validates and logs each inquiry, rate-limits by a salted IP
hash, and reports success only after Resend confirms email acceptance.

Required Supabase Edge Function secrets:

- `RESEND_API_KEY`: Resend API key for a verified 910CPR sending domain.
- `ADMIN_NOTIFY_EMAIL`: private administrative destination address.
- `REQUIREMENT_FROM_EMAIL`: verified sender, such as `website@910cpr.com`.
- `INQUIRY_HASH_SALT`: optional dedicated random salt for rate-limit hashes.

The function is intentionally deployed without JWT verification because the
website form is public. It compensates with an origin allowlist, honeypot,
minimum form-completion time, strict size and field validation, hourly rate
limiting, and a private RLS-enabled log table.
