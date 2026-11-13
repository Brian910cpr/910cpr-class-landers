// Pure, no-I/O fixture adaptation. Does not connect or authorize any target.
// Caller must independently verify a newly created disposable loopback stack.
const documents='tests/helpers/skills-checkout-documents.sql';
const profiles='tests/helpers/native-checkout-profile-schema.sql';
const once=(source,fragment)=>{if(source.split(fragment).length!==2)throw Error('local_storage_fixture_source_drift');return source.replace(fragment,'');};
export function adaptLocalSupabaseFixture(path,source){
 source=source.replaceAll('\r\n','\n');
 if(path===documents){
  for(const fragment of ["create schema storage;\n","create table storage.buckets(id text primary key,public boolean);\n","insert into storage.buckets values('class-session-docs',false);\n"])source=once(source,fragment);
 }else if(path===profiles){
  source=once(source,"create table storage.objects(id uuid primary key default gen_random_uuid(),bucket_id text not null,name text not null,metadata jsonb not null default '{}',unique(bucket_id,name));\n");
 }
 return source;
}
export const localSupabaseFixturePreflight=`do $local_fixture$
begin
 if current_setting('server_version_num')::int/10000<>17 then raise exception 'local_fixture_postgresql17_required'; end if;
 if inet_server_addr() is null or host(inet_server_addr()) not in ('127.0.0.1','::1') then raise exception 'local_fixture_loopback_required'; end if;
 if exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relkind in ('r','p') and c.relname<>'spatial_ref_sys') then raise exception 'local_fixture_public_schema_not_empty'; end if;
 if to_regclass('auth.users') is null or to_regclass('storage.buckets') is null or to_regclass('storage.objects') is null then raise exception 'local_fixture_managed_schemas_required'; end if;
 if not exists(select 1 from information_schema.columns where table_schema='storage' and table_name='buckets' and column_name='public' and data_type='boolean')
 or not exists(select 1 from information_schema.columns where table_schema='storage' and table_name='objects' and column_name='metadata' and data_type='jsonb') then raise exception 'local_fixture_storage_contract_mismatch'; end if;
 if not exists(select 1 from storage.buckets where id='class-session-docs' and public=false) then raise exception 'local_fixture_private_bucket_required'; end if;
end $local_fixture$;`;

// Native CLI may proxy a loopback client onto PostgreSQL's Unix socket.
// Only the runner's independent process/directory ownership check may opt in.
export function localSupabaseFixtureAdmission({verifiedNativeSocket=false}={}){
 if(verifiedNativeSocket!==true&&verifiedNativeSocket!==false)throw Error('invalid_native_socket_proof');
 return verifiedNativeSocket?localSupabaseFixturePreflight.replace("inet_server_addr() is null or host(inet_server_addr()) not in", "inet_server_addr() is not null and host(inet_server_addr()) not in"):localSupabaseFixturePreflight;
}
