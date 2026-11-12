-- Disposable fixture matching the document columns used by the existing staff
-- workbench. Never apply this fixture to a hosted project.
create schema storage;
create table storage.buckets(id text primary key,public boolean);
insert into storage.buckets values('class-session-docs',false);
create table public.class_session_documents(
 id uuid primary key default gen_random_uuid(),class_session_id uuid,
 document_type text,file_name text,storage_bucket text,storage_path text,
 content_type text,file_size bigint,sha256 text,source text,
 unique(storage_bucket,storage_path)
);
