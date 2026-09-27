/** Shared owner/runtime freshness contract. Database read time is not source time. */
export function registrationProof(row: any, now = new Date()) {
  const active = Array.isArray(row.registrations)
    ? row.registrations.filter((r: any) => ['registered','confirmed','completed'].includes(r.status)) : [];
  const native = ['landerware','manual'].includes(row.registration_backend);
  const proof = row.external_reconciliation || {};
  const observed = Date.parse(proof.source_observed_at || '');
  let status = 'external_reconciliation_required';
  if (!Array.isArray(row.registrations)) status = 'missing_registration_relationships';
  else if (native) status = 'current';
  else if (proof.complete === true && Number.isFinite(observed)) {
    const expected = proof.active_external_registration_ids;
    const actual = active.map((r: any) => r.external_registration_id).sort();
    if (observed > now.getTime() + 300000 || now.getTime() - observed > 3600000) status = 'stale_reconciliation';
    else if (!Array.isArray(expected) || expected.length !== proof.active_registration_count
      || new Set(expected).size !== expected.length || actual.some((id: any) => !id)
      || JSON.stringify([...expected].sort()) !== JSON.stringify(actual)) status = 'registration_relationship_mismatch';
    else status = 'current';
  }
  return {count_available: status === 'current', demand_status: status,
    source_observed_at: native ? null : proof.source_observed_at || null,
    reconciled_at: native ? null : proof.reconciled_at || null,
    source_sha256: native ? null : proof.source_sha256 || null,
    freshness_minutes: native ? null : 60,
    active_registration_count: status === 'current' ? active.length : null};
}
