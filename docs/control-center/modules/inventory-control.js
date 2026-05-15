const PROFILE_URL = "../../data/instructor_profiles.json";
const AVAILABILITY_URL = "../../data/instructor_availability.json";
const RANGE_URL = "../../data/appointment_range_registry.json";
const RECOMMENDATION_URL = "../../data/inventory_recommendations.json";
const AVAILABILITY_PATH = "docs/data/instructor_availability.json";
const RECOMMENDATION_PATH = "docs/data/inventory_recommendations.json";
const FLEXIBILITY_MODES = [
  "strict_preferred_only",
  "use_unused_time_if_useful",
  "fully_flexible_within_qualifications"
];
const COURSE_FAMILIES = ["ACLS", "PALS", "BLS", "Heartsaver", "HeartCode", "HSI", "ARC"];
const WEEKDAYS = [
  ["0", "Sun"],
  ["1", "Mon"],
  ["2", "Tue"],
  ["3", "Wed"],
  ["4", "Thu"],
  ["5", "Fri"],
  ["6", "Sat"]
];

const state = {
  profiles: { instructors: [] },
  availability: { schema_version: "0.1", updated_at: "", availability_blocks: [], source_notes: [] },
  ranges: { ranges: [] },
  recommendations: { recommendations: [] },
  oneOffRows: [],
  generatedBlocks: [],
  exclusions: [],
  directoryHandle: null
};

function $(id) {
  return document.getElementById(id);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function readJson(url, fallback) {
  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) return fallback;
    return await response.json();
  } catch {
    return fallback;
  }
}

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function dateFromIso(value) {
  const [year, month, day] = String(value).split("-").map(Number);
  if (!year || !month || !day) return null;
  return new Date(year, month - 1, day);
}

function toIsoDate(date) {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0")
  ].join("-");
}

function dateRange(startIso, endIso) {
  const start = dateFromIso(startIso);
  const end = dateFromIso(endIso);
  if (!start || !end || end < start) return [];
  const days = [];
  for (const cursor = new Date(start); cursor <= end; cursor.setDate(cursor.getDate() + 1)) {
    days.push(new Date(cursor));
  }
  return days;
}

function timeMinutes(value) {
  if (!value) return null;
  const [hour, minute] = String(value).split(":").map(Number);
  if (!Number.isFinite(hour) || !Number.isFinite(minute)) return null;
  return hour * 60 + minute;
}

function displayTime(value) {
  if (!value) return "";
  const [hourText, minuteText] = String(value).split(":");
  let hour = Number(hourText);
  const suffix = hour >= 12 ? "PM" : "AM";
  hour = hour % 12 || 12;
  return `${hour}:${minuteText} ${suffix}`;
}

function slug(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "") || "block";
}

function instructorByName(name) {
  return (state.profiles.instructors || []).find(instructor => instructor.display_name === name || instructor.short_name === name);
}

function instructorOptions(selected = "") {
  return (state.profiles.instructors || [])
    .map(instructor => `<option value="${escapeHtml(instructor.display_name)}" ${instructor.display_name === selected ? "selected" : ""}>${escapeHtml(instructor.display_name)}</option>`)
    .join("");
}

function flexibilityOptions(selected = "use_unused_time_if_useful") {
  return FLEXIBILITY_MODES
    .map(mode => `<option value="${mode}" ${mode === selected ? "selected" : ""}>${mode}</option>`)
    .join("");
}

function familyCheckboxes(name, selected = []) {
  const selectedSet = new Set(selected);
  return `<div class="checkbox-grid">${COURSE_FAMILIES.map(family => `
    <label><input type="checkbox" name="${name}" value="${family}" ${selectedSet.has(family) ? "checked" : ""}> ${family}</label>
  `).join("")}</div>`;
}

function weekdayCheckboxes(name, selected = ["1", "2", "3", "4", "5"]) {
  const selectedSet = new Set(selected.map(String));
  return `<div class="checkbox-grid">${WEEKDAYS.map(([value, label]) => `
    <label><input type="checkbox" name="${name}" value="${value}" ${selectedSet.has(value) ? "checked" : ""}> ${label}</label>
  `).join("")}</div>`;
}

function getChecked(form, name) {
  return Array.from(form.querySelectorAll(`input[name="${name}"]:checked`)).map(input => input.value);
}

function baseFields(prefix, profile) {
  return `
    <label>Instructor<select name="instructor" data-instructor-select data-prefix="${prefix}">${instructorOptions(profile?.display_name || "")}</select></label>
    <label>Location<input name="location" value="${escapeHtml(profile?.default_location || "Wilmington Shipyard")}" required></label>
    <label>Available start time<input name="available_start" type="time" value="${prefix === "range" ? "08:30" : "13:00"}" required></label>
    <label>Available end time<input name="available_end" type="time" value="${prefix === "range" ? "20:00" : "18:00"}" required></label>
    <label>Preferred anchor/start time<input name="preferred_anchor_start" type="time" value="${profile?.short_name === "Amy" ? "14:00" : ""}"></label>
    <label>Flexibility mode<select name="flexibility">${flexibilityOptions(profile?.default_flexibility)}</select></label>
    <div class="field span-field">Preferred course families${familyCheckboxes("preferred_course_families", profile?.preferred_families || [])}</div>
    <div class="field span-field">Allowed course families${familyCheckboxes("allowed_course_families", profile?.allowed_families || [])}</div>
    <label class="span-field">Notes<textarea name="notes" rows="3">${escapeHtml(profile?.default_availability_pattern_note || "")}</textarea></label>
  `;
}

function populateForms() {
  const amy = instructorByName("Amy Arnold") || state.profiles.instructors?.[0] || {};
  const nick = instructorByName("Nick") || state.profiles.instructors?.[0] || {};
  const brian = instructorByName("Brian") || state.profiles.instructors?.[0] || {};
  $("block-form").innerHTML = `
    <label>Start date<input name="start_date" type="date" required></label>
    <label>End date<input name="end_date" type="date" required></label>
    ${baseFields("block", nick)}
    <div class="field span-field">Days of week included${weekdayCheckboxes("days_of_week", ["1", "2", "3", "4", "5"])}</div>
  `;
  $("range-form").innerHTML = `
    <label>Start date<input name="start_date" type="date" required></label>
    <label>End date<input name="end_date" type="date" required></label>
    ${baseFields("range", brian)}
    <div class="field span-field">Days of week included${weekdayCheckboxes("days_of_week", ["1", "2", "3", "4", "5", "6"])}</div>
  `;
  if (!state.oneOffRows.length) {
    state.oneOffRows.push(defaultOneOffRow(amy));
  }
}

function defaultOneOffRow(profile = {}) {
  return {
    instructor: profile.display_name || "Amy Arnold",
    location: profile.default_location || "Wilmington Shipyard",
    date: "",
    available_start: "13:00",
    available_end: "18:00",
    preferred_anchor_start: profile.short_name === "Amy" ? "14:00" : "",
    preferred_course_families: profile.preferred_families || ["ACLS", "PALS"],
    allowed_course_families: profile.allowed_families || ["ACLS", "PALS", "BLS", "Heartsaver", "HeartCode"],
    flexibility: profile.default_flexibility || "use_unused_time_if_useful",
    notes: profile.default_availability_pattern_note || ""
  };
}

function buildBlockId(row) {
  const profile = instructorByName(row.instructor);
  const instructorSlug = slug(profile?.short_name || row.instructor);
  return `${instructorSlug}_${row.date}_${String(row.available_start).replace(":", "")}_${String(row.available_end).replace(":", "")}`;
}

function normalizeBlock(row, source = "manual_ui") {
  return {
    block_id: buildBlockId(row),
    instructor: row.instructor,
    location: row.location,
    date: row.date,
    available_start: row.available_start,
    available_end: row.available_end,
    preferred_anchor_start: row.preferred_anchor_start || "",
    preferred_course_families: row.preferred_course_families || [],
    allowed_course_families: row.allowed_course_families || [],
    flexibility: row.flexibility,
    source,
    notes: row.notes || ""
  };
}

function validateBlock(row) {
  const issues = [];
  const start = timeMinutes(row.available_start);
  const end = timeMinutes(row.available_end);
  const anchor = timeMinutes(row.preferred_anchor_start);
  if (!row.instructor) issues.push("Instructor required");
  if (!row.location) issues.push("Location required");
  if (!row.date) issues.push("Date required");
  if (start === null || end === null || start >= end) issues.push("Start time must be before end time");
  if (!row.allowed_course_families?.length) issues.push("At least one allowed course family required");
  if (row.preferred_anchor_start && (anchor === null || anchor < start || anchor >= end)) {
    issues.push("Preferred anchor must fall inside the availability window");
  }
  return issues;
}

function formToRows(form, mode) {
  const data = new FormData(form);
  const startDate = String(data.get("start_date") || "");
  const endDate = String(data.get("end_date") || "");
  const selectedDays = new Set(getChecked(form, "days_of_week"));
  const rowBase = {
    instructor: String(data.get("instructor") || ""),
    location: String(data.get("location") || ""),
    available_start: String(data.get("available_start") || ""),
    available_end: String(data.get("available_end") || ""),
    preferred_anchor_start: String(data.get("preferred_anchor_start") || ""),
    preferred_course_families: getChecked(form, "preferred_course_families"),
    allowed_course_families: getChecked(form, "allowed_course_families"),
    flexibility: String(data.get("flexibility") || "use_unused_time_if_useful"),
    notes: String(data.get("notes") || "")
  };
  const exclusionDates = new Set(state.exclusions.map(item => item.date));
  return dateRange(startDate, endDate)
    .filter(date => selectedDays.has(String(date.getDay())))
    .filter(date => mode !== "range" || !exclusionDates.has(toIsoDate(date)))
    .map(date => normalizeBlock({ ...rowBase, date: toIsoDate(date) }, mode === "range" ? "large_range_ui" : "block_builder_ui"));
}

function validateRangeForm(form) {
  const data = new FormData(form);
  const start = dateFromIso(data.get("start_date"));
  const end = dateFromIso(data.get("end_date"));
  const issues = [];
  if (!start || !end || end < start) issues.push("Range start and end dates are required, and end must be after start");
  for (const exclusion of state.exclusions) {
    const exclusionDate = dateFromIso(exclusion.date);
    if (!exclusionDate || exclusionDate < start || exclusionDate > end) {
      issues.push(`Excluded date ${exclusion.date} must fall inside the large range`);
    }
  }
  return issues;
}

function renderOneOffRows() {
  $("one-off-list").innerHTML = state.oneOffRows.map((row, index) => `
    <div class="entry-card" data-row="${index}">
      <div class="card-header">
        <strong>One-off ${index + 1}</strong>
        <div class="actions">
          <button class="secondary" type="button" data-copy-row="${index}">Copy Previous Row</button>
          <button class="secondary" type="button" data-delete-row="${index}">Delete Row</button>
        </div>
      </div>
      <div class="entry-grid">
        <label class="field">Instructor<select data-field="instructor">${instructorOptions(row.instructor)}</select></label>
        <label class="field">Location<input data-field="location" value="${escapeHtml(row.location)}"></label>
        <label class="field">Date<input data-field="date" type="date" value="${escapeHtml(row.date)}"></label>
        <label class="field">Preferred anchor/start time<input data-field="preferred_anchor_start" type="time" value="${escapeHtml(row.preferred_anchor_start)}"></label>
        <label class="field">Available start time<input data-field="available_start" type="time" value="${escapeHtml(row.available_start)}"></label>
        <label class="field">Available end time<input data-field="available_end" type="time" value="${escapeHtml(row.available_end)}"></label>
        <label class="field">Flexibility mode<select data-field="flexibility">${flexibilityOptions(row.flexibility)}</select></label>
      </div>
      <div class="field">Preferred course families${familyCheckboxes(`preferred_${index}`, row.preferred_course_families)}</div>
      <div class="field">Allowed course families${familyCheckboxes(`allowed_${index}`, row.allowed_course_families)}</div>
      <label class="field">Notes<textarea data-field="notes" rows="2">${escapeHtml(row.notes)}</textarea></label>
    </div>
  `).join("");

  $("one-off-list").querySelectorAll("[data-field]").forEach(input => {
    const updateRow = event => {
      const card = event.target.closest("[data-row]");
      state.oneOffRows[Number(card.dataset.row)][event.target.dataset.field] = event.target.value;
      renderPreview();
    };
    input.addEventListener("input", updateRow);
    input.addEventListener("change", updateRow);
  });
  $("one-off-list").querySelectorAll("input[type='checkbox']").forEach(input => {
    input.addEventListener("change", () => {
      state.oneOffRows.forEach((row, index) => {
        row.preferred_course_families = Array.from(document.querySelectorAll(`input[name="preferred_${index}"]:checked`)).map(item => item.value);
        row.allowed_course_families = Array.from(document.querySelectorAll(`input[name="allowed_${index}"]:checked`)).map(item => item.value);
      });
      renderPreview();
    });
  });
  $("one-off-list").querySelectorAll("[data-copy-row]").forEach(button => {
    button.addEventListener("click", () => {
      const source = state.oneOffRows[Math.max(0, Number(button.dataset.copyRow) - 1)] || state.oneOffRows[Number(button.dataset.copyRow)];
      state.oneOffRows.splice(Number(button.dataset.copyRow) + 1, 0, { ...source });
      render();
    });
  });
  $("one-off-list").querySelectorAll("[data-delete-row]").forEach(button => {
    button.addEventListener("click", () => {
      state.oneOffRows.splice(Number(button.dataset.deleteRow), 1);
      render();
    });
  });
}

function syncOneOffRowsFromDom() {
  const list = $("one-off-list");
  if (!list) return;
  list.querySelectorAll("[data-row]").forEach(card => {
    const index = Number(card.dataset.row);
    const row = state.oneOffRows[index];
    if (!row) return;
    card.querySelectorAll("[data-field]").forEach(input => {
      row[input.dataset.field] = input.value;
    });
    row.preferred_course_families = Array.from(card.querySelectorAll(`input[name="preferred_${index}"]:checked`)).map(input => input.value);
    row.allowed_course_families = Array.from(card.querySelectorAll(`input[name="allowed_${index}"]:checked`)).map(input => input.value);
  });
}

function renderAppointmentRanges() {
  const ranges = state.ranges.ranges || [];
  $("range-count").textContent = `${ranges.length} ranges`;
  $("appointment-range-table").innerHTML = `
    <table>
      <thead><tr><th>Owner</th><th>Range ID</th><th>Course ID</th><th>Location</th><th>Start</th><th>Last Verified</th><th>Last Valid</th><th>Broken After</th><th>Mode</th><th>Notice</th><th>Notes</th></tr></thead>
      <tbody>${ranges.map(range => {
        const helper = range.generation_mode === "daily_contiguous"
          ? "Estimated ID formula: start_appointmentDayId + days since start_date"
          : range.generation_mode === "selected_days_only"
            ? "IDs increment only across enabled appointment days. Do not use calendar-day math."
            : "";
        return `<tr>
          <td>${escapeHtml(range.owner)}</td>
          <td>${escapeHtml(range.range_id)}</td>
          <td>${escapeHtml(range.courseId)}</td>
          <td>${escapeHtml(range.location || "Not recorded")}</td>
          <td>${escapeHtml(range.start_date)}<br><span class="small-note">${escapeHtml(range.start_appointmentDayId)}</span></td>
          <td>${escapeHtml(range.verified_date || "Not recorded")}<br><span class="small-note">${escapeHtml(range.verified_appointmentDayId || "")}</span></td>
          <td>${escapeHtml(range.last_valid_date)}<br><span class="small-note">${escapeHtml(range.last_valid_appointmentDayId)}</span></td>
          <td>${escapeHtml(range.broken_after_appointmentDayId || "None recorded")}</td>
          <td>${escapeHtml(range.generation_mode)}<span class="small-note">${escapeHtml(helper)}</span></td>
          <td>${escapeHtml(range.minimum_notice_days)} days</td>
          <td>${escapeHtml(range.notes || "")}${range.diagnostic_url ? `<span class="small-note">Diagnostic URL: ${escapeHtml(range.diagnostic_url)}</span>` : ""}</td>
        </tr>`;
      }).join("")}</tbody>
    </table>
  `;
}

function renderRecommendations() {
  const recommendations = state.recommendations.recommendations || [];
  const instructors = new Set(recommendations.map(item => item.instructor).filter(Boolean));
  const businessPriority = recommendations.filter(item => (item.suggested_fits || []).some(fit => Number(fit.business_priority_boost || 0) > 0)).length;
  const conflicts = recommendations.filter(item => item.location_conflict_possible).length;
  $("recommendation-count").textContent = `${recommendations.length} recommendations`;
  $("recommendation-summary").innerHTML = `
    <div class="summary-card"><strong>${recommendations.length}</strong><span>Total recommendations</span></div>
    <div class="summary-card"><strong>${instructors.size}</strong><span>Instructors with recommendations</span></div>
    <div class="summary-card"><strong>${businessPriority}</strong><span>Business-priority recommendations</span></div>
    <div class="summary-card"><strong>${conflicts}</strong><span>Possible conflicts</span></div>
  `;
  if (!recommendations.length) {
    $("recommendation-table").innerHTML = `
      <div class="empty-state">
        No resolver recommendations have been generated yet. Run <code>python scripts/inventory_resolver_v1.py</code>.
      </div>
    `;
    return;
  }
  $("recommendation-table").innerHTML = groupedRecommendationsHtml(recommendations);
  $("recommendation-table").querySelectorAll("[data-rec-status]").forEach(button => {
    button.addEventListener("click", () => {
      updateRecommendationStatus(button.dataset.recId, button.dataset.recStatus);
    });
  });
}

function groupedRecommendationsHtml(recommendations) {
  const sorted = [...recommendations].sort((left, right) =>
    String(left.date || "").localeCompare(String(right.date || "")) ||
    String(left.instructor || "").localeCompare(String(right.instructor || "")) ||
    String(left.gap_start || "").localeCompare(String(right.gap_start || "")) ||
    topRankScore(right) - topRankScore(left)
  );
  const instructorGroups = new Map();
  for (const item of sorted) {
    if (!instructorGroups.has(item.instructor)) instructorGroups.set(item.instructor, new Map());
    const dateGroups = instructorGroups.get(item.instructor);
    if (!dateGroups.has(item.date)) dateGroups.set(item.date, []);
    dateGroups.get(item.date).push(item);
  }
  return Array.from(instructorGroups.entries()).map(([instructor, dateGroups]) => `
    <details class="rec-group" open>
      <summary>${escapeHtml(instructor)} <span class="muted">${countGroup(dateGroups)} recommendations</span></summary>
      ${Array.from(dateGroups.entries()).map(([date, items]) => `
        <details class="rec-date-group" open>
          <summary>${escapeHtml(date)} <span class="muted">${items.length} gaps</span></summary>
          <div class="rec-card-list">${items.map(renderRecommendationCard).join("")}</div>
        </details>
      `).join("")}
    </details>
  `).join("");
}

function countGroup(dateGroups) {
  return Array.from(dateGroups.values()).reduce((total, items) => total + items.length, 0);
}

function topRankScore(item) {
  const topFit = (item.suggested_fits || [])[0] || {};
  return Number(topFit.rank_score || 0);
}

function renderRecommendationCard(item) {
  const fits = item.suggested_fits || [];
  const topFit = fits[0] || {};
  const topReason = item.explanation || topFit.rank_reason || topFit.reason || "No reason recorded.";
  const badges = [];
  if (fits.some(fit => fit.preferred_match)) badges.push("Preferred");
  if (fits.some(fit => Number(fit.business_priority_boost || 0) > 0)) badges.push("Business Priority");
  if (item.location_conflict_possible) badges.push("Possible Conflict");
  return `
    <article class="rec-card" data-rec-id="${escapeHtml(item.recommendation_id)}">
      <div class="card-header">
        <div>
          <h3>${escapeHtml(item.gap_start)}-${escapeHtml(item.gap_end)} open</h3>
          <p class="muted">${escapeHtml(item.gap_minutes)} minutes at ${escapeHtml(item.location)}</p>
        </div>
        <span class="status ${statusClassForRecommendation(item.status)}">${escapeHtml(item.status || "suggested")}</span>
      </div>
      ${renderTimeline(item)}
      <div class="facts">
        <div class="fact"><span class="label">Suggested fits</span><span class="value">${renderPills(fits.map(fit => `${fit.rank}. ${fit.course_family} (${fit.estimated_minutes}m, score ${fit.rank_score ?? "n/a"}, ${fit.duration_fit_quality || "fit"})`))}</span></div>
        <div class="fact"><span class="label">Badges</span><span class="value">${renderBadges(badges)}</span></div>
        <div class="fact"><span class="label">Explanation</span><span class="value">${escapeHtml(topReason)}</span></div>
      </div>
      <div class="actions">
        <button type="button" data-rec-id="${escapeHtml(item.recommendation_id)}" data-rec-status="accepted">Accept</button>
        <button class="secondary" type="button" data-rec-id="${escapeHtml(item.recommendation_id)}" data-rec-status="ignored">Ignore</button>
        <button class="secondary" type="button" data-rec-id="${escapeHtml(item.recommendation_id)}" data-rec-status="blocked">Block</button>
      </div>
    </article>
  `;
}

function renderTimeline(item) {
  const segments = [
    ...(item.merged_occupied_windows || []).map(window => ({ type: "occupied", start: window.start, end: window.end, label: "OCCUPIED" })),
    { type: "open", start: item.gap_start, end: item.gap_end, label: "OPEN" }
  ].sort((left, right) => String(left.start).localeCompare(String(right.start)));
  return `<div class="op-timeline">${segments.map(segment => `
    <div class="op-segment ${segment.type}"><strong>${escapeHtml(segment.start)}-${escapeHtml(segment.end)}</strong><span>${segment.label}</span></div>
  `).join("")}</div>`;
}

function statusClassForRecommendation(status) {
  if (status === "accepted") return "normal";
  if (status === "blocked") return "action";
  if (status === "ignored") return "none";
  return "opportunity";
}

function updateRecommendationStatus(recommendationId, status) {
  const item = (state.recommendations.recommendations || []).find(recommendation => recommendation.recommendation_id === recommendationId);
  if (!item) return;
  item.status = status;
  renderRecommendations();
}

function renderExclusions() {
  $("exclusion-list").innerHTML = state.exclusions.map((exclusion, index) => `
    <div class="list-item">
      <div><strong>${escapeHtml(exclusion.date)}</strong><div class="muted">${escapeHtml(exclusion.reason || "No reason recorded")}</div></div>
      <button class="secondary" type="button" data-remove-exclusion="${index}">Remove Exclusion</button>
    </div>
  `).join("") || `<div class="list-item"><span>No exclusions yet.</span><span class="status none">Optional</span></div>`;
  $("exclusion-list").querySelectorAll("[data-remove-exclusion]").forEach(button => {
    button.addEventListener("click", () => {
      state.exclusions.splice(Number(button.dataset.removeExclusion), 1);
      renderExclusions();
      renderPreview();
    });
  });
}

function renderGeneratedTable() {
  $("block-count").textContent = `${currentBlocks().length} blocks`;
  $("generated-table").innerHTML = `
    <table>
      <thead><tr><th>Date</th><th>Instructor</th><th>Location</th><th>Window</th><th>Anchor</th><th>Preferred</th><th>Allowed</th><th>Flexibility</th><th>Source</th><th>Notes</th></tr></thead>
      <tbody>${currentBlocks().map(block => `
        <tr>
          <td>${escapeHtml(block.date)}</td>
          <td>${escapeHtml(block.instructor)}</td>
          <td>${escapeHtml(block.location)}</td>
          <td>${displayTime(block.available_start)} - ${displayTime(block.available_end)}</td>
          <td>${escapeHtml(block.preferred_anchor_start ? displayTime(block.preferred_anchor_start) : "None")}</td>
          <td>${renderPills(block.preferred_course_families)}</td>
          <td>${renderPills(block.allowed_course_families)}</td>
          <td>${escapeHtml(block.flexibility)}</td>
          <td>${escapeHtml(block.source)}</td>
          <td>${escapeHtml(block.notes)}</td>
        </tr>
      `).join("")}</tbody>
    </table>
  `;
}

function renderPills(items = []) {
  return `<div class="pill-list">${items.map(item => `<span class="pill">${escapeHtml(item)}</span>`).join("")}</div>`;
}

function renderBadges(items = []) {
  return items.length
    ? `<div class="pill-list">${items.map(item => `<span class="badge">${escapeHtml(item)}</span>`).join("")}</div>`
    : `<span class="muted">None</span>`;
}

function currentBlocks() {
  syncOneOffRowsFromDom();
  const oneOffBlocks = state.oneOffRows.map(row => normalizeBlock(row));
  return [...(state.availability.availability_blocks || []), ...oneOffBlocks, ...state.generatedBlocks];
}

function currentSourceNotes() {
  return [...(state.availability.source_notes || [])];
}

function buildAvailabilityModel() {
  return {
    schema_version: state.availability.schema_version || "0.1",
    updated_at: todayIso(),
    availability_blocks: currentBlocks(),
    source_notes: currentSourceNotes()
  };
}

function validateAll() {
  const issues = [];
  for (const block of currentBlocks()) {
    for (const issue of validateBlock(block)) {
      issues.push(`${block.block_id || "new block"}: ${issue}`);
    }
  }
  return issues;
}

function renderValidation() {
  const issues = validateAll();
  $("validation-list").innerHTML = issues.length
    ? issues.slice(0, 12).map(issue => `<div class="list-item"><span>${escapeHtml(issue)}</span><span class="status action">Fix</span></div>`).join("")
    : `<div class="list-item"><span>Generated availability data passes local validation.</span><span class="status normal">Ready</span></div>`;
}

function renderPreview() {
  const model = buildAvailabilityModel();
  $("json-preview").textContent = JSON.stringify(model, null, 2);
  renderGeneratedTable();
  renderValidation();
}

function render() {
  renderOneOffRows();
  renderExclusions();
  renderAppointmentRanges();
  renderRecommendations();
  renderPreview();
}

function generateBlockRows() {
  const form = $("block-form");
  const rows = formToRows(form, "block");
  state.generatedBlocks.push(...rows);
  renderPreview();
}

function generateRangeRows() {
  const form = $("range-form");
  const formIssues = validateRangeForm(form);
  if (formIssues.length) {
    $("validation-list").innerHTML = formIssues.map(issue => `<div class="list-item"><span>${escapeHtml(issue)}</span><span class="status action">Fix</span></div>`).join("");
    return;
  }
  const rows = formToRows(form, "range");
  state.generatedBlocks.push(...rows);
  renderPreview();
}

function addSourceNote() {
  const text = $("source-note-input").value.trim();
  if (!text) return;
  state.availability.source_notes = state.availability.source_notes || [];
  state.availability.source_notes.push({
    id: `source_note_${Date.now()}`,
    captured_at: new Date().toISOString(),
    source: "manual_paste",
    text
  });
  $("source-note-input").value = "";
  renderPreview();
}

async function saveJsonFile() {
  const content = JSON.stringify(buildAvailabilityModel(), null, 2) + "\n";
  await writeRepoJson(AVAILABILITY_PATH, "instructor_availability.json", content);
}

async function saveRecommendationsFile() {
  state.recommendations.generated_at = new Date().toISOString();
  const content = JSON.stringify(state.recommendations, null, 2) + "\n";
  await writeRepoJson(RECOMMENDATION_PATH, "inventory_recommendations.json", content);
}

async function writeRepoJson(relativePath, fallbackFilename, content) {
  if (window.showDirectoryPicker) {
    try {
      if (!state.directoryHandle) state.directoryHandle = await window.showDirectoryPicker({ mode: "readwrite" });
      const parts = relativePath.split("/");
      let dir = state.directoryHandle;
      for (const part of parts.slice(0, -1)) dir = await dir.getDirectoryHandle(part, { create: true });
      const file = await dir.getFileHandle(parts.at(-1), { create: true });
      const writable = await file.createWritable();
      await writable.write(content);
      await writable.close();
      return;
    } catch {
      downloadText(fallbackFilename, content, "application/json");
      return;
    }
  }
  downloadText(fallbackFilename, content, "application/json");
}

function downloadText(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function addOneOffRow() {
  const profile = instructorByName("Amy Arnold") || state.profiles.instructors?.[0] || {};
  const source = state.oneOffRows.at(-1) || defaultOneOffRow(profile);
  state.oneOffRows.push({ ...source, date: "" });
  render();
}

function wireEvents() {
  $("add-one-off-button").addEventListener("click", addOneOffRow);
  $("generate-block-button").addEventListener("click", generateBlockRows);
  $("generate-range-button").addEventListener("click", generateRangeRows);
  $("preview-all-button").addEventListener("click", renderPreview);
  $("preview-block-button").addEventListener("click", renderPreview);
  $("preview-range-button").addEventListener("click", renderPreview);
  $("save-json-button").addEventListener("click", saveJsonFile);
  $("download-json-button").addEventListener("click", () => downloadText("instructor_availability.json", JSON.stringify(buildAvailabilityModel(), null, 2) + "\n", "application/json"));
  $("save-recommendations-button").addEventListener("click", saveRecommendationsFile);
  $("download-recommendations-button").addEventListener("click", () => downloadText("inventory_recommendations.json", JSON.stringify(state.recommendations, null, 2) + "\n", "application/json"));
  $("add-source-note-button").addEventListener("click", addSourceNote);
  $("clear-generated-button").addEventListener("click", () => {
    state.generatedBlocks = [];
    renderPreview();
  });
  $("add-exclusion-button").addEventListener("click", () => {
    const date = $("excluded-date-input").value;
    if (!date) return;
    state.exclusions.push({ date, reason: $("exclusion-reason-input").value.trim() });
    $("excluded-date-input").value = "";
    $("exclusion-reason-input").value = "";
    renderExclusions();
    renderPreview();
  });
  document.addEventListener("change", event => {
    if (!event.target.matches("[data-instructor-select]")) return;
    const form = event.target.closest("form");
    const profile = instructorByName(event.target.value);
    if (!form || !profile) return;
    const location = form.querySelector('input[name="location"]');
    const flexibility = form.querySelector('select[name="flexibility"]');
    const notes = form.querySelector('textarea[name="notes"]');
    if (location) location.value = profile.default_location || location.value;
    if (flexibility) flexibility.value = profile.default_flexibility || flexibility.value;
    if (notes && !notes.value) notes.value = profile.default_availability_pattern_note || "";
  });
}

async function init() {
  state.profiles = await readJson(PROFILE_URL, state.profiles);
  state.availability = await readJson(AVAILABILITY_URL, state.availability);
  state.ranges = await readJson(RANGE_URL, state.ranges);
  state.recommendations = await readJson(RECOMMENDATION_URL, state.recommendations);
  if (!state.profiles.instructors?.length) {
    $("load-warning").classList.remove("hidden");
    $("load-warning").textContent = "Instructor profiles could not be loaded. Availability entry is running with fallback data.";
  }
  populateForms();
  wireEvents();
  render();
}

document.addEventListener("DOMContentLoaded", init);
