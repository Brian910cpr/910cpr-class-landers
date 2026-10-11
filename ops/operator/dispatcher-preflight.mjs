// Offline eligibility only. This module cannot publish, claim, or execute work.
const TYPES = new Set(['selftest.ping', 'site.healthcheck']);
const STATES = new Set(['idle', 'working', 'disabled']);
const REPOSITORY = 'Brian910cpr/910cpr-class-landers';

function requireValue(ok, message) {
  if (!ok) throw new Error(message);
}
function instant(value) {
  requireValue(typeof value === 'string' && /(?:Z|[+-]\d\d:\d\d)$/.test(value), 'Timestamp requires timezone');
  const result = Date.parse(value);
  requireValue(Number.isFinite(result), 'Invalid timestamp');
  return result;
}

/** Snapshot contract: enrolled identity + heartbeat + explicit local profile.
 * Active job IDs must eventually come from durable leases, never inference.
 * A result is a preview, not authorization to dispatch or proof of completion.
 */
export function preflight({workers, queue, now, staleSeconds = 180}) {
  const clock = instant(now);
  requireValue(Number.isInteger(staleSeconds) && staleSeconds > 0, 'Invalid stale window');
  requireValue(Array.isArray(workers) && Array.isArray(queue), 'Expected worker and queue arrays');
  const ids = new Set(), names = new Set(), jobs = new Set();
  const fleet = workers.map(({identity, heartbeat, profile}) => {
    requireValue(identity && heartbeat && profile, 'Missing worker snapshot fields');
    const {worker_id: id, worker_name: name, worker_version: version} = identity;
    requireValue(typeof id === 'string' && id.length > 0 && typeof name === 'string' && name.length > 0, 'Missing identity');
    requireValue(!ids.has(id) && !names.has(name), 'Duplicate worker identity');
    ids.add(id); names.add(name);
    requireValue(typeof version === 'string' && version.length > 0, 'Missing worker version');
    requireValue(identity.repository === REPOSITORY, 'Wrong repository');
    requireValue(heartbeat.worker_id === id && heartbeat.worker_name === name && heartbeat.worker_version === version, 'Heartbeat identity mismatch');
    requireValue(STATES.has(heartbeat.state), 'Unknown heartbeat state');
    requireValue(Array.isArray(identity.capabilities) && identity.capabilities.every(x => typeof x === 'string'), 'Invalid capabilities');
    requireValue(typeof profile.disabled === 'boolean', 'Explicit disabled flag required');
    const limit = profile.max_concurrency ?? 1;
    requireValue(Number.isInteger(limit) && limit > 0, 'Invalid concurrency');
    requireValue(Array.isArray(profile.active_job_ids) && profile.active_job_ids.every(x => typeof x === 'string' && x.length > 0), 'Invalid active jobs');
    requireValue(new Set(profile.active_job_ids).size === profile.active_job_ids.length, 'Duplicate active job');
    const age = clock - instant(heartbeat.observed_at_utc);
    const state = profile.disabled || heartbeat.state === 'disabled' ? 'disabled'
      : age < 0 || age >= staleSeconds * 1000 ? 'stale'
      : heartbeat.state === 'working' || profile.active_job_ids.length >= limit ? 'busy' : 'idle';
    return {worker_id: id, worker_name: name, worker_version: version,
      job_types: [...TYPES].filter(x => identity.capabilities.includes(`job.${x}`)),
      last_heartbeat: heartbeat.observed_at_utc, state, max_concurrency: limit,
      current_jobs: [...profile.active_job_ids]};
  });
  const preview = queue.map(job => {
    requireValue(job && typeof job.job_id === 'string' && job.job_id.length > 0, 'Missing durable job ID');
    requireValue(!jobs.has(job.job_id), 'Duplicate queued job ID'); jobs.add(job.job_id);
    // Queue intake is deliberately explicit; no backlog-title/command interpretation.
    requireValue(job.source === 'explicit' && job.worker_safe === true, 'Unapproved job source');
    requireValue(typeof job.job_type === 'string', 'Missing job type');
    const capable = fleet.filter(w => w.job_types.includes(job.job_type));
    const eligible = capable.filter(w => w.state === 'idle');
    return {job_id: job.job_id, job_type: job.job_type,
      eligible_worker_ids: eligible.map(w => w.worker_id).sort(),
      blocker: !TYPES.has(job.job_type) ? 'unsupported_job_type'
        : capable.length === 0 ? 'no_capable_worker'
        : eligible.length === 0 ? 'no_idle_capable_worker' : null};
  });
  return {schema_version: 1, mode: 'OFFLINE_PREFLIGHT_ONLY', dispatch_enabled: false,
    observed_at_utc: now, queue_depth: queue.length, fleet, preview};
}
