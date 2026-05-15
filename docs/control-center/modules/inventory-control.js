const PROFILE_URL = "../../data/instructor_profiles.json";
const AVAILABILITY_URL = "../../data/instructor_availability.json";
const RANGE_URL = "../../data/appointment_range_registry.json";
const RECOMMENDATION_URL = "../../data/inventory_recommendations.json";
const ACTION_QUEUE_URL = "../../data/inventory_action_queue.json";
const ADMIN_API_BASE = "http://127.0.0.1:5057/api/inventory-control";

const STEPS = [
  ["Instructor", "Choose Instructor"],
  ["Location", "Choose Location"],
  ["Entry Type", "Choose Availability Entry Type"],
  ["Time", "Choose Date/Time Blocks"],
  ["Behavior", "Choose Behavior"],
  ["Review", "Review & Add to Staging"],
  ["Save", "Staging Queue"]
];

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
  profiles: { schema_version: "0.1", instructors: [] },
  availability: { schema_version: "0.1", updated_at: "", availability_blocks: [], source_notes: [] },
  ranges: { schema_version: "0.1", ranges: [] },
  recommendations: { schema_version: "0.1", recommendations: [] },
  actionQueue: { schema_version: "0.1", updated_at: "", duplicate_prevented_count: 0, actions: [] },
  adminConnected: false,
  staticMode: true,
  currentStep: 1,
  stagedBlocks: [],
  editingStagedIndex: null,
  queueFilter: "draft",
  lastErrors: [],
  wizard: freshWizard()
};

function $(id) {
  return document.getElementById(id);
}

function freshWizard() {
  return {
    instructor: "",
    location: "",
    entryType: "",
    oneOff: { date: "", start: "", end: "", anchor: "" },
    block: { startDate: "", endDate: "", weekdays: ["1", "2", "3", "4", "5"], start: "", end: "", anchor: "" },
    range: { startDate: "", endDate: "", weekdays: ["1", "2", "3", "4", "5"], start: "", end: "", anchor: "", exclusions: [] },
    preferredFamilies: [],
    allowedFamilies: [],
    flexibility: "use_unused_time_if_useful",
    notes: ""
  };
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

async function apiGet(path) {
  const response = await fetch(`${ADMIN_API_BASE}${path}`, { cache: "no-store" });
  const data = await response.json();
  if (!response.ok || data.ok === false) throw new Error(data.error || `API ${path} failed`);
  return data;
}

async function apiPost(path, payload = {}) {
  const response = await fetch(`${ADMIN_API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await response.json();
  if (!response.ok || data.ok === false) throw new Error(data.error || `API ${path} failed`);
  return data;
}

function setAdminStatus(message, connected) {
  const banner = $("admin-server-status");
  if (!banner) return;
  banner.textContent = message;
  banner.classList.toggle("admin-connected", Boolean(connected));
}

function setLoadWarning(message) {
  const banner = $("load-warning");
  if (!banner) return;
  banner.classList.toggle("hidden", !message);
  banner.innerHTML = message ? escapeHtml(message) : "";
}

function showErrors(errors, focusSelector = "") {
  state.lastErrors = errors;
  const panel = $("error-panel");
  const count = $("top-error-count");
  if (count) {
    count.textContent = `${errors.length} error${errors.length === 1 ? "" : "s"}`;
    count.className = errors.length ? "status action" : "status none";
  }
  if (!panel) return;
  if (!errors.length) {
    panel.classList.add("hidden");
    panel.innerHTML = "";
    return;
  }
  panel.classList.remove("hidden");
  panel.innerHTML = `
    <strong>Fix this before continuing:</strong>
    <ul>${errors.map(error => `<li>${escapeHtml(error.message || error)}</li>`).join("")}</ul>
  `;
  panel.scrollIntoView({ behavior: "smooth", block: "start" });
  const target = focusSelector || errors.find(error => error.selector)?.selector;
  if (target) {
    const element = document.querySelector(target);
    if (element && typeof element.focus === "function") {
      setTimeout(() => element.focus(), 80);
    }
  }
}

function clearErrors() {
  showErrors([]);
}

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function dateFromIso(value) {
  const [year, month, day] = String(value || "").split("-").map(Number);
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
  return `${hour}:${minuteText || "00"} ${suffix}`;
}

function slug(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "") || "block";
}

function instructorByName(name) {
  return (state.profiles.instructors || []).find(instructor =>
    instructor.display_name === name || instructor.short_name === name || instructor.id === name
  );
}

function selectedProfile() {
  return instructorByName(state.wizard.instructor);
}

function familySetHtml(name, selected = []) {
  const selectedSet = new Set(selected);
  return `<div class="checkbox-grid">${COURSE_FAMILIES.map(family => `
    <label>
      <input type="checkbox" name="${name}" value="${family}" ${selectedSet.has(family) ? "checked" : ""}>
      ${escapeHtml(family)}
    </label>
  `).join("")}</div>`;
}

function weekdaySetHtml(name, selected = []) {
  const selectedSet = new Set(selected.map(String));
  return `<div class="checkbox-grid weekday-grid">${WEEKDAYS.map(([value, label]) => `
    <label>
      <input type="checkbox" name="${name}" value="${value}" ${selectedSet.has(value) ? "checked" : ""}>
      ${label}
    </label>
  `).join("")}</div>`;
}

function getChecked(name) {
  return Array.from(document.querySelectorAll(`input[name="${name}"]:checked`)).map(input => input.value);
}

function renderStepIndicator() {
  const indicator = $("step-indicator");
  indicator.innerHTML = STEPS.map(([label], index) => {
    const step = index + 1;
    const className = step === state.currentStep ? "active" : step < state.currentStep ? "done" : "";
    return `<li class="${className}"><span>${step}</span>${escapeHtml(label)}</li>`;
  }).join("");
  $("wizard-mode").textContent = `Step ${state.currentStep}`;
}

function renderWizard() {
  renderStepIndicator();
  const [, title] = STEPS[state.currentStep - 1];
  $("wizard-content").innerHTML = `
    <div class="wizard-step-heading">
      <h2>${escapeHtml(title)}</h2>
      <p class="muted">${escapeHtml(stepHelpText(state.currentStep))}</p>
    </div>
    ${renderStepBody(state.currentStep)}
  `;
  wireWizardStep();
  renderWizardActions();
  validateCurrentStep(false);
}

function stepHelpText(step) {
  const help = {
    1: "Start by choosing who owns this availability. Defaults load from the instructor profile.",
    2: "Confirm where the instructor can be used. The default location is loaded first.",
    3: "Choose one entry style. Only the selected path is shown after this point.",
    4: "Enter the actual availability window. Times are availability, not public class promises.",
    5: "Set course-family permissions and flexibility. Resolver logic decides what fits later.",
    6: "Review the generated blocks. Add to staging only after the summary looks right.",
    7: "Save only staged, validated blocks. The active form is ignored by the save operation."
  };
  return help[step] || "";
}

function renderStepBody(step) {
  if (step === 1) return renderInstructorStep();
  if (step === 2) return renderLocationStep();
  if (step === 3) return renderEntryTypeStep();
  if (step === 4) return renderTimeStep();
  if (step === 5) return renderBehaviorStep();
  if (step === 6) return renderReviewStep();
  return renderSaveStep();
}

function renderInstructorStep() {
  const profiles = state.profiles.instructors || [];
  if (!profiles.length) {
    return `<div class="empty-state">No instructor profiles were loaded. Check docs/data/instructor_profiles.json.</div>`;
  }
  return `<div class="choice-grid instructor-grid">${profiles.map(profile => `
    <button type="button" class="choice-card ${state.wizard.instructor === profile.display_name ? "selected" : ""}" data-select-instructor="${escapeHtml(profile.display_name)}">
      <strong>${escapeHtml(profile.display_name)}</strong>
      <span>${escapeHtml(profile.default_location || "No default location")}</span>
      <small>Preferred: ${escapeHtml((profile.preferred_families || []).join(", ") || "Not set")}</small>
    </button>
  `).join("")}</div>`;
}

function renderLocationStep() {
  const profile = selectedProfile();
  return `
    <div class="form-grid single-column">
      <label class="field">Location
        <input id="wizard-location" type="text" value="${escapeHtml(state.wizard.location)}" placeholder="${escapeHtml(profile?.default_location || "Wilmington Shipyard")}">
      </label>
      <div class="hint-card">
        Default location: <strong>${escapeHtml(profile?.default_location || "Not set")}</strong>
      </div>
    </div>
  `;
}

function renderEntryTypeStep() {
  const options = [
    ["one_off", "One-off day", "Best for erratic single-day availability."],
    ["block", "Block of days", "Best for several similar days in a row."],
    ["large_range", "Large range with exclusions", "Best for broad recurring availability with blackout dates."]
  ];
  return `<div class="choice-grid">${options.map(([value, label, note]) => `
    <button type="button" class="choice-card ${state.wizard.entryType === value ? "selected" : ""}" data-select-entry-type="${value}">
      <strong>${label}</strong>
      <span>${note}</span>
    </button>
  `).join("")}</div>`;
}

function renderTimeStep() {
  if (state.wizard.entryType === "one_off") {
    const model = state.wizard.oneOff;
    return `
      <div class="form-grid">
        <label class="field">Date<input id="oneoff-date" type="date" value="${escapeHtml(model.date)}"></label>
        <label class="field">Available start time<input id="oneoff-start" type="time" value="${escapeHtml(model.start)}"></label>
        <label class="field">Available end time<input id="oneoff-end" type="time" value="${escapeHtml(model.end)}"></label>
        <label class="field">Preferred anchor/start time<input id="oneoff-anchor" type="time" value="${escapeHtml(model.anchor)}"></label>
      </div>
    `;
  }
  if (state.wizard.entryType === "block") {
    const model = state.wizard.block;
    return `
      <div class="form-grid">
        <label class="field">Start date<input id="block-start-date" type="date" value="${escapeHtml(model.startDate)}"></label>
        <label class="field">End date<input id="block-end-date" type="date" value="${escapeHtml(model.endDate)}"></label>
        <label class="field">Available start time<input id="block-start" type="time" value="${escapeHtml(model.start)}"></label>
        <label class="field">Available end time<input id="block-end" type="time" value="${escapeHtml(model.end)}"></label>
        <label class="field">Preferred anchor/start time<input id="block-anchor" type="time" value="${escapeHtml(model.anchor)}"></label>
        <div class="field span-field">Days of week included${weekdaySetHtml("block-weekdays", model.weekdays)}</div>
      </div>
    `;
  }
  const model = state.wizard.range;
  return `
    <div class="form-grid">
      <label class="field">Start date<input id="range-start-date" type="date" value="${escapeHtml(model.startDate)}"></label>
      <label class="field">End date<input id="range-end-date" type="date" value="${escapeHtml(model.endDate)}"></label>
      <label class="field">Default start time<input id="range-start" type="time" value="${escapeHtml(model.start)}"></label>
      <label class="field">Default end time<input id="range-end" type="time" value="${escapeHtml(model.end)}"></label>
      <label class="field">Preferred anchor/start time<input id="range-anchor" type="time" value="${escapeHtml(model.anchor)}"></label>
      <div class="field span-field">Days of week included${weekdaySetHtml("range-weekdays", model.weekdays)}</div>
    </div>
    <div class="exclusion-tools">
      <label class="field">Excluded date<input id="excluded-date-input" type="date"></label>
      <label class="field">Exclusion reason<input id="exclusion-reason-input" placeholder="travel, unavailable, admin hold"></label>
      <button id="add-exclusion-button" type="button">Add Exclusion</button>
    </div>
    <div id="exclusion-list" class="list">${renderExclusionsHtml()}</div>
  `;
}

function renderBehaviorStep() {
  return `
    <div class="form-grid">
      <div class="field span-field">Preferred course families${familySetHtml("preferred-families", state.wizard.preferredFamilies)}</div>
      <div class="field span-field">Allowed course families${familySetHtml("allowed-families", state.wizard.allowedFamilies)}</div>
      <label class="field span-field">Flexibility mode
        <select id="wizard-flexibility">
          ${FLEXIBILITY_MODES.map(mode => `<option value="${mode}" ${mode === state.wizard.flexibility ? "selected" : ""}>${mode}</option>`).join("")}
        </select>
      </label>
      <label class="field span-field">Notes
        <textarea id="wizard-notes" rows="4" placeholder="Operator context for this availability block.">${escapeHtml(state.wizard.notes)}</textarea>
      </label>
    </div>
  `;
}

function renderReviewStep() {
  const blocks = generateWizardBlocks();
  const summary = humanSummary(blocks);
  return `
    <div class="review-grid">
      <article class="hint-card">
        <h3>Summary</h3>
        <p>${escapeHtml(summary)}</p>
        <dl class="summary-list">
          <div><dt>Instructor</dt><dd>${escapeHtml(state.wizard.instructor)}</dd></div>
          <div><dt>Location</dt><dd>${escapeHtml(state.wizard.location)}</dd></div>
          <div><dt>Entry type</dt><dd>${escapeHtml(entryTypeLabel(state.wizard.entryType))}</dd></div>
          <div><dt>Generated blocks</dt><dd>${blocks.length}</dd></div>
        </dl>
      </article>
      <article>
        <h3>Generated JSON Preview</h3>
        <pre class="code json-preview">${escapeHtml(JSON.stringify(blocks, null, 2))}</pre>
      </article>
    </div>
  `;
}

function renderSaveStep() {
  return `
    <div class="hint-card">
      <h3>Ready to Save</h3>
      <p>Use the Staging Queue below to save staged blocks. The active wizard form is never posted to JSON.</p>
      <p><strong>${state.stagedBlocks.length}</strong> staged block${state.stagedBlocks.length === 1 ? "" : "s"} ready.</p>
    </div>
  `;
}

function renderExclusionsHtml() {
  const exclusions = state.wizard.range.exclusions || [];
  if (!exclusions.length) return `<div class="list-item"><span>No exclusions yet.</span><span class="status none">Optional</span></div>`;
  return exclusions.map((exclusion, index) => `
    <div class="list-item">
      <div><strong>${escapeHtml(exclusion.date)}</strong><div class="muted">${escapeHtml(exclusion.reason || "No reason recorded")}</div></div>
      <button class="secondary" type="button" data-remove-exclusion="${index}">Remove Exclusion</button>
    </div>
  `).join("");
}

function wireWizardStep() {
  document.querySelectorAll("[data-select-instructor]").forEach(button => {
    button.addEventListener("click", () => selectInstructor(button.dataset.selectInstructor));
  });
  document.querySelectorAll("[data-select-entry-type]").forEach(button => {
    button.addEventListener("click", () => {
      state.wizard.entryType = button.dataset.selectEntryType;
      clearErrors();
      renderWizard();
    });
  });
  const location = $("wizard-location");
  if (location) {
    location.addEventListener("input", () => {
      state.wizard.location = location.value.trim();
      validateCurrentStep(false);
    });
  }
  bindTimeInputs();
  bindBehaviorInputs();
  const addExclusion = $("add-exclusion-button");
  if (addExclusion) addExclusion.addEventListener("click", addExclusionFromInputs);
  document.querySelectorAll("[data-remove-exclusion]").forEach(button => {
    button.addEventListener("click", () => {
      state.wizard.range.exclusions.splice(Number(button.dataset.removeExclusion), 1);
      renderWizard();
    });
  });
}

function selectInstructor(displayName) {
  const profile = instructorByName(displayName);
  state.wizard.instructor = displayName;
  state.wizard.location = profile?.default_location || "";
  state.wizard.preferredFamilies = [...(profile?.preferred_families || [])].filter(family => family !== "flexible");
  state.wizard.allowedFamilies = [...(profile?.allowed_families || [])];
  state.wizard.flexibility = profile?.default_flexibility || "use_unused_time_if_useful";
  state.wizard.notes = profile?.default_availability_pattern_note || "";
  const defaultStart = profile?.short_name === "Amy" ? "13:00" : "08:30";
  const defaultEnd = profile?.short_name === "Amy" ? "18:00" : "17:00";
  const defaultAnchor = profile?.short_name === "Amy" ? "14:00" : "";
  state.wizard.oneOff.start = state.wizard.oneOff.start || defaultStart;
  state.wizard.oneOff.end = state.wizard.oneOff.end || defaultEnd;
  state.wizard.oneOff.anchor = state.wizard.oneOff.anchor || defaultAnchor;
  state.wizard.block.start = state.wizard.block.start || defaultStart;
  state.wizard.block.end = state.wizard.block.end || defaultEnd;
  state.wizard.block.anchor = state.wizard.block.anchor || defaultAnchor;
  state.wizard.range.start = state.wizard.range.start || defaultStart;
  state.wizard.range.end = state.wizard.range.end || defaultEnd;
  state.wizard.range.anchor = state.wizard.range.anchor || defaultAnchor;
  clearErrors();
  renderWizard();
}

function bindTimeInputs() {
  const pairs = [
    ["oneOff", "date", "oneoff-date"],
    ["oneOff", "start", "oneoff-start"],
    ["oneOff", "end", "oneoff-end"],
    ["oneOff", "anchor", "oneoff-anchor"],
    ["block", "startDate", "block-start-date"],
    ["block", "endDate", "block-end-date"],
    ["block", "start", "block-start"],
    ["block", "end", "block-end"],
    ["block", "anchor", "block-anchor"],
    ["range", "startDate", "range-start-date"],
    ["range", "endDate", "range-end-date"],
    ["range", "start", "range-start"],
    ["range", "end", "range-end"],
    ["range", "anchor", "range-anchor"]
  ];
  for (const [group, key, id] of pairs) {
    const input = $(id);
    if (!input) continue;
    input.addEventListener("input", () => {
      state.wizard[group][key] = input.value;
      validateCurrentStep(false);
    });
  }
  document.querySelectorAll("input[name='block-weekdays']").forEach(input => {
    input.addEventListener("change", () => {
      state.wizard.block.weekdays = getChecked("block-weekdays");
      validateCurrentStep(false);
    });
  });
  document.querySelectorAll("input[name='range-weekdays']").forEach(input => {
    input.addEventListener("change", () => {
      state.wizard.range.weekdays = getChecked("range-weekdays");
      validateCurrentStep(false);
    });
  });
}

function bindBehaviorInputs() {
  document.querySelectorAll("input[name='preferred-families']").forEach(input => {
    input.addEventListener("change", () => {
      state.wizard.preferredFamilies = getChecked("preferred-families");
      validateCurrentStep(false);
    });
  });
  document.querySelectorAll("input[name='allowed-families']").forEach(input => {
    input.addEventListener("change", () => {
      state.wizard.allowedFamilies = getChecked("allowed-families");
      validateCurrentStep(false);
    });
  });
  const flexibility = $("wizard-flexibility");
  if (flexibility) {
    flexibility.addEventListener("change", () => {
      state.wizard.flexibility = flexibility.value;
      validateCurrentStep(false);
    });
  }
  const notes = $("wizard-notes");
  if (notes) {
    notes.addEventListener("input", () => {
      state.wizard.notes = notes.value;
    });
  }
}

function addExclusionFromInputs() {
  const dateInput = $("excluded-date-input");
  const reasonInput = $("exclusion-reason-input");
  if (!dateInput?.value) {
    showErrors([{ message: "Excluded date required.", selector: "#excluded-date-input" }]);
    return;
  }
  state.wizard.range.exclusions.push({ date: dateInput.value, reason: reasonInput?.value.trim() || "" });
  renderWizard();
}

function renderWizardActions() {
  const back = $("wizard-back-button");
  const next = $("wizard-next-button");
  const add = $("wizard-add-staging-button");
  const reset = $("wizard-reset-button");
  const valid = validateCurrentStep(false);
  back.disabled = state.currentStep === 1;
  next.classList.toggle("hidden", state.currentStep >= 6);
  add.classList.toggle("hidden", state.currentStep !== 6);
  reset.disabled = false;
  syncWizardButtonState(valid);
}

function validateCurrentStep(showPanel) {
  const result = validateStep(state.currentStep);
  if (showPanel || result.errors.length) {
    if (result.errors.length) showErrors(result.errors);
    else clearErrors();
  } else {
    clearErrors();
  }
  syncWizardButtonState(result.errors.length === 0);
  return result.errors.length === 0;
}

function syncWizardButtonState(valid) {
  const next = $("wizard-next-button");
  const add = $("wizard-add-staging-button");
  if (next) next.disabled = !valid;
  if (add) add.disabled = state.currentStep !== 6 || !valid;
}

function validateStep(step) {
  const errors = [];
  if (step >= 1 && !state.wizard.instructor) errors.push({ message: "Instructor required before Step 2.", selector: "[data-select-instructor]" });
  if (step >= 2 && !state.wizard.location) errors.push({ message: "Location required before Step 3.", selector: "#wizard-location" });
  if (step >= 3 && !state.wizard.entryType) errors.push({ message: "Entry type required before Step 4.", selector: "[data-select-entry-type]" });
  if (step >= 4 && state.wizard.entryType) errors.push(...validateTimeStep());
  if (step >= 5 && !state.wizard.allowedFamilies.length) errors.push({ message: "At least one allowed course family required before Review.", selector: "input[name='allowed-families']" });
  if (step >= 6) {
    const blocks = generateWizardBlocks();
    if (!blocks.length) errors.push({ message: "No valid date-level blocks were generated.", selector: "#wizard-content" });
    for (const block of blocks) {
      for (const issue of validateBlock(block)) errors.push({ message: `${block.block_id}: ${issue}`, selector: "#wizard-content" });
    }
  }
  return { errors };
}

function validateTimeStep() {
  const errors = [];
  const type = state.wizard.entryType;
  const model = type === "one_off" ? state.wizard.oneOff : type === "block" ? state.wizard.block : state.wizard.range;
  const start = timeMinutes(model.start);
  const end = timeMinutes(model.end);
  const anchor = timeMinutes(model.anchor);
  const startSelector = type === "one_off" ? "#oneoff-start" : type === "block" ? "#block-start" : "#range-start";
  const endSelector = type === "one_off" ? "#oneoff-end" : type === "block" ? "#block-end" : "#range-end";
  if (type === "one_off") {
    if (!model.date) errors.push({ message: "Date required.", selector: "#oneoff-date" });
  } else {
    const startDate = dateFromIso(model.startDate);
    const endDate = dateFromIso(model.endDate);
    const startDateSelector = type === "block" ? "#block-start-date" : "#range-start-date";
    const endDateSelector = type === "block" ? "#block-end-date" : "#range-end-date";
    if (!startDate) errors.push({ message: "Start date required.", selector: startDateSelector });
    if (!endDate) errors.push({ message: "End date required.", selector: endDateSelector });
    if (startDate && endDate && endDate < startDate) errors.push({ message: "End date must be after start date.", selector: endDateSelector });
    if (!model.weekdays.length) errors.push({ message: "At least one day of week must be selected.", selector: type === "block" ? "input[name='block-weekdays']" : "input[name='range-weekdays']" });
    if (type === "large_range") {
      for (const exclusion of model.exclusions) {
        const exclusionDate = dateFromIso(exclusion.date);
        if (!exclusionDate || !startDate || !endDate || exclusionDate < startDate || exclusionDate > endDate) {
          errors.push({ message: `Excluded date ${exclusion.date} must fall inside the large range.`, selector: "#excluded-date-input" });
        }
      }
    }
  }
  if (start === null) errors.push({ message: "Available start time required.", selector: startSelector });
  if (end === null) errors.push({ message: "Available end time required.", selector: endSelector });
  if (start !== null && end !== null && start >= end) errors.push({ message: "End time must be after start time.", selector: endSelector });
  if (model.anchor && (anchor === null || anchor < start || anchor >= end)) {
    errors.push({ message: "Preferred anchor must be inside the availability window.", selector: type === "one_off" ? "#oneoff-anchor" : type === "block" ? "#block-anchor" : "#range-anchor" });
  }
  return errors;
}

function validateBlock(block) {
  const issues = [];
  const start = timeMinutes(block.available_start);
  const end = timeMinutes(block.available_end);
  const anchor = timeMinutes(block.preferred_anchor_start);
  if (!block.instructor) issues.push("Instructor required");
  if (!block.location) issues.push("Location required");
  if (!block.date) issues.push("Date required");
  if (start === null || end === null || start >= end) issues.push("Start time must be before end time");
  if (!block.allowed_course_families?.length) issues.push("At least one allowed course family required");
  if (block.preferred_anchor_start && (anchor === null || anchor < start || anchor >= end)) {
    issues.push("Preferred anchor must fall inside the availability window");
  }
  return issues;
}

function generateWizardBlocks() {
  if (!state.wizard.instructor || !state.wizard.location || !state.wizard.entryType) return [];
  if (validateTimeStep().length) return [];
  const type = state.wizard.entryType;
  if (type === "one_off") {
    return [normalizeBlock({
      date: state.wizard.oneOff.date,
      start: state.wizard.oneOff.start,
      end: state.wizard.oneOff.end,
      anchor: state.wizard.oneOff.anchor,
      source: "manual_ui"
    })];
  }
  const model = type === "block" ? state.wizard.block : state.wizard.range;
  const selectedDays = new Set(model.weekdays.map(String));
  const exclusions = new Set((model.exclusions || []).map(item => item.date));
  return dateRange(model.startDate, model.endDate)
    .filter(date => selectedDays.has(String(date.getDay())))
    .filter(date => type !== "large_range" || !exclusions.has(toIsoDate(date)))
    .map(date => normalizeBlock({
      date: toIsoDate(date),
      start: model.start,
      end: model.end,
      anchor: model.anchor,
      source: type === "block" ? "block_builder_ui" : "large_range_ui"
    }));
}

function normalizeBlock(raw) {
  const block = {
    block_id: buildBlockId(raw.date, raw.start, raw.end),
    instructor: state.wizard.instructor,
    location: state.wizard.location,
    date: raw.date,
    available_start: raw.start,
    available_end: raw.end,
    preferred_anchor_start: raw.anchor || "",
    preferred_course_families: [...state.wizard.preferredFamilies],
    allowed_course_families: [...state.wizard.allowedFamilies],
    flexibility: state.wizard.flexibility,
    source: raw.source,
    notes: state.wizard.notes || ""
  };
  return block;
}

function buildBlockId(date, start, end) {
  const profile = selectedProfile();
  const instructorSlug = slug(profile?.short_name || state.wizard.instructor);
  return `${instructorSlug}_${date}_${String(start).replace(":", "")}_${String(end).replace(":", "")}`;
}

function entryTypeLabel(value) {
  return {
    one_off: "One-off day",
    block: "Block of days",
    large_range: "Large range with exclusions"
  }[value] || "Not selected";
}

function humanSummary(blocks) {
  if (!blocks.length) return "No valid blocks generated yet.";
  const dates = blocks.map(block => block.date).sort();
  const first = dates[0];
  const last = dates[dates.length - 1];
  const window = `${displayTime(blocks[0].available_start)}-${displayTime(blocks[0].available_end)}`;
  return `${blocks.length} block${blocks.length === 1 ? "" : "s"} for ${state.wizard.instructor} at ${state.wizard.location}, ${first}${first === last ? "" : ` through ${last}`}, ${window}.`;
}

function addCurrentWizardToStaging() {
  if (!validateCurrentStep(true)) return;
  const blocks = generateWizardBlocks();
  const invalid = blocks.flatMap(block => validateBlock(block).map(issue => ({ message: `${block.block_id}: ${issue}` })));
  if (invalid.length) {
    showErrors(invalid);
    return;
  }
  if (state.editingStagedIndex !== null) {
    state.stagedBlocks.splice(state.editingStagedIndex, 1, ...blocks);
    state.editingStagedIndex = null;
  } else {
    state.stagedBlocks.push(...blocks);
  }
  state.currentStep = 7;
  clearErrors();
  renderAll();
  document.querySelector("#staging")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function resetWizard() {
  state.wizard = freshWizard();
  state.currentStep = 1;
  state.editingStagedIndex = null;
  clearErrors();
  renderWizard();
}

function editStagedBlock(index) {
  const block = state.stagedBlocks[index];
  if (!block) return;
  state.editingStagedIndex = index;
  state.wizard = freshWizard();
  state.wizard.instructor = block.instructor;
  state.wizard.location = block.location;
  state.wizard.entryType = "one_off";
  state.wizard.oneOff = {
    date: block.date,
    start: block.available_start,
    end: block.available_end,
    anchor: block.preferred_anchor_start || ""
  };
  state.wizard.preferredFamilies = [...(block.preferred_course_families || [])];
  state.wizard.allowedFamilies = [...(block.allowed_course_families || [])];
  state.wizard.flexibility = block.flexibility || "use_unused_time_if_useful";
  state.wizard.notes = block.notes || "";
  state.currentStep = 4;
  renderAll();
  document.querySelector("#add-availability")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderStagingQueue() {
  $("staging-count").textContent = `${state.stagedBlocks.length} staged`;
  const save = $("save-staged-button");
  const valid = state.stagedBlocks.length > 0 && state.stagedBlocks.every(block => validateBlock(block).length === 0);
  save.disabled = !valid || !state.adminConnected;
  if (!state.stagedBlocks.length) {
    $("staging-table").innerHTML = `<div class="empty-state">No staged blocks yet. Complete the wizard and use Add to Staging.</div>`;
    return;
  }
  $("staging-table").innerHTML = blockTable(state.stagedBlocks, true);
  document.querySelectorAll("[data-edit-staged]").forEach(button => {
    button.addEventListener("click", () => editStagedBlock(Number(button.dataset.editStaged)));
  });
  document.querySelectorAll("[data-remove-staged]").forEach(button => {
    button.addEventListener("click", () => {
      state.stagedBlocks.splice(Number(button.dataset.removeStaged), 1);
      renderAll();
    });
  });
}

function renderSavedBlocks() {
  const blocks = state.availability.availability_blocks || [];
  $("saved-block-count").textContent = `${blocks.length} saved`;
  $("saved-block-table").innerHTML = blocks.length
    ? blockTable(blocks, false)
    : `<div class="empty-state">No saved availability blocks.</div>`;
}

function blockTable(blocks, staged) {
  return `
    <table>
      <thead><tr><th>Date</th><th>Instructor</th><th>Location</th><th>Window</th><th>Anchor</th><th>Preferred</th><th>Allowed</th><th>Flexibility</th><th>Source</th><th>Notes</th>${staged ? "<th>Actions</th>" : ""}</tr></thead>
      <tbody>${blocks.map((block, index) => `
        <tr>
          <td>${escapeHtml(block.date)}</td>
          <td>${escapeHtml(block.instructor)}</td>
          <td>${escapeHtml(block.location)}</td>
          <td>${displayTime(block.available_start)} - ${displayTime(block.available_end)}</td>
          <td>${block.preferred_anchor_start ? displayTime(block.preferred_anchor_start) : "None"}</td>
          <td>${renderPills(block.preferred_course_families)}</td>
          <td>${renderPills(block.allowed_course_families)}</td>
          <td>${escapeHtml(block.flexibility)}</td>
          <td>${escapeHtml(block.source)}</td>
          <td>${escapeHtml(block.notes || "")}</td>
          ${staged ? `<td class="actions"><button type="button" data-edit-staged="${index}">Edit staged block</button><button class="secondary" type="button" data-remove-staged="${index}">Remove staged block</button></td>` : ""}
        </tr>
      `).join("")}</tbody>
    </table>
  `;
}

async function saveStagedBlocks() {
  if (!state.adminConnected) {
    showErrors([{ message: "Static mode: preview only. Start local admin server to save changes." }]);
    return;
  }
  const stagedIssues = state.stagedBlocks.flatMap(block => validateBlock(block).map(issue => ({ message: `${block.block_id}: ${issue}` })));
  if (!state.stagedBlocks.length || stagedIssues.length) {
    showErrors(stagedIssues.length ? stagedIssues : [{ message: "No staged valid blocks exist. Save is disabled until blocks are staged." }]);
    return;
  }
  const model = {
    schema_version: state.availability.schema_version || "0.1",
    updated_at: new Date().toISOString(),
    availability_blocks: [...(state.availability.availability_blocks || []), ...state.stagedBlocks],
    source_notes: [...(state.availability.source_notes || [])]
  };
  try {
    const result = await apiPost("/availability", model);
    state.availability = result.availability || model;
    state.stagedBlocks = [];
    setAdminStatus("Availability saved through local admin server.", true);
    clearErrors();
    renderAll();
  } catch (error) {
    showErrors([{ message: `Save failed: ${error.message}` }]);
  }
}

function renderPills(items = []) {
  return `<div class="pill-list">${items.map(item => `<span class="pill">${escapeHtml(item)}</span>`).join("")}</div>`;
}

function renderBadges(items = []) {
  return items.length
    ? `<div class="pill-list">${items.map(item => `<span class="badge">${escapeHtml(item)}</span>`).join("")}</div>`
    : `<span class="muted">None</span>`;
}

function renderAppointmentRanges() {
  const ranges = state.ranges.ranges || [];
  $("range-count").textContent = `${ranges.length} ranges`;
  if (!ranges.length) {
    $("appointment-range-table").innerHTML = `<div class="empty-state">No appointment range registry loaded.</div>`;
    return;
  }
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
          <td>${escapeHtml(range.start_date || "Not recorded")}<br><span class="small-note">${escapeHtml(range.start_appointmentDayId || "")}</span></td>
          <td>${escapeHtml(range.verified_date || "Not recorded")}<br><span class="small-note">${escapeHtml(range.verified_appointmentDayId || "")}</span></td>
          <td>${escapeHtml(range.last_valid_date || "Not recorded")}<br><span class="small-note">${escapeHtml(range.last_valid_appointmentDayId || "")}</span></td>
          <td>${escapeHtml(range.broken_after_appointmentDayId || "None recorded")}</td>
          <td>${escapeHtml(range.generation_mode || "Not recorded")}<span class="small-note">${escapeHtml(helper)}</span></td>
          <td>${escapeHtml(range.minimum_notice_days ?? "Not set")} days</td>
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
    button.addEventListener("click", () => updateRecommendationStatus(button.dataset.recId, button.dataset.recStatus));
  });
  $("recommendation-table").querySelectorAll("[data-create-action]").forEach(button => {
    button.addEventListener("click", () => createDraftAction(button.dataset.createAction));
  });
}

function groupedRecommendationsHtml(recommendations) {
  const sorted = [...recommendations].sort((a, b) =>
    String(a.date).localeCompare(String(b.date)) ||
    String(a.gap_start).localeCompare(String(b.gap_start)) ||
    Number(b.rank_score || bestFitScore(b)) - Number(a.rank_score || bestFitScore(a))
  );
  const byInstructor = groupBy(sorted, item => item.instructor || "Unknown instructor");
  return Object.entries(byInstructor).map(([instructor, items]) => `
    <details class="rec-group">
      <summary>${escapeHtml(instructor)} (${items.length})</summary>
      ${Object.entries(groupBy(items, item => item.date || "Unknown date")).map(([date, dateItems]) => `
        <details class="rec-date-group" open>
          <summary>${escapeHtml(date)} (${dateItems.length})</summary>
          <div class="rec-card-list">${dateItems.map(recommendationCard).join("")}</div>
        </details>
      `).join("")}
    </details>
  `).join("");
}

function recommendationCard(recommendation) {
  const actionExists = (state.actionQueue.actions || []).some(action => action.source_recommendation_id === recommendation.recommendation_id);
  const fits = recommendation.suggested_fits || [];
  return `
    <article class="rec-card">
      <div class="card-header">
        <div>
          <h3>${escapeHtml(recommendation.gap_start)}-${escapeHtml(recommendation.gap_end)} ${escapeHtml(recommendation.location || "")}</h3>
          <p class="muted">${escapeHtml(recommendation.explanation || recommendation.reason || "Gap-fit recommendation.")}</p>
        </div>
        <span class="status ${recommendation.status === "accepted" ? "normal" : recommendation.status === "blocked" ? "action" : "opportunity"}">${escapeHtml(recommendation.status || "suggested")}</span>
      </div>
      <div class="op-timeline">${renderTimeline(recommendation)}</div>
      <div class="pill-list">
        ${(fits.some(fit => fit.preferred_family_match) ? "<span class=\"badge\">Preferred</span>" : "")}
        ${(fits.some(fit => Number(fit.business_priority_boost || 0) > 0) ? "<span class=\"badge\">Business Priority</span>" : "")}
        ${recommendation.location_conflict_possible ? "<span class=\"badge\">Possible Conflict</span>" : ""}
        ${actionExists ? "<span class=\"badge\">Draft Action Exists</span>" : ""}
      </div>
      <table class="mini-table">
        <thead><tr><th>Fit</th><th>Minutes</th><th>Score</th><th>Reason</th><th>Action</th></tr></thead>
        <tbody>${fits.map(fit => `
          <tr>
            <td>${escapeHtml(fit.course_family)}</td>
            <td>${escapeHtml(fit.estimated_minutes)}</td>
            <td>${escapeHtml(fit.rank_score ?? fit.rank ?? "")}</td>
            <td>${escapeHtml(fit.rank_reason || fit.reason || "")}</td>
            <td>${recommendation.status === "accepted" ? `<button type="button" data-create-action="${escapeHtml(recommendation.recommendation_id)}|${escapeHtml(fit.course_family)}">Create Draft Inventory Action</button>` : "<span class=\"muted\">Accept first</span>"}</td>
          </tr>
        `).join("")}</tbody>
      </table>
      <div class="actions">
        <button type="button" data-rec-status="accepted" data-rec-id="${escapeHtml(recommendation.recommendation_id)}">Accept</button>
        <button class="secondary" type="button" data-rec-status="ignored" data-rec-id="${escapeHtml(recommendation.recommendation_id)}">Ignore</button>
        <button class="secondary" type="button" data-rec-status="blocked" data-rec-id="${escapeHtml(recommendation.recommendation_id)}">Block</button>
      </div>
    </article>
  `;
}

function bestFitScore(recommendation) {
  return Math.max(0, ...(recommendation.suggested_fits || []).map(fit => Number(fit.rank_score || fit.rank || 0)));
}

function renderTimeline(recommendation) {
  const occupied = recommendation.existing_sessions_considered || [];
  const open = `<div class="op-segment open"><strong>${escapeHtml(recommendation.gap_start)}-${escapeHtml(recommendation.gap_end)}</strong><span>OPEN ${escapeHtml(recommendation.gap_minutes)} min</span></div>`;
  const occupiedHtml = occupied.map(session => `
    <div class="op-segment occupied"><strong>${escapeHtml(session.start_time || session.start || "")}-${escapeHtml(session.end_time || session.end || "")}</strong><span>OCCUPIED</span></div>
  `).join("");
  return open + occupiedHtml;
}

function groupBy(items, keyFn) {
  return items.reduce((groups, item) => {
    const key = keyFn(item);
    groups[key] = groups[key] || [];
    groups[key].push(item);
    return groups;
  }, {});
}

function updateRecommendationStatus(recommendationId, status) {
  const recommendation = (state.recommendations.recommendations || []).find(item => item.recommendation_id === recommendationId);
  if (!recommendation) return;
  recommendation.status = status;
  renderRecommendations();
}

function createDraftAction(encoded) {
  const [recommendationId, courseFamily] = encoded.split("|");
  const recommendation = (state.recommendations.recommendations || []).find(item => item.recommendation_id === recommendationId);
  const fit = (recommendation?.suggested_fits || []).find(item => item.course_family === courseFamily);
  if (!recommendation || !fit) return;
  const duplicate = (state.actionQueue.actions || []).some(action =>
    action.source_recommendation_id === recommendationId &&
    action.course_family === courseFamily &&
    action.proposed_start === recommendation.gap_start &&
    action.proposed_end === recommendation.gap_end
  );
  if (duplicate) {
    state.actionQueue.duplicate_prevented_count = Number(state.actionQueue.duplicate_prevented_count || 0) + 1;
    renderActionQueue();
    return;
  }
  const warnings = [];
  if (recommendation.location_conflict_possible) warnings.push("Possible Conflict");
  if (fit.fit_quality === "inefficient_fit") warnings.push("Inefficient Fit");
  if (!fit.business_priority_boost) warnings.push("Low Business Priority");
  state.actionQueue.actions = state.actionQueue.actions || [];
  state.actionQueue.actions.push({
    action_id: `draft_${slug(recommendation.instructor)}_${recommendation.date}_${String(recommendation.gap_start).replace(":", "")}_${slug(courseFamily)}`,
    source_recommendation_id: recommendationId,
    status: "draft",
    instructor: recommendation.instructor,
    date: recommendation.date,
    location: recommendation.location,
    proposed_start: recommendation.gap_start,
    proposed_end: recommendation.gap_end,
    course_family: courseFamily,
    estimated_minutes: fit.estimated_minutes,
    reason: fit.reason || fit.rank_reason || recommendation.explanation || "",
    created_at: new Date().toISOString(),
    operator_notes: "",
    warning_flags: warnings
  });
  saveActionQueueFile();
}

function renderActionQueue() {
  const actions = state.actionQueue.actions || [];
  const counts = {
    draft: actions.filter(action => action.status === "draft").length,
    ready: actions.filter(action => action.status === "ready").length,
    archived: actions.filter(action => action.status === "archived").length,
    completed: actions.filter(action => action.status === "completed").length
  };
  $("action-queue-summary").innerHTML = `
    <div class="summary-card"><strong>${counts.draft}</strong><span>Draft</span></div>
    <div class="summary-card"><strong>${counts.ready}</strong><span>Ready</span></div>
    <div class="summary-card"><strong>${counts.completed}</strong><span>Completed</span></div>
    <div class="summary-card"><strong>${counts.archived}</strong><span>Archived</span></div>
  `;
  const filtered = state.queueFilter === "all" ? actions : actions.filter(action => action.status === state.queueFilter);
  if (!filtered.length) {
    $("action-queue-table").innerHTML = `<div class="empty-state">No ${escapeHtml(state.queueFilter)} draft actions.</div>`;
    return;
  }
  $("action-queue-table").innerHTML = `
    <table>
      <thead><tr><th>Instructor</th><th>Date</th><th>Course</th><th>Time</th><th>Source</th><th>Status</th><th>Warnings</th><th>Notes</th><th>Actions</th></tr></thead>
      <tbody>${filtered.map(action => `
        <tr>
          <td>${escapeHtml(action.instructor)}</td>
          <td>${escapeHtml(action.date)}</td>
          <td>${escapeHtml(action.course_family)}</td>
          <td>${escapeHtml(action.proposed_start)}-${escapeHtml(action.proposed_end)}</td>
          <td>${escapeHtml(action.source_recommendation_id)}</td>
          <td><span class="status ${statusClassForAction(action.status)}">${escapeHtml(action.status)}</span></td>
          <td>${renderBadges(action.warning_flags || [])}</td>
          <td><textarea data-action-note="${escapeHtml(action.action_id)}" rows="2">${escapeHtml(action.operator_notes || "")}</textarea></td>
          <td class="actions">
            <button type="button" data-action-status="${escapeHtml(action.action_id)}" data-status="ready">Mark Ready</button>
            <button class="secondary" type="button" data-action-status="${escapeHtml(action.action_id)}" data-status="draft">Revert to Draft</button>
            <button class="secondary" type="button" data-action-status="${escapeHtml(action.action_id)}" data-status="archived">Archive</button>
            <button class="secondary" type="button" data-action-status="${escapeHtml(action.action_id)}" data-status="completed">Mark Completed</button>
            <button class="secondary" type="button" data-delete-action="${escapeHtml(action.action_id)}">Delete</button>
          </td>
        </tr>
      `).join("")}</tbody>
    </table>
  `;
  $("action-queue-table").querySelectorAll("[data-action-status]").forEach(button => {
    button.addEventListener("click", () => updateActionStatus(button.dataset.actionStatus, button.dataset.status));
  });
  $("action-queue-table").querySelectorAll("[data-delete-action]").forEach(button => {
    button.addEventListener("click", () => deleteAction(button.dataset.deleteAction));
  });
  $("action-queue-table").querySelectorAll("[data-action-note]").forEach(input => {
    input.addEventListener("input", () => {
      const action = findAction(input.dataset.actionNote);
      if (action) action.operator_notes = input.value;
    });
    input.addEventListener("change", saveActionQueueFile);
  });
}

function statusClassForAction(status) {
  if (status === "ready" || status === "completed") return "normal";
  if (status === "archived") return "none";
  return "opportunity";
}

function findAction(actionId) {
  return (state.actionQueue.actions || []).find(action => action.action_id === actionId);
}

function updateActionStatus(actionId, status) {
  const action = findAction(actionId);
  if (!action) return;
  action.status = status;
  saveActionQueueFile();
}

function deleteAction(actionId) {
  state.actionQueue.actions = (state.actionQueue.actions || []).filter(action => action.action_id !== actionId);
  saveActionQueueFile();
}

async function saveActionQueueFile() {
  state.actionQueue.updated_at = new Date().toISOString();
  if (!state.adminConnected) {
    showErrors([{ message: "Static mode: preview only. Start local admin server to save queue changes." }]);
    return;
  }
  try {
    const result = await apiPost("/action-queue", state.actionQueue);
    state.actionQueue = result.action_queue || state.actionQueue;
    renderActionQueue();
    renderRecommendations();
    renderManualChecklist();
  } catch (error) {
    showErrors([{ message: `Queue save failed: ${error.message}` }]);
  }
}

function renderManualChecklist() {
  const readyActions = (state.actionQueue.actions || []).filter(action => action.status === "ready");
  $("manual-checklist-count").textContent = `${readyActions.length} ready`;
  if (!readyActions.length) {
    $("manual-checklist").innerHTML = `<div class="empty-state">No ready actions. Mark a draft action Ready to create a manual Enrollware checklist.</div>`;
    return;
  }
  $("manual-checklist").innerHTML = readyActions.map(action => `
    <article class="manual-card">
      <div class="card-header">
        <div>
          <h3>${escapeHtml(action.course_family)} with ${escapeHtml(action.instructor)}</h3>
          <p class="muted">${escapeHtml(action.date)} ${displayTime(action.proposed_start)}-${displayTime(action.proposed_end)} at ${escapeHtml(action.location)}</p>
        </div>
        <span class="status normal">ready</span>
      </div>
      <div class="facts">
        <div class="fact"><span class="label">Estimated minutes</span><span class="value">${escapeHtml(action.estimated_minutes)}</span></div>
        <div class="fact"><span class="label">Reason</span><span class="value">${escapeHtml(action.reason || "")}</span></div>
        <div class="fact"><span class="label">Warnings</span><span class="value">${renderBadges(action.warning_flags || [])}</span></div>
        <div class="fact"><span class="label">Operator notes</span><span class="value">${escapeHtml(action.operator_notes || "No notes yet.")}</span></div>
      </div>
      <ol class="manual-steps">
        <li>Open Enrollware admin.</li>
        <li>Confirm instructor availability.</li>
        <li>Confirm room/location availability.</li>
        <li>Create or adjust session manually.</li>
        <li>Verify class appears correctly.</li>
        <li>Mark action completed.</li>
      </ol>
      <div class="actions">
        <button type="button" data-action-status="${escapeHtml(action.action_id)}" data-status="completed">Mark Completed</button>
        <button class="secondary" type="button" data-edit-action-note="${escapeHtml(action.action_id)}">Add/Edit Notes</button>
        <button class="secondary" type="button" data-copy-task="${escapeHtml(action.action_id)}">Copy Enrollware Task Summary</button>
      </div>
    </article>
  `).join("");
  $("manual-checklist").querySelectorAll("[data-action-status]").forEach(button => {
    button.addEventListener("click", () => updateActionStatus(button.dataset.actionStatus, button.dataset.status));
  });
  $("manual-checklist").querySelectorAll("[data-edit-action-note]").forEach(button => {
    button.addEventListener("click", () => editActionNotes(button.dataset.editActionNote));
  });
  $("manual-checklist").querySelectorAll("[data-copy-task]").forEach(button => {
    button.addEventListener("click", () => copyTaskSummary(button.dataset.copyTask));
  });
}

function editActionNotes(actionId) {
  const action = findAction(actionId);
  if (!action) return;
  const updated = prompt("Operator notes", action.operator_notes || "");
  if (updated === null) return;
  action.operator_notes = updated;
  saveActionQueueFile();
}

async function safeCopy(text) {
  try {
    if (!navigator.clipboard?.writeText) throw new Error("Clipboard API unavailable");
    await navigator.clipboard.writeText(text);
  } catch {
    const fallback = $("load-warning");
    fallback.classList.remove("hidden");
    fallback.innerHTML = `Clipboard unavailable. Select and copy this text:<br><textarea rows="8">${escapeHtml(text)}</textarea>`;
  }
}

function copyTaskSummary(actionId) {
  const action = findAction(actionId);
  if (!action) return;
  const text = `Inventory Action:
Instructor: ${action.instructor || ""}
Date: ${action.date || ""}
Time: ${displayTime(action.proposed_start)}-${displayTime(action.proposed_end)}
Course Family: ${action.course_family || ""}
Location: ${action.location || ""}
Reason: ${action.reason || ""}
Warnings: ${(action.warning_flags || []).join(", ") || "None"}

Manual Steps:
1. Open Enrollware admin.
2. Confirm instructor and room availability.
3. Create/adjust session manually.
4. Verify public/admin display.
5. Return here and mark completed.`;
  safeCopy(text);
}

async function runResolverFromUi() {
  if (!state.adminConnected) {
    showErrors([{ message: "Static mode: preview only. Start local admin server to run resolver." }]);
    return;
  }
  try {
    const result = await apiPost("/run-resolver", {});
    state.recommendations = result.recommendations || state.recommendations;
    renderRecommendations();
    renderActionQueue();
    renderManualChecklist();
    setAdminStatus("Resolver completed through local admin server. Recommendations refreshed.", true);
  } catch (error) {
    showErrors([{ message: `Resolver failed: ${error.message}` }]);
  }
}

function renderAll() {
  renderWizard();
  renderStagingQueue();
  renderSavedBlocks();
  renderAppointmentRanges();
  renderRecommendations();
  renderActionQueue();
  renderManualChecklist();
}

function wireEvents() {
  $("wizard-back-button").addEventListener("click", () => {
    if (state.currentStep > 1) {
      state.currentStep -= 1;
      clearErrors();
      renderWizard();
    }
  });
  $("wizard-next-button").addEventListener("click", () => {
    if (!validateCurrentStep(true)) return;
    if (state.currentStep < 6) {
      state.currentStep += 1;
      clearErrors();
      renderWizard();
    }
  });
  $("wizard-add-staging-button").addEventListener("click", addCurrentWizardToStaging);
  $("wizard-reset-button").addEventListener("click", resetWizard);
  $("save-staged-button").addEventListener("click", saveStagedBlocks);
  $("clear-staging-button").addEventListener("click", () => {
    state.stagedBlocks = [];
    renderAll();
  });
  $("run-resolver-button").addEventListener("click", runResolverFromUi);
  $("top-run-resolver-button").addEventListener("click", runResolverFromUi);
  $("queue-filter").addEventListener("change", event => {
    state.queueFilter = event.target.value;
    renderActionQueue();
  });
  $("copy-queue-button").addEventListener("click", () => safeCopy(JSON.stringify(state.actionQueue, null, 2)));
}

async function init() {
  try {
    const apiState = await apiGet("/state");
    state.adminConnected = true;
    state.staticMode = false;
    state.profiles = apiState.profiles || state.profiles;
    state.availability = apiState.availability || state.availability;
    state.ranges = apiState.ranges || state.ranges;
    state.recommendations = apiState.recommendations || state.recommendations;
    state.actionQueue = apiState.action_queue || state.actionQueue;
    setAdminStatus("Local admin server connected. Changes save to repo JSON files.", true);
  } catch {
    state.adminConnected = false;
    state.staticMode = true;
    setAdminStatus("Static mode: preview only. Start local admin server to save changes.", false);
    state.profiles = await readJson(PROFILE_URL, state.profiles);
    state.availability = await readJson(AVAILABILITY_URL, state.availability);
    state.ranges = await readJson(RANGE_URL, state.ranges);
    state.recommendations = await readJson(RECOMMENDATION_URL, state.recommendations);
    state.actionQueue = await readJson(ACTION_QUEUE_URL, state.actionQueue);
  }
  if (!state.profiles.instructors?.length) {
    setLoadWarning("Instructor profiles could not be loaded. Availability entry is running without profile defaults.");
  }
  wireEvents();
  renderAll();
}

document.addEventListener("DOMContentLoaded", init);
