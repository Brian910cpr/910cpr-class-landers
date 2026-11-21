// Server-side preparation only. No producer or transport is enabled by this module.
// Never pass customer text or exception messages into telemetry.
const SOURCES = new Set(['ai', 'customer_lookup', 'database', 'gmail', 'calendar',
  'fieldy', 'github', 'validation', 'deployment', 'policy_review']);
const STATUSES = new Set(['queued', 'in_flight', 'success', 'retry', 'blocked', 'error']);
const SUMMARIES = Object.freeze({ queued: 'Operation queued', in_flight: 'Operation started',
  success: 'Operation completed', retry: 'Operation retry scheduled',
  blocked: 'Operation blocked; inspect authorized operation diagnostics',
  error: 'Operation failed; inspect authorized operation diagnostics' });
const FIELDS = new Set(['event_id', 'correlation_id', 'source', 'operation_type',
  'timestamp', 'status', 'duration_ms', 'visibility']);
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

/** Build a safe envelope using a server-owned operation registry.
 * Registry entries: { source, visibility }. Never construct the registry from request data.
 * IDs must be generated opaque UUIDs, never customer/external record identifiers.
 */
export function createActivityEvent(input, registry) {
  if (!input || typeof input !== 'object' || Array.isArray(input) ||
      Object.keys(input).some(key => !FIELDS.has(key))) throw new TypeError('Invalid event fields');
  for (const key of ['event_id', 'correlation_id']) {
    if (typeof input[key] !== 'string' || !UUID.test(input[key])) throw new TypeError('Invalid opaque ID');
  }
  if (!SOURCES.has(input.source) || !STATUSES.has(input.status)) throw new TypeError('Invalid source or status');
  if (typeof input.operation_type !== 'string' || !/^[a-z][a-z0-9_.]{0,63}$/.test(input.operation_type) ||
      !Object.hasOwn(registry, input.operation_type)) throw new TypeError('Unregistered operation');
  const operation = registry[input.operation_type];
  if (operation.source !== input.source || !['owner', 'staff'].includes(operation.visibility) ||
      input.visibility !== operation.visibility) throw new TypeError('Operation scope mismatch');
  if (typeof input.timestamp !== 'string' || !Number.isFinite(Date.parse(input.timestamp)) ||
      new Date(input.timestamp).toISOString() !== input.timestamp) throw new TypeError('Expected canonical UTC timestamp');
  const terminal = ['success', 'blocked', 'error'].includes(input.status);
  if (terminal ? !Number.isSafeInteger(input.duration_ms) || input.duration_ms < 0 : input.duration_ms !== null) {
    throw new TypeError('Invalid duration');
  }
  // Construct explicitly: no payload, URLs, messages, prompts, tokens, or arbitrary summaries.
  return Object.freeze({ schema_version: 1, event_id: input.event_id,
    correlation_id: input.correlation_id, source: input.source,
    operation_type: input.operation_type, timestamp: input.timestamp,
    status: input.status, duration_ms: input.duration_ms,
    visibility: operation.visibility, safe_summary: SUMMARIES[input.status] });
}
