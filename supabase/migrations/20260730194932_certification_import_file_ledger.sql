-- Review-only migration. Do not apply before the certification importer dry run
-- and its security/data-quality review are approved.

create table if not exists public.certification_import_files (
  id uuid primary key default gen_random_uuid(),
  source_system text not null default 'google_drive',
  source_folder_id text not null,
  source_file_id text not null,
  source_file_name text not null,
  source_file_modified_at timestamptz,
  source_file_size bigint,
  source_file_md5 text,
  source_file_sha256 text,
  parser_version text not null,
  inspection_status text not null check (
    inspection_status in (
      'discovered',
      'inspected',
      'unsupported',
      'partial_failure',
      'failed'
    )
  ),
  rows_parsed integer not null default 0 check (rows_parsed >= 0),
  rows_invalid integer not null default 0 check (rows_invalid >= 0),
  rows_duplicate integer not null default 0 check (rows_duplicate >= 0),
  error_summary jsonb not null default '[]'::jsonb,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  last_inspected_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (source_system, source_file_id)
);

create index if not exists certification_import_files_folder_modified_idx
  on public.certification_import_files (
    source_folder_id,
    source_file_modified_at desc
  );

create index if not exists certification_import_files_sha256_idx
  on public.certification_import_files (source_file_sha256)
  where source_file_sha256 is not null;

alter table public.certification_import_files enable row level security;

revoke all on table public.certification_import_files from public;
revoke all on table public.certification_import_files from anon, authenticated;
grant select, insert, update on table public.certification_import_files to service_role;

comment on table public.certification_import_files is
  'Private file-level inspection ledger for general certification-history imports.';
comment on column public.certification_import_files.source_file_sha256 is
  'Content hash used to detect renamed/duplicated source files without relying on filenames.';
