# August BLS Seed Policy Recommendation

Recommendation: **B. Adjust selector to prefer known public-friendly time bands**, but only through existing config-driven policy.

Smallest safe rule change: update `data/config/seed_strategy_policy.json` `preferred_start_times_by_family.BLS` after Brian approves the desired BLS public time order. Do not hardcode times in selector code.

Current facts:

- Current BLS preferred starts: ['08:30', '09:00']
- Common requested bands checked: {'09:15': {'dynamic_candidate_count': 78, 'public_sellable_count': 0, 'dynamic_public_sellable_available': False, 'selected_count': 0, 'public_filter_hidden_reasons': {'max_offers_per_course_per_week_exceeded': 44, 'course_id_not_enabled': 26, 'course_family_disabled': 13, 'course_family_not_enabled': 13, 'max_total_offers_per_day_exceeded': 8}}, '12:30': {'dynamic_candidate_count': 78, 'public_sellable_count': 0, 'dynamic_public_sellable_available': False, 'selected_count': 0, 'public_filter_hidden_reasons': {'max_offers_per_course_per_week_exceeded': 44, 'course_id_not_enabled': 26, 'course_family_disabled': 13, 'course_family_not_enabled': 13, 'max_total_offers_per_day_exceeded': 8}}, '18:15': {'dynamic_candidate_count': 72, 'public_sellable_count': 0, 'dynamic_public_sellable_available': False, 'selected_count': 0, 'public_filter_hidden_reasons': {'max_offers_per_course_per_week_exceeded': 40, 'course_id_not_enabled': 24, 'course_family_disabled': 12, 'course_family_not_enabled': 12, 'max_total_offers_per_day_exceeded': 8}}, '18:45': {'dynamic_candidate_count': 72, 'public_sellable_count': 0, 'dynamic_public_sellable_available': False, 'selected_count': 0, 'public_filter_hidden_reasons': {'max_offers_per_course_per_week_exceeded': 40, 'course_id_not_enabled': 24, 'course_family_disabled': 12, 'course_family_not_enabled': 12, 'max_total_offers_per_day_exceeded': 8}}}
- `09:15`, `12:30`, `18:15`, and `18:45` exist as dynamic candidates (300 total), but they are not present in the current August BLS public-sellable set. Hidden reasons: {'max_offers_per_course_per_week_exceeded': 168, 'course_id_not_enabled': 100, 'course_family_disabled': 50, 'course_family_not_enabled': 50, 'max_total_offers_per_day_exceeded': 32}.
- The selector is not purely choosing earliest time; it is choosing the first available preferred BLS time, then title priority, then start time.
- Four BLS seeds across August 3, 4, 10, and 11 are reasonable but shallow; deeper August spread would require either a longer public sellable candidate window or a seed strategy that intentionally samples later weeks.
