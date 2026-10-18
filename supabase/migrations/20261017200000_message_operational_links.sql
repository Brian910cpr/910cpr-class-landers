-- Existing person_id / registration_id reference the older LanderWare model.
-- Keep those records intact and explicitly link the operational CRM model.
alter table public.landerware_messages
 add column if not exists customer_id uuid references public.customers(id),
 add column if not exists operational_registration_id uuid references public.registrations(id);
create index if not exists landerware_messages_customer_history
 on public.landerware_messages(customer_id,created_at desc);
create index if not exists landerware_messages_operational_registration_history
 on public.landerware_messages(operational_registration_id,created_at desc);

create or replace function public.landerware_link_paid_message()
returns trigger language plpgsql security definer set search_path='' as $$
begin
 if new.template_key='retail-paid-confirmation-v3' then
   select r.customer_id,r.id into new.customer_id,new.operational_registration_id
   from public.landerware_public_order_students st
   join public.registrations r on r.id=st.registration_id
   where new.idempotency_key='public-order-paid:'||st.order_id::text||':'||st.email
     and new.recipient=st.email;
 end if;
 return new;
end $$;
revoke all on function public.landerware_link_paid_message() from public,anon,authenticated;
drop trigger if exists landerware_link_paid_message on public.landerware_messages;
create trigger landerware_link_paid_message before insert on public.landerware_messages
 for each row execute function public.landerware_link_paid_message();

update public.landerware_messages m set customer_id=r.customer_id,operational_registration_id=r.id
from public.landerware_public_order_students st
join public.registrations r on r.id=st.registration_id
where m.template_key='retail-paid-confirmation-v3'
 and m.idempotency_key='public-order-paid:'||st.order_id::text||':'||st.email
 and m.recipient=st.email and m.customer_id is null and m.operational_registration_id is null;
