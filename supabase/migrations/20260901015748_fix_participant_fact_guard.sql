-- Correct the shared trigger to inspect the credential-only completion_id field through JSON.
create or replace function public.validate_participant_fact_identity()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  v_customer uuid;
  v_session uuid;
  v_course uuid;
  v_completion public.participant_completions%rowtype;
begin
  select r.customer_id,r.class_session_id,s.course_id
    into v_customer,v_session,v_course
  from public.registrations r
  join public.class_sessions s on s.id=r.class_session_id
  where r.id=new.registration_id;
  if v_customer is null
     or new.customer_id<>v_customer
     or new.class_session_id<>v_session
     or new.course_id<>v_course then
    raise exception 'participant fact identity does not match canonical registration/session/course';
  end if;
  if tg_table_name='participant_credentials' and (to_jsonb(new)->>'completion_id') is not null then
    select * into v_completion from public.participant_completions
      where id=(to_jsonb(new)->>'completion_id')::uuid;
    if not found
       or v_completion.customer_id<>new.customer_id
       or v_completion.registration_id<>new.registration_id
       or v_completion.class_session_id<>new.class_session_id
       or v_completion.course_id<>new.course_id then
      raise exception 'credential completion does not match canonical participant fact identity';
    end if;
  end if;
  return new;
end;
$$;
revoke all on function public.validate_participant_fact_identity() from public, anon, authenticated;
