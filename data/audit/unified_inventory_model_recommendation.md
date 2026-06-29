# Unified Inventory Model Recommendation

Use a single `course_location_inventory` artifact that merges Class Report rows first, then traceable appointment/dynamic/request rows. Public pages render stacked rows from this one model while preserving internal `row_source` metadata.

```json
{
  "recommended_output": "data/public/course_location_inventory.json",
  "status": "proposal",
  "row_sources": [
    "existing_enrollware_class",
    "appointment_seed",
    "dynamic_offer",
    "anchor_class",
    "request_only"
  ],
  "fields": [
    "course_key",
    "course_display_name",
    "course_family",
    "town",
    "location_name",
    "start_datetime_local",
    "end_datetime_local",
    "display_date",
    "display_time",
    "row_source",
    "booking_url",
    "button_text",
    "price",
    "public_status",
    "reason_if_hidden",
    "sort_order",
    "source_file",
    "source_id",
    "confidence"
  ]
}
```
