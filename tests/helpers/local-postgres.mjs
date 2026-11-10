// Connection settings for disposable localhost tests only. This module never
// connects, creates a database, installs software, or reads a credential file.
export function localPsql(database,source=process.env){
 if(!/^(?:native_checkout_test|skills_claim_test(?:_\d+)?)$/.test(database||''))throw Error('isolated_test_database_required');
 const port=Number(source.SKILLS_TEST_PORT||5432);
 if(!Number.isInteger(port)||port<1||port>65535)throw Error('invalid_test_port');
 const env={...source};
 // PGHOSTADDR can override the apparent -h host; do not inherit production
 // service definitions, options, passwords, or an implicit ~/.pgpass either.
 for(const name of Object.keys(env))if(/^PG/i.test(name))delete env[name];
 Object.assign(env,{PGHOSTADDR:'127.0.0.1',PGCONNECT_TIMEOUT:'3',PGPASSWORD:'',PGPASSFILE:process.platform==='win32'?'NUL':'/dev/null',PGOPTIONS:'-c statement_timeout=30000 -c lock_timeout=15000'});
 return {command:source.SKILLS_TEST_PSQL||'psql',env,args:['-X','-w','-q','-t','-A','-h','127.0.0.1','-p',String(port),'-U','postgres','-d',database,'-v','ON_ERROR_STOP=1']};
}

// Target major observed by the coordinator: Supabase PostgreSQL17.6.
// Pure metadata guard only; never opens a connection or authorizes a hosted DB.
export const TARGET_POSTGRES_MAJOR=17;
export function assertLocalTargetServer(server,database){
 if(!/^(?:native_checkout_test|skills_claim_test(?:_\d+)?)$/.test(database||''))throw Error('isolated_test_database_required');
 if(server?.database!==database)throw Error('isolated_test_database_mismatch');
 if(!Number.isInteger(server.version)||Math.floor(server.version/10000)!==TARGET_POSTGRES_MAJOR)throw Error('postgresql17_target_required');
 if(server.recovery!==false)throw Error('isolated_primary_required');
 return {major:TARGET_POSTGRES_MAJOR,version:server.version,database};
}
