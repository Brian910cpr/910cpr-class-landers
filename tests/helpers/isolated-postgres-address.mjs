// Destructive fixture harnesses may target only loopback, or the exact GitHub
// postgres:17 service published onto loopback and verified through local Docker.
// Never accept an environment-supplied IP, metadata file, Docker host or context.
import assert from 'node:assert/strict';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {mkdtemp, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {isIP} from 'node:net';

const execFileAsync=promisify(execFile);
const idPattern=/^[a-f0-9]{64}$/;
const imagePattern=/^sha256:[a-f0-9]{64}$/;
const networkPattern=/^github_network_[a-f0-9]{32}$/;

export function assertLocalPostgresClient({args,env,port,database}) {
 assert(Number.isInteger(port)&&port>0&&port<65536,'invalid local PostgreSQL port');
 assert(/^(?:native_(?:checkout|demand_snapshot|scheduler_concurrency)_test|skills_claim_test(?:_\d+)?)$/.test(database),'isolated test database required');
 assert.deepEqual(args,['-X','-w','-q','-t','-A','-h','127.0.0.1','-p',String(port),'-U','postgres','-d',database,'-v','ON_ERROR_STOP=1'],'psql must use the exact isolated loopback target');
 const expected={PGHOSTADDR:'127.0.0.1',PGCONNECT_TIMEOUT:'3',PGPASSWORD:'',PGPASSFILE:process.platform==='win32'?'NUL':'/dev/null'};
 for(const [name,value] of Object.entries(expected))assert.equal(env[name],value,`unsafe ${name}`);
 assert(/^\-c statement_timeout=(?:20000|30000) -c lock_timeout=15000$/.test(env.PGOPTIONS),'unsafe PGOPTIONS');
 const permitted=new Set([...Object.keys(expected),'PGOPTIONS']);
 for(const name of Object.keys(env))if(/^PG/i.test(name))assert(permitted.has(name),`unexpected PostgreSQL environment setting: ${name}`);
}

export function githubPostgresContainerId(source) {
 assert.equal(source.GITHUB_ACTIONS,'true','non-loopback server requires the GitHub job PostgreSQL service');
 assert(/^[1-9]\d*$/.test(source.GITHUB_RUN_ID||''),'GitHub run identity required');
 assert(idPattern.test(source.NATIVE_TEST_POSTGRES_CONTAINER_ID||''),'exact job.services.postgres.id required');
 return source.NATIVE_TEST_POSTGRES_CONTAINER_ID;
}

// Pure validators are exported for adversarial tests. Runtime metadata always
// comes from /usr/bin/docker against the fixed local Unix socket below.
export function githubPostgresNetwork(container,containerId) {
 assert.equal(container?.Id,containerId,'Docker container identity mismatch');
 assert.equal(container?.State?.Running,true,'PostgreSQL service is not running');
 assert.equal(container?.Config?.Image,'postgres:17','unexpected PostgreSQL service image');
 assert(imagePattern.test(container?.Image||''),'missing immutable container image identity');
 const entries=Object.entries(container?.NetworkSettings?.Networks||{});
 assert.equal(entries.length,1,'expected exactly one GitHub job network');
 const [name,attachment]=entries[0];
 assert(networkPattern.test(name),'expected a GitHub job network');
 assert.equal(container?.HostConfig?.NetworkMode,name,'container network mode mismatch');
 assert(idPattern.test(attachment?.NetworkID||''),'missing exact Docker network identity');
 assert.equal(isIP(attachment?.IPAddress||''),4,'missing IPv4 container address');
 return {...attachment,name};
}

export function assertGithubPostgresService({container,image,network}, {containerId,port,address}) {
 assert(idPattern.test(containerId),'exact Docker container identity required');
 assert(Number.isInteger(port)&&port>0&&port<65536,'invalid published PostgreSQL port');
 const attachment=githubPostgresNetwork(container,containerId);
 assert.equal(address,attachment.IPAddress,'SQL server address is not the verified job PostgreSQL service');
 assert.equal(isIP(address),4,'invalid SQL server address');
 assert.equal(image?.Id,container.Image,'running image differs from inspected postgres:17');
 assert(image?.RepoTags?.includes('postgres:17'),'inspected image lacks postgres:17 tag');
 assert(image?.RepoDigests?.some(d=>/^(?:docker\.io\/library\/)?postgres@sha256:[a-f0-9]{64}$/.test(d)),'missing official postgres image repository digest');
 assert.equal(network?.Id,attachment.NetworkID,'Docker network identity mismatch');
 assert.equal(network?.Name,attachment.name,'Docker network name mismatch');
 assert.equal(network?.Driver,'bridge','PostgreSQL service must use a local bridge');
 assert.equal(network?.Scope,'local','PostgreSQL service network must be local');
 assert.equal(network?.Containers?.[containerId]?.IPv4Address,`${address}/${attachment.IPPrefixLen}`,'container is not attached at the verified network address');
 assert(Number.isInteger(attachment.IPPrefixLen)&&attachment.IPPrefixLen>=1&&attachment.IPPrefixLen<=32,'invalid network prefix');
 for(const [bindings,requested] of [[container.NetworkSettings?.Ports?.['5432/tcp'],false],[container.HostConfig?.PortBindings?.['5432/tcp'],true]]) {
  assert(Array.isArray(bindings)&&bindings.length>0,'PostgreSQL port is not published');
  // Docker stores omitted host IP as "" in HostConfig, then resolves it to
  // 0.0.0.0/:: in NetworkSettings. Only the resolved mapping proves publication.
  const ipv4=requested?['','127.0.0.1','0.0.0.0']:['127.0.0.1','0.0.0.0'];
  assert(bindings.some(b=>ipv4.includes(b.HostIp)&&b.HostPort===String(port)),'PostgreSQL port is not published onto the expected IPv4 loopback port');
  for(const binding of bindings) {
   assert([...ipv4,'::','::1'].includes(binding.HostIp),'unexpected published interface');
   assert.equal(binding.HostPort,String(port),'published PostgreSQL port mismatch');
  }
 }
}

export function localDockerInvocation(kind,reference,configDirectory) {
 assert(['container','image','network'].includes(kind),'unexpected Docker inspection type');
 assert(kind==='image'?reference==='postgres:17':idPattern.test(reference),'unsafe Docker reference');
 return {file:'/usr/bin/docker',args:['--host','unix:///var/run/docker.sock','inspect','--type',kind,reference],
  options:{env:{PATH:'/usr/bin:/bin',HOME:configDirectory,DOCKER_CONFIG:configDirectory},timeout:5000,maxBuffer:2*1024*1024}};
}

export async function assertIsolatedPostgresServerAddress(address,connection,source=process.env) {
 assertLocalPostgresClient(connection);
 if(address==='127.0.0.1')return;
 const containerId=githubPostgresContainerId(source);
 const directory=await mkdtemp(join(tmpdir(),'native-pg-docker-'));
 try {
  const inspect=async(kind,reference)=>{
   const {file,args,options}=localDockerInvocation(kind,reference,directory);
   const {stdout}=await execFileAsync(file,args,options);
   const result=JSON.parse(stdout);
   assert(Array.isArray(result)&&result.length===1,'expected exactly one Docker inspection result');
   return result[0];
  };
  const container=await inspect('container',containerId);
  const attachment=githubPostgresNetwork(container,containerId);
  const image=await inspect('image','postgres:17');
  const network=await inspect('network',attachment.NetworkID);
  assertGithubPostgresService({container,image,network},{containerId,port:connection.port,address});
 } finally {await rm(directory,{recursive:true,force:true});}
}
