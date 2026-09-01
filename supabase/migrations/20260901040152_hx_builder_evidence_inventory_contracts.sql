-- Dockmaster: history is reconstructed from evidence; the original logbook page is never erased.

-- Durable, cross-batch source identity. Exact replays are suppressed by the
-- global fingerprint key; changed content for the same source identity remains
-- a separate version that must reconcile as conflicting/review-required.
alter table public.lifecycle_import_records add column if not exists source_system text;
alter table public.lifecycle_import_records add column if not exists source_fingerprint text;
alter table public.lifecycle_import_records add column if not exists source_fingerprint_algorithm text;
alter table public.lifecycle_import_records add column if not exists predecessor_import_record_id uuid
  references public.lifecycle_import_records(id) on delete restrict;

update public.lifecycle_import_records r
set source_system=b.source_system
from public.lifecycle_import_batches b
where b.id=r.batch_id and r.source_system is null;

update public.lifecycle_import_records
set source_fingerprint=encode(extensions.digest(convert_to(original_values::text,'utf8'),'sha256'),'hex'),
    source_fingerprint_algorithm='sha256-jsonb-text-legacy-v1'
where source_fingerprint is null;

update public.lifecycle_import_records
set source_fingerprint_algorithm='sha256-jsonb-text-legacy-v1'
where source_fingerprint_algorithm is null;

alter table public.lifecycle_import_records alter column source_system set not null;
alter table public.lifecycle_import_records alter column source_fingerprint set not null;
alter table public.lifecycle_import_records alter column source_fingerprint_algorithm set not null;

alter table public.lifecycle_import_records
  drop constraint if exists lifecycle_import_records_source_fingerprint_format;
alter table public.lifecycle_import_records
  add constraint lifecycle_import_records_source_fingerprint_format
  check (source_fingerprint ~ '^[0-9a-f]{64}$');
alter table public.lifecycle_import_records
  drop constraint if exists lifecycle_import_records_predecessor_not_self;
alter table public.lifecycle_import_records
  add constraint lifecycle_import_records_predecessor_not_self
  check (predecessor_import_record_id is null or predecessor_import_record_id <> id);

create unique index if not exists lifecycle_import_records_global_fingerprint_unique
  on public.lifecycle_import_records(source_system,source_record_id,entity_type,source_fingerprint_algorithm,source_fingerprint);
create index if not exists lifecycle_import_records_source_identity_idx
  on public.lifecycle_import_records(source_system,source_record_id,entity_type);
create index if not exists lifecycle_import_records_predecessor_idx
  on public.lifecycle_import_records(predecessor_import_record_id);

-- Extend the existing production immutability guard to cover the durable
-- source-version identity introduced above. Reconciliation/link columns may
-- still change, but the forensic source page and its version cannot.
create or replace function public.protect_import_source_identity()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin
  if new.batch_id is distinct from old.batch_id
     or new.source_record_id is distinct from old.source_record_id
     or new.entity_type is distinct from old.entity_type
     or new.original_values is distinct from old.original_values
     or new.source_system is distinct from old.source_system
     or new.source_fingerprint is distinct from old.source_fingerprint
     or new.source_fingerprint_algorithm is distinct from old.source_fingerprint_algorithm
     or new.predecessor_import_record_id is distinct from old.predecessor_import_record_id then
    raise exception 'import source identity, version, predecessor, and original values are immutable';
  end if;
  return new;
end;
$$;
revoke all on function public.protect_import_source_identity() from public, anon, authenticated;
grant execute on function public.protect_import_source_identity() to service_role;

create or replace function public.validate_import_record_predecessor()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  v_prior public.lifecycle_import_records%rowtype;
begin
  if new.predecessor_import_record_id is null then
    return new;
  end if;
  select * into v_prior from public.lifecycle_import_records
  where id=new.predecessor_import_record_id;
  if not found then
    return new; -- the foreign key reports the missing row
  end if;
  if v_prior.source_system is distinct from new.source_system
     or v_prior.source_record_id is distinct from new.source_record_id
     or v_prior.entity_type is distinct from new.entity_type then
    raise exception 'import predecessor must have the same source_system, source_record_id, and entity_type';
  end if;
  return new;
end;
$$;
revoke all on function public.validate_import_record_predecessor() from public, anon, authenticated;
grant execute on function public.validate_import_record_predecessor() to service_role;

drop trigger if exists lifecycle_import_records_predecessor_guard on public.lifecycle_import_records;
create trigger lifecycle_import_records_predecessor_guard
before insert on public.lifecycle_import_records
for each row execute function public.validate_import_record_predecessor();

-- Canonical credential inventory concepts observed in the reviewed Enrollware
-- evidence. The source aliases point at product master; they do not create a
-- second inventory catalog. Prices are the historical 910CPR sale prices in
-- the source sample and remain reviewable product-master data.
insert into public.products
  (product_key,name,product_type,certifying_body,customer_price,unit_cost,fulfillment_mode,reorder_threshold,active)
select 'aha-25-3001-bls-provider-ecard','AHA BLS Provider eCard (25-3001)',
       'credential_ecard','AHA',8.00,null,'digital_code',0,false
where not exists (
  select 1 from public.products where product_key='aha-25-3001-bls-provider-ecard'
     or lower(name) in ('aha bls provider ecard (25-3001)','aha bls provider ecard')
);

insert into public.products
  (product_key,name,product_type,certifying_body,customer_price,unit_cost,fulfillment_mode,reorder_threshold,active)
select 'aha-25-3002-heartsaver-first-aid-cpr-aed-ecard',
       'AHA Heartsaver First Aid CPR AED eCard (25-3002)',
       'credential_ecard','AHA',30.00,null,'digital_code',0,false
where not exists (
  select 1 from public.products
  where product_key='aha-25-3002-heartsaver-first-aid-cpr-aed-ecard'
     or lower(name) in ('aha heartsaver first aid cpr aed ecard (25-3002)',
                       'aha heartsaver first aid cpr aed ecard')
);

create table if not exists public.historical_product_aliases (
  source_system text not null,
  source_value text not null,
  product_id uuid not null references public.products(id) on delete restrict,
  provenance jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  primary key (source_system,source_value)
);

do $$
declare
  v_bls_ids uuid[];
  v_heartsaver_ids uuid[];
  v_existing uuid;
begin
  select array_agg(id order by id) into v_bls_ids from public.products
  where product_key='aha-25-3001-bls-provider-ecard'
     or lower(name) in ('aha bls provider ecard (25-3001)','aha bls provider ecard');
  if coalesce(cardinality(v_bls_ids),0) <> 1 then
    raise exception 'AHA BLS Provider eCard canonical product resolution returned % candidates',
      coalesce(cardinality(v_bls_ids),0);
  end if;
  select product_id into v_existing from public.historical_product_aliases
  where source_system='enrollware_student_report' and source_value='AHA-BLS-ECARD';
  if v_existing is not null and v_existing <> v_bls_ids[1] then
    raise exception 'AHA-BLS-ECARD alias collision: existing product % differs from canonical %',
      v_existing,v_bls_ids[1];
  end if;
  insert into public.historical_product_aliases(source_system,source_value,product_id,provenance)
  values ('enrollware_student_report','AHA-BLS-ECARD',v_bls_ids[1],
          '{"authority":"curated","aha_product_number":"25-3001","legacy_product_number":"20-3001"}'::jsonb)
  on conflict (source_system,source_value) do nothing;

  select array_agg(id order by id) into v_heartsaver_ids from public.products
  where product_key='aha-25-3002-heartsaver-first-aid-cpr-aed-ecard'
     or lower(name) in ('aha heartsaver first aid cpr aed ecard (25-3002)',
                       'aha heartsaver first aid cpr aed ecard');
  if coalesce(cardinality(v_heartsaver_ids),0) <> 1 then
    raise exception 'AHA Heartsaver First Aid CPR AED eCard canonical product resolution returned % candidates',
      coalesce(cardinality(v_heartsaver_ids),0);
  end if;
  select product_id into v_existing from public.historical_product_aliases
  where source_system='enrollware_student_report' and source_value='AHA-HS-FACPRAED-ECARD';
  if v_existing is not null and v_existing <> v_heartsaver_ids[1] then
    raise exception 'AHA-HS-FACPRAED-ECARD alias collision: existing product % differs from canonical %',
      v_existing,v_heartsaver_ids[1];
  end if;
  insert into public.historical_product_aliases(source_system,source_value,product_id,provenance)
  values ('enrollware_student_report','AHA-HS-FACPRAED-ECARD',v_heartsaver_ids[1],
          '{"authority":"curated","aha_product_number":"25-3002","legacy_product_number":"20-3002"}'::jsonb)
  on conflict (source_system,source_value) do nothing;
end
$$;

create table if not exists public.inventory_entitlement_pools (
  id uuid primary key default gen_random_uuid(),
  pool_key text not null unique,
  product_id uuid not null references public.products(id) on delete restrict,
  owner_kind text not null check (owner_kind in ('customer','organization','internal','external')),
  owner_customer_id uuid references public.customers(id) on delete restrict,
  owner_organization_id uuid references public.organizations(id) on delete restrict,
  external_owner_reference text,
  unit_kind text not null,
  status text not null default 'unknown' check (status in ('active','exhausted','closed','unknown')),
  reconciliation_status text not null default 'unreviewed' check (
    reconciliation_status in ('unreviewed','accepted','superseded','conflicting','rejected','unknown')
  ),
  source text not null,
  source_record_id text not null,
  import_batch_id uuid not null references public.lifecycle_import_batches(id) on delete restrict,
  provenance jsonb not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (source, source_record_id),
  check (
    (owner_kind='customer' and owner_customer_id is not null and owner_organization_id is null)
    or (owner_kind='organization' and owner_organization_id is not null and owner_customer_id is null)
    or (owner_kind='internal' and owner_customer_id is null and owner_organization_id is null)
    or (owner_kind='external' and owner_customer_id is null and owner_organization_id is null
        and external_owner_reference is not null)
  )
);

create table if not exists public.inventory_entitlement_events (
  id uuid primary key default gen_random_uuid(),
  event_key text not null unique,
  pool_id uuid not null references public.inventory_entitlement_pools(id) on delete restrict,
  event_type text not null check (event_type in ('acquired','allocated','consumed','released','expired','corrected','reconciled')),
  quantity_delta integer not null check (quantity_delta <> 0),
  customer_id uuid references public.customers(id) on delete restrict,
  registration_id uuid references public.registrations(id) on delete restrict,
  class_session_id uuid references public.class_sessions(id) on delete restrict,
  registration_order_item_id uuid references public.registration_order_items(id) on delete set null,
  source text not null,
  source_record_id text not null,
  import_batch_id uuid not null references public.lifecycle_import_batches(id) on delete restrict,
  occurred_at timestamptz,
  recorded_at timestamptz not null default now(),
  confidence_state text not null check (confidence_state in ('confirmed','probable','possible','unknown','conflicting','rejected')),
  confidence numeric(5,4) check (confidence is null or confidence between 0 and 1),
  reconciliation_status text not null default 'unreviewed' check (
    reconciliation_status in ('unreviewed','accepted','superseded','conflicting','rejected','unknown')
  ),
  provenance jsonb not null,
  reverses_event_id uuid references public.inventory_entitlement_events(id) on delete restrict,
  unique (source, source_record_id, event_type, pool_id),
  check (
    (event_type in ('acquired','released','corrected','reconciled') and quantity_delta <> 0)
    or (event_type in ('allocated','consumed','expired') and quantity_delta < 0)
  ),
  check (reverses_event_id is null or reverses_event_id <> id)
);

create table if not exists public.lifecycle_evidence_assertions (
  id uuid primary key default gen_random_uuid(),
  assertion_key text not null unique,
  fact_type text not null check (fact_type in (
    'identity','session','registration','attendance','completion','credential',
    'payment','product_fulfillment','requirement','reschedule','inventory_entitlement','other'
  )),
  source text not null,
  source_record_id text not null,
  import_batch_id uuid not null references public.lifecycle_import_batches(id) on delete restrict,
  import_record_id uuid references public.lifecycle_import_records(id) on delete restrict,
  customer_id uuid references public.customers(id) on delete restrict,
  registration_id uuid references public.registrations(id) on delete restrict,
  class_session_id uuid references public.class_sessions(id) on delete restrict,
  completion_id uuid references public.participant_completions(id) on delete restrict,
  credential_id uuid references public.participant_credentials(id) on delete restrict,
  registration_order_id uuid references public.registration_orders(id) on delete restrict,
  registration_order_item_id uuid references public.registration_order_items(id) on delete restrict,
  inventory_pool_id uuid references public.inventory_entitlement_pools(id) on delete restrict,
  inventory_event_id uuid references public.inventory_entitlement_events(id) on delete restrict,
  asserted_value jsonb not null,
  original_source_value jsonb not null,
  confidence_state text not null check (confidence_state in ('confirmed','probable','possible','unknown','conflicting','rejected')),
  confidence numeric(5,4) check (confidence is null or confidence between 0 and 1),
  reconciliation_status text not null default 'unreviewed' check (
    reconciliation_status in ('unreviewed','accepted','superseded','conflicting','rejected','unknown')
  ),
  effective_at timestamptz,
  source_created_at timestamptz,
  observed_at timestamptz,
  recorded_at timestamptz not null default now(),
  supersedes_assertion_id uuid references public.lifecycle_evidence_assertions(id) on delete restrict,
  reconciliation_notes text,
  unique (source, source_record_id, fact_type, assertion_key),
  check (supersedes_assertion_id is null or supersedes_assertion_id <> id)
);

create index if not exists inventory_entitlement_pools_product_idx
  on public.inventory_entitlement_pools(product_id);
create index if not exists inventory_entitlement_pools_customer_idx
  on public.inventory_entitlement_pools(owner_customer_id);
create index if not exists inventory_entitlement_pools_organization_idx
  on public.inventory_entitlement_pools(owner_organization_id);
create index if not exists inventory_entitlement_pools_batch_idx
  on public.inventory_entitlement_pools(import_batch_id);
create index if not exists inventory_entitlement_pools_review_idx
  on public.inventory_entitlement_pools(reconciliation_status,status);
create index if not exists inventory_entitlement_events_pool_time_idx
  on public.inventory_entitlement_events(pool_id, occurred_at);
create index if not exists inventory_entitlement_events_customer_idx
  on public.inventory_entitlement_events(customer_id);
create index if not exists inventory_entitlement_events_registration_idx
  on public.inventory_entitlement_events(registration_id);
create index if not exists inventory_entitlement_events_session_idx
  on public.inventory_entitlement_events(class_session_id);
create index if not exists inventory_entitlement_events_order_item_idx
  on public.inventory_entitlement_events(registration_order_item_id);
create index if not exists inventory_entitlement_events_batch_idx
  on public.inventory_entitlement_events(import_batch_id);
create index if not exists inventory_entitlement_events_reversal_idx
  on public.inventory_entitlement_events(reverses_event_id);
create unique index if not exists inventory_entitlement_events_one_reversal_unique
  on public.inventory_entitlement_events(reverses_event_id) where reverses_event_id is not null;
create index if not exists inventory_entitlement_events_review_idx
  on public.inventory_entitlement_events(reconciliation_status,recorded_at);
create index if not exists lifecycle_evidence_assertions_batch_idx
  on public.lifecycle_evidence_assertions(import_batch_id);
create index if not exists lifecycle_evidence_assertions_import_record_idx
  on public.lifecycle_evidence_assertions(import_record_id);
create index if not exists lifecycle_evidence_assertions_customer_idx
  on public.lifecycle_evidence_assertions(customer_id);
create index if not exists lifecycle_evidence_assertions_registration_idx
  on public.lifecycle_evidence_assertions(registration_id);
create index if not exists lifecycle_evidence_assertions_session_idx
  on public.lifecycle_evidence_assertions(class_session_id);
create index if not exists lifecycle_evidence_assertions_completion_idx
  on public.lifecycle_evidence_assertions(completion_id);
create index if not exists lifecycle_evidence_assertions_credential_idx
  on public.lifecycle_evidence_assertions(credential_id);
create index if not exists lifecycle_evidence_assertions_order_idx
  on public.lifecycle_evidence_assertions(registration_order_id);
create index if not exists lifecycle_evidence_assertions_order_item_idx
  on public.lifecycle_evidence_assertions(registration_order_item_id);
create index if not exists lifecycle_evidence_assertions_pool_idx
  on public.lifecycle_evidence_assertions(inventory_pool_id);
create index if not exists lifecycle_evidence_assertions_inventory_event_idx
  on public.lifecycle_evidence_assertions(inventory_event_id);
create index if not exists lifecycle_evidence_assertions_supersedes_idx
  on public.lifecycle_evidence_assertions(supersedes_assertion_id);
create unique index if not exists lifecycle_evidence_assertions_one_superseder_unique
  on public.lifecycle_evidence_assertions(supersedes_assertion_id) where supersedes_assertion_id is not null;
create index if not exists lifecycle_evidence_assertions_source_idx
  on public.lifecycle_evidence_assertions(source,source_record_id,fact_type);
create index if not exists lifecycle_evidence_assertions_review_idx
  on public.lifecycle_evidence_assertions(reconciliation_status,recorded_at);

do $$
declare t text;
begin
  foreach t in array array[
    'historical_product_aliases','inventory_entitlement_pools','inventory_entitlement_events','lifecycle_evidence_assertions'
  ] loop
    execute format('alter table public.%I enable row level security',t);
    execute format('revoke all on table public.%I from anon, authenticated',t);
    execute format('grant all on table public.%I to service_role',t);
  end loop;
end
$$;

create or replace function public.protect_append_only_history()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin
  raise exception 'historical evidence and inventory events are append-only; insert a correction or reversal';
end;
$$;
revoke all on function public.protect_append_only_history() from public, anon, authenticated;
grant execute on function public.protect_append_only_history() to service_role;

drop trigger if exists inventory_entitlement_events_append_only on public.inventory_entitlement_events;
create trigger inventory_entitlement_events_append_only
before update or delete on public.inventory_entitlement_events
for each row execute function public.protect_append_only_history();

drop trigger if exists lifecycle_evidence_assertions_append_only on public.lifecycle_evidence_assertions;
create trigger lifecycle_evidence_assertions_append_only
before update or delete on public.lifecycle_evidence_assertions
for each row execute function public.protect_append_only_history();
