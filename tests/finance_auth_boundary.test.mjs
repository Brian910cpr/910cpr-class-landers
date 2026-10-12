import test from 'node:test';
import assert from 'node:assert/strict';
import finance from '../worker/finance-worker.js';

const endpoint='https://schedule.910cpr.com/admin/finance/unknown';
const origin='https://www.910cpr.com';
const env={HOT_SYNC_ADMIN_KEY:'local-fixture-only',STRIPE_SECRET_KEY:'unused-local-fixture'};
const request=(headers={},method='GET')=>new Request(endpoint,{method,headers:{Origin:origin,...headers}});

test('legacy finance denies anonymous, corporate and malformed owner sessions without touching financial data',async()=>{
  for(const headers of [{},{'X-Maxim-Session':'corporate-fixture'},{'X-LanderWare-Owner-Session':'malformed'},{'X-Hot-Sync-Admin-Key':'wrong-fixture'}]){
    const response=await finance.fetch(request(headers),env);
    assert.equal(response.status,401);
    assert.equal((await response.json()).code,'authentication_failed');
    assert.match(response.headers.get('cache-control'),/no-store/);
  }
});

test('legacy finance requires configured authority and retains its exact key boundary',async()=>{
  assert.equal((await finance.fetch(request(),{})).status,503);
  // Unknown route proves authorization passed without invoking Stripe or writing payments.
  assert.equal((await finance.fetch(request({'X-Hot-Sync-Admin-Key':env.HOT_SYNC_ADMIN_KEY}),env)).status,404);
});

test('finance CORS permits owner sessions only at first-party origins',async()=>{
  const response=await finance.fetch(request({},'OPTIONS'),env);
  assert.equal(response.status,204);
  assert.equal(response.headers.get('access-control-allow-origin'),origin);
  assert.equal(response.headers.get('access-control-allow-headers'),'Content-Type,X-Hot-Sync-Admin-Key,X-LanderWare-Owner-Session');
  assert.equal((await finance.fetch(new Request(endpoint,{headers:{Origin:'https://untrusted.example'}}),env)).status,403);
});
