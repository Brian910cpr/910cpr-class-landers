const STRIPE_API = "https://api.stripe.com/v1";
const PAYMENT_METHODS = new Set(["check", "cash", "venmo", "cash_app", "external_ach", "other"]);

export async function handleFinanceApi(request, env, url, origin, helpers) {
  if (!url.pathname.startsWith("/admin/finance/")) return null;
  if (!env.STRIPE_SECRET_KEY) return helpers.json({ error: "Stripe is not configured for LanderWare.", code: "stripe_unavailable" }, 503, origin);

  if (url.pathname === "/admin/finance/invoices" && request.method === "GET") {
    return listOpenInvoices(env, origin, helpers);
  }

  const paymentMatch = url.pathname.match(/^\/admin\/finance\/invoices\/(in_[A-Za-z0-9]+)\/outside-payment$/);
  if (paymentMatch && request.method === "POST") {
    return recordOutsidePayment(paymentMatch[1], request, env, origin, helpers);
  }

  return helpers.json({ error: "Financial endpoint not found.", code: "not_found" }, 404, origin);
}

async function listOpenInvoices(env, origin, helpers) {
  try {
    const params = new URLSearchParams({ status: "open", limit: "100", "expand[]": "data.customer" });
    const response = await stripeRequest(env, `/invoices?${params}`);
    const payload = await response.json();
    if (!response.ok) return stripeFailure(payload, response.status, origin, helpers);

    const notesByInvoice = await loadReceiptNotes(env);
    const now = Date.now();
    const invoices = (payload.data || []).map((invoice) => {
      const dueAt = invoice.due_date ? invoice.due_date * 1000 : null;
      const ageDays = Math.max(0, Math.floor((now - (invoice.created || 0) * 1000) / 86400000));
      const customer = typeof invoice.customer === "object" && invoice.customer ? invoice.customer : null;
      return {
        id: invoice.id,
        number: invoice.number || invoice.id,
        status: dueAt && dueAt < now ? "past_due" : "open",
        amount_due: invoice.amount_due || 0,
        amount_remaining: invoice.amount_remaining || 0,
        currency: invoice.currency || "usd",
        created: invoice.created || null,
        due_date: invoice.due_date || null,
        age_days: ageDays,
        customer_name: invoice.customer_name || customer?.name || "Customer",
        customer_email: invoice.customer_email || customer?.email || "",
        description: invoice.description || firstLineDescription(invoice),
        hosted_invoice_url: invoice.hosted_invoice_url || "",
        invoice_pdf: invoice.invoice_pdf || "",
        last_outside_payment: notesByInvoice.get(invoice.id) || null,
      };
    }).sort((a, b) => (a.due_date || a.created || 0) - (b.due_date || b.created || 0));

    return helpers.json({ invoices, has_more: Boolean(payload.has_more), synced_at: new Date().toISOString() }, 200, origin);
  } catch (error) {
    return helpers.safeError(error, origin);
  }
}

async function recordOutsidePayment(invoiceId, request, env, origin, helpers) {
  if (!env.HOT_SYNC_D1) return helpers.json({ error: "Financial receipt storage is not connected.", code: "storage_unavailable" }, 503, origin);
  try {
    const input = await helpers.requestJson(request);
    const method = helpers.cleanText(input.method, 40, true).toLowerCase();
    if (!PAYMENT_METHODS.has(method)) throw new helpers.ValidationError("Payment method is not allowed.");
    const reference = helpers.cleanText(input.reference, 160);
    const comment = helpers.cleanText(input.comment, 2000);
    const receivedDate = normalizeDate(input.received_date);
    const actor = helpers.actor(env);
    const receiptId = `pay_${crypto.randomUUID().replace(/-/g, "")}`;
    const now = new Date().toISOString();

    const retrieveResponse = await stripeRequest(env, `/invoices/${encodeURIComponent(invoiceId)}`);
    const invoice = await retrieveResponse.json();
    if (!retrieveResponse.ok) return stripeFailure(invoice, retrieveResponse.status, origin, helpers);
    if (invoice.status === "paid") return helpers.json({ error: "This invoice is already paid in Stripe.", code: "already_paid" }, 409, origin);
    if (invoice.status !== "open") return helpers.json({ error: `Only open invoices can be marked paid. Stripe reports ${invoice.status}.`, code: "invoice_not_open" }, 409, origin);

    const body = new URLSearchParams({ paid_out_of_band: "true" });
    const payResponse = await stripeRequest(env, `/invoices/${encodeURIComponent(invoiceId)}/pay`, {
      method: "POST",
      body,
      idempotencyKey: `landerware-outside-${receiptId}`,
    });
    const paidInvoice = await payResponse.json();
    if (!payResponse.ok) return stripeFailure(paidInvoice, payResponse.status, origin, helpers);

    const amount = Number(invoice.amount_remaining || invoice.amount_due || 0);
    await env.HOT_SYNC_D1.batch([
      env.HOT_SYNC_D1.prepare(`INSERT INTO financial_payment_receipts
        (id,invoice_id,invoice_number,customer_name,amount,currency,payment_method,reference,received_date,comment,recorded_at,recorded_by,stripe_status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)`)
        .bind(receiptId, invoiceId, invoice.number || invoiceId, invoice.customer_name || "Customer", amount, invoice.currency || "usd", method, reference, receivedDate, comment, now, actor, paidInvoice.status || "paid"),
      env.HOT_SYNC_D1.prepare("INSERT INTO admin_audit_log (id,logged_at,actor,action,record_type,record_id,payload_json) VALUES (?,?,?,?,?,?,?)")
        .bind(crypto.randomUUID(), now, actor, "record_outside_payment", "stripe_invoice", invoiceId, JSON.stringify({ receipt_id: receiptId, invoice_number: invoice.number, amount, currency: invoice.currency, method, reference, received_date: receivedDate, comment, stripe_status: paidInvoice.status })),
    ]);

    return helpers.json({
      receipt: { id: receiptId, invoice_id: invoiceId, invoice_number: invoice.number || invoiceId, amount, currency: invoice.currency || "usd", method, reference, received_date: receivedDate, comment, recorded_at: now, recorded_by: actor },
      invoice: { id: paidInvoice.id, number: paidInvoice.number, status: paidInvoice.status, paid_out_of_band: true },
    }, 200, origin);
  } catch (error) {
    return helpers.safeError(error, origin);
  }
}

async function loadReceiptNotes(env) {
  const map = new Map();
  if (!env.HOT_SYNC_D1) return map;
  try {
    const result = await env.HOT_SYNC_D1.prepare(`SELECT invoice_id,payment_method,reference,received_date,comment,recorded_at,recorded_by
      FROM financial_payment_receipts ORDER BY recorded_at DESC LIMIT 500`).all();
    for (const row of result.results || []) if (!map.has(row.invoice_id)) map.set(row.invoice_id, row);
  } catch (_) {
    // Migration may not be deployed yet. Stripe reconciliation remains available.
  }
  return map;
}

function normalizeDate(value) {
  const text = String(value || "").trim();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(text)) throw new Error("Received date must be YYYY-MM-DD.");
  const parsed = new Date(`${text}T12:00:00Z`);
  if (Number.isNaN(parsed.getTime())) throw new Error("Received date is invalid.");
  return text;
}

function firstLineDescription(invoice) {
  const lines = invoice.lines?.data || [];
  return lines[0]?.description || "Stripe invoice";
}

async function stripeRequest(env, path, options = {}) {
  const headers = {
    Authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
    "Stripe-Version": env.STRIPE_API_VERSION || "2026-06-24.dahlia",
  };
  if (options.body) headers["Content-Type"] = "application/x-www-form-urlencoded";
  if (options.idempotencyKey) headers["Idempotency-Key"] = options.idempotencyKey;
  return fetch(`${STRIPE_API}${path}`, { method: options.method || "GET", headers, body: options.body });
}

function stripeFailure(payload, status, origin, helpers) {
  const message = payload?.error?.message || "Stripe rejected the request.";
  return helpers.json({ error: message, code: payload?.error?.code || "stripe_error" }, status >= 400 && status < 600 ? status : 502, origin);
}
