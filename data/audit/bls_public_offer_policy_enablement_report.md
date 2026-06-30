# BLS Public Offer Policy Enablement Report

Status: read-only audit. No deploy was performed.

## Policy Change

Enabled only these reviewed AHA BLS course IDs in `data/config/public_offer_policy.json`: `209806`, `359474`, `210549`.

## Before / After

- Before August BLS public sellable offers: 0
- After August BLS public sellable offers: 24
- Before August BLS selected seeds: 0
- After August BLS selected seeds: 6
- After August total selected seeds: 6
- After real August BLS Enrollware rows: 3

## Course ID Decisions

| courseId | Name | course_key | Destination | Enabled now | Reason |
| --- | --- | --- | --- | --- | --- |
| 209806 | AHA BLS Provider | aha_bls_provider | docs/bls.html#bls-provider | True | Reviewed AHA BLS course ID; enabled narrowly in public_offer_policy so existing public filters and seed strategy can evaluate it. |
| 359474 | AHA BLS Provider Renewal | aha_bls_provider_renewal | docs/bls.html#bls-renewal | True | Reviewed AHA BLS course ID; enabled narrowly in public_offer_policy so existing public filters and seed strategy can evaluate it. |
| 210549 | AHA HeartCode BLS | aha_heartcode_bls | docs/bls.html#bls-heartcode | True | Reviewed AHA BLS course ID; enabled narrowly in public_offer_policy so existing public filters and seed strategy can evaluate it. |

## Seed Count Sanity

- August looks alive enough after this policy change: True
- Selector assessment: `reasonable_conservative`
- Reason: Four BLS seeds are selected across two Monday/Tuesday pairs in August, supplementing existing real August BLS Enrollware inventory.

Large generated preview files remain tracked on this branch for review reproducibility; see `public_offer_policy_safety_check.md` for sizes and recommendation.
