(() => {
  "use strict";
  const form = document.getElementById("registration");
  if (!form) return;
  const API = "https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/public-event-registration";
  const event = form.dataset.event, bls = form.dataset.course === "bls";
  const $ = id => document.getElementById(id);
  const count = $("count"), guests = $("guests"), submit = $("submit"), status = $("status"), resume = $("resume-checkout");
  const key = "pool-checkout:" + event, query = new URLSearchParams(location.search);
  const uuid = value => /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value || "");
  const money = cents => new Intl.NumberFormat("en-US", {style:"currency",currency:"USD"}).format(cents / 100);
  let busy = false, pending = false, confirmed = false, available = false, remaining = 0;
  let courseCents = bls ? 2500 : 0, ebookCents = 1851, saved = null, lastPayload = null;
  try { saved = JSON.parse(sessionStorage.getItem(key)); } catch (_) { /* Storage is optional. */ }
  let requestId = uuid(query.get("request_id")) ? query.get("request_id") : uuid(saved?.requestId) ? saved.requestId : null;
  let submitted = !!requestId;
  if (saved?.requestId === requestId && saved?.payload) lastPayload = saved.payload;
  const guestCache = [];
  function remember() {
    try {
      if (requestId) sessionStorage.setItem(key, JSON.stringify({requestId, payload:confirmed ? null : lastPayload}));
      else sessionStorage.removeItem(key);
    } catch (_) { /* A failed browser store never blocks checkout. */ }
  }
  function message(text, kind = "") { status.textContent = text; status.className = "msg" + (kind ? " " + kind : ""); }
  function bookSelected() { return bls && form.querySelector('[name="manual"]:checked')?.value === "ebook"; }
  function lockFields(locked) { $("registration-fields").querySelectorAll("input,select,button").forEach(el => el.disabled = locked); }
  function captureGuests() {
    guests.querySelectorAll(".checkout-guest").forEach((row, i) => {
      guestCache[i] = {first:row.querySelector("[data-first]").value,last:row.querySelector("[data-last]").value};
    });
  }
  function renderGuests() {
    captureGuests();
    const needed = Number(count.value) - 1;
    while (guests.children.length > needed) guests.lastElementChild.remove();
    for (let i = guests.children.length; i < needed; i++) {
      const row = document.createElement("div"); row.className = "checkout-guest";
      const title = document.createElement("h4"); title.textContent = "Attendee " + (i + 2); row.append(title);
      const fields = document.createElement("div"); fields.className = "fields";
      for (const part of ["first","last"]) {
        const field = document.createElement("div"); field.className = "field";
        const input = document.createElement("input"), label = document.createElement("label");
        input.id = "guest-" + i + "-" + part; input.dataset[part] = ""; input.required = true;
        input.maxLength = 60; input.autocomplete = "off"; input.value = guestCache[i]?.[part] || "";
        label.htmlFor = input.id; label.textContent = part === "first" ? "First name" : "Last name";
        field.append(label, input); fields.append(field);
      }
      row.append(fields); guests.append(row);
    }
  }
  function refresh() {
    const n = Number(count.value), total = n * (courseCents + (bookSelected() ? ebookCents : 0));
    $("attendee-total").textContent = n + (n === 1 ? " attendee" : " attendees");
    $("total").textContent = bls ? money(total) : "FREE";
    if (confirmed) { submit.hidden = true; return; }
    submit.disabled = busy || (!pending && (!available || n > remaining));
    submit.textContent = busy ? "Please wait…" : pending ? "Check registration status" : !available ? (remaining === 0 ? "Registration unavailable" : "Checking availability…") : bls ? "Continue to secure checkout · " + money(total) : "Reserve " + (n === 1 ? "my free spot" : n + " free spots");
  }
  function restore(payload) {
    if (!payload) return;
    count.value = String(payload.attendeeCount || 1);
    for (const [id, field] of [["first","firstName"],["last","lastName"],["email","email"],["phone","phone"]]) $(id).value = payload[field] || "";
    if (bls) form.querySelector('[name="manual"][value="' + (payload.ebookQty > 0 ? "ebook" : "none") + '"]').checked = true;
    (payload.guestNames || []).forEach((name, i) => {
      const parts = name.trim().split(/\s+/); guestCache[i] = {first:parts.shift() || "", last:parts.join(" ")};
    });
    renderGuests();
    form.querySelectorAll("[data-survey]").forEach(el => el.value = payload.survey?.[el.dataset.survey] || "");
  }
  async function api(body) {
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 20000);
    try {
      const response = await fetch(API + "?event=" + encodeURIComponent(event), {
        ...(body ? {method:"POST", headers:{"content-type":"application/json"},body:JSON.stringify({event,...body})} : {}),
        signal:controller.signal, cache:"no-store"
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok || !result.ok) {
        const error = new Error(result.error || "Registration could not be checked. Please try again.");
        error.status = response.status; error.result = result; throw error;
      }
      return result;
    } finally { clearTimeout(timer); }
  }
  async function load() {
    try {
      const result = await api(), e = result.event, pricing = result.pricing || e?.pricing;
      if (!e || !Number.isInteger(e.remaining)) throw Error("Availability unavailable");
      remaining = Math.max(0, e.remaining);
      available = e.registration_status === "open" && Date.parse(e.start_at) > Date.now() && remaining > 0;
      if (pricing) {
        if (Number.isInteger(pricing.courseUnitCents)) courseCents = pricing.courseUnitCents;
        if (Number.isInteger(pricing.ebookUnitCents)) ebookCents = pricing.ebookUnitCents;
      }
      $("seatLabel").textContent = e.registration_status !== "open" || Date.parse(e.start_at) <= Date.now() ? "Registration for this event is closed." : remaining > 0 ? remaining + " of " + e.handsOnCapacity + " shared hands-on spots remain." : "Hands-on spots are full.";
      Array.from(count.options).forEach(option => option.disabled = Number(option.value) > remaining);
      // Never erase attendee details or silently shrink a group after a capacity update.
      if (!pending && Number(count.value) > remaining && remaining > 0) message("There are only " + remaining + " spots left. Please adjust the number attending.", "error");
    } catch (_) {
      available = false;
      $("seatLabel").textContent = "We could not check availability. Refresh to try again or call 910-395-5193.";
    }
    refresh();
  }
  function confirm(result) {
    confirmed = true; pending = false; lockFields(true); resume.hidden = true;
    $("registration-fields").hidden = true;
    const box = $("confirmation"); box.replaceChildren(); box.hidden = false;
    const title = document.createElement("h3"); title.textContent = "You're registered.";
    const info = document.createElement("p"), n = result.attendeeCount || lastPayload?.attendeeCount;
    info.textContent = (n ? "We saved " + n + " hands-on spot" + (n === 1 ? "" : "s") : "Your place is confirmed") + " for " + (bls ? "AHA BLS Provider" : "Family & Friends CPR") + ".";
    const when = document.createElement("p"); when.textContent = "Monday, February 15, 2027 · 11:00 AM–2:00 PM. Earl Jackson Pool, 750 Bess Street, Wilmington, NC 28401.";
    const layers = document.createElement("p"); layers.textContent = "Wear comfortable lighter layers for the heated indoor pool area. No swimsuit needed.";
    box.append(title, info, when, layers); message(bls ? "Payment confirmed." : "Free registration confirmed.", "ok");
    lastPayload = null; remember(); refresh(); box.focus();
  }
  function checkoutLink(value) {
    try { const url = new URL(value); return url.protocol === "https:" && url.hostname === "checkout.stripe.com" ? url.href : null; } catch (_) { return null; }
  }
  async function handle(result, redirect = false) {
    if (result.confirmed) { confirm(result); return; }
    if (result.expired || result.status === "expired") {
      pending = false; submitted = false; requestId = null; lastPayload = null; remember();
      resume.hidden = true; lockFields(false);
      message("The checkout hold expired. Your details are still here. Review them and start a new checkout.", "error");
      await load(); return;
    }
    pending = true; lockFields(true);
    const url = checkoutLink(result.checkoutUrl);
    resume.hidden = !url;
    if (url) resume.href = url;
    message(result.processing ? "Your payment is processing. Please check status again without paying again." : result.checkoutUnavailable ? "Your registration is saved, but checkout could not open. Please check status again after " + new Date(result.holdExpiresAt).toLocaleTimeString([], {hour:"numeric",minute:"2-digit"}) + ". Do not start another registration before then." : url ? "Your registration is saved but not yet paid. Return to secure checkout to finish." : "Your registration is being checked. It is not confirmed yet. Check the status again before starting another registration.");
    refresh();
    if (redirect && url) location.assign(url);
  }
  async function checkStatus() {
    if (busy || !requestId) return;
    busy = true; pending = true; lockFields(true); refresh(); message("Checking your registration…");
    try {
      const result = await api({action:"status",requestId, ...(query.get("session_id") ? {checkoutSessionId:query.get("session_id")} : {})});
      await handle(result);
    } catch (error) {
      if (error.result?.expired || error.result?.status === "expired") await handle({expired:true});
      else if ((error.status === 404 || /not.found|unknown.request/i.test(error.message)) && lastPayload) {
        // A lost first response is retried with the same key and exact original data.
        try { await handle(await api({...lastPayload,requestId})); }
        catch (_) { message("We could not confirm the previous attempt. Check status again or call 910-395-5193. Please do not submit a second registration.", "error"); }
      } else message("We could not confirm this registration yet. Check status again or call 910-395-5193. Payment is not confirmed.", "error");
    } finally { busy = false; refresh(); }
  }
  count.addEventListener("change", () => { renderGuests(); refresh(); });
  form.querySelectorAll('[name="manual"]').forEach(el => el.addEventListener("change", refresh));
  form.addEventListener("submit", async e => {
    e.preventDefault();
    if (busy || confirmed) return;
    if (pending || submitted) { await checkStatus(); return; }
    if (!available || !form.reportValidity()) return;
    captureGuests();
    const n = Number(count.value);
    if (n > remaining) { message("There are not enough hands-on spots for this group.", "error"); return; }
    requestId = crypto.randomUUID(); submitted = true;
    lastPayload = {firstName:$("first").value.trim(),lastName:$("last").value.trim(),email:$("email").value.trim(),phone:$("phone").value.trim(),company:$("company").value.trim(),attendeeCount:n,guestNames:guestCache.slice(0,n-1).map(x => (x.first.trim() + " " + x.last.trim()).trim()),ebookQty:bookSelected() ? n : 0,survey:Object.fromEntries(Array.from(form.querySelectorAll("[data-survey]")).map(el => [el.dataset.survey,el.value]))};
    remember(); busy = true; lockFields(true); refresh(); message(bls ? "Saving your registration and opening secure checkout…" : "Reserving your free spots…");
    try { await handle(await api({...lastPayload,requestId}), bls); }
    catch (error) {
      if (["invalid_input","registration_closed","capacity","duplicate_registration"].includes(error.result?.code) && !error.result?.paymentPending) {
        submitted = false; pending = false; requestId = null; remember(); lockFields(false); await load();
        message(error.message, "error");
      } else {
        pending = true; message("The result of this attempt is not confirmed. Use Check registration status to safely retry without creating a second registration.", "error");
      }
    } finally { busy = false; refresh(); }
  });
  $("copy-page-details")?.addEventListener("click", async () => {
    const lines = ["URL: " + location.origin + location.pathname];
    for (const name of ["page-id","build-id","release-built-at","asset-version"]) {
      lines.push(name + ": " + (document.querySelector('meta[name="' + name + '"]')?.content || ""));
    }
    try { await navigator.clipboard.writeText(lines.join("\n")); $("page-details-status").textContent = "Copied"; }
    catch (_) { $("page-details-status").textContent = "Copy unavailable"; }
  });
  restore(lastPayload); renderGuests(); refresh();
  if (requestId) { pending = true; checkStatus(); }
  else if (query.has("paid") || query.has("session_id")) message("Payment cannot be confirmed from this link alone. Please call 910-395-5193 if you already paid.", "error");
  else if (query.has("checkout_cancelled")) message("Checkout was canceled. No payment has been confirmed.");
  load();
  window.addEventListener("pageshow", e => { if (e.persisted && requestId && !confirmed) checkStatus(); });
})();
