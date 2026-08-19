(function () {
  "use strict";

  const storageKey = "910cpr-color-theme";
  const root = document.documentElement;
  const media = window.matchMedia("(prefers-color-scheme: dark)");

  function installPageContrastFixes() {
    if (document.getElementById("site-theme-page-contrast")) return;
    const style = document.createElement("style");
    style.id = "site-theme-page-contrast";
    style.textContent = `
      /* Admin planner used hard-coded light cards. In dark mode that left
         near-white text on near-white calendar/event surfaces. */
      html[data-theme="dark"] body .month {
        background: #111a27 !important;
        border-color: #39495d !important;
      }
      html[data-theme="dark"] body .dow {
        color: #b9c6d5 !important;
      }
      html[data-theme="dark"] body .d {
        background: #172334 !important;
        color: #eef5fc !important;
        border-color: #53657a !important;
      }
      html[data-theme="dark"] body .d.empty {
        background: transparent !important;
        border-color: transparent !important;
      }
      html[data-theme="dark"] body .d.hasclass {
        background: #173550 !important;
        border-color: #4d8bb3 !important;
      }
      html[data-theme="dark"] body .d.today {
        outline-color: #8bd4ff !important;
      }
      html[data-theme="dark"] body .d.selected {
        outline-color: #ffffff !important;
      }
      html[data-theme="dark"] body .d .num,
      html[data-theme="dark"] body .d .tiny {
        color: #eef5fc !important;
      }

      html[data-theme="dark"] body .event {
        background: #172334 !important;
        color: #eef5fc !important;
        border-left-color: #69b9ee !important;
      }
      html[data-theme="dark"] body .event.class {
        background: #173550 !important;
        color: #f5f9fd !important;
        border-left-color: #69b9ee !important;
      }
      html[data-theme="dark"] body .event.gap {
        background: #3d321b !important;
        color: #fff4d6 !important;
        border-left-color: #e4ad43 !important;
      }
      html[data-theme="dark"] body .event.offer {
        background: #17392f !important;
        color: #e9fff4 !important;
        border-left-color: #58bf8a !important;
      }
      html[data-theme="dark"] body .event.block {
        background: #442326 !important;
        color: #ffe9ea !important;
        border-left-color: #e2777d !important;
      }
      html[data-theme="dark"] body .event.available {
        background: #302644 !important;
        color: #f3ecff !important;
        border-left-color: #ae8be0 !important;
      }
      html[data-theme="dark"] body .event .time {
        color: #ffffff !important;
      }
      html[data-theme="dark"] body .event small,
      html[data-theme="dark"] body .event .muted {
        color: #c7d4e2 !important;
      }
      html[data-theme="dark"] body .event.gap small,
      html[data-theme="dark"] body .event.gap .muted {
        color: #ead9ad !important;
      }
      html[data-theme="dark"] body .event.class small,
      html[data-theme="dark"] body .event.class .muted {
        color: #c5dded !important;
      }
    `;
    document.head.appendChild(style);
  }

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

  installPageContrastFixes();
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

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", installToggle, { once: true });
  else installToggle();

  media.addEventListener("change", function (event) {
    if (!savedTheme()) applyTheme(event.matches ? "dark" : "light");
  });
})();
