-- Issue #150: complete future operational Session participant audit.
-- Roster names are intentionally queried at runtime and are not committed to a public artifact.
with future as (
  select cs.id as session_id, cs.start_at, c.name as course, l.name as location,
    cs.source, count(r.id) filter (where r.status in ('registered','confirmed','completed'))::int as canonical_count,
    coalesce(jsonb_agg(trim(concat_ws(' ',cu.first_name,cu.last_name)) order by cu.last_name,cu.first_name)
      filter (where r.status in ('registered','confirmed','completed')),'[]'::jsonb) as roster_names
  from public.class_sessions cs
  join public.courses c on c.id=cs.course_id
  join public.locations l on l.id=cs.location_id
  left join public.registrations r on r.class_session_id=cs.id
  left join public.customers cu on cu.id=r.customer_id
  where cs.start_at>=now() and cs.record_scope='operational'
    and cs.status in ('scheduled','active','completed')
  group by cs.id,c.name,l.name
)
select *, canonical_count as es_count, canonical_count as dashboard_count,
  canonical_count as workspace_count,
  array_remove(array[
    case when canonical_count is null then 'UNKNOWN_AS_ZERO' end
  ],null) as flags
from future
order by start_at;
