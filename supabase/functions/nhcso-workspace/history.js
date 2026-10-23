// Historical summaries belong to canonical sessions, never editable NHCSO rows.
export const HISTORY_PAGE_SIZE = 40;
export const NHCSO_HISTORY_ORGANIZATION_KEY = "hist_org_9c5e13364df2bf5e339e75f0";

/** @param {{from: (table: string) => any}} admin @param {number} offset */
export async function listHistoricalClasses(admin, offset = 0) {
  if (!Number.isSafeInteger(offset) || offset < 0 || offset > 100000) {
    throw new Error("Invalid history offset");
  }
  const { data, error, count } = await admin.from("class_sessions")
    .select("id,external_class_id,start_at,timezone,source_location_label,source_instructor_label,courses!class_sessions_course_id_fkey(name),organizations!inner(organization_key)", { count: "exact" })
    .eq("organizations.organization_key", NHCSO_HISTORY_ORGANIZATION_KEY)
    .eq("source", "enrollware_history").eq("record_scope", "historical")
    .order("start_at", { ascending: false }).order("id", { ascending: false })
    .range(offset, offset + HISTORY_PAGE_SIZE - 1);
  if (error) throw error;
  const history = (data || []).map(/** @param {{id: string, external_class_id?: string, start_at: string, timezone?: string, courses?: {name?: string}, source_location_label?: string, source_instructor_label?: string}} row */ row => {
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: row.timezone || "America/New_York", year: "numeric", month: "2-digit",
      day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23",
    }).formatToParts(new Date(row.start_at));
    const part = (/** @type {string} */ name) => parts.find(p => p.type === name)?.value || "";
    return [`${part("year")}-${part("month")}-${part("day")}`,
      `${part("hour")}:${part("minute")}`, row.external_class_id || row.id,
      row.courses?.name || "Unknown course", row.source_location_label || "Unknown location",
      row.source_instructor_label || ""];
  });
  return { history, total: count, next_offset: offset + history.length < (count || 0) ? offset + history.length : null };
}
