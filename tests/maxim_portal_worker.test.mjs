import assert from 'node:assert/strict';
import { test } from 'node:test';
import worker from '../cloudflare/maxim-portal/src/index.js';

const schedule = {
  sessions: [
    {
      session_id: 'class-1',
      course_id: '359474',
      start_at: '2026-08-01T09:15:00-04:00',
      registration_status: 'open',
      public_direct_booking: true,
      registration_url: 'https://coastalcprtraining.enrollware.com/enroll?id=class-1'
    },
    {
      session_id: 'class-2',
      course_id: '359474',
      start_at: '2026-08-02T09:15:00-04:00',
      registration_status: 'open',
      public_direct_booking: true,
      registration_url: 'https://coastalcprtraining.enrollware.com/enroll?id=class-2'
    }
  ]
};

class Store {
  constructor() {
    this.people = new Map();
    this.registrations = [];
  }

  async createRegistration(data, person, offer, availabilityRow) {
    const active = this.registrations.find((row) =>
      row.person_id === person.personId &&
      row.corporate_customer === (data.corporateCustomer || 'MAXIM') &&
      row.credential_key === offer.credentialKey &&
      row.status === 'registered' &&
      !row.superseded_by
    );
    if (active && !data.moveFromRegistrationId) {
      return { error: 'duplicate_active_registration', existingRegistration: active, status: 409 };
    }
    if (data.moveFromRegistrationId && active && active.registration_id !== data.moveFromRegistrationId) {
      return { error: 'duplicate_active_registration', existingRegistration: active, status: 409 };
    }

    this.people.set(person.personId, person);
    const registration = {
      registration_id: `reg_${this.registrations.length + 1}`,
      person_id: person.personId,
      first_name: person.firstName,
      last_name: person.lastName,
      renewal_id: data.renewalId || data.sourceRenewalId || null,
      source_renewal_ref: data.renewalId || data.sourceRenewalId || null,
      source_person_ref: data.sourcePersonReference || null,
      corporate_customer: data.corporateCustomer || 'MAXIM',
      billing_account: data.billingAccount || null,
      course_id: offer.courseId,
      credential_key: offer.credentialKey,
      class_id: data.classId,
      registration_url: availabilityRow.registration_url,
      starts_at: data.startsAt,
      status: 'registered',
      superseded_by: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    if (data.moveFromRegistrationId) {
      const prior = this.registrations.find((row) => row.registration_id === data.moveFromRegistrationId);
      if (prior) {
        prior.status = 'superseded';
        prior.superseded_by = registration.registration_id;
      }
    }
    this.registrations.push(registration);
    return { ok: true, registrationId: registration.registration_id, personId: person.personId };
  }

  async listRegistrations() {
    return this.registrations.filter((row) => row.status === 'registered' && !row.superseded_by);
  }
}

function env(store = new Store(), scheduleFuture = schedule, overrides = {}) {
  return {
    STORE: store,
    SCHEDULE_FUTURE_JSON: scheduleFuture,
    PUBLIC_ORIGIN: 'https://www.910cpr.com',
    PORTAL_PATH: '/corp/maxim.html',
    ...overrides
  };
}

function registrationPayload(overrides = {}) {
  return {
    person: {
      personId: 'maxim_jane_doe',
      firstName: 'Jane',
      lastName: 'Doe',
      email: 'jane@example.com',
      phone: '910-555-0100'
    },
    corporateCustomer: 'MAXIM',
    billingAccount: 'Maxim #031',
    renewalId: 'renewal-1',
    sourceRenewalId: 'renewal-1',
    sourcePersonReference: 'Jane Doe',
    offerKey: 'bls-renewal',
    courseId: '359474',
    classId: 'class-1',
    startsAt: '2026-08-01T09:15:00-04:00',
    ...overrides
  };
}

async function postRegistration(environment, payload) {
  return worker.fetch(new Request('https://www.910cpr.com/api/corp/maxim/registrations', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload)
  }), environment);
}

async function postRegistrationWithHeaders(environment, payload, headers) {
  return worker.fetch(new Request('https://www.910cpr.com/api/corp/maxim/registrations', {
    method: 'POST',
    headers: { 'content-type': 'application/json', ...headers },
    body: JSON.stringify(payload)
  }), environment);
}

async function readRegistrations(environment) {
  const response = await worker.fetch(new Request('https://www.910cpr.com/api/corp/maxim/registrations'), environment);
  assert.equal(response.status, 200);
  return response.json();
}

test('successful registration persists a native MAXIM registration', async () => {
  const environment = env();
  const response = await postRegistration(environment, registrationPayload());
  assert.equal(response.status, 200);
  const result = await response.json();
  assert.equal(result.ok, true);

  const reread = await readRegistrations(environment);
  assert.equal(reread.registrations.length, 1);
  assert.equal(reread.registrations[0].corporate_customer, 'MAXIM');
  assert.equal(reread.registrations[0].billing_account, 'Maxim #031');
  assert.equal(reread.registrations[0].course_id, '359474');
  assert.equal(reread.registrations[0].renewal_id, 'renewal-1');
  assert.equal(reread.registrations[0].source_renewal_ref, 'renewal-1');
  assert.equal(reread.registrations[0].source_person_ref, 'Jane Doe');
});

test('stale slot is rejected before write', async () => {
  const environment = env();
  const response = await postRegistration(environment, registrationPayload({ classId: 'missing-class' }));
  assert.equal(response.status, 409);
  assert.deepEqual((await readRegistrations(environment)).registrations, []);
});

test('duplicate active registration is protected', async () => {
  const environment = env();
  assert.equal((await postRegistration(environment, registrationPayload())).status, 200);
  const duplicate = await postRegistration(environment, registrationPayload({ classId: 'class-2', startsAt: '2026-08-02T09:15:00-04:00' }));
  assert.equal(duplicate.status, 409);
  assert.equal((await readRegistrations(environment)).registrations.length, 1);
});

test('move preserves old registration history and supersedes only after replacement', async () => {
  const store = new Store();
  const environment = env(store);
  const first = await postRegistration(environment, registrationPayload());
  const firstBody = await first.json();
  assert.equal(first.status, 200);

  const moved = await postRegistration(environment, registrationPayload({
    classId: 'class-2',
    startsAt: '2026-08-02T09:15:00-04:00',
    moveFromRegistrationId: firstBody.registrationId
  }));
  assert.equal(moved.status, 200);
  const active = await readRegistrations(environment);
  assert.equal(active.registrations.length, 1);
  assert.equal(active.registrations[0].class_id, 'class-2');

  const prior = store.registrations.find((row) => row.registration_id === firstBody.registrationId);
  assert.equal(prior.status, 'superseded');
  assert.equal(prior.superseded_by, active.registrations[0].registration_id);
});

test('registration survives API reread with same store', async () => {
  const store = new Store();
  const environment = env(store);
  await postRegistration(environment, registrationPayload());
  const firstRead = await readRegistrations(environment);
  const secondRead = await readRegistrations(environment);
  assert.deepEqual(secondRead.registrations, firstRead.registrations);
});

test('deployed auth guard rejects unauthenticated corporate writes', async () => {
  const environment = env(new Store(), schedule, {
    REQUIRE_MAXIM_PORTAL_AUTH: 'true',
    MAXIM_PORTAL_AUTH_TOKEN: 'test-secret'
  });
  const rejected = await postRegistration(environment, registrationPayload());
  assert.equal(rejected.status, 401);

  const accepted = await postRegistrationWithHeaders(environment, registrationPayload(), {
    authorization: 'Bearer test-secret'
  });
  assert.equal(accepted.status, 200);
});
