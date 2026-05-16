(function () {
  const AUDIT_URL = "../../../debug/class_mapping_tree_audit.json";

  const stateEl = document.getElementById("load-state");
  const statusEl = document.getElementById("overall-status");
  const summaryEl = document.getElementById("summary-cards");
  const warningsEl = document.getElementById("warnings-list");
  const warningCountEl = document.getElementById("warning-count");
  const treeEl = document.getElementById("tree-root");
  const comparisonEl = document.getElementById("comparison-table");
  const missingEl = document.getElementById("missing-sessions");

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function statusClass(status) {
    const normalized = String(status || "none").toLowerCase();
    if (["healthy", "warning", "broken", "opportunity", "inactive"].includes(normalized)) return normalized;
    return "warning";
  }

  function statusPill(status) {
    const label = status || "unknown";
    return `<span class="pill ${statusClass(label)}">${escapeHtml(label)}</span>`;
  }

  function metric(label, value) {
    return `<div class="metric-card"><span class="label">${escapeHtml(label)}</span><span class="value">${escapeHtml(value)}</span></div>`;
  }

  function renderSummary(audit) {
    const totals = audit.totals || {};
    summaryEl.innerHTML = [
      metric("Last Audit", audit.generated_at ? new Date(audit.generated_at).toLocaleString() : "unknown"),
      metric("Future Sessions", totals.future_sessions_total || 0),
      metric("Hub Visible", totals.hub_visible_unique_sessions || 0),
      metric("Hidden / Not Surfaced", totals.hidden_or_not_surfaced_sessions || 0),
      metric("Orphan Hub IDs", totals.orphan_hub_session_ids || 0),
      metric("Duplicate IDs", totals.duplicate_session_ids || 0)
    ].join("");
    statusEl.className = `status ${statusClass(audit.overall_status)}`;
    statusEl.textContent = audit.overall_status || "unknown";
  }

  function renderWarnings(audit) {
    const warnings = audit.warnings || [];
    warningCountEl.textContent = String(warnings.length);
    warningCountEl.className = `status ${warnings.length ? "warning" : "normal"}`;
    warningsEl.innerHTML = warnings.length
      ? warnings.map((warning) => `<div class="warning-item">${escapeHtml(warning)}</div>`).join("")
      : `<div class="muted">No warnings recorded in the latest audit.</div>`;
  }

  function renderTree(audit) {
    const tree = audit.tree || {};
    treeEl.innerHTML = Object.entries(tree).map(([category, node]) => {
      const children = Object.entries(node.children || {})
        .map(([name, count]) => `<div class="tree-child"><span>${escapeHtml(name)}</span><strong>${escapeHtml(count)}</strong></div>`)
        .join("");
      return `
        <details class="tree-node" open>
          <summary class="tree-toggle">
            <span class="tree-title">${escapeHtml(category)} ${statusPill(node.status)}</span>
            <span>${escapeHtml(node.count || 0)} future / ${escapeHtml(node.hub_visible_count || 0)} hub</span>
          </summary>
          <div class="tree-children">${children || `<div class="muted-small">No subtype rows.</div>`}</div>
        </details>
      `;
    }).join("");
  }

  function renderComparison(audit) {
    const rows = audit.categories || [];
    comparisonEl.innerHTML = `
      <table class="mapping-table">
        <thead>
          <tr>
            <th>Category</th>
            <th>Future</th>
            <th>Homepage Preview</th>
            <th>Hub Visible</th>
            <th>Minimum</th>
            <th>Status</th>
            <th>Hub</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map((row) => `
            <tr>
              <td>${escapeHtml(row.category)}</td>
              <td>${escapeHtml(row.future_sessions_total)}</td>
              <td>${escapeHtml(row.homepage_preview_count)}</td>
              <td>${escapeHtml(row.hub_visible_count)}</td>
              <td>${escapeHtml(row.expected_minimum || "")}</td>
              <td>${statusPill(row.status)}</td>
              <td>${row.hub_path ? `<span class="muted-small">${escapeHtml(row.hub_path)}</span>` : ""}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  function renderMissing(audit) {
    const rows = audit.missing_inventory_analysis || [];
    missingEl.innerHTML = rows.length ? `
      <table class="mapping-table">
        <thead>
          <tr>
            <th>Session</th>
            <th>Category</th>
            <th>Course</th>
            <th>Start</th>
            <th>Expected Hub</th>
            <th>Reason</th>
          </tr>
        </thead>
        <tbody>
          ${rows.slice(0, 50).map((row) => `
            <tr>
              <td>${escapeHtml(row.session_id)}</td>
              <td>${escapeHtml(row.category)}<div class="muted-small">${escapeHtml(row.subtype || "")}</div></td>
              <td>${escapeHtml(row.course_name)}</td>
              <td>${escapeHtml(row.start_at || "")}</td>
              <td>${escapeHtml(row.expected_hub || "")}</td>
              <td>${escapeHtml(row.reason)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    ` : `<div class="muted">No missing inventory samples recorded.</div>`;
  }

  function renderAudit(audit) {
    stateEl.classList.add("hidden");
    renderSummary(audit);
    renderWarnings(audit);
    renderTree(audit);
    renderComparison(audit);
    renderMissing(audit);
  }

  fetch(AUDIT_URL, { cache: "no-store" })
    .then((response) => {
      if (!response.ok) throw new Error(`Audit file not found: ${AUDIT_URL}`);
      return response.json();
    })
    .then(renderAudit)
    .catch((error) => {
      stateEl.classList.remove("hidden");
      stateEl.textContent = `${error.message}. Run python scripts/audit_class_mapping_tree.py.`;
      statusEl.className = "status broken";
      statusEl.textContent = "missing audit";
    });
}());
