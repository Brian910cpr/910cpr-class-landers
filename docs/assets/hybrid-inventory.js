(function () {
  function parsePayload(node) {
    if (!node) return null;
    const raw = node.getAttribute("data-flexible-availability");
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch (error) {
      console.error("Invalid flexible availability payload", error);
      return null;
    }
  }

  function cacheKey(payload) {
    return `hybrid-flex:${payload.locationId}:${payload.courseId}:${(payload.seedDates || []).join(",")}`;
  }

  function readCache(payload) {
    try {
      const raw = sessionStorage.getItem(cacheKey(payload));
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (!parsed || !parsed.savedAt || !Array.isArray(parsed.rows)) return null;
      const ageMs = Date.now() - parsed.savedAt;
      if (ageMs > (Number(payload.cacheSeconds || 180) * 1000)) return null;
      return parsed.rows;
    } catch (_error) {
      return null;
    }
  }

  function writeCache(payload, rows) {
    try {
      sessionStorage.setItem(cacheKey(payload), JSON.stringify({ savedAt: Date.now(), rows }));
    } catch (_error) {
      // Ignore storage issues and keep the live result.
    }
  }

  function formatTime(raw) {
    return String(raw || "").trim();
  }

  function renderRows(container, rows, appointmentPageUrl) {
    if (!container) return;
    if (!rows.length) {
      container.innerHTML = `
        <div class="slug-flexible-empty">
          <strong>No live flexible times were returned.</strong>
          <p>Use the open-seat page to review the latest live availability.</p>
          <a class="button secondary" href="${escapeHtml(appointmentPageUrl)}">View all available open seats</a>
        </div>
      `;
      container.hidden = false;
      return;
    }

    container.innerHTML = rows.map((row) => `
      <article class="slug-flex-row">
        <div class="slug-flex-row-copy">
          <div class="slug-flex-row-title">${escapeHtml(row.dateLabel || "Flexible time")}</div>
          <div class="slug-flex-row-meta">
            <span class="slug-pill-chip">${escapeHtml(formatTime(row.startTime))}</span>
            <span class="slug-pill-chip slug-pill-chip-format">Flexible time</span>
          </div>
        </div>
        <div class="slug-flex-row-actions">
          <a class="button small primary" href="${escapeHtml(row.enrollmentUrl)}">Register</a>
        </div>
      </article>
    `).join("");
    container.hidden = false;
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function extractRowsFromHtml(html, seedDate) {
    const doc = new DOMParser().parseFromString(`<div>${html}</div>`, "text/html");
    const anchors = Array.from(doc.querySelectorAll("a[href*='appointmentDayId=']"));
    return anchors.map((anchor) => {
      const href = anchor.getAttribute("href") || "";
      const matchDay = href.match(/appointmentDayId=(\d+)/);
      const matchTime = href.match(/startTime=([^&]+)/);
      const matchCourse = href.match(/courseId=(\d+)/);
      const dateLabel = seedDate ? formatSeedDate(seedDate) : "Flexible time";
      return {
        appointmentDayId: matchDay ? matchDay[1] : "",
        startTime: matchTime ? decodeURIComponent(matchTime[1].replace(/\+/g, " ")) : anchor.textContent.trim(),
        courseId: matchCourse ? matchCourse[1] : "",
        enrollmentUrl: href.startsWith("http") ? href : `https://coastalcprtraining.enrollware.com${href}`,
        dateLabel,
      };
    });
  }

  function formatSeedDate(seed) {
    const text = String(seed || "");
    if (!/^\d{6}$/.test(text)) return "Flexible time";
    const month = Number(text.slice(0, 2)) - 1;
    const day = Number(text.slice(2, 4));
    const year = 2000 + Number(text.slice(4, 6));
    const date = new Date(year, month, day);
    if (Number.isNaN(date.getTime())) return "Flexible time";
    return date.toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
    });
  }

  async function fetchSeedDate(payload, seedDate) {
    const response = await fetch(payload.endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json; charset=utf-8",
      },
      body: JSON.stringify({
        date: seedDate,
        locationId: payload.locationId,
        courseId: payload.courseId,
      }),
    });
    if (!response.ok) {
      throw new Error(`Flexible availability returned ${response.status}`);
    }
    const data = await response.json();
    return extractRowsFromHtml((data && data.d) || "", seedDate);
  }

  async function loadFlexibleAvailability(section) {
    const payload = parsePayload(section);
    if (!payload) return;

    const button = section.querySelector("[data-flexible-load]");
    const results = section.querySelector("[data-flexible-results]");
    const note = section.querySelector("[data-flexible-note]");
    if (!button || !results) return;

    const cached = readCache(payload);
    if (cached) {
      renderRows(results, cached, payload.appointmentPageUrl);
      if (note) {
        note.textContent = "Showing recently refreshed flexible times.";
      }
      return;
    }

    button.disabled = true;
    button.textContent = "Loading flexible times...";
    if (note) {
      note.textContent = "Checking live open-seat availability now.";
    }

    try {
      const seedDates = Array.isArray(payload.seedDates) ? payload.seedDates : [];
      const rowGroups = [];
      for (const seedDate of seedDates.slice(0, 5)) {
        // Stop early once we have enough useful rows for the public panel.
        const rows = await fetchSeedDate(payload, seedDate);
        rowGroups.push(...rows);
        if (rowGroups.length >= 8) {
          break;
        }
      }

      const deduped = [];
      const seen = new Set();
      rowGroups.forEach((row) => {
        const key = `${row.appointmentDayId}|${row.startTime}|${row.courseId}`;
        if (!key || seen.has(key)) return;
        seen.add(key);
        deduped.push(row);
      });

      writeCache(payload, deduped);
      renderRows(results, deduped, payload.appointmentPageUrl);
      if (note) {
        note.textContent = deduped.length
          ? "Live flexible times loaded from Enrollware."
          : "No live flexible times were returned for the nearby dates checked.";
      }
    } catch (_error) {
      if (note) {
        note.textContent = "Live flexible times could not be loaded here. Use the open-seat page for the latest availability.";
      }
      renderRows(results, [], payload.appointmentPageUrl);
    } finally {
      button.disabled = false;
      button.textContent = "Refresh flexible availability";
    }
  }

  function init() {
    document.querySelectorAll("[data-flexible-availability]").forEach((section) => {
      const button = section.querySelector("[data-flexible-load]");
      if (!button) return;
      button.addEventListener("click", function () {
        loadFlexibleAvailability(section);
      });
    });
  }

  window.addEventListener("DOMContentLoaded", init);
})();
