(() => {
  'use strict';
  // Public Supabase anon key, not an owner credential. The Edge Function verifies its JWT.
  const PUBLIC_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndrdHdnY253ZHZiZWJjb2JneWV5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ1Njg0NDcsImV4cCI6MjEwMDE0NDQ0N30.UdjRtCNY9PbAC569s9KG0FRKSbZqykgi0XDMgPsY05I';
  const form = document.querySelector('[data-group-request]');
  if (!form) return;
  const button = form.querySelector('[type="submit"]');
  const status = document.getElementById('group-request-status');
  const started = Date.now();
  const requestId = crypto.randomUUID();
  let sending = false, received = false;
  button.disabled = false;
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (sending || received || !form.reportValidity()) return;
    sending = true;
    button.disabled = true;
    button.textContent = 'Sending…';
    status.textContent = 'Saving your request…';
    const fields = Object.fromEntries(new FormData(form));
    try {
      const response = await fetch('https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/group-request', {
        method: 'POST', headers: {'content-type': 'application/json', apikey:PUBLIC_ANON_KEY, authorization:`Bearer ${PUBLIC_ANON_KEY}`},
        signal: AbortSignal.timeout(20000),
        body: JSON.stringify({...fields, requestId, formElapsedMs: Date.now() - started})
      });
      const result = await response.json();
      if (!response.ok || !result.received || !result.reference) throw Error(result.error || 'Your request could not be confirmed.');
      received = true;
      status.textContent = `Request received. Reference ${result.reference}. Your class is not booked yet. 910CPR will contact you to confirm dates and pricing.`;
      button.textContent = 'Request received';
    } catch (error) {
      status.textContent = `${error.name === 'TimeoutError' || error.name === 'AbortError' ? 'The connection timed out. You can retry safely.' : error.message} Your details are still here. You can also call 910-395-5193.`;
      button.textContent = 'Retry request';
    } finally {
      sending = false;
      button.disabled = received;
    }
  });
})();
