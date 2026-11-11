-- Synthetic database-only stand-ins. No installed pg_net, Vault or network.
do $$begin
 if not exists(select 1 from pg_roles where rolname='anon') then create role anon;end if;
 if not exists(select 1 from pg_roles where rolname='authenticated') then create role authenticated;end if;
 if not exists(select 1 from pg_roles where rolname='service_role') then create role service_role bypassrls;end if;
 if exists(select 1 from pg_roles where rolname in ('anon','authenticated','service_role')
   and (rolcanlogin or rolsuper or rolcreatedb or rolcreaterole or rolreplication
     or rolbypassrls<>(rolname='service_role'))) then
   raise exception 'unexpected_test_role_privileges';
 end if;
end$$;
create schema net;
create schema vault;
create table net._http_response(id bigint,status_code integer,timed_out boolean,error_msg text);
create table vault.decrypted_secrets(id uuid,decrypted_secret text);
create table net.captured(id bigint generated always as identity,url text,body jsonb,params jsonb,headers jsonb,timeout_milliseconds int);
create function net.http_post(url text,body jsonb,params jsonb,headers jsonb,timeout_milliseconds int)
returns bigint language plpgsql as $$declare n bigint;begin
 insert into net.captured(url,body,params,headers,timeout_milliseconds) values($1,$2,$3,$4,$5) returning id into n;
 return n;
end$$;
create function public.native_checkout_confirmation_health() returns jsonb language sql as $$select '{"healthy":true}'::jsonb$$;
