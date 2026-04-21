(function () {
  function activateTab(scope, trigger) {
    if (!scope || !trigger) return;
    const targetSelector = trigger.getAttribute("data-tab-target");
    if (!targetSelector) return;

    const panel = scope.querySelector(targetSelector);
    if (!panel) return;

    scope.querySelectorAll(".tab-btn, .slug-quick-pick").forEach((element) => {
      const sameTarget = element.getAttribute("data-tab-target") === targetSelector;
      element.classList.toggle("active", sameTarget);
    });
    scope.querySelectorAll(".tab-panel").forEach((element) => {
      element.classList.toggle("active", element === panel);
    });

    const program = trigger.getAttribute("data-program");
    const inputSelector = scope.getAttribute("data-sync-program");
    if (program && inputSelector) {
      const input = document.querySelector(inputSelector);
      if (input) input.value = program;
    }

    const bannerLink = scope.parentElement && scope.parentElement.querySelector("[data-full-schedule-link]");
    const bannerRaw = panel.getAttribute("data-banner");
    if (bannerLink && bannerRaw) {
      try {
        const data = JSON.parse(bannerRaw);
        if (data.url) bannerLink.setAttribute("href", data.url);
        if (data.label) bannerLink.textContent = data.label;
      } catch (error) {
        console.error(error);
      }
    }
  }

  function scopeForTrigger(trigger) {
    const explicitScope = trigger.getAttribute("data-tab-scope");
    if (explicitScope) return document.querySelector(explicitScope);
    return trigger.closest("[data-tabs]");
  }

  function bindTriggers() {
    document.querySelectorAll("[data-tab-target]").forEach((trigger) => {
      trigger.addEventListener("click", () => {
        activateTab(scopeForTrigger(trigger), trigger);
      });
    });
  }

  function activateProgramFromQuery() {
    const requestedProgram = new URLSearchParams(window.location.search).get("program");
    if (!requestedProgram) return;

    const target = Array.from(document.querySelectorAll("[data-program]")).find((button) => {
      return button.getAttribute("data-program") === requestedProgram;
    });
    if (!target) return;

    activateTab(scopeForTrigger(target), target);
  }

  function initializeScopes() {
    document.querySelectorAll("[data-tabs]").forEach((scope) => {
      const active = scope.querySelector(".tab-btn.active, .slug-quick-pick.active, .tab-panel.active");
      if (!active) {
        const fallback = scope.querySelector(".tab-btn, .slug-quick-pick");
        if (fallback) activateTab(scope, fallback);
        return;
      }

      if (active.matches(".tab-panel")) {
        const trigger = scope.querySelector(`[data-tab-target="#${active.id}"]`);
        if (trigger) activateTab(scope, trigger);
        return;
      }

      activateTab(scope, active);
    });
  }

  bindTriggers();
  initializeScopes();
  activateProgramFromQuery();
})();
