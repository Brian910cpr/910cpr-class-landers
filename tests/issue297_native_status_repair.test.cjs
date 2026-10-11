const test = require('node:test');
const assert = require('node:assert/strict');
const {loadEndpoint} = require('./helpers/canonical_demand_endpoint.cjs');
const api = loadEndpoint(() => {throw Error('Unexpected network call');});

test('issue297: correcting existing native statuses restores two seats without new relationships', () => {
  const session = {id:'native-session',source:'landerware_event',registration_backend:'landerware',
    external_class_id:'lw-native-session',registrations:[
      {id:'seat-A',status:'active'}, {id:'seat-B',status:'active'}]};
  assert.equal(api.projectDemand(session).active_registration_count,0);
  const corrected = {...session,registrations:session.registrations.map(r=>({...r,status:'registered'}))};
  assert.equal(api.projectDemand(corrected).active_registration_count,2);
  assert.deepEqual(corrected.registrations.map(r=>r.id),session.registrations.map(r=>r.id));
  assert.equal(api.projectDemand(corrected).demand_status,'current');
  // A native correction must not refresh or guess another session's external roster.
  const external = {...corrected,id:'unrelated-external',source:'enrollware',
    registration_backend:'enrollware',external_class_id:'12345'};
  assert.equal(api.projectDemand(external).active_registration_count,null);
  assert.equal(api.projectDemand(external).demand_status,'external_reconciliation_required');
  assert.equal(api.projectDemand({...corrected,registrations:[{status:'registered'}]}).active_registration_count,1);
});
