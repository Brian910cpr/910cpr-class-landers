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

  function installMaximSendLinkEmail() {
    if (!/^\/corp\/maxim(?:\.html)?$/.test(window.location.pathname)) return;
    if (typeof window.emailScheduleLink !== "function") return;

    const style = document.createElement("style");
    style.textContent = ".maxim-send-backdrop{position:fixed;inset:0;z-index:80;background:rgba(20,32,51,.5);display:none;place-items:center;padding:16px}.maxim-send-backdrop.open{display:grid}.maxim-send-card{width:min(520px,100%);background:var(--site-card-surface,#fff);color:var(--ink,#142033);border:1px solid var(--line,#d9e0e8);border-radius:14px;box-shadow:0 20px 55px rgba(20,32,51,.24);padding:18px}.maxim-send-card h2{margin:0 0 4px}.maxim-send-card p{margin:0 0 14px;color:var(--muted,#657083)}.maxim-send-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.maxim-send-grid label{font-size:11px;font-weight:700;color:var(--muted,#657083)}.maxim-send-grid input,.maxim-send-grid select{display:block;width:100%;margin-top:4px;padding:9px;border:1px solid var(--line,#d9e0e8);border-radius:8px;background:var(--site-card-surface,#fff);color:inherit}.maxim-send-grid .wide{grid-column:1/-1}.maxim-send-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:16px}.maxim-send-error{min-height:18px;margin-top:8px;color:var(--red,#b63b3b);font-size:12px}@media(max-width:560px){.maxim-send-grid{grid-template-columns:1fr}.maxim-send-grid .wide{grid-column:auto}}";
    document.head.appendChild(style);

    const backdrop = document.createElement("div");
    backdrop.className = "maxim-send-backdrop";
    backdrop.setAttribute("aria-hidden", "true");
    backdrop.innerHTML = '<section class="maxim-send-card" role="dialog" aria-modal="true" aria-labelledby="maximSendTitle"><h2 id="maximSendTitle">Confirm scheduling reminder</h2><p>Review the details before anything is sent.</p><div class="maxim-send-grid"><label class="wide">Send to<input id="maximSendTo" type="text" readonly></label><label>Course<select id="maximSendCourse"><option value="BLS">AHA BLS</option><option value="HS Total">Heartsaver Total</option></select></label><label>Billing code<select id="maximSendBilling"><option value="#031">Maxim #031</option><option value="#0852">MaximBH #0852</option><option value="#502">MaximDSP #502</option></select></label><label class="wide">Requested by (Maxim member)<input id="maximSendRequestedBy" type="text" autocomplete="name" placeholder="Name of Maxim staff member"></label></div><div class="maxim-send-error" id="maximSendError" role="alert"></div><div class="maxim-send-actions"><button type="button" class="btn" id="maximSendCancel">Cancel</button><button type="button" class="btn primary" id="maximSendConfirm">Confirm & Send</button></div></section>';
    document.body.appendChild(backdrop);

    const sendTo = backdrop.querySelector("#maximSendTo");
    const course = backdrop.querySelector("#maximSendCourse");
    const billing = backdrop.querySelector("#maximSendBilling");
    const requestedBy = backdrop.querySelector("#maximSendRequestedBy");
    const error = backdrop.querySelector("#maximSendError");
    const confirm = backdrop.querySelector("#maximSendConfirm");
    let pendingPerson = null;

    function closeModal() {
      pendingPerson = null;
      backdrop.classList.remove("open");
      backdrop.setAttribute("aria-hidden", "true");
      error.textContent = "";
    }

    backdrop.querySelector("#maximSendCancel").addEventListener("click", closeModal);
    backdrop.addEventListener("click", function (event) { if (event.target === backdrop) closeModal(); });

    window.emailScheduleLink = function (id) {
      const person = trainingFlow.find(function (item) { return item.id === id; });
      if (!person) return;
      if (!person.email) {
        alert("This employee does not have an email address.");
        return;
      }
      pendingPerson = person;
      sendTo.value = person.name + " <" + person.email + ">";
      course.value = String(person.course || "").includes("BLS") ? "BLS" : "HS Total";
      billing.value = ["#031", "#0852", "#502"].includes(person.billing) ? person.billing : "#031";
      requestedBy.value = "";
      error.textContent = "";
      backdrop.classList.add("open");
      backdrop.setAttribute("aria-hidden", "false");
      requestedBy.focus();
    };

    confirm.addEventListener("click", async function () {
      if (!pendingPerson) return;
      const requester = requestedBy.value.trim();
      if (!requester) {
        error.textContent = "Enter the Maxim member requesting this reminder.";
        requestedBy.focus();
        return;
      }
      confirm.disabled = true;
      error.textContent = "Sending...";
      const api = "https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/maxim-link-email";
      const response = await fetch(api, {
        method: "POST",
        headers: maximApiHeaders(),
        body: JSON.stringify({
          employeeId: pendingPerson.id,
          course: course.value,
          billingAccount: billing.value,
          requestedBy: requester
        })
      });
      const result = await response.json().catch(function () { return {}; });
      confirm.disabled = false;
      if (!response.ok) {
        error.textContent = result.error || "Could not send the scheduling reminder.";
        return;
      }
      pendingPerson.linkSentDate = result.linkSentDate;
      pendingPerson.stage = result.workflowStage;
      pendingPerson.course = result.course || course.value;
      pendingPerson.billing = result.billingAccount || billing.value;
      const sentEmail = pendingPerson.email;
      closeModal();
      renderTrainingFlow();
      alert("Scheduling reminder sent to " + sentEmail + ".");
    });
  }

  function installPageEnhancements() {
    installToggle();
    installMaximSendLinkEmail();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", installPageEnhancements, { once: true });
  else installPageEnhancements();

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