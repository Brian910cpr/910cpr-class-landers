(function () {
  function parseStart(value) {
    if (!value) {
      return null;
    }
    var date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  function removeExpiredItems(group) {
    var now = new Date();
    group.querySelectorAll(".js-session-item[data-session-start]").forEach(function (item) {
      var start = parseStart(item.getAttribute("data-session-start"));
      if (!start || start <= now) {
        item.remove();
      }
    });
  }

  function promoteCurtainItems(group) {
    var primaryGrid = group.querySelector(".session-grid:not(.extra)");
    var extraGrid = group.querySelector(".session-grid.extra");
    if (!primaryGrid || !extraGrid) {
      return;
    }

    while (primaryGrid.children.length < 8 && extraGrid.firstElementChild) {
      primaryGrid.appendChild(extraGrid.firstElementChild);
    }

    var curtain = extraGrid.closest(".session-curtain");
    if (curtain && !extraGrid.children.length) {
      curtain.remove();
    }
  }

  function hasVisibleItems(group) {
    return Boolean(group.querySelector(".js-session-item"));
  }

  function appendFallback(group) {
    if (group.querySelector(".js-live-session-empty")) {
      return;
    }

    var empty = document.createElement("div");
    empty.className = "js-live-session-empty";

    var message = document.createElement("p");
    message.textContent = "No upcoming times are currently listed.";
    empty.appendChild(message);

    var link = group.getAttribute("data-empty-link");
    if (link) {
      var footer = document.createElement("p");
      var anchor = document.createElement("a");
      anchor.className = "text-link strong-link";
      anchor.href = link;
      anchor.textContent = group.getAttribute("data-empty-link-label") || "See full schedule for this course";
      footer.appendChild(anchor);
      empty.appendChild(footer);
    }

    var targetGrid = group.querySelector(".upcoming-grid, .session-grid");
    var curtain = group.querySelector(".session-curtain");
    if (targetGrid) {
      targetGrid.remove();
    }
    if (curtain) {
      curtain.remove();
    }

    var footerRow = group.querySelector(".upcoming-footer-link, .full-schedule-row");
    if (footerRow) {
      footerRow.remove();
    }

    group.appendChild(empty);
  }

  function refreshLiveSessionGroups() {
    document.querySelectorAll(".js-live-session-group").forEach(function (group) {
      removeExpiredItems(group);
      promoteCurtainItems(group);
      if (!hasVisibleItems(group)) {
        appendFallback(group);
      }
    });
  }

  window.addEventListener("DOMContentLoaded", refreshLiveSessionGroups);
})();
