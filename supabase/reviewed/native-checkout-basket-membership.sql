-- Additive read-only prerequisite for the shared single-course checkout.
-- Basket activation is irrelevant: existing basket children must stay protected.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
do $guard$
declare existing oid:=to_regprocedure('public.native_checkout_basket_contains_order(uuid)');
begin
 if existing is not null and not exists(select 1 from pg_proc p join pg_language l on l.oid=p.prolang
 where p.oid=existing and p.prosrc=$expected$
begin
 if to_regclass('public.native_checkout_basket_items') is null then return false; end if;
 return (select exists(select 1 from public.native_checkout_basket_items where order_id=p_order_id));
end $expected$
 and l.lanname='plpgsql' and not p.prosecdef and p.provolatile='s'
 and p.proconfig=array['search_path=""']) then
 raise exception 'basket_membership_source_mismatch'; end if;
end $guard$;
create or replace function public.native_checkout_basket_contains_order(p_order_id uuid) returns boolean
language plpgsql stable security invoker set search_path='' as $membership$
begin
 if to_regclass('public.native_checkout_basket_items') is null then return false; end if;
 return (select exists(select 1 from public.native_checkout_basket_items where order_id=p_order_id));
end $membership$;
revoke all on function public.native_checkout_basket_contains_order(uuid) from public,anon,authenticated;
grant execute on function public.native_checkout_basket_contains_order(uuid) to service_role;
commit;
