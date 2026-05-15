const REGISTRY_URL = "../../data/theme_registry.json";
const SCHEDULE_URL = "../../data/theme_schedule.json";
const AUDIT_URL = "../../../debug/theme_builder_audit.json";
const ASSET_DIR = "../../assets/themes/";
const REPO_ASSET_DIR = "docs/assets/themes/";
const ROLE_IDS = {
  RL100: "Hero Background",
  RL110: "Hero Corner Badge",
  RL200: "Section Divider",
  RL210: "Archive Divider",
  RL300: "Card Edge Frame",
  RL310: "Card Corner Accent",
  RL400: "Trust Strip Accent",
  RL500: "Footer Divider",
  RL600: "Texture Overlay",
  RL700: "Badge Ribbon"
};
const SCOPE_TYPES = ["global", "course_slug", "certifying_body", "city", "page_type"];
const SAMPLE_CONTEXTS = {
  global: {},
  "BLS hub": { course_slug: "bls", page_type: "hub" },
  "ACLS hub": { course_slug: "acls", page_type: "hub" },
  "PALS hub": { course_slug: "pals", page_type: "hub" },
  "Heartsaver hub": { course_slug: "heartsaver", page_type: "hub" },
  "Wilmington class page": { city: "Wilmington", page_type: "class" },
  "Burgaw class page": { city: "Burgaw", page_type: "class" }
};

const state = {
  registry: null,
  schedule: null,
  audit: null,
  selectedTheme: "TH000",
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

function statusClass(value) {
  return value === "direct override" ? "normal" : value === "inherited" ? "opportunity" : "action";
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

function repoPathToUrl(path) {
  if (!path) return "";
  return `../../${String(path).replace(/^docs\//, "")}`;
}

function sanitizeSlug(value) {
  return String(value || "theme-asset")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "theme-asset";
}

function nextThemeId() {
  const ids = Object.keys(state.registry.themes || {})
    .map(id => Number(id.replace("TH", "")))
    .filter(Number.isFinite);
  return `TH${String(Math.max(-1, ...ids) + 1).padStart(3, "0")}`;
}

function nextRuleId() {
  const existing = (state.schedule.rules || [])
    .map(rule => Number(String(rule.id || "").replace("theme-rule-", "")))
    .filter(Number.isFinite);
  return `theme-rule-${String(Math.max(0, ...existing) + 1).padStart(3, "0")}`;
}

function nextVariant(themeId, roleId) {
  const themeAssets = Object.values(state.registry.themes?.[themeId]?.assets || {});
  const prefix = `${themeId}-${roleId}-V`;
  const variants = themeAssets
    .map(asset => String(asset).split("/").at(-1) || "")
    .filter(filename => filename.startsWith(prefix))
    .map(filename => Number(filename.slice(prefix.length, prefix.length + 2)))
    .filter(Number.isFinite);
  return `V${String(Math.max(0, ...variants) + 1).padStart(2, "0")}`;
}

function themeOptions(selected = "") {
  return Object.entries(state.registry.themes || {})
    .map(([id, theme]) => `<option value="${id}" ${id === selected ? "selected" : ""}>${id} ${escapeHtml(theme.label || "")}</option>`)
    .join("");
}

function roleOptions(selected = "") {
  return Object.entries(state.registry.roles || ROLE_IDS)
    .map(([id, label]) => `<option value="${id}" ${id === selected ? "selected" : ""}>${id} ${escapeHtml(label)}</option>`)
    .join("");
}

function scopeOptions(selected = "global") {
  return SCOPE_TYPES.map(type => `<option value="${type}" ${type === selected ? "selected" : ""}>${type.replace("_", " ")}</option>`).join("");
}

function resolveAsset(themeId, roleId, seen = new Set()) {
  const theme = state.registry.themes?.[themeId];
  if (!theme || seen.has(themeId)) return { asset: "", source: "", status: "missing" };
  seen.add(themeId);
  const direct = theme.assets?.[roleId];
  if (direct) return { asset: direct, source: themeId, status: "direct override" };
  if (theme.inherits) {
    const inherited = resolveAsset(theme.inherits, roleId, seen);
    if (inherited.asset) return { ...inherited, status: "inherited" };
  }
  if (themeId !== "TH000") {
    const fallback = resolveAsset("TH000", roleId, seen);
    if (fallback.asset) return { ...fallback, status: "inherited" };
  }
  return { asset: "", source: "", status: "missing" };
}

function scheduleStatus(rule, today = new Date()) {
  if (rule.enabled === false) return "Disabled";
  const start = new Date(`${rule.start}T00:00:00`);
  const end = new Date(`${rule.end}T00:00:00`);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return "Invalid";
  if (today < start) return "Upcoming";
  if (today >= end) return "Expired";
  return "Active now";
}

function renderThemeList() {
  const list = $("theme-list");
  list.innerHTML = Object.entries(state.registry.themes || {}).map(([id, theme]) => `
    <button class="list-item theme-list-button" type="button" data-theme="${id}">
      <strong>${id}</strong><span>${escapeHtml(theme.label || "")}</span>
    </button>
  `).join("");
  list.querySelectorAll("[data-theme]").forEach(button => {
    button.addEventListener("click", () => {
      state.selectedTheme = button.dataset.theme;
      render();
    });
  });
}

function renderSelectedTheme() {
  const theme = state.registry.themes[state.selectedTheme] || {};
  $("selected-theme-status").outerHTML = `<span id="selected-theme-status" class="status ${theme.active ? "normal" : "none"}">${theme.active ? "Active flag on" : "Inactive"}</span>`;
  $("selected-theme-details").innerHTML = `
    <div class="fact"><span class="label">Theme</span><span class="value">${state.selectedTheme}</span></div>
    <div class="fact"><span class="label">Label</span><span class="value">${escapeHtml(theme.label)}</span></div>
    <div class="fact"><span class="label">Inherits</span><span class="value">${escapeHtml(theme.inherits || "none")}</span></div>
    <div class="fact"><span class="label">Notes</span><span class="value">${escapeHtml(theme.notes || "")}</span></div>
    <div class="fact"><span class="label">Asset fallback</span><span class="value">Missing role assets inherit from ${escapeHtml(theme.inherits || "TH000")}.</span></div>
  `;
}

function renderForms() {
  $("theme-parent-select").innerHTML = themeOptions("TH000");
  $("asset-theme-select").innerHTML = themeOptions(state.selectedTheme);
  $("preview-theme-select").innerHTML = themeOptions(state.selectedTheme);
  $("asset-role-select").innerHTML = roleOptions("RL100");
  document.querySelectorAll("[data-scope-type]").forEach(select => {
    select.innerHTML = scopeOptions("global");
  });
  $("preview-context-select").innerHTML = Object.keys(SAMPLE_CONTEXTS).map(key => `<option value="${escapeHtml(key)}">${escapeHtml(key)}</option>`).join("");
  if (!$("preview-date-input").value) $("preview-date-input").value = new Date().toISOString().slice(0, 10);
}

function renderScheduleSummary() {
  const resolver = window.ThemeResolver?.resolveActiveTheme;
  const resolved = resolver ? resolver(state.registry, state.schedule, {}, new Date()) : { theme: "TH000", reason: "Resolver unavailable." };
  $("active-schedule-summary").innerHTML = `
    <div class="fact"><span class="label">Resolved now</span><span class="value">${escapeHtml(resolved.theme)}</span></div>
    <div class="fact"><span class="label">Reason</span><span class="value">${escapeHtml(resolved.reason)}</span></div>
    <div class="fact"><span class="label">Schedule file</span><span class="value">docs/data/theme_schedule.json</span></div>
  `;
}

function renderRoleMatrix() {
  const roles = state.registry.roles || ROLE_IDS;
  $("role-matrix").innerHTML = `
    <table>
      <thead><tr><th>Role ID</th><th>Role</th><th>Current theme asset</th><th>Parent/fallback asset</th><th>Effective asset</th><th>Status</th><th>Preview</th></tr></thead>
      <tbody>${Object.entries(roles).map(([roleId, roleName]) => {
        const theme = state.registry.themes[state.selectedTheme] || {};
        const direct = theme.assets?.[roleId] || "";
        const parent = theme.inherits ? resolveAsset(theme.inherits, roleId).asset : "";
        const effective = resolveAsset(state.selectedTheme, roleId);
        const url = repoPathToUrl(effective.asset);
        return `<tr>
          <td>${roleId}</td>
          <td>${escapeHtml(roleName)}</td>
          <td>${escapeHtml(direct || "No direct asset")}</td>
          <td>${escapeHtml(parent || "No fallback asset")}</td>
          <td>${escapeHtml(effective.asset || "Missing")}</td>
          <td><span class="status ${statusClass(effective.status)}">${effective.status === "inherited" ? `Inherited from ${effective.source}` : effective.status}</span></td>
          <td><div class="asset-preview">${url ? `<img src="${url}" alt="">` : "Missing"}</div></td>
        </tr>`;
      }).join("")}</tbody>
    </table>
  `;
}

function renderScheduleTable() {
  $("schedule-table").innerHTML = `
    <table>
      <thead><tr><th>Rule</th><th>Theme</th><th>Dates</th><th>Scope</th><th>Status</th><th>Actions</th></tr></thead>
      <tbody>${(state.schedule.rules || []).map((rule, index) => `
        <tr>
          <td>${escapeHtml(rule.label || rule.id)}<br><span class="muted">${escapeHtml(rule.id)}</span></td>
          <td>${escapeHtml(rule.theme)}</td>
          <td>${escapeHtml(rule.start)} to ${escapeHtml(rule.end)}<br><span class="muted">End date is exclusive</span></td>
          <td>${escapeHtml(rule.scope?.type || "global")} ${escapeHtml(rule.scope?.value || "")}</td>
          <td><span class="status ${scheduleStatus(rule) === "Active now" ? "normal" : scheduleStatus(rule) === "Upcoming" ? "opportunity" : "none"}">${scheduleStatus(rule)}</span></td>
          <td class="actions">
            <button class="secondary" type="button" data-edit-rule="${index}">Edit</button>
            <button type="button" data-toggle-rule="${index}">${rule.enabled === false ? "Enable" : "Disable"}</button>
            <button class="secondary" type="button" data-delete-rule="${index}">Delete</button>
          </td>
        </tr>
      `).join("")}</tbody>
    </table>
  `;
  document.querySelectorAll("[data-toggle-rule]").forEach(button => {
    button.addEventListener("click", () => {
      const rule = state.schedule.rules[Number(button.dataset.toggleRule)];
      rule.enabled = rule.enabled === false;
      render();
    });
  });
  document.querySelectorAll("[data-edit-rule]").forEach(button => {
    button.addEventListener("click", () => editScheduleRule(Number(button.dataset.editRule)));
  });
  document.querySelectorAll("[data-delete-rule]").forEach(button => {
    button.addEventListener("click", () => {
      state.schedule.rules.splice(Number(button.dataset.deleteRule), 1);
      render();
    });
  });
}

async function assetExists(path) {
  if (!path) return false;
  try {
    const response = await fetch(repoPathToUrl(path), { method: "HEAD", cache: "no-store" });
    return response.ok;
  } catch {
    return false;
  }
}

async function runBrowserAudit() {
  const issues = [];
  for (const [themeId, theme] of Object.entries(state.registry.themes || {})) {
    if (!/^TH\d{3}$/.test(themeId)) issues.push({ severity: "error", message: "Invalid Theme ID format", detail: themeId });
    if (theme.inherits && !state.registry.themes[theme.inherits]) issues.push({ severity: "error", message: "Theme inherits unknown parent", detail: `${themeId} -> ${theme.inherits}` });
    for (const [roleId, asset] of Object.entries(theme.assets || {})) {
      if (!state.registry.roles?.[roleId]) issues.push({ severity: "error", message: "Invalid Role ID", detail: `${themeId} ${roleId}` });
      if (!(await assetExists(asset))) issues.push({ severity: "error", message: "Asset reference does not exist", detail: asset });
    }
  }
  for (const roleId of ["RL100", "RL200"]) {
    const asset = state.registry.themes?.TH000?.assets?.[roleId];
    if (!asset) issues.push({ severity: "error", message: `TH000 missing critical fallback role ${roleId}`, detail: "" });
  }
  for (const rule of state.schedule.rules || []) {
    if (!state.registry.themes?.[rule.theme]) issues.push({ severity: "error", message: "Schedule rule references unknown theme", detail: rule.id });
    const start = new Date(`${rule.start}T00:00:00`);
    const end = new Date(`${rule.end}T00:00:00`);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) issues.push({ severity: "error", message: "Schedule rule has invalid dates", detail: rule.id });
    else if (end <= start) issues.push({ severity: "error", message: "Schedule rule end must be after start", detail: rule.id });
  }
  state.audit = {
    status: issues.some(issue => issue.severity === "error") ? "fail" : "pass",
    error_count: issues.filter(issue => issue.severity === "error").length,
    warning_count: issues.filter(issue => issue.severity === "warning").length,
    issues
  };
  renderAudit();
}

function renderAudit() {
  const audit = state.audit || {};
  $("audit-summary").innerHTML = `
    <div class="fact"><span class="label">Status</span><span class="value">${escapeHtml(audit.status || "Not run")}</span></div>
    <div class="fact"><span class="label">Errors</span><span class="value">${audit.error_count ?? "Unknown"}</span></div>
    <div class="fact"><span class="label">Warnings</span><span class="value">${audit.warning_count ?? "Unknown"}</span></div>
    <div class="fact"><span class="label">Audit output</span><span class="value">debug/theme_builder_audit.json when local script is run</span></div>
  `;
  $("audit-issues").innerHTML = (audit.issues || []).slice(0, 12).map(issue => `
    <div class="list-item"><div><strong>${escapeHtml(issue.message)}</strong><div class="muted">${escapeHtml(issue.detail)}</div></div><span class="status ${issue.severity === "error" ? "action" : "due"}">${escapeHtml(issue.severity)}</span></div>
  `).join("") || `<div class="list-item"><span>No audit issues from the loaded data.</span><span class="status normal">PASS</span></div>`;
}

function renderPreview() {
  const contextName = $("preview-context-select").value || "global";
  const date = $("preview-date-input").value || new Date().toISOString().slice(0, 10);
  const selectedTheme = $("preview-theme-select").value || state.selectedTheme;
  const resolver = window.ThemeResolver?.resolveActiveTheme;
  const resolved = resolver ? resolver(state.registry, state.schedule, SAMPLE_CONTEXTS[contextName], date) : { theme: "TH000", reason: "Resolver unavailable." };
  const hero = resolveAsset(resolved.theme, "RL100");
  const divider = resolveAsset(resolved.theme, "RL200");
  const selectedHero = resolveAsset(selectedTheme, "RL100");
  $("preview-result").innerHTML = `
    <div class="fact"><span class="label">Selected theme preview</span><span class="value">${escapeHtml(selectedTheme)} ${selectedHero.status === "inherited" ? `(inherited from ${selectedHero.source})` : ""}</span></div>
    <div class="fact"><span class="label">Resolved active theme</span><span class="value">${escapeHtml(resolved.theme)}</span></div>
    <div class="fact"><span class="label">Reason</span><span class="value">${escapeHtml(resolved.reason)}</span></div>
    <div class="theme-swatch"><div class="theme-swatch-hero" style="background-image:url('${repoPathToUrl(hero.asset)}')"></div><div class="theme-swatch-divider" style="background-image:url('${repoPathToUrl(divider.asset)}')"></div></div>
  `;
}

function render() {
  renderThemeList();
  renderSelectedTheme();
  renderForms();
  renderScheduleSummary();
  renderRoleMatrix();
  renderScheduleTable();
  renderAudit();
  renderPreview();
}

function addTheme(form) {
  const data = new FormData(form);
  const id = nextThemeId();
  state.registry.themes[id] = {
    label: String(data.get("label") || "").trim(),
    inherits: data.get("inherits") || "TH000",
    active: data.get("active") === "true",
    scope: data.get("scope_type") || "global",
    notes: String(data.get("notes") || ""),
    assets: {}
  };
  if (data.get("start") && data.get("end")) {
    state.schedule.rules.push({
      id: nextRuleId(),
      theme: id,
      label: state.registry.themes[id].label,
      start: data.get("start"),
      end: data.get("end"),
      scope: data.get("scope_type") === "global" ? { type: "global" } : { type: data.get("scope_type"), value: data.get("scope_value") || "" },
      enabled: data.get("active") === "true"
    });
  }
  state.selectedTheme = id;
  form.reset();
  render();
}

function addScheduleRule() {
  const theme = prompt("Theme ID to schedule", state.selectedTheme || "TH000");
  if (!theme || !state.registry.themes[theme]) {
    alert("Unknown Theme ID.");
    return;
  }
  const label = prompt("Schedule label", state.registry.themes[theme].label || theme) || theme;
  const start = prompt("Start date, inclusive (YYYY-MM-DD)", new Date().toISOString().slice(0, 10));
  const end = prompt("End date, exclusive (YYYY-MM-DD)", "");
  if (!start || !end) return;
  const scopeType = prompt("Scope type: global, course_slug, certifying_body, city, page_type", "global") || "global";
  const scopeValue = scopeType === "global" ? "" : prompt("Scope value", "") || "";
  state.schedule.rules.push({
    id: nextRuleId(),
    theme,
    label,
    start,
    end,
    scope: scopeType === "global" ? { type: "global" } : { type: scopeType, value: scopeValue },
    enabled: true
  });
  render();
}

function editScheduleRule(index) {
  const rule = state.schedule.rules[index];
  if (!rule) return;
  const theme = prompt("Theme ID", rule.theme) || rule.theme;
  if (!state.registry.themes[theme]) {
    alert("Unknown Theme ID.");
    return;
  }
  rule.theme = theme;
  rule.label = prompt("Schedule label", rule.label || rule.id) || rule.label || rule.id;
  rule.start = prompt("Start date, inclusive (YYYY-MM-DD)", rule.start) || rule.start;
  rule.end = prompt("End date, exclusive (YYYY-MM-DD)", rule.end) || rule.end;
  const scopeType = prompt("Scope type: global, course_slug, certifying_body, city, page_type", rule.scope?.type || "global") || rule.scope?.type || "global";
  const scopeValue = scopeType === "global" ? "" : prompt("Scope value", rule.scope?.value || "") || "";
  rule.scope = scopeType === "global" ? { type: "global" } : { type: scopeType, value: scopeValue };
  render();
}

async function writeJsonFile(relativePath, data) {
  const content = JSON.stringify(data, null, 2) + "\n";
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
      // Fall through to download when browser directory write is unavailable or denied.
    }
  }
  downloadText(partsFilename(relativePath), content, "application/json");
}

function partsFilename(path) {
  return path.split("/").at(-1);
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

async function registerAsset(form) {
  const data = new FormData(form);
  const themeId = String(data.get("theme"));
  const roleId = String(data.get("role"));
  const file = data.get("file");
  if (!state.registry.themes[themeId] || !state.registry.roles[roleId] || !file?.name) return;
  const ext = file.name.split(".").at(-1).toLowerCase();
  const filename = `${themeId}-${roleId}-${nextVariant(themeId, roleId)}_${sanitizeSlug(data.get("name") || file.name)}.${ext}`;
  const repoPath = `${REPO_ASSET_DIR}${filename}`;
  state.registry.themes[themeId].assets = state.registry.themes[themeId].assets || {};
  state.registry.themes[themeId].assets[roleId] = repoPath;
  let savedToDirectory = false;
  if (window.showDirectoryPicker) {
    try {
      if (!state.directoryHandle) state.directoryHandle = await window.showDirectoryPicker({ mode: "readwrite" });
      let dir = state.directoryHandle;
      for (const part of REPO_ASSET_DIR.replace(/\/$/, "").split("/")) dir = await dir.getDirectoryHandle(part, { create: true });
      const handle = await dir.getFileHandle(filename, { create: true });
      const writable = await handle.createWritable();
      await writable.write(file);
      await writable.close();
      savedToDirectory = true;
    } catch {
      savedToDirectory = false;
    }
  }
  if (!savedToDirectory) {
    const url = URL.createObjectURL(file);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }
  form.reset();
  render();
}

async function init() {
  state.registry = await readJson(REGISTRY_URL, null);
  state.schedule = await readJson(SCHEDULE_URL, null);
  state.audit = await readJson(AUDIT_URL, null);
  if (!state.registry || !state.schedule) {
    $("load-warning").classList.remove("hidden");
    $("load-warning").textContent = "Theme registry or schedule could not be loaded. The public site is unchanged.";
    state.registry = state.registry || { default_theme: "TH000", roles: ROLE_IDS, themes: { TH000: { label: "default", inherits: null, assets: {} } } };
    state.schedule = state.schedule || { default_theme: "TH000", rules: [] };
  }
  render();
}

document.addEventListener("DOMContentLoaded", () => {
  $("theme-form").addEventListener("submit", event => {
    event.preventDefault();
    addTheme(event.currentTarget);
  });
  $("asset-form").addEventListener("submit", event => {
    event.preventDefault();
    registerAsset(event.currentTarget);
  });
  $("preview-form").addEventListener("submit", event => {
    event.preventDefault();
    renderPreview();
  });
  $("add-theme-button").addEventListener("click", () => $("theme-form").scrollIntoView({ behavior: "smooth", block: "center" }));
  $("add-rule-button").addEventListener("click", addScheduleRule);
  $("save-registry-button").addEventListener("click", () => writeJsonFile("docs/data/theme_registry.json", state.registry));
  $("save-schedule-button").addEventListener("click", () => writeJsonFile("docs/data/theme_schedule.json", state.schedule));
  $("download-registry-button").addEventListener("click", () => downloadText("theme_registry.json", JSON.stringify(state.registry, null, 2) + "\n", "application/json"));
  $("download-schedule-button").addEventListener("click", () => downloadText("theme_schedule.json", JSON.stringify(state.schedule, null, 2) + "\n", "application/json"));
  $("run-audit-button").addEventListener("click", runBrowserAudit);
  init();
});
