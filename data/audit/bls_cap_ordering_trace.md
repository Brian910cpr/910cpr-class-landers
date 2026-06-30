# BLS cap ordering trace

- Script: `scripts/filter_public_sellable_offers.py`
- Function: `apply_offer_limits`
- Previous cap sort: `(date, start_time, course_id)`
- Result of previous sort: earlier starts could consume `max_offers_per_course_per_week`, `max_offers_per_course_per_day`, and `max_total_offers_per_day` before BLS preferred times were evaluated.
- New AHA BLS cap sort: `(month, seed_strategy_policy BLS preferred time rank, date, start_time, course_id)`
- Scope: course IDs `209806`, `359474`, `210549` only.
- Safety gates: unchanged and still run before cap ordering.
- Cap counts: unchanged.
- Course ID enablement: unchanged.
