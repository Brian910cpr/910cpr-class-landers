(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.ResolvedSelectorAvailability = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

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
      minutes: (hour * 60) + Number(parts.minute),
    };
  }

  function startMinutes(startTime) {
    const [hour, minute] = String(startTime || "").split(":").map(Number);
    return (hour * 60) + minute;
  }

  function isPastStart(day, slot, now) {
    if (!day || !slot) return true;
    if (day.date < now.dateKey) return true;
    if (day.date > now.dateKey) return false;
    return startMinutes(slot.startTime) <= now.minutes;
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

  return {
    schemaVersion: "selector-resolved-availability.v1",
    businessNow,
    startMinutes,
    isPastStart,
    selectableStartTimes,
    isSelectableDate,
    filterDatesByCourse,
    slotKey,
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