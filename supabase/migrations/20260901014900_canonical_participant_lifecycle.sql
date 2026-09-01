-- Dockmaster: one participant keeps one canonical ledger across every intake channel.

create table if not exists public.lifecycle_import_batches (
  id uuid primary key default gen_random_uuid(),
  batch_key text not null unique,
  source_system text not null,
  source_file_identity text,
  parser_version text not null,
  mode text not null default 'dry_run' check (mode in ('dry_run','pilot','full')),
  status text not null default 'prepared' check (status in ('prepared','running','review_required','completed','failed','reversed')),
  started_at timestamptz,
  completed_at timestamptz,
  reversed_at timestamptz,
  created_by text not null,
  summary jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.lifecycle_import_records (
  id uuid primary key default gen_random_uuid(),
  batch_id uuid not null references public.lifecycle_import_batches(id) on delete restrict,
  source_record_id text not null,
  entity_type text not null,
  source_document_identity text,
  original_values jsonb not null,
  proposed_values jsonb not null default '{}'::jsonb,
  confidence numeric(5,4),
  ambiguity_state text not null default 'unknown' check (ambiguity_state in ('unknown','exact','alias','new','ambiguous','rejected')),
  reconciliation_status text not null default 'pending' check (reconciliation_status in ('pending','matched','proposed','ambiguous','rejected','applied','unchanged','reversed')),
  customer_id uuid references public.customers(id),
  registration_id uuid references public.registrations(id),
  class_session_id uuid references public.class_sessions(id),
  error_reason text,
  applied_at timestamptz,
  reversed_at timestamptz,
  created_at timestamptz not null default now(),
  unique (batch_id, source_record_id, entity_type)
);

create table if not exists public.customer_identity_aliases (
  id uuid primary key default gen_random_uuid(),
  source_system text not null,
  source_identity text not null,
  customer_id uuid references public.customers(id) on delete restrict,
  resolution_status text not null check (resolution_status in ('matched','ambiguous','pending_review','rejected')),
  confidence numeric(5,4),
  candidate_customer_ids uuid[] not null default '{}',
  source_values jsonb not null default '{}'::jsonb,
  import_record_id uuid references public.lifecycle_import_records(id) on delete set null,
  resolved_by text,
  resolved_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (source_system, source_identity),
  check ((resolution_status = 'matched' and customer_id is not null) or resolution_status <> 'matched')
);

create table if not exists public.registration_supersessions (
  id uuid primary key default gen_random_uuid(),
  idempotency_key text not null unique,
  source_registration_id uuid not null references public.registrations(id) on delete restrict,
  target_registration_id uuid not null references public.registrations(id) on delete restrict,
  source_session_id uuid not null references public.class_sessions(id) on delete restrict,
  target_session_id uuid not null references public.class_sessions(id) on delete restrict,
  reason text not null,
  source text not null,
  actor jsonb not null,
  financial_policy text not null check (financial_policy in ('transfer','retain','none')),
  transferred_order_id uuid references public.registration_orders(id) on delete set null,
  occurred_at timestamptz not null default now(),
  details jsonb not null default '{}'::jsonb,
  check (source_registration_id <> target_registration_id),
  check (source_session_id <> target_session_id)
);

create table if not exists public.registration_requirements (
  id uuid primary key default gen_random_uuid(),
  registration_id uuid not null references public.registrations(id) on delete cascade,
  requirement_key text not null,
  requirement_type text not null,
  state text not null check (state in ('known','unknown','satisfied','unsatisfied','not_applicable','waived')),
  source text not null,
  notes text,
  satisfied_at timestamptz,
  satisfied_by text,
  superseded_from_requirement_id uuid references public.registration_requirements(id) on delete set null,
  provenance jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (registration_id, requirement_key)
);

create table if not exists public.registration_requirement_evidence (
  id uuid primary key default gen_random_uuid(),
  registration_requirement_id uuid not null references public.registration_requirements(id) on delete cascade,
  evidence_type text not null,
  document_id uuid,
  external_reference text,
  observed_value jsonb not null default '{}'::jsonb,
  source text not null,
  confidence numeric(5,4),
  verified_at timestamptz,
  verified_by text,
  created_at timestamptz not null default now()
);

create table if not exists public.participant_completions (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references public.customers(id) on delete restrict,
  registration_id uuid not null references public.registrations(id) on delete restrict,
  class_session_id uuid not null references public.class_sessions(id) on delete restrict,
  course_id uuid not null references public.courses(id) on delete restrict,
  completion_status text not null check (completion_status in ('attended','passed','failed','incomplete','unknown')),
  completed_at timestamptz,
  source_system text not null,
  source_record_identity text,
  evidence jsonb not null default '{}'::jsonb,
  confidence numeric(5,4),
  recorded_by text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (registration_id, course_id)
);
create unique index if not exists participant_completions_source_identity_unique
  on public.participant_completions(source_system, source_record_identity)
  where source_record_identity is not null;

create table if not exists public.participant_credentials (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references public.customers(id) on delete restrict,
  registration_id uuid not null references public.registrations(id) on delete restrict,
  class_session_id uuid not null references public.class_sessions(id) on delete restrict,
  course_id uuid not null references public.courses(id) on delete restrict,
  completion_id uuid references public.participant_completions(id) on delete set null,
  credential_type text not null,
  credential_number text,
  issued_at timestamptz,
  expires_on date,
  status text not null check (status in ('pending','issued','expired','revoked','unknown')),
  source_system text not null,
  source_record_identity text,
  evidence jsonb not null default '{}'::jsonb,
  confidence numeric(5,4),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index if not exists participant_credentials_source_identity_unique
  on public.participant_credentials(source_system, source_record_identity)
  where source_record_identity is not null;

create table if not exists public.participant_lifecycle_events (
  id uuid primary key default gen_random_uuid(),
  event_key text not null unique,
  event_type text not null,
  customer_id uuid references public.customers(id) on delete restrict,
  registration_id uuid references public.registrations(id) on delete restrict,
  class_session_id uuid references public.class_sessions(id) on delete restrict,
  related_registration_id uuid references public.registrations(id) on delete restrict,
  source text not null,
  actor jsonb not null default '{}'::jsonb,
  occurred_at timestamptz not null default now(),
  details jsonb not null default '{}'::jsonb,
  import_record_id uuid references public.lifecycle_import_records(id) on delete set null,
  correction_of_event_id uuid references public.participant_lifecycle_events(id) on delete restrict,
  created_at timestamptz not null default now()
);

alter table public.registration_order_items add column if not exists source_item_key text;
create unique index if not exists registration_order_items_source_item_unique
  on public.registration_order_items(order_id, source_item_key)
  where source_item_key is not null;

create index if not exists customer_identity_aliases_customer_idx on public.customer_identity_aliases(customer_id);
create index if not exists lifecycle_import_records_customer_idx on public.lifecycle_import_records(customer_id);
create index if not exists lifecycle_import_records_registration_idx on public.lifecycle_import_records(registration_id);
create index if not exists registration_supersessions_source_idx on public.registration_supersessions(source_registration_id);
create index if not exists registration_supersessions_target_idx on public.registration_supersessions(target_registration_id);
create index if not exists registration_requirements_registration_idx on public.registration_requirements(registration_id);
create index if not exists participant_completions_customer_completed_idx on public.participant_completions(customer_id, completed_at desc);
create index if not exists participant_credentials_customer_expiry_idx on public.participant_credentials(customer_id, expires_on desc);
create index if not exists participant_lifecycle_events_customer_time_idx on public.participant_lifecycle_events(customer_id, occurred_at desc);
create index if not exists participant_lifecycle_events_registration_time_idx on public.participant_lifecycle_events(registration_id, occurred_at desc);

do $$
declare t text;
begin
  foreach t in array array[
    'lifecycle_import_batches','lifecycle_import_records','customer_identity_aliases',
    'registration_supersessions','registration_requirements','registration_requirement_evidence',
    'participant_completions','participant_credentials','participant_lifecycle_events'
  ] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('revoke all on table public.%I from anon, authenticated', t);
    execute format('grant all on table public.%I to service_role', t);
  end loop;
end $$;

create or replace function public.register_participant(
  p_idempotency_key text,
  p_source text,
  p_session_id uuid,
  p_customer jsonb,
  p_actor jsonb default '{}'::jsonb,
  p_organization_id uuid default null,
  p_external_identity jsonb default null,
  p_requirements jsonb default '[]'::jsonb,
  p_order jsonb default null,
  p_notes text default null,
  p_import_record_id uuid default null
) returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  v_customer_id uuid;
  v_registration_id uuid;
  v_event public.participant_lifecycle_events%rowtype;
  v_email text := lower(nullif(trim(p_customer->>'email'),''));
  v_phone text := nullif(regexp_replace(coalesce(p_customer->>'phone',''),'\D','','g'),'');
  v_first text := nullif(trim(p_customer->>'first_name'),'');
  v_last text := nullif(trim(p_customer->>'last_name'),'');
  v_existing_id uuid;
  v_alias public.customer_identity_aliases%rowtype;
  v_candidates uuid[] := '{}';
  v_email_candidates uuid[] := '{}';
  v_phone_candidates uuid[] := '{}';
  v_req jsonb;
  v_item jsonb;
  v_order_id uuid;
  v_order_status text;
  v_external_source text := nullif(trim(p_external_identity->>'source_system'),'');
  v_external_key text := nullif(trim(p_external_identity->>'source_identity'),'');
begin
  if nullif(trim(p_idempotency_key),'') is null or nullif(trim(p_source),'') is null then
    raise exception 'idempotency_key and source are required';
  end if;
  if not exists(select 1 from public.class_sessions where id=p_session_id) then
    raise exception 'canonical session not found';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('register:'||p_idempotency_key,0));

  select * into v_event from public.participant_lifecycle_events where event_key='register:'||p_idempotency_key;
  if found then
    return jsonb_build_object('ok',true,'idempotent_replay',true,'resolution','matched',
      'customer_id',v_event.customer_id,'registration_id',v_event.registration_id,'class_session_id',v_event.class_session_id);
  end if;

  if p_customer ? 'id' and nullif(p_customer->>'id','') is not null then
    v_existing_id := (p_customer->>'id')::uuid;
    select id into v_customer_id from public.customers where id=v_existing_id;
    if v_customer_id is null then raise exception 'customer id not found'; end if;
  elsif v_external_source is not null and v_external_key is not null then
    select * into v_alias from public.customer_identity_aliases
      where source_system=v_external_source and source_identity=v_external_key for update;
    if found and v_alias.resolution_status='matched' then
      v_customer_id := v_alias.customer_id;
    elsif found then
      return jsonb_build_object('ok',false,'resolution','review_required','alias_id',v_alias.id,
        'candidate_customer_ids',v_alias.candidate_customer_ids);
    end if;
  end if;

  if v_customer_id is null then
    if v_email is not null then
      select coalesce(array_agg(id order by id),'{}') into v_email_candidates
      from public.customers where lower(email)=v_email;
    end if;
    if v_phone is not null then
      select coalesce(array_agg(id order by id),'{}') into v_phone_candidates
      from public.customers where regexp_replace(coalesce(phone,''),'\D','','g')=v_phone;
    end if;

    if cardinality(v_email_candidates)=1 and cardinality(v_phone_candidates)=1
       and v_email_candidates[1]<>v_phone_candidates[1] then
      v_candidates := array[v_email_candidates[1],v_phone_candidates[1]];
    elsif cardinality(v_email_candidates)>1 or cardinality(v_phone_candidates)>1 then
      v_candidates := array(select distinct unnest(v_email_candidates||v_phone_candidates));
    elsif cardinality(v_email_candidates)=1 then
      v_customer_id := v_email_candidates[1];
    elsif cardinality(v_phone_candidates)=1 then
      v_customer_id := v_phone_candidates[1];
    end if;

    if cardinality(v_candidates)>0 then
      if v_external_source is null or v_external_key is null then
        raise exception 'ambiguous customer identity requires external source identity';
      end if;
      insert into public.customer_identity_aliases(
        source_system,source_identity,resolution_status,candidate_customer_ids,source_values,confidence,import_record_id
      ) values(v_external_source,v_external_key,'ambiguous',v_candidates,p_customer,null,p_import_record_id)
      on conflict(source_system,source_identity) do update set
        resolution_status='ambiguous',customer_id=null,candidate_customer_ids=excluded.candidate_customer_ids,
        source_values=excluded.source_values,confidence=null,import_record_id=excluded.import_record_id,updated_at=now()
      returning id into v_existing_id;
      insert into public.participant_lifecycle_events(event_key,event_type,source,actor,details,import_record_id)
      values('identity-review:'||p_idempotency_key,'identity_ambiguous',p_source,p_actor,
        jsonb_build_object('alias_id',v_existing_id,'candidate_customer_ids',v_candidates),p_import_record_id);
      return jsonb_build_object('ok',false,'resolution','review_required','alias_id',v_existing_id,
        'candidate_customer_ids',v_candidates);
    end if;

    if v_customer_id is null then
      if v_first is null or v_last is null then raise exception 'first_name and last_name are required for a new customer'; end if;
      insert into public.customers(first_name,last_name,email,phone,organization_id)
      values(v_first,v_last,v_email,nullif(trim(p_customer->>'phone'),''),p_organization_id)
      returning id into v_customer_id;
    end if;
  end if;

  update public.customers set
    organization_id=coalesce(organization_id,p_organization_id),
    phone=coalesce(phone,nullif(trim(p_customer->>'phone'),'')),
    email=coalesce(email,v_email),
    updated_at=now()
  where id=v_customer_id;

  if v_external_source is not null and v_external_key is not null then
    insert into public.customer_identity_aliases(
      source_system,source_identity,customer_id,resolution_status,confidence,source_values,import_record_id,resolved_by,resolved_at
    ) values(v_external_source,v_external_key,v_customer_id,'matched',
      coalesce((p_external_identity->>'confidence')::numeric,1),p_customer,p_import_record_id,
      coalesce(p_actor->>'label',p_source),now())
    on conflict(source_system,source_identity) do update set
      customer_id=case when customer_identity_aliases.resolution_status='matched'
                         and customer_identity_aliases.customer_id<>excluded.customer_id
                       then customer_identity_aliases.customer_id else excluded.customer_id end,
      resolution_status=case when customer_identity_aliases.resolution_status='matched'
                         and customer_identity_aliases.customer_id<>excluded.customer_id
                       then 'ambiguous' else 'matched' end,
      candidate_customer_ids=case when customer_identity_aliases.resolution_status='matched'
                         and customer_identity_aliases.customer_id<>excluded.customer_id
                       then array[customer_identity_aliases.customer_id,excluded.customer_id] else '{}' end,
      source_values=excluded.source_values,updated_at=now();
    select * into v_alias from public.customer_identity_aliases
      where source_system=v_external_source and source_identity=v_external_key;
    if v_alias.resolution_status<>'matched' then
      return jsonb_build_object('ok',false,'resolution','review_required','alias_id',v_alias.id,
        'candidate_customer_ids',v_alias.candidate_customer_ids);
    end if;
  end if;

  select id into v_registration_id from public.registrations
    where customer_id=v_customer_id and class_session_id=p_session_id for update;
  if v_registration_id is null then
    insert into public.registrations(customer_id,class_session_id,status,registration_source,external_registration_id)
    values(v_customer_id,p_session_id,
      coalesce(nullif(p_customer->>'registration_status',''),'registered'),p_source,
      nullif(p_external_identity->>'registration_identity',''))
    returning id into v_registration_id;
  else
    update public.registrations set
      external_registration_id=coalesce(external_registration_id,nullif(p_external_identity->>'registration_identity','')),
      updated_at=now()
    where id=v_registration_id;
  end if;

  if jsonb_typeof(p_requirements)='array' then
    for v_req in select value from jsonb_array_elements(p_requirements) loop
      insert into public.registration_requirements(
        registration_id,requirement_key,requirement_type,state,source,notes,satisfied_at,satisfied_by,provenance
      ) values(
        v_registration_id,v_req->>'key',coalesce(v_req->>'type',v_req->>'key'),
        coalesce(v_req->>'state','unknown'),p_source,v_req->>'notes',
        case when v_req->>'state' in ('satisfied','waived') then coalesce((v_req->>'satisfied_at')::timestamptz,now()) end,
        v_req->>'satisfied_by',coalesce(v_req->'provenance','{}'::jsonb)
      ) on conflict(registration_id,requirement_key) do update set
        state=case when registration_requirements.state in ('satisfied','waived')
                   and excluded.state not in ('satisfied','waived')
                   then registration_requirements.state else excluded.state end,
        notes=coalesce(excluded.notes,registration_requirements.notes),
        satisfied_at=coalesce(registration_requirements.satisfied_at,excluded.satisfied_at),
        satisfied_by=coalesce(registration_requirements.satisfied_by,excluded.satisfied_by),
        provenance=registration_requirements.provenance||excluded.provenance,
        updated_at=now();
    end loop;
  end if;

  if p_order is not null then
    select id,status into v_order_id,v_order_status from public.registration_orders
      where registration_id=v_registration_id for update;
    if v_order_id is null then
      insert into public.registration_orders(
        registration_id,status,currency,course_amount,materials_amount,total_amount
      ) values(
        v_registration_id,coalesce(p_order->>'status','payment_pending'),
        coalesce(p_order->>'currency','usd'),coalesce((p_order->>'course_amount')::numeric,0),
        coalesce((p_order->>'materials_amount')::numeric,0),coalesce((p_order->>'total_amount')::numeric,0)
      ) returning id,status into v_order_id,v_order_status;
    end if;
    if jsonb_typeof(p_order->'items')='array' then
      for v_item in select value from jsonb_array_elements(p_order->'items') loop
        if nullif(v_item->>'source_item_key','') is null then raise exception 'order item source_item_key is required'; end if;
        insert into public.registration_order_items(
          order_id,item_type,product_id,description,quantity,unit_amount,fulfillment_status,source_item_key
        ) values(
          v_order_id,v_item->>'item_type',nullif(v_item->>'product_id','')::uuid,v_item->>'description',
          coalesce((v_item->>'quantity')::integer,1),coalesce((v_item->>'unit_amount')::numeric,0),
          coalesce(v_item->>'fulfillment_status','not_required'),v_item->>'source_item_key'
        ) on conflict(order_id,source_item_key) where source_item_key is not null do update set
          description=excluded.description,
          fulfillment_status=case when registration_order_items.fulfillment_status='fulfilled'
                                  then 'fulfilled' else excluded.fulfillment_status end,
          updated_at=now();
      end loop;
    end if;
  end if;

  insert into public.participant_lifecycle_events(
    event_key,event_type,customer_id,registration_id,class_session_id,source,actor,details,import_record_id
  ) values(
    'register:'||p_idempotency_key,
    case when p_source like '%import%' or p_source='enrollware' then 'imported' else 'registered' end,
    v_customer_id,v_registration_id,p_session_id,p_source,p_actor,
    jsonb_build_object('notes',p_notes,'organization_id',p_organization_id,'order_id',v_order_id),
    p_import_record_id
  );

  return jsonb_build_object('ok',true,'idempotent_replay',false,'resolution','matched',
    'customer_id',v_customer_id,'registration_id',v_registration_id,'class_session_id',p_session_id,
    'order_id',v_order_id);
end;
$$;

create or replace function public.move_registration(
  p_idempotency_key text,
  p_source_registration_id uuid,
  p_target_session_id uuid,
  p_reason text,
  p_source text,
  p_actor jsonb default '{}'::jsonb,
  p_financial_policy text default 'transfer'
) returns jsonb
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  v_source public.registrations%rowtype;
  v_target_id uuid;
  v_move public.registration_supersessions%rowtype;
  v_order_id uuid;
  v_has_completion boolean;
  v_target_course uuid;
  v_source_course uuid;
begin
  if nullif(trim(p_idempotency_key),'') is null or nullif(trim(p_reason),'') is null then
    raise exception 'idempotency_key and reason are required';
  end if;
  if p_financial_policy not in ('transfer','retain','none') then raise exception 'invalid financial policy'; end if;
  perform pg_advisory_xact_lock(hashtextextended('move:'||p_idempotency_key,0));

  select * into v_move from public.registration_supersessions where idempotency_key=p_idempotency_key;
  if found then
    return jsonb_build_object('ok',true,'idempotent_replay',true,'source_registration_id',v_move.source_registration_id,
      'target_registration_id',v_move.target_registration_id,'supersession_id',v_move.id,
      'transferred_order_id',v_move.transferred_order_id);
  end if;

  select * into v_source from public.registrations where id=p_source_registration_id for update;
  if not found then raise exception 'source registration not found'; end if;
  if v_source.class_session_id=p_target_session_id then raise exception 'target session must differ from source session'; end if;
  select course_id into v_source_course from public.class_sessions where id=v_source.class_session_id;
  select course_id into v_target_course from public.class_sessions where id=p_target_session_id;
  if v_target_course is null then raise exception 'target session not found'; end if;
  if v_source_course<>v_target_course then raise exception 'target session course differs from source course'; end if;

  select exists(select 1 from public.participant_completions where registration_id=v_source.id) into v_has_completion;

  insert into public.registrations(customer_id,class_session_id,status,registration_source)
  values(v_source.customer_id,p_target_session_id,
    case when v_source.status='completed' then 'registered' else v_source.status end,p_source)
  on conflict(customer_id,class_session_id) do update set updated_at=now()
  returning id into v_target_id;

  select id into v_order_id from public.registration_orders where registration_id=v_source.id for update;
  if p_financial_policy='transfer' and v_order_id is not null then
    if exists(select 1 from public.registration_orders where registration_id=v_target_id) then
      raise exception 'target registration already has an order';
    end if;
    update public.registration_orders set registration_id=v_target_id,updated_at=now() where id=v_order_id;
  elsif p_financial_policy<>'transfer' then
    v_order_id:=null;
  end if;

  insert into public.registration_requirements(
    registration_id,requirement_key,requirement_type,state,source,notes,satisfied_at,satisfied_by,
    superseded_from_requirement_id,provenance
  )
  select v_target_id,requirement_key,requirement_type,state,p_source,notes,satisfied_at,satisfied_by,id,
    provenance||jsonb_build_object('moved_from_registration_id',v_source.id)
  from public.registration_requirements where registration_id=v_source.id
  on conflict(registration_id,requirement_key) do nothing;

  if not v_has_completion then
    update public.registrations set status='rescheduled',updated_at=now() where id=v_source.id;
  end if;

  insert into public.registration_supersessions(
    idempotency_key,source_registration_id,target_registration_id,source_session_id,target_session_id,
    reason,source,actor,financial_policy,transferred_order_id,details
  ) values(
    p_idempotency_key,v_source.id,v_target_id,v_source.class_session_id,p_target_session_id,
    p_reason,p_source,p_actor,p_financial_policy,
    case when p_financial_policy='transfer' then v_order_id end,
    jsonb_build_object('source_status_preserved',v_has_completion,'source_course_id',v_source_course)
  ) returning * into v_move;

  insert into public.participant_lifecycle_events(
    event_key,event_type,customer_id,registration_id,class_session_id,related_registration_id,source,actor,details
  ) values(
    'move:'||p_idempotency_key,'moved',v_source.customer_id,v_source.id,v_source.class_session_id,v_target_id,
    p_source,p_actor,jsonb_build_object('target_session_id',p_target_session_id,'reason',p_reason,
      'financial_policy',p_financial_policy,'transferred_order_id',v_move.transferred_order_id,
      'completed_source_preserved',v_has_completion)
  );

  return jsonb_build_object('ok',true,'idempotent_replay',false,'source_registration_id',v_source.id,
    'target_registration_id',v_target_id,'supersession_id',v_move.id,
    'transferred_order_id',v_move.transferred_order_id,'completed_source_preserved',v_has_completion);
end;
$$;

revoke all on function public.register_participant(text,text,uuid,jsonb,jsonb,uuid,jsonb,jsonb,jsonb,text,uuid)
  from public, anon, authenticated;
grant execute on function public.register_participant(text,text,uuid,jsonb,jsonb,uuid,jsonb,jsonb,jsonb,text,uuid)
  to service_role;
revoke all on function public.move_registration(text,uuid,uuid,text,text,jsonb,text)
  from public, anon, authenticated;
grant execute on function public.move_registration(text,uuid,uuid,text,text,jsonb,text)
  to service_role;
