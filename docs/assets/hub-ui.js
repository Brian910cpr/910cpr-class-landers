(function () {
  function activateTab(scope, trigger) {
    if (!scope || !trigger) return;

    const targetSelector = trigger.getAttribute("data-tab-target");
    if (!targetSelector) return;

    const targetPanel = scope.querySelector(targetSelector);
    if (!targetPanel) return;

    scope.querySelectorAll(".tab-btn, .slug-quick-pick").forEach(function (button) {
      button.classList.toggle("active", button === trigger);
    });

    const groupProgram = trigger.getAttribute("data-program") || "";

    scope.querySelectorAll(".tab-btn").forEach(function (button) {
      if (button === trigger) {
        return;
      }
      if (button.getAttribute("data-tab-target") === targetSelector) {
        button.classList.add("active");
      } else {
        button.classList.remove("active");
      }
    });

    scope.querySelectorAll(".slug-quick-pick").forEach(function (button) {
      if (button === trigger) {
        return;
      }
      if (button.getAttribute("data-tab-target") === targetSelector) {
        button.classList.add("active");
      } else {
        button.classList.remove("active");
      }
    });

    scope.querySelectorAll(".tab-panel").forEach(function (panel) {
      panel.classList.toggle("active", panel === targetPanel);
    });

    const bannerData = targetPanel.getAttribute("data-banner");
    if (bannerData) {
      try {
        const parsed = JSON.parse(bannerData);
        scope.parentElement.querySelectorAll("[data-full-schedule-link]").forEach(function (link) {
          if (parsed.url) {
            link.setAttribute("href", parsed.url);
          }
          if (parsed.label) {
            link.textContent = parsed.label;
          }
        });
      } catch (error) {
        console.warn("Unable to parse banner data", error);
      }
    }

    const syncSelector = scope.getAttribute("data-sync-program");
    if (syncSelector && groupProgram) {
      const input = document.querySelector(syncSelector);
      if (input) {
        input.value = groupProgram;
      }
    }
  }

  function scopeForTrigger(trigger) {
    const explicitScope = trigger.getAttribute("data-tab-scope");
    if (explicitScope) {
      return document.querySelector(explicitScope);
    }
    return trigger.closest("[data-tabs]");
  }

  function bindTriggers() {
    document.querySelectorAll("[data-tab-target]").forEach(function (trigger) {
      trigger.addEventListener("click", function () {
        activateTab(scopeForTrigger(trigger), trigger);
      });
    });
  }

  function activateProgramFromQuery() {
    const params = new URLSearchParams(window.location.search);
    const requestedProgram = params.get("program");
    if (!requestedProgram) return;

    const trigger = Array.from(document.querySelectorAll("[data-program]")).find(function (button) {
      return button.getAttribute("data-program") === requestedProgram;
    });

    if (!trigger) return;
    activateTab(scopeForTrigger(trigger), trigger);
  }

  function initializeScopes() {
    document.querySelectorAll("[data-tabs]").forEach(function (scope) {
      const activeTrigger = scope.querySelector(".tab-btn.active, .slug-quick-pick.active, .tab-btn, .slug-quick-pick");
      if (activeTrigger) {
        activateTab(scopeForTrigger(activeTrigger), activeTrigger);
      }
    });
  }

  window.addEventListener("DOMContentLoaded", function () {
    bindTriggers();
    initializeScopes();
    activateProgramFromQuery();
  });
})();
