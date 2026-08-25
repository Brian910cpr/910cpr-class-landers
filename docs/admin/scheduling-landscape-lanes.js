(function () {
  "use strict";
  const DATA = "/data/admin/scheduling_landscape.json";
  const escapeHtml = (value) => String(value ?? "").replace(/[<>&"]/g, (char) => ({"<":"&lt;",">":"&gt;","&":"&amp;","\"":"&quot;"})[char]);
  const key = (date, time, lane) => `${date}|${time}|${lane}`;
  let model;
  let laneIndex = new Map();
  let hoverTimer;

  document.documentElement.dataset.theme = "light";
  document.documentElement.style.colorScheme = "light";

  function removeThemeToggle() {
    document.querySelectorAll(".site-theme-toggle").forEach((button) => button.remove());
    if (document.documentElement.dataset.theme !== "light") document.documentElement.dataset.theme = "light";
    document.documentElement.style.colorScheme = "light";
  }

  function installDelayedInspection() {
    const matrix = document.getElementById("matrix");
    matrix.addEventListener("pointerover", (event) => {
      const cell = event.target.closest(".cell,.lane-cell");
      if (!cell || cell.contains(event.relatedTarget)) return;
      clearTimeout(hoverTimer);
      hoverTimer = setTimeout(() => cell.click(), 650);
    });
    matrix.addEventListener("pointerout", (event) => {
      const cell = event.target.closest(".cell,.lane-cell");
      if (!cell || cell.contains(event.relatedTarget)) return;
      clearTimeout(hoverTimer);
    });
    matrix.addEventListener("click", () => clearTimeout(hoverTimer));
  }

  function installDayKeyboardNavigation() {
    document.addEventListener("keydown", (event) => {
      if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
      const tag = document.activeElement?.tagName;
      if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") return;
      const buttonId = event.key === "ArrowLeft" ? "prevDay" : event.key === "ArrowRight" ? "nextDay" : "";
      if (!buttonId) return;
      event.preventDefault();
      document.getElementById(buttonId)?.click();
    });
  }

  function fitFullDayToViewport() {
    const matrix = document.getElementById("matrix");
    const wrap = document.getElementById("wrap");
    const rowCount = matrix.tBodies[0]?.rows.length || 96;
    const headerHeight = matrix.tHead?.getBoundingClientRect().height || 88;
    const viewportHeight = window.visualViewport?.height || document.documentElement.clientHeight;
    const availableHeight = Math.max(240, viewportHeight - wrap.getBoundingClientRect().top - 2);
    const rowHeight = Math.max(2, (availableHeight - headerHeight) / rowCount);
    const root = document.documentElement.style;
    root.setProperty("--slot-h", `${rowHeight}px`);
    root.setProperty("--hour-font", `${Math.min(8, rowHeight)}px`);
  }

  function installViewportFitting() {
    let resizeFrame;
    const fitSoon = () => {
      cancelAnimationFrame(resizeFrame);
      resizeFrame = requestAnimationFrame(fitFullDayToViewport);
    };
    window.addEventListener("resize", fitSoon, {passive: true});
    window.visualViewport?.addEventListener("resize", fitSoon, {passive: true});
    new ResizeObserver(fitSoon).observe(document.querySelector(".topbar"));
    new MutationObserver(fitSoon).observe(document.getElementById("matrix"), {childList: true});
    fitSoon();
  }

  function showLane(cell, lane, time) {
    const drawer = document.getElementById("drawer");
    const items = Array.isArray(cell?.items) ? cell.items : [];
    document.getElementById("drawerTitle").textContent = `${time} · ${lane.label}`;
    document.getElementById("drawerBody").innerHTML = `<dl class="meta"><dt>Date</dt><dd>${escapeHtml(document.getElementById("datePick").value)}</dd><dt>Lane</dt><dd>${escapeHtml(lane.label)}</dd><dt>Status</dt><dd><b>${escapeHtml(cell?.result || "clear")}</b></dd><dt>Source</dt><dd>${escapeHtml(cell?.sourceLabel || "—")}</dd></dl>${items.length ? `<h3>Source records</h3><ul class="reasons">${items.map((item) => `<li>${escapeHtml(item.courseName || item.title || "Record")} · ${escapeHtml(item.start || "")}–${escapeHtml(item.end || "")}${item.sessionId ? ` · session ${escapeHtml(item.sessionId)}` : ""}</li>`).join("")}</ul>` : "<p>No source record overlaps this time.</p>"}`;
    drawer.classList.add("open");
    drawer.setAttribute("aria-hidden", "false");
  }

  function addLanes() {
    if (!model) return;
    const matrix = document.getElementById("matrix");
    const header = matrix.querySelector("thead tr");
    if (!header || header.querySelector(".lane-head")) return;
    const lanes = model.lanes || [];
    const date = document.getElementById("datePick").value;
    let insertionPoint = header.querySelector(".time-head");
    lanes.forEach((lane, index) => {
      const th = document.createElement("th");
      th.className = `lane-head ${index === lanes.length - 1 ? "lane-divider" : ""}`;
      th.innerHTML = `<div title="${escapeHtml(lane.description || lane.label)}">${escapeHtml(lane.label)}</div>`;
      insertionPoint.after(th);
      insertionPoint = th;
    });
    matrix.querySelectorAll("tbody tr").forEach((row) => {
      const time = row.querySelector(".cell")?.dataset.time;
      if (!time) return;
      let cellPoint = row.querySelector(".time");
      lanes.forEach((lane, index) => {
        const record = laneIndex.get(key(date, time, lane.laneId));
        const td = document.createElement("td");
        td.className = `lane-cell ${record?.result || "none"} ${index === lanes.length - 1 ? "lane-divider" : ""}`;
        td.title = `${lane.label}: ${record?.sourceLabel || record?.result || "clear"}`;
        td.addEventListener("click", () => showLane(record, lane, time));
        cellPoint.after(td);
        cellPoint = td;
      });
    });
  }

  fetch(DATA, {cache: "no-store"}).then((response) => response.json()).then((payload) => {
    model = payload;
    laneIndex = new Map((model.laneCells || []).map((cell) => [key(cell.date, cell.startTime, cell.laneId), cell]));
    const matrix = document.getElementById("matrix");
    new MutationObserver(addLanes).observe(matrix, {childList: true});
    new MutationObserver(removeThemeToggle).observe(document.body, {childList: true, subtree: true});
    new MutationObserver(removeThemeToggle).observe(document.documentElement, {attributes: true, attributeFilter: ["data-theme"]});
    installDelayedInspection();
    installDayKeyboardNavigation();
    installViewportFitting();
    removeThemeToggle();
    addLanes();
  }).catch((error) => console.error("Operational landscape lanes unavailable", error));
})();
