const STATUS = {
  normal: { label: "NORMAL", icon: "🟢", rank: 0 },
  due: { label: "DUE SOON", icon: "🟡", rank: 1 },
  action: { label: "ACTION NEEDED", icon: "🔴", rank: 2 },
  none: { label: "NOT CONFIGURED", icon: "⚫", rank: -1 },
  opportunity: { label: "OPPORTUNITY", icon: "🔵", rank: 0.5 }
};

const state = {
  generatedAt: new Date(),
  checks: {},
  debug: {}
};

function fmtDate(date) {
  if (!date) return "Not available";
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(date);
}

function ageDays(date) {
  if (!date) return null;
  return Math.max(0, Math.floor((Date.now() - date.getTime()) / 86400000));
}

function freshnessStatus(days, yellowAt, redAt) {
  if (days === null) return "none";
  if (days >= redAt) return "action";
  if (days >= yellowAt) return "due";
  return "normal";
}

function statusMarkup(status) {
  const meta = STATUS[status] || STATUS.none;
  return `<span class="status ${status}">${meta.icon} ${meta.label}</span>`;
}

async function readJson(path) {
  try {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

async function fileMeta(path) {
  try {
    const response = await fetch(path, { method: "HEAD", cache: "no-store" });
    if (!response.ok) return null;
    const modified = response.headers.get("Last-Modified");
    return {
      path,
      modified: modified ? new Date(modified) : null
    };
  } catch {
    return null;
  }
}

function setCardStatus(id, status) {
  const node = document.querySelector(`[data-status-for="${id}"]`);
  if (node) node.outerHTML = statusMarkup(status).replace("<span", `<span data-status-for="${id}"`);
}

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) node.textContent = value;
}

function addAction(id, status, title, why, fix) {
  state.checks[id] = { status, title, why, fix };
}

function renderNextActions() {
  const items = Object.values(state.checks)
    .filter(item => ["action", "due", "opportunity"].includes(item.status))
    .sort((a, b) => (STATUS[b.status].rank - STATUS[a.status].rank))
    .slice(0, 3);
  const node = document.getElementById("next-actions");
  if (!node) return;
  if (!items.length) {
    node.innerHTML = `<div class="list-item"><span>No urgent actions detected from available sources.</span>${statusMarkup("normal")}</div>`;
    return;
  }
  node.innerHTML = items.map((item, index) => `
    <div class="list-item">
      <div><strong>${index + 1}. ${item.title}</strong><div class="muted">${item.why}</div><div>${item.fix}</div></div>
      ${statusMarkup(item.status)}
    </div>
  `).join("");
}

function renderTimeline() {
  const node = document.getElementById("recent-timeline");
  if (!node) return;
  const timeline = state.debug.status?.recent_changes || [];
  if (!timeline.length) {
    node.innerHTML = `
      <div class="timeline-day">
        <strong>No timeline file configured</strong>
        <span class="muted">Add recent_changes to debug/control_center_status.json after uploads, builds, theme edits, or audits.</span>
      </div>`;
    return;
  }
  node.innerHTML = timeline.slice(0, 8).map(day => `
    <div class="timeline-day">
      <strong>${day.date || "Undated"}</strong>
      ${(day.items || []).map(item => `<span>${item}</span>`).join("")}
    </div>
  `).join("");
}

function renderFeatureRegistry() {
  const features = [
    ["Dynamic curated sessions", "ACTIVE", "Highlights useful live sessions on course and hub pages.", "scripts/build_slug_hubs.py / docs/data/schedule_future.json", "Use when schedule freshness changes."],
    ["Expired-class replacement layout", "ACTIVE", "Guides users from stale class URLs to live replacement options.", "lander templates and generated class pages", "Use when expired sessions still receive traffic."],
    ["Emergency outage banner", "AVAILABLE BUT INACTIVE", "Sitewide emergency messaging for phone, booking, or schedule outages.", "future control flag / shared template", "Use during operational incidents."],
    ["Theme engine", "PARTIAL", "Seasonal or campaign styling with default fallback assets.", "docs/control-center/modules/theme-builder.html", "Use for EMS Week, Nurses Week, holidays, and default resets."],
    ["Appointment layer", "PLANNED", "Future scheduling or consultation workflow above class inventory.", "not configured", "Use when private or group scheduling needs a dedicated layer."],
    ["Build stamp system", "PARTIAL", "Records last build timestamps and page counts for regression checks.", "debug/control_center_status.json", "Use after every hub or full rebuild."],
    ["SEO diagnostics", "PLANNED", "Collects canonical, sitemap, indexing, and Search Console warnings.", "future debug/seo_audit.json", "Use when Google reports indexing issues."],
    ["Support snapshot export", "ACTIVE", "Creates a pasteable diagnostic summary for ChatGPT troubleshooting.", "docs/control-center/index.html", "Use with Search Console emails, screenshots, and warnings."]
  ];
  const node = document.getElementById("feature-registry-list");
  if (!node) return;
  const statusLight = {
    ACTIVE: "🟢",
    PARTIAL: "🟡",
    PLANNED: "⚫",
    "AVAILABLE BUT INACTIVE": "🔵",
    EXPERIMENTAL: "🔵"
  };
  node.innerHTML = features.map(([name, status, description, where, used]) => `
    <div class="list-item">
      <div>
        <strong>${name}</strong>
        <div class="muted">${description}</div>
        <div><span class="label">Where:</span> ${where}</div>
        <div><span class="label">Use:</span> ${used}</div>
      </div>
      <span class="status opportunity">${statusLight[status] || "⚫"} ${status}</span>
    </div>
  `).join("");
}

function exportSnapshot() {
  const lines = [
    "910CPR Control Center Diagnostic Snapshot",
    `Generated: ${fmtDate(state.generatedAt)}`,
    "",
    "SYSTEM STATUS",
    "--------------",
    `Class Report: ${state.checks.classReport?.why || "Not configured"}`,
    `schedule_future.json: ${state.checks.futureSchedule?.why || "Not configured"}`,
    `Last Build: ${state.debug.status?.last_successful_build || "Not configured"}`,
    `Pages Generated: ${state.debug.status?.pages_generated ?? "Not configured"}`,
    `Build Result: ${state.debug.status?.result || "Not configured"}`,
    "",
    "THEME STATUS",
    "------------",
    `Active Theme: ${state.debug.status?.theme?.active || "TH000 Default"}`,
    `Upcoming Theme: ${state.debug.status?.theme?.upcoming || "Not configured"}`,
    "",
    "SEO HEALTH",
    "----------",
    `Canonical warnings: ${state.debug.status?.seo?.canonical_warnings ?? "Not configured"}`,
    `Missing sitemap references: ${state.debug.status?.seo?.missing_sitemap_references ?? "Not configured"}`,
    "",
    "ASSET HEALTH",
    "------------",
    `Missing hero images: ${state.debug.assets?.missing_hero_images ?? "Not configured"}`,
    `Broken image references: ${state.debug.assets?.broken_image_references ?? "Not configured"}`,
    `Oversized images: ${state.debug.assets?.oversized_images ?? "Not configured"}`,
    "",
    "STALE SESSION HEALTH",
    "--------------------",
    `Stale pages: ${state.debug.stale?.stale_pages ?? "Not configured"}`,
    `Expired sessions: ${state.debug.stale?.expired_sessions ?? "Not configured"}`,
    `Orphaned pages: ${state.debug.stale?.orphaned_pages ?? "Not configured"}`,
    "",
    "RECENT WARNINGS",
    "---------------",
    ...Object.values(state.checks)
      .filter(item => ["action", "due"].includes(item.status))
      .map(item => `- ${item.title}: ${item.why}`)
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "control-center-report.txt";
  link.click();
  URL.revokeObjectURL(url);
}

async function initDashboard() {
  state.debug.status = await readJson("../../debug/control_center_status.json");
  state.debug.assets = await readJson("../../debug/missing_assets_audit.json") || await readJson("../../debug/theme_asset_audit.json");
  state.debug.stale = await readJson("../../debug/stale_sessions_audit.json");

  const classReport = await fileMeta("../../data/Class Report.xlsx");
  const classAge = ageDays(classReport?.modified);
  const classStatus = freshnessStatus(classAge, 4, 8);
  setCardStatus("class-report", classStatus);
  setText("class-report-modified", classReport?.modified ? fmtDate(classReport.modified) : "Not configured or not readable from static page");
  setText("class-report-age", classAge === null ? "Unknown" : `${classAge} days`);
  addAction("classReport", classStatus, "Upload new Class Report", classAge === null ? "data/Class Report.xlsx is not readable from this page." : `Class Report age is ${classAge} days.`, "Upload the current Enrollware Class Report, then run the Hubs Builder.");

  const schedule = await fileMeta("../data/schedule_future.json");
  const scheduleAge = ageDays(schedule?.modified);
  const scheduleStatus = freshnessStatus(scheduleAge, 4, 8);
  setCardStatus("future-schedule", scheduleStatus);
  setText("future-schedule-modified", schedule?.modified ? fmtDate(schedule.modified) : "Not configured or not readable from static page");
  setText("future-schedule-age", scheduleAge === null ? "Unknown" : `${scheduleAge} days`);
  addAction("futureSchedule", scheduleStatus, "Run Hubs Builder", scheduleAge === null ? "docs/data/schedule_future.json is not readable from this page." : `schedule_future.json age is ${scheduleAge} days.`, "Refresh schedule/content outputs before public inventory drifts.");

  const build = state.debug.status;
  const buildStatus = build ? (build.result === "SUCCESS" ? "normal" : "action") : "none";
  setCardStatus("last-build", buildStatus);
  setText("last-successful-build", build?.last_successful_build || "Not configured");
  setText("last-successful-build-duplicate", build?.last_successful_build || "Not configured");
  setText("last-failed-build", build?.last_failed_build || "Not configured");
  setText("last-build-result", build?.result || "Not configured");
  setText("pages-generated", build?.pages_generated ?? "Not configured");
  addAction("lastBuild", buildStatus, "Check last build status", build ? `Last build result is ${build.result || "unknown"}.` : "debug/control_center_status.json is missing.", "Create or update debug/control_center_status.json after each build.");

  const assets = state.debug.assets;
  const assetProblems = (assets?.missing_hero_images || 0) + (assets?.broken_image_references || 0) + (assets?.missing_theme_assets || 0);
  const assetStatus = assets ? (assetProblems > 0 ? "action" : "normal") : "none";
  setCardStatus("asset-health", assetStatus);
  setText("missing-hero-images", assets?.missing_hero_images ?? "Not configured");
  setText("broken-image-references", assets?.broken_image_references ?? "Not configured");
  setText("missing-theme-assets", assets?.missing_theme_assets ?? "Not configured");
  setText("oversized-images", assets?.oversized_images ?? "Not configured");
  addAction("assetHealth", assetStatus, "Run Asset Audit", assets ? `${assetProblems} missing or broken asset issues detected.` : "No asset audit file exists yet.", "Run or create the asset audit, then open Theme Builder for missing theme assets.");

  const stale = state.debug.stale;
  const staleProblems = (stale?.stale_pages || 0) + (stale?.expired_sessions || 0) + (stale?.orphaned_pages || 0);
  const staleStatus = stale ? (staleProblems > 0 ? "due" : "normal") : "none";
  setCardStatus("stale-sessions", staleStatus);
  setText("stale-pages", stale?.stale_pages ?? "Not configured");
  setText("expired-sessions", stale?.expired_sessions ?? "Not configured");
  setText("orphaned-pages", stale?.orphaned_pages ?? "Not configured");
  addAction("staleSessions", staleStatus, "Run stale session audit", stale ? `${staleProblems} stale session issues detected.` : "debug/stale_sessions_audit.json is missing.", "Audit expired sessions and remove or redirect orphaned generated pages.");

  setText("active-theme", build?.theme?.active || "TH000 Default");
  setText("upcoming-theme", build?.theme?.upcoming || "Not configured");
  setText("theme-activation", build?.theme?.days_until_activation ?? "Not configured");

  renderNextActions();
  renderTimeline();
  renderFeatureRegistry();
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.body.dataset.page === "dashboard") initDashboard();
  document.querySelectorAll("[data-export-snapshot]").forEach(button => {
    button.addEventListener("click", exportSnapshot);
  });
});
