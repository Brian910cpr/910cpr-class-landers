const DATA_URL = "../../../debug/inventory_control_center_data.json";

const state = {
  data: null,
  debugDataset: "public_offerings",
  debugSearch: ""
};

function byId(id) {
  return document.getElementById(id);
}

function text(value, fallback = "Unknown") {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function number(value) {
  return Number.isFinite(Number(value)) ? Number(value).toLocaleString() : text(value);
}

function moneyDisplay(value) {
  if (!value) return "unknown";
  if (value.display) return value.display;
  if (value.known_revenue) return `$${Number(value.known_revenue).toLocaleString()}`;
  return "unknown";
}

function escapeHtml(value) {
  return text(value, "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function pill(label, kind = "") {
  return `<span class="pill ${kind}">${escapeHtml(label)}</span>`;
}

function metric(label, value, hint = "") {
  return `
    <article class="metric">
      <span class="label">${escapeHtml(label)}</span>
      <span class="value">${escapeHtml(value)}</span>
      <span class="hint">${escapeHtml(hint)}</span>
    </article>
  `;
}

async function fetchJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return response.json();
}

function showLoadWarning(message) {
  const node = byId("load-warning");
  if (!node) return;
  node.classList.remove("hidden");
  node.textContent = message;
}

function setHtml(id, html) {
  const node = byId(id);
  if (node) node.innerHTML = html;
}

function renderSystem(data) {
  const totals = data.totals || {};
  setHtml("system-kpis", [
    metric("Availability Blocks", number(totals.availability_blocks), "Instructor/location blocks loaded"),
    metric("Candidates", number(totals.total_candidates), "All theoretical inventory"),
    metric("Public Offerings", number(totals.public_offerings), "Currently exposed"),
    metric("Suppressed", number(totals.suppressed_candidates), "Hidden by policy or fit"),
    metric("Invalid / Out of Range", number(totals.invalid_candidates), "No safe public link"),
    metric("Appointment Containers", number(totals.appointment_container_count), "Verified owned ranges")
  ].join(""));

  const warnings = data.warnings || [];
  const actionCount = warnings.filter(item => item.severity === "action").length;
  const dueCount = warnings.filter(item => item.severity === "due").length;
  setHtml("warning-count", `${actionCount} action / ${dueCount} due`);
  setHtml("attention-list", warnings.length ? warnings.map(item => `
    <article class="warning-card ${escapeHtml(item.severity)}">
      <strong>${escapeHtml(item.title)}</strong>
      <div>${escapeHtml(item.detail)}</div>
      <div class="muted">${escapeHtml(item.fix)}</div>
      ${pill(item.group || "Operations", item.severity === "action" ? "action" : item.severity === "due" ? "due" : "")}
    </article>
  `).join("") : `<div class="list-row"><strong>No urgent items from loaded data.</strong><span class="muted">Keep regenerating debug files before decisions.</span></div>`);

  const sources = data.source_statuses || [];
  const missing = sources.filter(source => !source.loaded).length;
  setHtml("data-source-status", missing ? `${missing} missing` : "all loaded");
  setHtml("source-list", sources.map(source => `
    <div class="source-row">
      <strong>${escapeHtml(source.key)}</strong>
      <div class="muted">${escapeHtml(source.path)}</div>
      <div>${source.loaded ? "Loaded" : "Missing"}${source.age_hours !== null && source.age_hours !== undefined ? ` / ${escapeHtml(source.age_hours)} hours old` : ""}</div>
    </div>
  `).join(""));
}

function renderRevenue(data) {
  const revenue = data.revenue || {};
  setHtml("revenue-kpis", [
    metric("Total Potential", moneyDisplay(revenue.total_public_offering_revenue_potential), "Unknown when course prices are missing"),
    metric("Anchor Potential", moneyDisplay(revenue.anchor_revenue_potential), "Tier 1 public offerings"),
    metric("Secondary Potential", moneyDisplay(revenue.secondary_escalation_revenue_potential), "Tier 2 public offerings"),
    metric("Tertiary Potential", moneyDisplay(revenue.tertiary_escalation_revenue_potential), "Tier 3 public offerings"),
    metric("Working Hours Exposed", number(revenue.estimated_working_hours_exposed), "Sum of public offering durations"),
    metric("Revenue / Work Hour", text(revenue.estimated_revenue_per_working_hour), "Placeholder until prices are complete")
  ].join(""));

  const placeholders = [
    ["Admin Hours", revenue.admin_hours],
    ["Overhead Cost", revenue.overhead_cost],
    ["Instructor Pay Estimate", revenue.instructor_pay_estimate],
    ["Estimated Margin", revenue.estimated_margin],
    ["Net / Working Hour", revenue.net_per_working_hour]
  ];
  setHtml("revenue-placeholders", placeholders.map(([label, value]) => `
    <article class="metric">
      <span class="label">${escapeHtml(label)}</span>
      <span class="value">${escapeHtml(text(value, "placeholder"))}</span>
      <span class="hint">Future finance field</span>
    </article>
  `).join(""));
}

function timelineSlot(item) {
  const status = item.status || "public";
  const title = `${item.start_time || ""} ${item.course_name || ""}`.trim();
  return `
    <div class="slot ${escapeHtml(status)}">
      <small><strong>${escapeHtml(item.start_time || "")}</strong> ${escapeHtml(item.end_time || "")}</small>
      <small>${escapeHtml(item.course_name || "Unknown course")}</small>
      <small>${escapeHtml(item.occupancy_pool || "No pool")}</small>
      <small title="${escapeHtml(title)}">${escapeHtml(status)}</small>
    </div>
  `;
}

function renderGeometry(data) {
  const blocks = data.inventory_geometry || [];
  setHtml("geometry-list", blocks.map(block => `
    <article class="block-row">
      <div class="panel-header">
        <div>
          <strong>${escapeHtml(block.instructor)} / ${escapeHtml(block.date)} / ${escapeHtml(block.start_time)}-${escapeHtml(block.end_time)}</strong>
          <div class="muted">${escapeHtml(block.location)}</div>
        </div>
        <div>${pill(block.anchor_status || "not required")} ${pill(`rings: ${(block.escalation_ring_status || []).join(", ") || "none"}`)}</div>
      </div>
      <div class="facts">
        <div class="fact"><span>Public offerings</span><span>${number(block.public_count)}</span></div>
        <div class="fact"><span>Suppressed offerings</span><span>${number(block.suppressed_count)}</span></div>
        <div class="fact"><span>Invalid / out of range</span><span>${number(block.invalid_count)}</span></div>
        <div class="fact"><span>Remaining usable time</span><span>${number(block.remaining_usable_minutes)} minutes</span></div>
      </div>
      <div class="timeline">${(block.timeline || []).slice(0, 18).map(timelineSlot).join("") || "<div class='slot'>No candidates</div>"}</div>
      ${block.notes ? `<p class="muted">${escapeHtml(block.notes)}</p>` : ""}
    </article>
  `).join(""));
}

function renderRings(data) {
  const rings = data.escalation_rings || [];
  setHtml("ring-grid", rings.map(ring => `
    <article class="panel">
      <div class="panel-header">
        <h3>Tier ${escapeHtml(ring.tier)}: ${escapeHtml(ring.label)}</h3>
        ${pill(`${number(ring.public_count)} public`)}
      </div>
      <div class="facts">
        <div class="fact"><span>Total candidates</span><span>${number(ring.candidates)}</span></div>
        <div class="fact"><span>Suppressed</span><span>${number(ring.suppressed_count)}</span></div>
        <div class="fact"><span>Revenue potential</span><span>${escapeHtml(moneyDisplay(ring.revenue))}</span></div>
        <div class="fact"><span>Seat filling success</span><span>${escapeHtml(ring.seat_fill_success)}</span></div>
        <div class="fact"><span>Conversion rate</span><span>${escapeHtml(ring.conversion_rate)}</span></div>
        <div class="fact"><span>Time to first seat</span><span>${escapeHtml(ring.time_to_first_seat)}</span></div>
        <div class="fact"><span>Momentum triggers</span><span>${number(ring.momentum_trigger_count)}</span></div>
      </div>
    </article>
  `).join(""));
}

function renderPools(data) {
  const pools = data.occupancy_pools || [];
  setHtml("pool-grid", pools.map(pool => `
    <article class="panel">
      <div class="panel-header">
        <h3>${escapeHtml(pool.occupancy_pool)}</h3>
        ${pool.fragmentation_warning ? pill("fragmenting", "due") : pill("stable", "good")}
      </div>
      <div class="facts">
        <div class="fact"><span>Public offerings</span><span>${number(pool.public_count)}</span></div>
        <div class="fact"><span>Suppressed offerings</span><span>${number(pool.suppressed_count)}</span></div>
        <div class="fact"><span>Compatible courses</span><span>${number(pool.compatible_course_count)}</span></div>
        <div class="fact"><span>Grouping success</span><span>${escapeHtml(pool.grouping_success)}</span></div>
        <div class="fact"><span>Fragmentation suppressions</span><span>${number(pool.fragmentation_suppressed_count)}</span></div>
      </div>
      <p class="muted">${escapeHtml((pool.compatible_course_ids || []).join(", ") || "No course ids")}</p>
    </article>
  `).join(""));
}

function renderAppointments(data) {
  const groups = data.appointment_container_groups || [];
  const blocks = data.appointment_blocks || [];
  const groupRows = groups.length ? groups.map(group => `
    <article class="block-row">
      <div class="panel-header">
        <div>
          <strong>${escapeHtml(group.container_group)}</strong>
          <div class="muted">${number(group.container_count)} containers / ${number(group.public_offering_dependency_count)} public offerings depend on this group</div>
        </div>
        <div>
          ${group.missing_or_unsafe_count ? pill(`${number(group.missing_or_unsafe_count)} missing/unsafe`, "action") : pill("verified fields", "good")}
          ${group.unused_container_count ? pill(`${number(group.unused_container_count)} unused`, "due") : ""}
        </div>
      </div>
    </article>
  `).join("") : "";
  const blockRows = blocks.map(block => `
    <article class="block-row">
      <div class="panel-header">
        <div>
          <strong>${escapeHtml(block.container_name || block.container_id)}</strong>
          <div class="muted">${escapeHtml(block.container_group || "ungrouped")} / ${escapeHtml(block.location_name)}</div>
        </div>
        <div>${(block.flags || []).length ? (block.flags || []).map(flag => pill(flag, flag === "expired" || flag === "unsafe_range" ? "action" : "due")).join(" ") : pill("range verified", "good")}</div>
      </div>
      <div class="facts">
        <div class="fact"><span>Instructor</span><span>${escapeHtml(block.instructor_name)}</span></div>
        <div class="fact"><span>Room / resource</span><span>${escapeHtml(block.room_or_resource_name)}</span></div>
        <div class="fact"><span>Base date / id</span><span>${escapeHtml(block.base_date)} / ${escapeHtml(block.base_appointmentDayId)}</span></div>
        <div class="fact"><span>First valid</span><span>${escapeHtml(block.first_valid_date)} / ${escapeHtml(block.first_valid_appointmentDayId)}</span></div>
        <div class="fact"><span>Last valid</span><span>${escapeHtml(block.last_valid_date)} / ${escapeHtml(block.last_valid_appointmentDayId)}</span></div>
        <div class="fact"><span>First invalid id</span><span>${escapeHtml(block.first_invalid_appointmentDayId)}</span></div>
        <div class="fact"><span>Days remaining</span><span>${escapeHtml(text(block.days_remaining_until_expiration))}</span></div>
        <div class="fact"><span>Public dependencies</span><span>${number(block.public_offering_dependency_count)}</span></div>
        <div class="fact"><span>Tags</span><span>${escapeHtml((block.tags || []).join(", "))}</span></div>
        <div class="fact"><span>Status</span><span>${escapeHtml(block.status)}</span></div>
        <div class="fact"><span>Notes</span><span>${escapeHtml(block.notes)}</span></div>
      </div>
    </article>
  `).join("");
  setHtml("appointment-list", groupRows + blockRows);
}

function renderInstructors(data) {
  const instructors = data.instructors || [];
  setHtml("instructor-grid", instructors.map(instructor => `
    <article class="panel">
      <div class="panel-header">
        <h3>${escapeHtml(instructor.instructor)}</h3>
        ${pill(`${number(instructor.public_offerings)} public`)}
      </div>
      <div class="facts">
        <div class="fact"><span>Availability blocks</span><span>${number(instructor.availability_blocks)}</span></div>
        <div class="fact"><span>Suppressed offerings</span><span>${number(instructor.suppressed_offerings)}</span></div>
        <div class="fact"><span>Anchor-required blocks</span><span>${number(instructor.anchor_required_blocks)}</span></div>
        <div class="fact"><span>Working hours exposed</span><span>${number(instructor.estimated_working_hours)}</span></div>
        <div class="fact"><span>Revenue potential</span><span>${escapeHtml(moneyDisplay(instructor.revenue))}</span></div>
        <div class="fact"><span>Preferred anchor style</span><span>${escapeHtml(instructor.preferred_anchor_style)}</span></div>
        <div class="fact"><span>Escalation tolerance</span><span>${escapeHtml(instructor.escalation_tolerance)}</span></div>
        <div class="fact"><span>Last paid</span><span>${escapeHtml(instructor.last_paid)}</span></div>
        <div class="fact"><span>Estimated due</span><span>${escapeHtml(instructor.estimated_due)}</span></div>
        <div class="fact"><span>Payment alert</span><span>${escapeHtml(instructor.payment_alert)}</span></div>
      </div>
      <p class="muted">${escapeHtml(instructor.notes || "No notes")}</p>
    </article>
  `).join(""));
}

function renderRules(data) {
  const rules = data.course_rules || [];
  const rows = rules.map(rule => `
    <tr>
      <td>${escapeHtml(rule.clean_course_name)}</td>
      <td>${escapeHtml(rule.course_id)}</td>
      <td>${escapeHtml(rule.course_family)}</td>
      <td>${escapeHtml(rule.duration_minutes)} min</td>
      <td>${escapeHtml(rule.occupancy_pool)}</td>
      <td>${escapeHtml(rule.escalation_tier)}</td>
      <td>${rule.anchor_eligible ? "yes" : "no"}</td>
      <td>${rule.post_anchor_eligible ? "yes" : "no"}</td>
      <td>${escapeHtml(rule.default_capacity)}</td>
      <td>${escapeHtml(rule.price || "unknown")}</td>
      <td>${(rule.warnings || []).length ? (rule.warnings || []).map(item => pill(item, "due")).join(" ") : pill("complete", "good")}</td>
    </tr>
  `).join("");
  setHtml("rules-table", `
    <table>
      <thead><tr><th>Course</th><th>ID</th><th>Family</th><th>Duration</th><th>Occupancy Pool</th><th>Tier</th><th>Anchor</th><th>Post Anchor</th><th>Capacity</th><th>Price</th><th>Warnings</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `);
}

function renderDebug(data) {
  const debug = data.debug || {};
  const rows = debug[state.debugDataset] || [];
  const needle = state.debugSearch.trim().toLowerCase();
  const filtered = needle ? rows.filter(row => JSON.stringify(row).toLowerCase().includes(needle)) : rows;
  const visible = filtered.slice(0, 250);
  setHtml("debug-table", `
    <table>
      <thead><tr><th>Date</th><th>Time</th><th>Instructor</th><th>Location</th><th>Course</th><th>Family</th><th>Pool</th><th>Tier</th><th>Container</th><th>Score</th><th>Status</th><th>Reasons</th><th>Registration URL</th></tr></thead>
      <tbody>${visible.map(row => `
        <tr>
          <td>${escapeHtml(row.date)}</td>
          <td>${escapeHtml(row.start_time)}-${escapeHtml(row.end_time)}</td>
          <td>${escapeHtml(row.instructor)}</td>
          <td>${escapeHtml(row.location)}</td>
          <td>${escapeHtml(row.course_name)}</td>
          <td>${escapeHtml(row.course_family)}</td>
          <td>${escapeHtml(row.occupancy_pool)}</td>
          <td>${escapeHtml(row.escalation_tier)}</td>
          <td>${escapeHtml(row.appointment_container_group || "")}<br>${escapeHtml(row.appointment_container_id || "")}</td>
          <td>${escapeHtml(row.score)}</td>
          <td>${escapeHtml(row.status)}</td>
          <td class="reason-cell">${escapeHtml((row.reasons || []).join(", "))}</td>
          <td class="url-cell">${row.registration_url ? `<a href="${escapeHtml(row.registration_url)}">${escapeHtml(row.registration_url)}</a>` : ""}</td>
        </tr>
      `).join("")}</tbody>
    </table>
    <div class="list-row">Showing ${number(visible.length)} of ${number(filtered.length)} matching rows.</div>
  `);
}

function renderAll() {
  const data = state.data;
  if (!data) return;
  renderSystem(data);
  renderRevenue(data);
  renderGeometry(data);
  renderRings(data);
  renderPools(data);
  renderAppointments(data);
  renderInstructors(data);
  renderRules(data);
  renderDebug(data);
}

async function loadData() {
  try {
    state.data = await fetchJson(DATA_URL);
    const warning = byId("load-warning");
    if (warning) warning.classList.add("hidden");
    renderAll();
  } catch (error) {
    showLoadWarning(`Could not load ${DATA_URL}. Run python scripts/build_inventory_control_center_data.py from the repository root, then serve the repo with a local static server. ${error.message}`);
  }
}

function setupTabs() {
  document.querySelectorAll("[data-tab]").forEach(button => {
    button.addEventListener("click", () => {
      document.querySelectorAll("[data-tab]").forEach(item => item.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach(panel => panel.classList.remove("active"));
      button.classList.add("active");
      const panel = byId(button.dataset.tab);
      if (panel) panel.classList.add("active");
    });
  });
}

function setupDebugControls() {
  const search = byId("debug-search");
  const dataset = byId("debug-dataset");
  if (search) {
    search.addEventListener("input", event => {
      state.debugSearch = event.target.value;
      renderDebug(state.data || {});
    });
  }
  if (dataset) {
    dataset.addEventListener("change", event => {
      state.debugDataset = event.target.value;
      renderDebug(state.data || {});
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupDebugControls();
  const refresh = byId("refresh-button");
  if (refresh) refresh.addEventListener("click", loadData);
  loadData();
});
