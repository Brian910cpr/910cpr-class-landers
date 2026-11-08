export const FAMILY = "nseaswim-pool-family-2027-02-15";
export const BLS = "nseaswim-pool-bls-2027-02-15";
export const EVENT_SLUGS = [FAMILY, BLS];
export const CAPACITY = 30;
// Stripe requires at least 30 minutes; reserve five additional minutes for setup/retries.
export const HOLD_MINUTES = 35;
export const COURSE_CENTS = 2500;
export const EBOOK_CENTS = 2000;
export const uuidOk = (v: unknown): v is string => typeof v === "string" && /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(v);
export class InputError extends Error {}
function field(value: unknown, label: string, max: number, required = true) {
  if (typeof value !== "string" || value.trim().length > max || /[\x00-\x1f\x7f]/.test(value)) throw new InputError(`Please enter a valid ${label}.`);
  const result = value.trim();
  if (required && !result) throw new InputError(`Please enter your ${label}.`);
  return result;
}
export function normalizeInput(body: any, event: string) {
  if (!uuidOk(body.requestId)) throw new InputError("Please reload the form before submitting.");
  const firstName = field(body.firstName, "first name", 80);
  const lastName = field(body.lastName, "last name", 80);
  const email = field(body.email, "email address", 160).toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw new InputError("Please enter a valid email address.");
  const phone = field(body.phone ?? "", "phone number", 40, false);
  const attendeeCount = body.attendeeCount ?? body.numberAttending ?? 1;
  if (typeof attendeeCount !== "number" || !Number.isInteger(attendeeCount) || attendeeCount < 1 || attendeeCount > CAPACITY) throw new InputError("Choose between 1 and 30 attendees.");
  const rawGuests = body.guestNames ?? body.additionalGuests ?? [];
  const names = typeof rawGuests === "string" ? rawGuests.split(/\n|,/).filter(x => x.trim()) : rawGuests;
  if (!Array.isArray(names) || names.length !== attendeeCount - 1) throw new InputError("Please provide a name for every additional attendee.");
  const guestNames = names.map(name => field(name, "guest name", 120));
  const rawEmails = body.guestEmails ?? [];
  if (!Array.isArray(rawEmails) || rawEmails.length !== guestNames.length) throw new InputError("Please provide an email address for every additional attendee.");
  const guestEmails = rawEmails.map(value => {
    const email = field(value, "guest email address", 160).toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw new InputError("Please enter a valid email address for every additional attendee.");
    return email;
  });
  const identities = new Set([`${firstName} ${lastName}`.toLowerCase().replace(/\s+/g," ")+"|"+email]);
  guestNames.forEach((name,index) => {
    const identity = name.toLowerCase().replace(/\s+/g," ")+"|"+guestEmails[index];
    if (identities.has(identity)) throw new InputError("Please list each attendee only once.");
    identities.add(identity);
  });
  const ebookQty = body.ebookQty ?? 0;
  if (typeof ebookQty !== "number" || !Number.isInteger(ebookQty) || ebookQty < 0 || ebookQty > attendeeCount || (event === FAMILY && ebookQty !== 0)) throw new InputError("Choose a valid optional eManual quantity.");
  // Never merge user JSON into payment, group, or recovery metadata.
  const survey: Record<string, string | boolean> = {};
  if (body.survey && typeof body.survey === "object" && !Array.isArray(body.survey)) {
    for (const [key, value] of Object.entries(body.survey).slice(0, 20)) {
      if (!/^[a-zA-Z][a-zA-Z0-9_]{0,49}$/.test(key)) continue;
      if (typeof value === "boolean") survey[key] = value;
      else if (typeof value === "string") survey[key] = value.trim().slice(0, 500);
    }
  }
  return { requestId: body.requestId.toLowerCase(), firstName, lastName, email, phone, attendeeCount, guestNames, guestEmails, ebookQty, survey };
}
export async function fingerprint(input: ReturnType<typeof normalizeInput>, event: string) {
  const { requestId: _requestId, ...data } = input;
  const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(JSON.stringify({event, ...data})));
  return Array.from(new Uint8Array(bytes), b => b.toString(16).padStart(2, "0")).join("");
}
export function checkoutMatches(checkout: any, order: any, registrationId: string) {
  return checkout.id === order.stripe_checkout_session_id && checkout.client_reference_id === registrationId &&
    checkout.currency === "usd" && checkout.amount_total === Math.round(Number(order.total_amount) * 100) &&
    checkout.mode === "payment" && checkout.metadata?.order_id === order.id;
}
