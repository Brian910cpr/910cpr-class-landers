-- Dockmaster: history is reconstructed from evidence; the original logbook page is never erased.

-- Durable, cross-batch source identity. Exact replays are suppressed by the
-- global fingerprint key; changed content for the same source identity remains
-- a separate version that must reconcile as conflicting/review-required.
alter table public.lifecycle_import_records add column if not exists source_system text;
alter table public.lifecycle_import_records add column if not exists source_fingerprint text;
alter table public.lifecycle_import_records add column if not exists source_fingerprint_algorithm text;

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

create unique index if not exists lifecycle_import_records_global_fingerprint_unique
  on public.lifecycle_import_records(source_system,source_record_id,entity_type,source_fingerprint_algorithm,source_fingerprint);
create index if not exists lifecycle_import_records_source_identity_idx
  on public.lifecycle_import_records(source_system,source_record_id,entity_type);

create table if not exists public.inventory_entitlement_pools (
  id uuid primary key default gen_random_uuid(),
  pool_key text not null unique,
  product_id uuid not null references public.products(id) on delete restrict,
  owner_kind text not null check (owner_kind in ('customer','organization','internal','external')),
  owner_customer_id uuid references public.customers(id) on delete restrict,
  owner_organization_id uuid references public.organizations(id) on delete restrict,
  external_owner_reference text,
  unit_kind text not null,
  status text not null default 'active' check (status in ('active','exhausted','closed','unknown')),
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
  provenance jsonb not null,
  reverses_event_id uuid references public.inventory_entitlement_events(id) on delete restrict,
  unique (source, source_record_id, event_type, pool_id),
  check (
    (event_type in ('acquired','released','corrected','reconciled') and quantity_delta <> 0)
    or (event_type in ('allocated','consumed','expired') and quantity_delta < 0)
  )
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
  import_record_id uuid references public.lifecycle_import_records(id) on delete set null,
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
  unique (source, source_record_id, fact_type, assertion_key)
);

create index if not exists inventory_entitlement_pools_product_idx
  on public.inventory_entitlement_pools(product_id);
create index if not exists inventory_entitlement_pools_customer_idx
  on public.inventory_entitlement_pools(owner_customer_id);
create index if not exists inventory_entitlement_pools_organization_idx
  on public.inventory_entitlement_pools(owner_organization_id);
create index if not exists inventory_entitlement_pools_batch_idx
  on public.inventory_entitlement_pools(import_batch_id);
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

do $$
declare t text;
begin
  foreach t in array array[
    'inventory_entitlement_pools','inventory_entitlement_events','lifecycle_evidence_assertions'
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
