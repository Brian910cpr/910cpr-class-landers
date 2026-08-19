const JSON_HEADERS = { 'content-type': 'application/json; charset=utf-8' };
const FROM = 'brian@910cpr.com';
const SUBJECT = 'Maxim CPR recertification reminder';

function json(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: JSON_HEADERS });
}

function escapeHtml(value) {
  return String(value || '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[character]));
}

function validEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || '').trim());
}

async function readJson(request) {
  try { return await request.json(); } catch { return null; }
}

function authorized(request, env) {
  return Boolean(env.MAXIM_EMAIL_SECRET) &&
    request.headers.get('authorization') === `Bearer ${env.MAXIM_EMAIL_SECRET}`;
}

export default {
  async fetch(request, env) {
    if (request.method !== 'POST') return json({ error: 'Not found' }, 404);
    if (!authorized(request, env)) return json({ error: 'Unauthorized' }, 401);
    if (!env.EMAIL?.send) return json({ error: 'Email binding is not configured' }, 503);

    const data = await readJson(request);
    const to = String(data?.to || '').trim();
    const firstName = String(data?.firstName || '').trim();
    if (!validEmail(to)) return json({ error: 'A valid employee email is required' }, 400);

    const greeting = firstName ? `Hi ${firstName},` : 'Hello,';
    const scheduleUrl = env.MAXIM_SCHEDULING_URL || 'https://www.910cpr.com/corp/maxim';
    const text = `${greeting}\n\nMaxim has asked me to remind you that your CPR Card is expiring soon, and they would like you to choose a date most convenient for you to recertify.\n\nChoose a date here:\n${scheduleUrl}\n\nIf you need further info on scheduling, please reply here or call 910CPR at 910-395-5193.\n\nOther Maxim-specific questions should be forwarded to your Maxim representative at 910-251-8990.\n\nThank you!\nBrian`;
    const html = `<p>${escapeHtml(greeting)}</p><p>Maxim has asked me to remind you that your CPR Card is expiring soon, and they would like you to choose a date most convenient for you to recertify.</p><p><a href="${escapeHtml(scheduleUrl)}">Choose a recertification date</a></p><p>If you need further info on scheduling, please reply here or call 910CPR at <a href="tel:+19103955193">910-395-5193</a>.</p><p>Other Maxim-specific questions should be forwarded to your Maxim representative at <a href="tel:+19102518990">910-251-8990</a>.</p><p>Thank you!<br>Brian</p>`;

    try {
      const result = await env.EMAIL.send({
        to,
        from: { email: FROM, name: 'Brian | 910CPR' },
        replyTo: FROM,
        subject: SUBJECT,
        text,
        html
      });
      return json({ ok: true, messageId: result.messageId });
    } catch (error) {
      console.error('Maxim reminder email failed', error?.code, error?.message);
      return json({ error: 'Email delivery failed', code: error?.code || null }, 502);
    }
  }
};
