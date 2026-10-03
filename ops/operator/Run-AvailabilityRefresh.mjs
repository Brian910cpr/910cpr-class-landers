// Local adapter for the same publication watchdog. gh uses its existing keyring;
// no token is read, copied, stored, or sent to a new service.
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { mkdir, readFile, writeFile, rename } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { checkAndRefresh, health, FEED, WORKFLOW } from '../../worker/availability-refresh-watchdog.mjs';

const runFile = promisify(execFile);
export function localRequest(ghPath, { execute = runFile, network = fetch } = {}) {
  return async (url, options = {}) => {
    if (url.startsWith(`${FEED}?watchdog=`)) return network(url, options);
    const isRead = url === `${WORKFLOW}/runs?branch=main&per_page=10` && !options.method;
    const isDispatch = url === `${WORKFLOW}/dispatches` && options.method === 'POST'
      && options.body === JSON.stringify({ ref: 'main' });
    if (!isRead && !isDispatch) throw new Error('request_not_allowlisted');
    const endpoint = url.slice('https://api.github.com/'.length);
    const args = ['api', endpoint, '--method', isDispatch ? 'POST' : 'GET'];
    if (isDispatch) args.push('-f', 'ref=main');
    try {
      const { stdout } = await execute(ghPath, args, {
        windowsHide: true, timeout: 30_000, maxBuffer: 1024 * 1024,
      });
      return isDispatch ? new Response(null, { status: 204 })
        : new Response(stdout, { headers: { 'Content-Type': 'application/json' } });
    } catch {
      // CLI errors may contain environment details; only expose the bounded code.
      throw new Error('refresh_check_failed');
    }
  };
}

export async function runLocal(stateDirectory, ghPath) {
  await mkdir(stateDirectory, { recursive: true });
  const statePath = resolve(stateDirectory, 'publication-watchdog.json');
  const STATE = {
    async get() {
      try { return JSON.parse(await readFile(statePath, 'utf8')); }
      catch (error) { if (error.code === 'ENOENT') return null; throw error; }
    },
    async put(_key, value) {
      const temp = `${statePath}.next`;
      await writeFile(temp, value, 'utf8');
      await rename(temp, statePath);
    },
  };
  const result = await checkAndRefresh({ STATE, GITHUB_ACTIONS_TOKEN: 'managed-by-local-gh' }, {
    request: localRequest(ghPath),
  });
  const observed = { ...health(result), runtime: 'local-task-scheduler', observedAt: new Date().toISOString() };
  await writeFile(resolve(stateDirectory, 'health.json'), JSON.stringify(observed, null, 2), 'utf8');
  return observed;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const [stateDirectory, ghPath] = process.argv.slice(2);
  if (!stateDirectory || !ghPath) throw new Error('Usage: Run-AvailabilityRefresh.mjs STATE_DIRECTORY GH_EXECUTABLE');
  try {
    const result = await runLocal(resolve(stateDirectory), ghPath);
    process.exitCode = result.ok ? 0 : 1;
  } catch {
    console.error('availability_refresh_local_failure');
    process.exitCode = 1;
  }
}
