(function (root) {
  "use strict";

  function scheduleRows(data) {
    return Array.isArray(data) ? data : (data && Array.isArray(data.sessions) ? data.sessions : []);
  }

  function normalizeSessions(data, parseDate, courseName) {
    return scheduleRows(data).map((record) => {
      const start = parseDate(record.start_at || record.start || record.startTime || record.start_time || record.timing?.start_at);
      const end = parseDate(record.end_at || record.end || record.endTime || record.end_time || record.timing?.end_at);
      return { ...record, _start: start, _end: end, _name: courseName(record) };
    }).filter((record) => record._start);
  }

  function monthSummary(sessions, year, month, keyOf) {
    const rows = sessions.filter((record) => record._start.getFullYear() === year && record._start.getMonth() === month);
    return { sessionCount: rows.length, dateCount: new Set(rows.map((record) => keyOf(record._start))).size };
  }

  function reconcileSchedule({ loadedCount, normalizedCount, monthSessionCount, monthDateCount, renderedSessionCount, renderedDateCount, loadError = "" }) {
    const errors = [];
    if (loadError) errors.push(`Schedule feed failed to load: ${loadError}`);
    if (loadedCount !== normalizedCount) errors.push(`${loadedCount} sessions loaded but only ${normalizedCount} normalized successfully.`);
    if (monthSessionCount !== renderedSessionCount) errors.push(`${monthSessionCount} sessions belong to this month but only ${renderedSessionCount} are represented on calendar dates.`);
    if (monthDateCount !== renderedDateCount) errors.push(`${monthDateCount} dates should contain classes but only ${renderedDateCount} rendered.`);
    return { ok: errors.length === 0, errors };
  }

  function instructorName(record) {
    return String(record.lead_instructor_name || record.instructor || record.instructor_name || "Unassigned").trim() || "Unassigned";
  }

  function instructorNames(sessions) {
    return [...new Set(sessions.map(instructorName))].sort((a, b) => a === "Unassigned" ? 1 : b === "Unassigned" ? -1 : a.localeCompare(b));
  }

  function overlaps(left, right) {
    const leftEnd = left._end || left._start;
    const rightEnd = right._end || right._start;
    return left._start < rightEnd && right._start < leftEnd;
  }

  function annotateConflicts(sessions, locationName) {
    return sessions.map((record) => ({
      ...record,
      _overlapCount: sessions.filter((other) => other !== record && overlaps(record, other)).length,
      _locationConflict: sessions.some((other) => other !== record && overlaps(record, other) && locationName(record) && locationName(other).toLowerCase() === locationName(record).toLowerCase()),
    }));
  }

  function brianExceptionRows(events, visible = true) {
    if (!visible) return [];
    return events.filter((event) => event.source_type === "inverse_google_calendar");
  }

  const api = { scheduleRows, normalizeSessions, monthSummary, reconcileSchedule, instructorName, instructorNames, overlaps, annotateConflicts, brianExceptionRows };
  root.ScheduleModel = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
