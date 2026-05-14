# Inventory Rule Configuration

This directory separates course consumption requirements from availability window permissions.

`course_consumption_rules.json` answers: what does this course require once scheduled?

`availability_window_policies.json` answers: what does this instructor/location/resource window permit?

The resolver must combine both, plus existing reservations and resource constraints, before publishing inventory. Appointment slot intervals only control potential start-time spacing. They do not define how much capacity a scheduled course consumes.

Do not attach block length or inventory consumption behavior to an instructor record. Instructor availability is limited to when the instructor may be used, where they may be used, and which course families they are eligible to teach.
