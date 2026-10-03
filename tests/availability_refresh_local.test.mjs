import test from 'node:test';
import assert from 'node:assert/strict';
import { localRequest } from '../ops/operator/Run-AvailabilityRefresh.mjs';
import { WORKFLOW, FEED } from '../worker/availability-refresh-watchdog.mjs';

test('uses local gh login without reading token or passing Authorization', async () => {
  const calls = [];
  const request = localRequest('gh.exe', { execute: async (...args) => { calls.push(args); return { stdout: '{"workflow_runs":[]}' }; } });
  const response = await request(`${WORKFLOW}/runs?branch=main&per_page=10`, { headers: { Authorization: 'Bearer sentinel' } });
  assert.deepEqual(await response.json(), { workflow_runs: [] });
  assert.equal(JSON.stringify(calls).includes('sentinel'), false);
  assert.deepEqual(calls[0][1], ['api', 'repos/Brian910cpr/910cpr-class-landers/actions/workflows/refresh-admin-availability.yml/runs?branch=main&per_page=10', '--method', 'GET']);
  assert.equal(calls[0][2].windowsHide, true);
});
test('only the existing main refresh can be dispatched', async () => {
  const calls = [];
  const request = localRequest('gh.exe', { execute: async (...args) => { calls.push(args); return { stdout: '' }; } });
  assert.equal((await request(`${WORKFLOW}/dispatches`, { method: 'POST', body: '{"ref":"main"}' })).status, 204);
  assert.deepEqual(calls[0][1].slice(-2), ['-f', 'ref=main']);
  await assert.rejects(request(`${WORKFLOW}/dispatches`, { method: 'POST', body: '{"ref":"other"}' }));
  await assert.rejects(request('https://api.github.com/user/repos', {}));
  assert.equal(calls.length, 1);
});
test('forwards only public feed reads to network and sanitizes CLI errors', async () => {
  const request = localRequest('gh.exe', { network: async () => Response.json({ source: 'public' }), execute: async () => { throw new Error('sensitive upstream output'); } });
  assert.deepEqual(await (await request(`${FEED}?watchdog=1`)).json(), { source: 'public' });
  await assert.rejects(request(`${WORKFLOW}/runs?branch=main&per_page=10`), { message: 'refresh_check_failed' });
});
