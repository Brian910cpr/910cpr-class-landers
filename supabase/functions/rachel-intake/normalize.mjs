export function normalizePhone(value) {
  const digits = String(value || '').replace(/\D/g, '');
  if (digits.length === 10) return `+1${digits}`;
  if (digits.length === 11 && digits.startsWith('1')) return `+${digits}`;
  return digits ? `+${digits}` : null;
}
const text = (value, max = 20000) => {
  const result = String(value ?? '').trim();
  return result ? result.slice(0, max) : null;
};
const list = (value, max = 20) => Array.isArray(value) ? value.map(v => text(v, 500)).filter(Boolean).slice(0, max) : [];

export function normalizeRachelPayload(body) {
  const call = body?.call || body || {};
  const answers = call.extracted_answers || call.extractedAnswers || {};
  const externalCallId = text(call.external_call_id || call.externalCallId || call.call_id || call.callId, 200);
  if (!externalCallId) throw new Error('external_call_id is required; do not synthesize an operational id');

  const callerPhone = normalizePhone(call.caller_phone || call.callerPhone || call.from);
  const testNumber = normalizePhone(call.test_number || call.testNumber);
  const isTest = Boolean(call.is_test ?? call.isTest) || Boolean(testNumber && callerPhone === testNumber);

  return {
    source: 'marblism_rachel',
    transport: ['email_bridge', 'webhook', 'manual_fixture'].includes(body?.transport) ? body.transport : 'email_bridge',
    external_call_id: externalCallId,
    direction: text(call.direction, 20) || 'inbound',
    caller_phone: callerPhone,
    caller_name: text(call.caller_name || call.callerName, 200),
    started_at: text(call.started_at || call.startedAt || call.timestamp, 100),
    duration_seconds: Number.isFinite(Number(call.duration_seconds ?? call.durationSeconds)) ? Number(call.duration_seconds ?? call.durationSeconds) : null,
    is_test: isTest,
    summary: text(call.summary),
    transcript: text(call.transcript, 100000),
    recording_url: text(call.recording_url || call.recordingUrl, 2000),
    outcome: text(call.outcome, 500),
    extracted_answers: answers,
    raw_payload: body,
    intake: {
      organization_name: text(answers.organization || answers.organization_name, 300),
      requested_credential: text(answers.requested_credential || answers.credential, 300),
      deadline: text(answers.deadline, 300),
      requested_location: text(answers.location || answers.requested_location, 500),
      flexibility: text(answers.flexibility, 500),
      preferred_windows: list(answers.preferred_windows),
      alternate_windows: list(answers.alternate_windows),
      group_size: Number.isInteger(Number(answers.group_size)) && Number(answers.group_size) > 0 ? Number(answers.group_size) : null,
      unresolved_questions: list(answers.unresolved_questions),
      escalation_flags: list(answers.escalation_flags, 10)
    }
  };
}

export function intakeDetails(event) {
  const i = event.intake;
  return [
    `Caller: ${event.caller_name || 'Unknown'} (${event.caller_phone || 'unknown number'})`,
    `Credential: ${i.requested_credential || 'Unknown'}`,
    `Deadline: ${i.deadline || 'Unknown'}`,
    `Location: ${i.requested_location || 'Unknown'}`,
    `Flexibility: ${i.flexibility || 'Unknown'}`,
    `Preferred windows: ${i.preferred_windows.join('; ') || 'Unknown'}`,
    `Alternate windows: ${i.alternate_windows.join('; ') || 'Unknown'}`,
    `Group size: ${i.group_size || 'Unknown'}`,
    `Unresolved: ${i.unresolved_questions.join('; ') || 'None recorded'}`,
    `Escalation flags: ${i.escalation_flags.join(', ') || 'None'}`,
    `Call ID: ${event.external_call_id}`,
    `Recording: ${event.recording_url || 'Not supplied'}`,
    '',
    'Summary:', event.summary || 'Not supplied',
    '',
    'Transcript:', event.transcript || 'Not supplied'
  ].join('\n');
}
