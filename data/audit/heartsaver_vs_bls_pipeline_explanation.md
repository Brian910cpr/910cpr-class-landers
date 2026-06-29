# Heartsaver vs BLS/ACLS/PALS Pipeline Explanation

Heartsaver grouping is primarily defined in `data/config/slug_hubs.json`, `scripts/build_slug_hubs.py`, `data/config/course_catalog.json`, and `data/config/course_map.json`.

BLS/ACLS/PALS grouping is also defined in `data/config/slug_hubs.json` and rendered through `scripts/build_slug_hubs.py`, but those families are simpler tab structures around provider/renewal/HeartCode paths.

Heartsaver has more buyer variants: CPR AED only, First Aid CPR AED, pediatric options, online+skills, classroom, group/workplace, and adjacent HSI/ARC alternatives. That explains the extra guidance, but it should still render from the same stacked inventory model: course/date/time/location/button.

Current Heartsaver check/request behavior is real appointment-seed output when it has `appointmentDayId` links and `data-source-offer-id`, but it is not broad August coverage. It should be treated as a growth layer, not the August safety net.
