# Owner access migration published; account gate remains

- Timestamp: 2026-09-13T17:59:00Z
- Work-item state: BLOCKED
- Issue: #215; remaining account gate #140.
- PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/221
- Merge: 76ebb52aad9b292ad6c2be4a7a3e6399ef1674d2
- Production: https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/34772936739 (success).

The application migration is published. Eight owner pages share the session helper; NOW, ALL Classes, HOT_SYNC Class Admin and Admin Port use the same deployed HOT_SYNC authority. Owner APIs no longer fall back to Maxim sessions. Deployed versions: canonical-session-workspace 2, class-registry 3, instructor-workbench 3, production-board 5, owner-dashboard 3. Each rejects missing owner access with HTTP 401. Five endpoints share owner-auth.ts, which preserves a distinction between rejected credentials and authority outages. Corporate session-workspace remains at its verified version 2 baseline.

All 21 changed public HTML/JS files return HTTP 200 and byte-match the committed repair. Exact unversioned owner URLs also match. Live NOW and ALL Classes show the new helper and the expected owner access gates. Local private-fixture DOM checks cover all eight pages, including lock cleanup; 36 related Node tests, 3 Admin Port tests, 7 legacy baseline tests and the Maxim gate regression test pass. Production source-integrity and Cloudflare preflight checks are green.

Do not close #215. The latest post-owner-update #140 evidence still has HTTP 401 from GitHub's configured HOT_SYNC credential. This session has no Cloudflare secret-management capability, and no accepted owner credential was provided. No secret was read, guessed, rotated or inserted into source. An enabled public Supabase anon JWT is used only by the public group form; it is not owner access. The separate Finance Worker still requires deployed secret parity. Accepted-key owner/corporate browser proof and ongoing health are unverified. The next account action is to reconcile the deployed HOT_SYNC Worker secret with the intended GitHub Actions secret, then run the canonical verifier and publishers described in #140.
