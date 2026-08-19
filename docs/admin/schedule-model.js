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

  const api = { scheduleRows, normalizeSessions, monthSummary, reconcileSchedule };
  root.ScheduleModel = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
