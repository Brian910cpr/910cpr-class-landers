(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.ResolvedSelectorAvailability = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  // Customer sales never fall back to an external checkout or an unverified owned route.
  // Native capabilities are a server-maintained allow-list projected by the page generator.
  function registrationAction(course, context = {}, capabilities = {}) {
    course = course || {};
    const clean = value => String(value || '').replace(/[\r\n]+/g, ' ').slice(0, 400);
    const requestOnly = course.dynamicBookingMode === 'request';
    const date = context.date || course.date || '';
    const time = context.startTime || course.startTime || '';
    // Preserve only the explicitly selected Heartsaver Skills variants. This is
    // a reservation path; choices/reserve still revalidate on the server.
    const skillsVariants = ['cpr-aed', 'first-aid-cpr-aed'];
    const venue = value => ['Wilmington; Shipyard Blvd', ':: Wilmington; Shipyard Blvd'].includes(value)
      ? 'Wilmington; Shipyard Blvd' : '';
    if (!requestOnly && String(course.courseId) === '509474' && context.familyContext === 'heartsaver' &&
        skillsVariants.includes(context.skillsContext) && context.skillsContextVerified === true &&
        /^\d{4}-\d{2}-\d{2}$/.test(date) && /^\d{2}:\d{2}$/.test(time) && Number.isFinite(startMinutes(time)) &&
        String(context.pagePath || '').toLowerCase() === '/heartsaver.html' && course.publicSelectable === true &&
        ['seated_class', 'dynamic_appointment'].includes(course.offerType) && course.durationMinutes === 45 &&
        course.schedulerConsumptionMinutes === 60 && course.cleanupBufferMinutes === 15 &&
        venue(course.location) && course.instructor && course.availabilityBlockId && !course.isFull &&
        !['closed','full','cancelled','canceled','completed'].includes(String(course.registrationStatus || course.registration_status || course.status || '').toLowerCase())) {
      const sources = [course.registrationUrl, course.appointmentUrl].filter(Boolean);
      const valid = sources.length > 0 && sources.every(value => {
        try {
          const u = new URL(value, 'https://www.910cpr.com');
          const q = u.searchParams;
          if (u.protocol !== 'https:' || !['www.910cpr.com','910cpr.com'].includes(u.host) ||
              u.pathname !== '/register/skills-session/' || u.username || u.password || u.hash) return false;
          for (const key of q.keys()) if (!['course','date','startTime','location','instructor','skillsContext','context'].includes(key) || q.getAll(key).length !== 1) return false;
          return q.get('course') === '509474' && q.get('date') === date && q.get('startTime') === time &&
            venue(q.get('location')) === venue(course.location) && q.get('instructor') === course.instructor &&
            (!q.has('skillsContext') || q.get('skillsContext') === context.skillsContext) &&
            (!q.has('context') || q.get('context') === context.familyContext) &&
            q.has('skillsContext') === q.has('context');
        } catch { return false; }
      });
      if (valid) {
        const q = new URLSearchParams({course:'509474',date,startTime:time,location:venue(course.location),
          instructor:course.instructor,skillsContext:context.skillsContext,context:'heartsaver'});
        return {mode:'skills-reservation',href:'https://www.910cpr.com/register/skills-session/?'+q,
          label:'Schedule skills session',notice:'Skills reservation only. This form does not collect payment.'};
      }
    }
    const ids = [];
    let badIdentity = false;
    for (const value of requestOnly ? [] : [course.registrationUrl, course.appointmentUrl]) {
      if (!value) continue;
      try {
        const url = new URL(value, 'https://www.910cpr.com');
        if (url.protocol !== 'https:' || url.username || url.password || url.hash) { badIdentity = true;continue; }
        let values;
        if (['www.910cpr.com','910cpr.com'].includes(url.host) && url.pathname === '/register/') {
          values = url.searchParams.getAll('session');
          const codes = url.searchParams.getAll('course');
          if (codes.length > 1 || (codes.length && codes[0] !== String(course.courseId))) badIdentity = true;
        } else if (url.host === 'coastalcprtraining.enrollware.com' && url.pathname === '/enroll') {
          values = url.searchParams.getAll('id');
        } else { badIdentity = true;continue; }
        if (values.length !== 1 || !/^\d+$/.test(values[0])) { badIdentity = true;continue; }
        ids.push(values[0]);
      } catch { badIdentity = true; }
    }
    const sid = ids[0] || '';
    const cap = capabilities.sessions?.[sid];
    const closed = ['closed','full','cancelled','canceled','completed'].includes(String(course.registrationStatus || course.registration_status || course.status || '').toLowerCase()) || course.isFull === true;
    const advanced = ['241108','209818','209811','209805','251496','209812'].includes(String(course.courseId)) ||
      ['ACLS','PALS'].includes(String(course.courseFamily || course.family || '').trim().toUpperCase());
    if (course.seatedBookingMode !== 'request' && (!advanced || course.seatedBookingMode === 'native') &&
        !badIdentity && ids.length && ids.every(id => id === sid) && cap && !closed &&
        course.offerType === 'seated_class' && String(course.courseId) === String(cap.courseId) &&
        date === cap.date && Number.isFinite(startMinutes(time)) && startMinutes(time) === startMinutes(cap.startTime) &&
        course.location === cap.location) {
      return {mode:'native',href:'https://www.910cpr.com/register/?session='+encodeURIComponent(sid),label:'Register',notice:''};
    }
    const body = ['I would like to ask about this class. This is a request, not a confirmed reservation.',
      '', 'Course: '+clean(course.courseName || 'Class option'), 'Course ID: '+clean(course.courseId),
      'Date: '+clean(date || 'Not selected'), 'Start: '+clean(time || course.displayStartTime || 'Not selected'),
      'Duration: '+clean(course.durationMinutes || 'Not supplied')+' minutes', 'Location: '+clean(course.location || 'Not supplied')];
    if (sid) body.push('Class reference: '+sid);
    const path = String(context.pagePath || '');
    if (/^\/(?:courses\/)?[a-z0-9_-]+[.]html$/.test(path)) body.push('Page: https://www.910cpr.com'+path);
    const query = new URLSearchParams({subject:'Class request'+(sid?' '+sid:''),body:body.join('\n')});
    return {mode:'request',href:'mailto:brian@910cpr.com?'+query,label:'Request this class',notice:'Request only. No seat is reserved until 910CPR confirms registration.'};
  }

  function registrationDestination(course, context, capabilities) {
    return registrationAction(course, context, capabilities).href;
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
    registrationAction,
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
