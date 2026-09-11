-- The deployed historical class importer targets source_label directly.
-- These indexes make that existing conflict target valid. Preflight confirmed
-- there are no cross-source duplicate labels in production.
create unique index if not exists historical_course_aliases_source_label_uidx
  on public.historical_course_aliases(source_label);
create unique index if not exists historical_location_aliases_source_label_uidx
  on public.historical_location_aliases(source_label);
create unique index if not exists historical_instructor_aliases_source_label_uidx
  on public.historical_instructor_aliases(source_label);
