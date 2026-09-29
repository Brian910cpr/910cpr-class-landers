revoke all privileges on table public.nhcso_classes from anon, authenticated;
revoke all privileges on table public.nhcso_students from anon, authenticated;
revoke all privileges on table public.nhcso_documents from anon, authenticated;

grant select, insert, update, delete on table public.nhcso_classes to service_role;
grant select, insert, update, delete on table public.nhcso_students to service_role;
grant select, insert, update, delete on table public.nhcso_documents to service_role;
