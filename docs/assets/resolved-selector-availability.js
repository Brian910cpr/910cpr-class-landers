(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.ResolvedSelectorAvailability = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  // Preserve native destinations through every selector rebuild. The original
  // BLS Initial seated-class route is supported by the existing retail checkout;
  // other unconverted offers retain their current backend until explicitly ready.
  function registrationDestination(course) {
    const owned = value => {
      if (typeof value !== 'string' || !value) return null;
      try {
        const url = new URL(value, 'https://www.910cpr.com');
        if (url.protocol !== 'https:' || !['www.910cpr.com', '910cpr.com'].includes(url.host) ||
            url.username || url.password || url.hash ||
            !['/register/', '/register/checkout/', '/register/skills-session/'].includes(url.pathname)) return null;
        const session = url.searchParams.getAll('session');
        if (session.length > 1 || (session.length && !/^(?:\d+|lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})$/i.test(session[0]))) return null;
        if (!session.length && !/^\d+$/.test(url.searchParams.get('course') || '')) return null;
        return url.pathname + url.search;
      } catch { return null; }
    };
    const native = owned(course.registrationUrl) || owned(course.appointmentUrl);
    if (native) return native;
    if (String(course.courseId) === '209806' && course.offerType === 'seated_class') {
      try {
        const url = new URL(course.appointmentUrl);
        const ids = url.searchParams.getAll('id');
        if (url.protocol === 'https:' && url.host === 'coastalcprtraining.enrollware.com' &&
            !url.username && !url.password && !url.hash && url.pathname === '/enroll' &&
            ids.length === 1 && /^\d+$/.test(ids[0])) return '/register/?session=' + encodeURIComponent(ids[0]);
      } catch { /* Incomplete legacy identity cannot invent a native session. */ }
    }
    return course.appointmentUrl || course.registrationUrl || '';
  }

  function businessNow(timeZone = "America/New_York", now = new Date()) {
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).formatToParts(now).reduce((values, part) => {
      values[part.type] = part.value;
      return values;
    }, {});
    const hour = Number(parts.hour === "24" ? "0" : parts.hour);
    return {
      dateKey: `${parts.year}-${parts.month}-${parts.day}`,
      instant: now.getTime(),
      minutes: (hour * 60) + Number(parts.minute),
    };
  }

  function startMinutes(startTime) {
    const match = String(startTime || "").trim().match(/^(\d{1,2}):(\d{2})(?:\s*([AP]M))?$/i);
    if (!match) return Number.NaN;
    let hour = Number(match[1]);
    const minute = Number(match[2]);
    const meridiem = (match[3] || "").toUpperCase();
    if (meridiem) {
      hour %= 12;
      if (meridiem === "PM") hour += 12;
    }
    if (hour > 23 || minute > 59) return Number.NaN;
    return (hour * 60) + minute;
  }

  function isPastStart(day, slot, now) {
    if (!day || !slot) return true;
    if (Number.isFinite(now.instant) && slot.courses?.length &&
        slot.courses.every(course => course.offerType !== 'seated_class' &&
          course.validUntil && Date.parse(course.validUntil) <= now.instant)) return true;
    if (day.date < now.dateKey) return true;
    if (day.date > now.dateKey) return false;
    const minutes = startMinutes(slot.startTime);
    return !Number.isFinite(minutes) || minutes <= now.minutes;
  }

  function selectableStartTimes(day, now) {
    return (day?.startTimes || []).filter((slot) => !isPastStart(day, slot, now));
  }

  function isSelectableDate(day, now) {
    return Boolean(day && day.date >= now.dateKey && selectableStartTimes(day, now).length);
  }

  function filterDatesByCourse(dates, courseIds) {
    const ids = courseIds instanceof Set
      ? courseIds
      : new Set(Array.isArray(courseIds) ? courseIds.map(String) : [String(courseIds)]);
    return (Array.isArray(dates) ? dates : []).map((day) => {
      const startTimes = (day.startTimes || []).map((slot) => ({
        ...slot,
        courses: (slot.courses || []).filter((course) => ids.has(String(course.courseId))),
      })).filter((slot) => slot.courses.length);
      return { ...day, startTimes };
    }).filter((day) => day.startTimes.length);
  }

  function slotKey(course) {
    return [
      course.courseId,
      course.date,
      course.startTime,
      course.appointmentDayId || "",
      course.availabilityBlockId || "",
    ].join("|");
  }

  // Compatibility helpers for consumers that opt in to bounded fetching and
  // publication leases. Existing business-clock-only callers retain their API.
  async function fetchPublication(url, {request = fetch, timeoutMs = 10000} = {}) {
    let lastError;
    for (let attempt = 0; attempt < 2; attempt++) {
      const controller = new AbortController();
      let timer;
      try {
        return await Promise.race([
          (async () => {
            const response = await request(url, {cache: 'no-store', signal: controller.signal});
            if (!response.ok) throw Error('Publication request failed');
            const data = await response.json();
            if (data?.schemaVersion !== 'selector-resolved-availability.v1' || !Array.isArray(data.dates))
              throw Error('Publication has unexpected shape');
            return data;
          })(),
          new Promise((_, reject) => {
            timer = setTimeout(() => { controller.abort(); reject(Error('Publication request timed out')); }, timeoutMs);
          }),
        ]);
      } catch (error) { lastError = error; }
      finally { clearTimeout(timer); }
    }
    throw lastError;
  }

  function datesForPublication(dates, validUntil, instant = Date.now()) {
    const live = value => Number.isFinite(Date.parse(value)) && Date.parse(value) > instant;
    return (Array.isArray(dates) ? dates : []).map(day => ({...day,
      startTimes: (day.startTimes || []).map(slot => ({...slot,
        courses: (slot.courses || []).filter(course => course.offerType === 'seated_class' ||
          (live(validUntil) && (!course.validUntil || live(course.validUntil)))),
      })).filter(slot => slot.courses.length),
    })).filter(day => day.startTimes.length);
  }

  return {
    schemaVersion: "selector-resolved-availability.v1",
    businessNow,
    registrationDestination,
    startMinutes,
    isPastStart,
    selectableStartTimes,
    isSelectableDate,
    filterDatesByCourse,
    slotKey,
    fetchPublication,
    datesForPublication,
  };
});

(function installMaximSupportChat() {
  if (typeof window === "undefined" || typeof document === "undefined") return;
  if (!/^\/corp\/maxim(?:\.html)?\/?$/.test(window.location.pathname)) return;

  function install() {
    document.querySelector(".chat-shell")?.remove();

    window._support = window._support || { ui: {}, user: {} };
    const support = window._support;
    support.account = "168a2136-bb03-4c4d-a39a-764bd189f30d";
    support.ui.contactMode = "default";
    support.ui.enableKb = "false";
    support.ui.mailbox = "87557538";
    support.ui.styles = { widgetColor: "#258544" };
    support.ui.shoutboxFacesMode = "brand-avatar";
    support.ui.widget = {
      icon: "webChat",
      allowBotProcessing: "true",
      slug: "coastal-cpr-training-slash-910cpr-com",
      label: {
        text: "Let me know if you have any questions!",
        mode: "notification",
        delay: 10,
        primary: "",
        secondary: "",
      },
      position: "bottom-left",
    };
    support.ui.overrides = support.ui.overrides || {};
    support.ui.overrides.confirmationMessage = "Thanks! Your message has been submitted. We'll get back to you here or via email.";
    support.ui.user = { authpath: "/m/api/reamaze/v2/customers/auth?brand=4875169" };

    if (!document.querySelector('script[src="https://cdn.reamaze.com/assets/reamaze-godaddy-loader.js"]')) {
      const loader = document.createElement("script");
      loader.async = true;
      loader.src = "https://cdn.reamaze.com/assets/reamaze-godaddy-loader.js";
      document.head.appendChild(loader);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", install, { once: true });
  } else {
    install();
  }
})();
