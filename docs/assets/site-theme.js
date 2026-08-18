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
