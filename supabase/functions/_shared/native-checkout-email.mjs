import { renderCheckoutEmail } from './checkout-email-template.mjs';

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const INSTANT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})$/i;
const bad = () => { throw Error('native_mail_invalid_confirmation'); };
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const text = (value, max, required = false) => {
  if (value === undefined || value === null) { if (required) bad(); return undefined; }
  if (typeof value !== 'string' || value.length > max || /[\x00-\x1f\x7f]/.test(value) || (required && !value.trim())) bad();
  return value;
};
const instant = value => {
  if (typeof value !== 'string' || !INSTANT.test(value) || !Number.isFinite(Date.parse(value))) bad();
  return value;
};

// Allow only the existing first-party recovery capability. Do not copy raw URL
// fields into email HTML, follow redirects, or accept arbitrary query state.
function recoveryUrl(value) {
  if (typeof value !== 'string' || value.length > 2048 || /[\s\\]/.test(value)) bad();
  let url;
  try { url = new URL(value); } catch { bad(); }
  const entries = [...url.searchParams];
  if (url.origin !== 'https://www.910cpr.com' || url.username || url.password || url.hash ||
      !['/register/', '/register/checkout/'].includes(url.pathname) ||
      entries.length !== 1 || entries[0][0] !== 'recover' || !UUID.test(entries[0][1])) bad();
  return url.href;
}

function canonicalData(input) {
  if (!object(input) || !['confirmation', 'recovery', 'reminder'].includes(input.kind)) bad();
  const data = {
    kind: input.kind,
    course: text(input.course, 500, true),
    courseId: text(typeof input.courseId === 'number' && Number.isSafeInteger(input.courseId) ? String(input.courseId) : input.courseId, 100, true),
    startsAt: instant(input.startsAt),
    firstName: text(input.firstName, 200),
    venue: text(input.venue, 500),
    address: text(input.address, 2000),
  };
  if (input.endsAt !== undefined && input.endsAt !== null) {
    data.endsAt = instant(input.endsAt);
    if (Date.parse(data.endsAt) <= Date.parse(data.startsAt)) bad();
  }
  if (input.selectedOptions !== undefined && input.selectedOptions !== null && !Array.isArray(input.selectedOptions)) bad();
  const options = input.selectedOptions || [];
  if (options.length > 100) bad();
  data.selectedOptions = options.map(option => {
    if (!object(option)) bad();
    return { key: text(option.key, 200, true), display_name: text(option.display_name, 1000), name: text(option.name, 1000) };
  });
  if (data.kind === 'recovery') {
    data.recoveryUrl = recoveryUrl(input.recoveryUrl);
    data.holdExpiresAt = instant(input.holdExpiresAt);
  }
  return data;
}

// Input is the service-only durable claim. Database authorization, paid evidence,
// recipient matching and lease settlement remain mandatory consumer duties.
export function renderNativeCheckoutClaim(claim) {
  if (!object(claim) || !UUID.test(claim.messageId || '') || !UUID.test(claim.lease || '') ||
      typeof claim.customerTemplate !== 'boolean') bad();
  if (claim.customerTemplate) {
    // No raw subject/body/HTML fallback. Only whitelisted canonical fields reach
    // the existing renderer, and this transport never promises automatic codes.
    return renderCheckoutEmail(canonicalData(claim.confirmation), { automaticCodeDelivery: false });
  }
  // The deployed claim has one non-customer lane: owner fulfillment. It remains
  // plain text and cannot turn a malformed customer claim into arbitrary mail.
  if (claim.recipient !== 'brian@910cpr.com' || claim.confirmation != null) bad();
  return { subject: claim.subject, text: claim.body };
}
