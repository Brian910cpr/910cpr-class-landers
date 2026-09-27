-- Private input contract for verified cash/bill ingesters. Never store balances in public assets.
create table if not exists public.owner_dashboard_finance_snapshots (
  id uuid primary key default gen_random_uuid(),
  observed_at timestamptz not null,
  expires_at timestamptz not null,
  obligations_through timestamptz not null,
  source text not null,
  payload jsonb not null,
  created_at timestamptz not null default now(),
  check (expires_at > observed_at),
  check (jsonb_typeof(payload) = 'object')
);
alter table public.owner_dashboard_finance_snapshots enable row level security;
revoke all on public.owner_dashboard_finance_snapshots from anon, authenticated;
grant select, insert on public.owner_dashboard_finance_snapshots to service_role;
create index if not exists owner_dashboard_finance_observed_idx on public.owner_dashboard_finance_snapshots (observed_at desc);

create or replace function public.owner_dashboard_snapshot()
returns jsonb language sql stable security invoker set search_path = public, pg_temp as $$
with missing_cards as (
  select r.id registration_id, r.customer_id, s.id session_id, s.start_at,
         coalesce(c.name,'Course unknown') course_name,
         concat_ws(' ',p.first_name,p.last_name) person_name
  from registrations r
  join class_sessions s on s.id=r.class_session_id
  left join courses c on c.id=s.course_id
  left join customers p on p.id=r.customer_id
  where s.record_scope='operational' and s.status in ('scheduled','active','completed')
    and s.end_at <= now()
    and r.status in ('registered','confirmed','completed')
    and (r.status='completed' or exists (
      select 1 from participant_completions pc where pc.registration_id=r.id
      and pc.completion_status in ('passed','completed')
    ))
    and nullif(trim(r.historical_ecard_code),'') is null
    and not exists (select 1 from participant_credentials cr where cr.registration_id=r.id
      and cr.status in ('issued','active','claimed','expired')
      and nullif(trim(cr.credential_number),'') is not null)
), card_classes as (
  select session_id,start_at,course_name,count(*) people,
    jsonb_agg(jsonb_build_object('id',customer_id,'name',person_name) order by person_name) participants
  from missing_cards group by session_id,start_at,course_name
), products_due as (
  select oi.id,oi.description,oi.quantity,oi.fulfillment_status,
    o.status order_status, o.paid_at, r.class_session_id session_id,
    r.customer_id,concat_ws(' ',c.first_name,c.last_name) person_name,p.name product_name
  from registration_order_items oi
  join registration_orders o on o.id=oi.order_id
  join registrations r on r.id=o.registration_id
  left join customers c on c.id=r.customer_id
  join products p on p.id=oi.product_id
  where oi.fulfillment_status in ('pending','awaiting_attention','reserved','awaiting_fulfillment','unfulfilled')
    and (p.fulfillment_mode in ('digital','electronic','digital_code','inventory_code','manual_digital')
      or p.product_type in ('ebook','online_course','digital','eproduct','electronic'))
    and r.status in ('registered','confirmed','completed')
    and o.status not in ('cancelled','canceled','refunded','expired','failed')
)
select jsonb_build_object(
  'generated_at',now(),
  'ecards',jsonb_build_object('class_count',(select count(*) from card_classes),
    'person_count',(select count(*) from missing_cards),
    'rows',coalesce((select jsonb_agg(x) from (select * from card_classes order by start_at desc limit 100) x),'[]'::jsonb),
    'scope','Recorded completions without linked eCard evidence; check issuance before issuing again.'),
  'products',jsonb_build_object('person_count',(select count(distinct customer_id) from products_due),
    'item_count',(select count(*) from products_due),
    'rows',coalesce((select jsonb_agg(x) from (select * from products_due order by paid_at nulls last,id limit 100) x),'[]'::jsonb)),
  'upcoming',coalesce((select jsonb_agg(x) from (
    select s.id,s.start_at,s.end_at,c.name course_name,l.name location_name,
      (select count(*) from registrations r where r.class_session_id=s.id and r.status in ('registered','confirmed','completed')) participant_count
    from class_sessions s left join courses c on c.id=s.course_id left join locations l on l.id=s.location_id
    where s.record_scope='operational' and s.status in ('scheduled','active')
      and s.end_at>=now() and s.start_at<now()+interval '7 days'
    order by s.start_at limit 8
  ) x),'[]'::jsonb),
  'board',coalesce((select jsonb_agg(x) from (
    select id,title,owner,lane,summary,flags,updated_at,implementation_status,context_manifest
    from production_board_cards where lane in ('doing','decision','next') order by brian_override desc,updated_at desc
  ) x),'[]'::jsonb),
  'finance',(select to_jsonb(f) from owner_dashboard_finance_snapshots f order by observed_at desc limit 1)
);
$$;
revoke all on function public.owner_dashboard_snapshot() from public, anon, authenticated;
grant execute on function public.owner_dashboard_snapshot() to service_role;
