import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {localPsql} from './helpers/local-postgres.mjs';
import {assertLocalPostgresClient,githubPostgresContainerId,assertGithubPostgresService,
 localDockerInvocation,assertIsolatedPostgresServerAddress} from './helpers/isolated-postgres-address.mjs';

const containerId='a'.repeat(64),networkId='b'.repeat(64),imageId='sha256:'+'c'.repeat(64);
const networkName='github_network_'+'d'.repeat(32),address='172.18.0.2',port=5432;
const database='native_demand_snapshot_test';
function connection(){return {port,database,
 args:['-X','-w','-q','-t','-A','-h','127.0.0.1','-p','5432','-U','postgres','-d',database,'-v','ON_ERROR_STOP=1'],
 env:{PGHOSTADDR:'127.0.0.1',PGCONNECT_TIMEOUT:'3',PGPASSWORD:'',PGPASSFILE:process.platform==='win32'?'NUL':'/dev/null',PGOPTIONS:'-c statement_timeout=20000 -c lock_timeout=15000'}};}
function metadata(){return {
 container:{Id:containerId,State:{Running:true},Config:{Image:'postgres:17'},Image:imageId,
  HostConfig:{NetworkMode:networkName,PortBindings:{'5432/tcp':[{HostIp:'',HostPort:'5432'}]}},
  NetworkSettings:{Ports:{'5432/tcp':[{HostIp:'0.0.0.0',HostPort:'5432'},{HostIp:'::',HostPort:'5432'}]},
   Networks:{[networkName]:{NetworkID:networkId,IPAddress:address,IPPrefixLen:16}}}},
 image:{Id:imageId,RepoTags:['postgres:17'],RepoDigests:['postgres@sha256:'+'e'.repeat(64)]},
 network:{Id:networkId,Name:networkName,Driver:'bridge',Scope:'local',Containers:{[containerId]:{IPv4Address:address+'/16'}}}
};}
const target={containerId,port,address};

test('native localhost remains accepted without Docker or GitHub context',async()=>{
 await assertIsolatedPostgresServerAddress('127.0.0.1',connection(),{});
});
test('existing skills helper remains compatible and scrubs inherited PostgreSQL overrides',async()=>{
 const database='skills_claim_test_509474';
 const psql=localPsql(database,{SKILLS_TEST_PORT:'55439',PGHOSTADDR:'remote.invalid',PGSERVICE:'production',PGPASSWORD:'unused'});
 await assertIsolatedPostgresServerAddress('127.0.0.1',{...psql,port:55439,database},{});
});
test('verified GitHub postgres:17 service permits its exact container address',()=>{
 assertGithubPostgresService(metadata(),target);
});
test('explicit IPv4 loopback publication also passes',()=>{
 const m=metadata();m.container.NetworkSettings.Ports['5432/tcp']=[{HostIp:'127.0.0.1',HostPort:'5432'}];
 m.container.HostConfig.PortBindings['5432/tcp']=[{HostIp:'127.0.0.1',HostPort:'5432'}];
 assertGithubPostgresService(m,target);
});

for(const [name,mutate] of [
 ['remote psql hostname',c=>c.args[6]='db.example.invalid'],
 ['hostaddr override',c=>c.env.PGHOSTADDR='172.18.0.2'],
 ['postgres service credentials',c=>c.env.PGSERVICE='production'],
 ['postgres service file',c=>c.env.PGSERVICEFILE='/tmp/production-service'],
 ['password',c=>c.env.PGPASSWORD='unexpected'],
 ['password file',c=>c.env.PGPASSFILE='/tmp/pgpass'],
 ['extra PG settings',c=>c.env.PGHOST='remote.invalid'],
 ['case-variant PG setting',c=>c.env.pghostaddr='remote.invalid'],
 ['options injection',c=>c.env.PGOPTIONS+=' -c search_path=unsafe'],
 ['duplicate host argument',c=>c.args.push('-h','remote.invalid')],
 ['mismatched port',c=>c.port=5433],
 ['invalid port',c=>c.port=NaN],
 ['nonfixture database',c=>c.database='production'],
])test(`rejects ${name} before address verification`,()=>{const c=connection();mutate(c);assert.throws(()=>assertLocalPostgresClient(c));});

for(const [name,mutate] of [
 ['different container ID',m=>m.container.Id='f'.repeat(64)],
 ['stopped container',m=>m.container.State.Running=false],
 ['wrong configured image',m=>m.container.Config.Image='postgres:16'],
 ['forged image tag over a different image',m=>m.container.Image='sha256:'+'f'.repeat(64)],
 ['missing image digest',m=>m.image.RepoDigests=[]],
 ['unrelated repository digest',m=>m.image.RepoDigests=['attacker/postgres@sha256:'+'e'.repeat(64)]],
 ['missing postgres:17 tag',m=>m.image.RepoTags=['postgres:latest']],
 ['host network mode',m=>m.container.HostConfig.NetworkMode='host'],
 ['arbitrary private network',m=>{m.container.NetworkSettings.Networks={bridge:Object.values(m.container.NetworkSettings.Networks)[0]};m.container.HostConfig.NetworkMode='bridge';}],
 ['multiple networks',m=>m.container.NetworkSettings.Networks.bridge={}],
 ['forged attachment network ID',m=>m.container.NetworkSettings.Networks[networkName].NetworkID='f'.repeat(64)],
 ['different container IP',m=>m.container.NetworkSettings.Networks[networkName].IPAddress='172.18.0.3'],
 ['mismatched network name',m=>m.network.Name='github_network_'+'f'.repeat(32)],
 ['nonbridge driver',m=>m.network.Driver='overlay'],
 ['nonlocal scope',m=>m.network.Scope='swarm'],
 ['missing network membership',m=>m.network.Containers={}],
 ['forged network address',m=>m.network.Containers[containerId].IPv4Address='172.18.0.99/16'],
 ['invalid prefix',m=>{m.container.NetworkSettings.Networks[networkName].IPPrefixLen=0;m.network.Containers[containerId].IPv4Address=address+'/0';}],
 ['unpublished port',m=>m.container.NetworkSettings.Ports={}],
 ['different published host port',m=>m.container.NetworkSettings.Ports['5432/tcp'][0].HostPort='5433'],
 ['unresolved actual publication',m=>m.container.NetworkSettings.Ports['5432/tcp'][0].HostIp=''],
 ['remote published interface',m=>m.container.NetworkSettings.Ports['5432/tcp'][0].HostIp='192.0.2.10'],
 ['forged requested binding',m=>m.container.HostConfig.PortBindings['5432/tcp'][0].HostPort='5433'],
])test(`rejects Docker metadata with ${name}`,()=>{const m=metadata();mutate(m);assert.throws(()=>assertGithubPostgresService(m,target));});

test('server IP must match the inspected service, never merely an RFC1918 range',()=>{
 for(const unexpected of ['127.0.0.2','172.18.0.99','10.0.0.1','192.168.1.1','db.example.invalid','::1'])
  assert.throws(()=>assertGithubPostgresService(metadata(),{...target,address:unexpected}));
});
test('container identity must come from explicit GitHub context',()=>{
 const source={GITHUB_ACTIONS:'true',GITHUB_RUN_ID:'1234',NATIVE_TEST_POSTGRES_CONTAINER_ID:containerId};
 assert.equal(githubPostgresContainerId(source),containerId);
 for(const patch of [{GITHUB_ACTIONS:'false'},{GITHUB_RUN_ID:''},{NATIVE_TEST_POSTGRES_CONTAINER_ID:''},{NATIVE_TEST_POSTGRES_CONTAINER_ID:'a'.repeat(12)},{NATIVE_TEST_POSTGRES_CONTAINER_ID:'--host=tcp://remote'}])
  assert.throws(()=>githubPostgresContainerId({...source,...patch}));
});
test('forged server-IP metadata does not authorize a remote or container address',async()=>{
 await assert.rejects(assertIsolatedPostgresServerAddress(address,connection(),{
  NATIVE_TEST_POSTGRES_SERVER_ADDRESS:address,NATIVE_TEST_POSTGRES_CONTAINER_ID:containerId,
  DOCKER_HOST:'tcp://remote.invalid:2375',DOCKER_CONTEXT:'remote',GITHUB_ACTIONS:'false'}));
});
test('Docker inspection pins binary and local socket, with no inherited credentials/context',()=>{
 const call=localDockerInvocation('container',containerId,'/tmp/empty-test-config');
 assert.equal(call.file,'/usr/bin/docker');
 assert.deepEqual(call.args,['--host','unix:///var/run/docker.sock','inspect','--type','container',containerId]);
 assert.deepEqual(call.options.env,{PATH:'/usr/bin:/bin',HOME:'/tmp/empty-test-config',DOCKER_CONFIG:'/tmp/empty-test-config'});
 assert(!('DOCKER_HOST' in call.options.env));assert(!('DOCKER_CONTEXT' in call.options.env));
 assert.throws(()=>localDockerInvocation('container','--host=tcp://remote','/tmp/config'));
 assert.throws(()=>localDockerInvocation('image','attacker/postgres:17','/tmp/config'));
});
test('race harnesses verify the target before fixture mutation and CI passes the exact service ID',()=>{
 const snapshot=readFileSync(new URL('./native-demand-snapshot-concurrency.mjs',import.meta.url),'utf8');
 const scheduler=readFileSync(new URL('./native-scheduler-concurrency.mjs',import.meta.url),'utf8');
 for(const [source,mutation] of [[snapshot,'await writer.query(fixture)'],[scheduler,'await c.query(await readFile']]) {
  assert(source.includes('await assertIsolatedPostgresServerAddress('));
  assert(source.indexOf('await assertIsolatedPostgresServerAddress(')<source.indexOf(mutation));
 }
 const workflow=readFileSync(new URL('../.github/workflows/verify-skills-native-claim.yml',import.meta.url),'utf8');
 for(const name of ['Verify atomic native demand snapshots on independent PostgreSQL connections','Verify minute scheduler admission on independent PostgreSQL connections']) {
  const step=workflow.split(`- name: ${name}`)[1]?.split('\n      - ')[0];
  assert(step?.includes('NATIVE_TEST_POSTGRES_CONTAINER_ID: ${{ job.services.postgres.id }}'));
 }
 assert(workflow.includes('tests/isolated-postgres-address.test.mjs tests/local-postgres-harness.test.mjs'));
});
