(function (root) {
  "use strict";

  const ACTIVE_REGISTRATION_STATUSES = new Set(["registered", "confirmed", "completed"]);

  function participantRows(session) {
    return Array.isArray(session?.participants) ? session.participants : [];
  }

  function participantCount(session) {
    if (session?.count_available !== true) return null;
    return Number.isInteger(session.participant_count) ? session.participant_count : null;
  }

  function countLabel(session) {
    const count = participantCount(session);
    return count === null ? "—" : String(count);
  }

  function asUnknownExternal(session) {
    return {
      ...session,
      participants: [],
      participant_count: null,
      registered_count: null,
      count_available: false,
      roster_available: false,
      count_source: "external_projection_only",
    };
  }

  function canonicalKey(session) {
    return String(session?.session_id || session?.id || "");
  }

  function externalKey(session) {
    return String(session?.external_class_id || session?.class_id || "");
  }

  function courseKey(session) {
    return String(session?.course_name || session?._name || session?.course?.display_name || "")
      .toLowerCase().replace(/\baha\b|\bprovider\b/g, "").replace(/[^a-z0-9]+/g, "").trim();
  }

  function mergeCanonical(externalRows, canonicalRows) {
    const remaining = [...canonicalRows];
    const result = externalRows.map((external) => {
      const id = canonicalKey(external);
      const externalId = externalKey(external);
      const start = new Date(external.start_at || external.start || external._start || "").getTime();
      const course = courseKey(external);
      const index = remaining.findIndex((canonical) =>
        (id && canonicalKey(canonical) === id) ||
        (externalId && externalKey(canonical) === externalId) ||
        (Number.isFinite(start) && new Date(canonical.start_at || canonical._start || "").getTime() === start && course && courseKey(canonical) === course)
      );
      if (index < 0) return asUnknownExternal(external);
      const canonical = remaining.splice(index, 1)[0];
      return { ...external, ...canonical };
    });
    return result.concat(remaining);
  }

  const api = { ACTIVE_REGISTRATION_STATUSES, participantRows, participantCount, countLabel, asUnknownExternal, mergeCanonical };
  root.CanonicalSessionModel = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
