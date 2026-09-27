const TIMEZONE = "America/New_York";

export function localDate(now = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: TIMEZONE, year: "numeric", month: "2-digit", day: "2-digit" }).format(now);
}

export function localMidnight(day: string): string {
  const stamp = Date.parse(`${day}T00:00:00Z`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day) || !Number.isFinite(stamp) || new Date(stamp).toISOString().slice(0, 10) !== day) {
    throw new RangeError("Dates must be real calendar dates in YYYY-MM-DD format");
  }
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone: TIMEZONE, year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23",
  });
  let instant = stamp;
  // Resolve the zone at the boundary itself, including 23/25-hour DST days.
  for (let attempt = 0; attempt < 3; attempt++) {
    const parts = Object.fromEntries(formatter.formatToParts(new Date(instant)).map(part => [part.type, part.value]));
    const wall = Date.UTC(+parts.year, +parts.month - 1, +parts.day, +parts.hour, +parts.minute, +parts.second);
    const correction = stamp - wall;
    if (correction === 0) return new Date(instant).toISOString();
    instant += correction;
  }
  throw new RangeError("Could not resolve local midnight");
}

export function demandRange(query: URLSearchParams, now = new Date()) {
  const from = query.get("from") || localDate(now);
  const start = localMidnight(from);
  const end = new Date(`${from}T00:00:00Z`);
  end.setUTCDate(end.getUTCDate() + 366);
  const to = query.get("to") || end.toISOString().slice(0, 10);
  const stop = localMidnight(to);
  if (stop <= start || Date.parse(stop) - Date.parse(start) > 367 * 86400000) throw new RangeError("Invalid date range");
  return { from, to, start, stop };
}
