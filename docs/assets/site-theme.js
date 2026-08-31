(function () {
  "use strict";

  const storageKey = "910cpr-color-theme";
  const root = document.documentElement;
  const media = window.matchMedia("(prefers-color-scheme: dark)");

  function savedTheme() {
    try {
      const value = localStorage.getItem(storageKey);
      return value === "dark" || value === "light" ? value : null;
    } catch (_) {
      return null;
    }
  }

  function applyTheme(theme) {
    root.dataset.theme = theme;
    root.style.colorScheme = theme;
    document.querySelectorAll(".site-theme-toggle").forEach(function (button) {
      const nextTheme = theme === "dark" ? "light" : "dark";
      button.setAttribute("aria-label", "Use " + nextTheme + " mode");
      button.setAttribute("aria-pressed", String(theme === "dark"));
      button.querySelector(".site-theme-toggle-icon").textContent = theme === "dark" ? "☀" : "☾";
      button.querySelector(".site-theme-toggle-label").textContent = theme === "dark" ? "Light" : "Dark";
    });
  }

  function loadStylesheet(href) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }

  function loadPageThemeOverrides() {
    if (location.pathname === "/admin/dashboard.html") {
      loadStylesheet("/assets/admin-dashboard-theme.css?v=20260819.1");
    }

    if (location.pathname === "/corp/maxim" || location.pathname === "/corp/maxim.html") {
      loadStylesheet("/assets/maxim-theme.css?v=20260819.1");
    }
  }

  function suppressUnavailablePublicSessions() {
    const suppressedSessionIds = ["13973422"];
    suppressedSessionIds.forEach(function (sessionId) {
      document.querySelectorAll('a[href*="' + sessionId + '"]').forEach(function (link) {
        const container = link.closest(".class-finder-card, .course-session-row, article, li, .course, .session-card, .class-card");
        if (container) container.hidden = true;
        else link.hidden = true;
      });
    });
  }

  function minutesBetween(startDate, startTime, endDate, endTime) {
    if (!startDate || !startTime || !endDate || !endTime) return null;
    const start = new Date(startDate + "T" + startTime + ":00");
    const end = new Date(endDate + "T" + endTime + ":00");
    const minutes = Math.round((end.getTime() - start.getTime()) / 60000);
    return Number.isFinite(minutes) && minutes >= 0 ? minutes : null;
  }

  function formatMinutes(total) {
    if (total == null) return "";
    const hours = Math.floor(total / 60);
    const minutes = total % 60;
    if (!minutes) return hours + "h";
    if (!hours) return minutes + "m";
    return hours + "h " + minutes + "m";
  }

  function installSessionTimingControls() {
    if (location.pathname !== "/admin/instructor-session.html") return;
    const create = document.getElementById("create");
    if (!create || create.querySelector("[data-landerware-end-time]")) return;
    const fields = Array.from(create.querySelectorAll(".field"));
    const dateField = fields.find(function (field) { return field.querySelector('input[type="date"]'); });
    const startField = fields.find(function (field) { return field.querySelector('input[type="time"]'); });
    if (!dateField || !startField) return;
    const startDate = dateField.querySelector('input[type="date"]');
    const startTime = startField.querySelector('input[type="time"]');

    const endTimeField = document.createElement("div");
    endTimeField.className = "field";
    endTimeField.dataset.landerwareEndTime = "1";
    endTimeField.innerHTML = '<label>End time</label><input type="time" data-session-end-time>';
    startField.insertAdjacentElement("afterend", endTimeField);

    const overnightField = document.createElement("div");
    overnightField.className = "field";
    overnightField.innerHTML = '<label style="display:flex;align-items:center;gap:7px;margin-top:22px"><input type="checkbox" data-session-other-end-date style="width:auto"> Ends on a different date</label>';
    endTimeField.insertAdjacentElement("afterend", overnightField);

    const endDateField = document.createElement("div");
    endDateField.className = "field";
    endDateField.hidden = true;
    endDateField.innerHTML = '<label>End date</label><input type="date" data-session-end-date>';
    overnightField.insertAdjacentElement("afterend", endDateField);

    const duration = document.createElement("div");
    duration.style.cssText = "font-size:12px;font-weight:800;align-self:end;padding:9px 0";
    duration.setAttribute("aria-label", "Scheduled class length");
    duration.dataset.sessionDurationPreview = "1";
    endDateField.insertAdjacentElement("afterend", duration);

    const endTime = endTimeField.querySelector("input");
    const differentDate = overnightField.querySelector("input");
    const endDate = endDateField.querySelector("input");

    function syncDates() {
      if (!differentDate.checked) {
        endDate.value = startDate.value;
        endDateField.hidden = true;
      } else {
        endDateField.hidden = false;
        if (!endDate.value && startDate.value) endDate.value = startDate.value;
      }
      const minutes = minutesBetween(startDate.value, startTime.value, endDate.value || startDate.value, endTime.value);
      duration.textContent = minutes == null ? "" : formatMinutes(minutes);
    }

    differentDate.addEventListener("change", syncDates);
    [startDate, startTime, endTime, endDate].forEach(function (input) { input.addEventListener("input", syncDates); });
    syncDates();
  }

  function installDurationCues() {
    document.querySelectorAll("[data-session-duration-minutes]").forEach(function (host) {
      if (host.querySelector(".landerware-duration-cue")) return;
      const scheduled = Number(host.dataset.sessionDurationMinutes);
      const advertised = Number(host.dataset.advertisedDurationMinutes);
      if (!Number.isFinite(scheduled)) return;
      const cue = document.createElement("span");
      cue.className = "landerware-duration-cue";
      cue.textContent = formatMinutes(scheduled);
      cue.style.cssText = "margin-left:6px;font-size:11px;font-weight:800;white-space:nowrap";
      if (Number.isFinite(advertised) && scheduled < advertised) cue.style.color = "#b33a3a";
      host.appendChild(cue);
    });
  }

  loadPageThemeOverrides();
  applyTheme(savedTheme() || (media.matches ? "dark" : "light"));

  function installToggle() {
    if (document.querySelector(".site-theme-toggle")) return;

    const button = document.createElement("button");
    button.type = "button";
    button.className = "site-theme-toggle";
    button.innerHTML = '<span class="site-theme-toggle-icon" aria-hidden="true"></span><span class="site-theme-toggle-label"></span>';
    button.addEventListener("click", function () {
      const theme = root.dataset.theme === "dark" ? "light" : "dark";
      try { localStorage.setItem(storageKey, theme); } catch (_) { /* Preference remains active for this page. */ }
      applyTheme(theme);
    });

    const phone = document.querySelector('a[href^="tel:"]');
    if (phone && phone.parentNode) {
      phone.insertAdjacentElement("afterend", button);
    } else {
      const header = document.querySelector("header, .site-brand-bar, .selector-brand-bar");
      if (header) header.appendChild(button);
      else {
        button.classList.add("site-theme-fallback");
        document.body.appendChild(button);
      }
    }
    applyTheme(root.dataset.theme);
  }

  function installPageBehavior() {
    installToggle();
    suppressUnavailablePublicSessions();
    installSessionTimingControls();
    installDurationCues();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", installPageBehavior, { once: true });
  else installPageBehavior();

  media.addEventListener("change", function (event) {
    if (!savedTheme()) applyTheme(event.matches ? "dark" : "light");
  });

  if (location.pathname.startsWith("/corp/nhcso")) {
    const script = document.createElement("script");
    script.src = "/corp/nhcso/compact-rail.js?v=20260819.1";
    script.defer = true;
    document.head.appendChild(script);
  }
})();