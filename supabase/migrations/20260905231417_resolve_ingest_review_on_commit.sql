create or replace function public.resolve_ingest_review_on_fact_commit()
returns trigger
language plpgsql
set search_path = 'pg_catalog'
as $$
begin
  if new.resolution = 'committed' then
    update public.ingest_review_queue
    set status = 'resolved', decided_at = coalesce(decided_at, now())
    where ingest_fact_id = new.id and status = 'open';
  end if;
  return new;
end;
$$;

drop trigger if exists resolve_ingest_review_on_fact_commit_trg on public.ingest_facts;
create trigger resolve_ingest_review_on_fact_commit_trg
after insert or update of resolution on public.ingest_facts
for each row execute function public.resolve_ingest_review_on_fact_commit();
