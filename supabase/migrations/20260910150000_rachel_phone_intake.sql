create table public.phone_call_events (
  id uuid primary key default gen_random_uuid(),
  source text not null default 'marblism_rachel',
  transport text not null check (transport in ('email_bridge','webhook','manual_fixture')),
  external_call_id text not null,
  direction text not null default 'inbound',
  caller_phone text,
  caller_name text,
  started_at timestamptz,
  duration_seconds integer check (duration_seconds is null or duration_seconds >= 0),
  is_test boolean not null default false,
  summary text,
  transcript text,
  recording_url text,
  outcome text,
  extracted_answers jsonb not null default '{}'::jsonb,
  raw_payload jsonb not null,
  matched_customer_id uuid references public.customers(id),
  received_at timestamptz not null default now(),
  unique (source, external_call_id)
);

create table public.phone_intakes (
  id uuid primary key default gen_random_uuid(),
  call_event_id uuid not null unique references public.phone_call_events(id),
  customer_id uuid references public.customers(id),
  organization_name text,
  requested_credential text,
  deadline text,
  requested_location text,
  flexibility text,
  preferred_windows jsonb not null default '[]'::jsonb,
  alternate_windows jsonb not null default '[]'::jsonb,
  group_size integer check (group_size is null or group_size > 0),
  unresolved_questions jsonb not null default '[]'::jsonb,
  escalation_flags text[] not null default '{}',
  status text not null default 'action_required' check (status in ('action_required','reviewing','resolved','dismissed')),
  production_board_card_id uuid unique references public.production_board_cards(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index phone_call_events_phone_idx on public.phone_call_events(caller_phone);
create index phone_call_events_received_idx on public.phone_call_events(received_at desc);
create index phone_intakes_status_idx on public.phone_intakes(status, created_at desc);

alter table public.phone_call_events enable row level security;
alter table public.phone_intakes enable row level security;
revoke all on public.phone_call_events, public.phone_intakes from anon, authenticated;
grant select, insert, update on public.phone_call_events, public.phone_intakes to service_role;

create or replace function public.create_phone_intake_event(p_event jsonb, p_intake jsonb)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  call_row public.phone_call_events;
  intake_row public.phone_intakes;
  card_row public.production_board_cards;
  inserted boolean := false;
begin
  insert into public.phone_call_events (
    source, transport, external_call_id, direction, caller_phone, caller_name,
    started_at, duration_seconds, is_test, summary, transcript, recording_url,
    outcome, extracted_answers, raw_payload, matched_customer_id
  ) values (
    p_event->>'source', p_event->>'transport', p_event->>'external_call_id', coalesce(p_event->>'direction','inbound'),
    p_event->>'caller_phone', p_event->>'caller_name', (p_event->>'started_at')::timestamptz,
    (p_event->>'duration_seconds')::integer, coalesce((p_event->>'is_test')::boolean,false),
    p_event->>'summary', p_event->>'transcript', p_event->>'recording_url', p_event->>'outcome',
    coalesce(p_event->'extracted_answers','{}'::jsonb), p_event->'raw_payload', (p_event->>'matched_customer_id')::uuid
  )
  on conflict (source, external_call_id) do nothing
  returning * into call_row;

  inserted := call_row.id is not null;
  if not inserted then
    select * into call_row from public.phone_call_events
      where source=p_event->>'source' and external_call_id=p_event->>'external_call_id';
    return jsonb_build_object('status','duplicate','call_event_id',call_row.id,'test',call_row.is_test);
  end if;

  if call_row.is_test then
    return jsonb_build_object('status','retained_test','call_event_id',call_row.id,'operational_item_created',false);
  end if;

  insert into public.production_board_cards(title,project,owner,lane,value_score,work_score,summary,details,flags,brian_override)
  values ('NEW PHONE INTAKE','Phone Intake','Brian','next',9,2,coalesce(p_event->>'summary','Rachel call requiring human follow-up'),
    p_intake->>'rendered_details',array['CUSTOMER IMPACT','ACTION REQUIRED'],false)
  returning * into card_row;

  insert into public.phone_intakes (
    call_event_id, customer_id, organization_name, requested_credential, deadline,
    requested_location, flexibility, preferred_windows, alternate_windows, group_size,
    unresolved_questions, escalation_flags, production_board_card_id
  ) values (
    call_row.id, call_row.matched_customer_id, p_intake->>'organization_name', p_intake->>'requested_credential',
    p_intake->>'deadline', p_intake->>'requested_location', p_intake->>'flexibility',
    coalesce(p_intake->'preferred_windows','[]'::jsonb), coalesce(p_intake->'alternate_windows','[]'::jsonb),
    (p_intake->>'group_size')::integer, coalesce(p_intake->'unresolved_questions','[]'::jsonb),
    coalesce(array(select jsonb_array_elements_text(coalesce(p_intake->'escalation_flags','[]'::jsonb))),array[]::text[]), card_row.id
  ) returning * into intake_row;

  insert into public.production_board_activity(card_id,action,detail,actor)
  values (card_row.id,'phone_intake_created',jsonb_build_object('call_event_id',call_row.id,'phone_intake_id',intake_row.id,
    'external_call_id',call_row.external_call_id,'matched_customer_id',call_row.matched_customer_id),'Rachel intake receiver');

  return jsonb_build_object('status','created','call_event_id',call_row.id,'phone_intake_id',intake_row.id,
    'production_board_card_id',card_row.id,'matched_customer_id',call_row.matched_customer_id);
end;
$$;

revoke all on function public.create_phone_intake_event(jsonb,jsonb) from public, anon, authenticated;
grant execute on function public.create_phone_intake_event(jsonb,jsonb) to service_role;
