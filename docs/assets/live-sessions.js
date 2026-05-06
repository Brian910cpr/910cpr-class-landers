(function () {
  function parseStart(value) {
    if (!value) {
      return null;
    }
    var date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  function inferStartFromMarkup(item) {
    if (!item) {
      return null;
    }

    var existing = parseStart(item.getAttribute("data-session-start"));
    if (existing) {
      return existing;
    }

    var dateNode = item.querySelector(".upcoming-date");
    var timeNode = item.querySelector(".upcoming-time");
    if (dateNode && timeNode) {
      var parsed = parseStart(dateNode.textContent.trim() + " " + timeNode.textContent.trim());
      if (parsed) {
        item.setAttribute("data-session-start", parsed.toISOString());
        return parsed;
      }
    }

    return null;
  }

  function removeExpiredItems(group) {
    var now = new Date();
    group.querySelectorAll(".js-session-item[data-session-start], .js-session-item:not([data-session-start])").forEach(function (item) {
      var start = inferStartFromMarkup(item);
      if (start && start < now) {
        item.remove();
      }
    });
  }

  function removeEmptyDayCards(group) {
    group.querySelectorAll(".slug-day-card").forEach(function (card) {
      if (!card.querySelector(".slug-time-row") && !card.querySelector(".js-session-item")) {
        card.remove();
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
    return Boolean(group.querySelector(".js-session-item, .slug-time-row, .slug-day-card"));
  }

  function appendFallback(group) {
    if (group.querySelector(".js-live-session-empty")) {
      return;
    }

    var empty = document.createElement("div");
    empty.className = "js-live-session-empty";

    var message = document.createElement("p");
    message.textContent = "No selected class times are showing here.";
    empty.appendChild(message);

    var link = group.getAttribute("data-empty-link");
    if (link) {
      var footer = document.createElement("p");
      var anchor = document.createElement("a");
      anchor.className = "text-link strong-link";
      anchor.href = link;
      anchor.textContent = group.getAttribute("data-empty-link-label") || "See upcoming classes";
      footer.appendChild(anchor);
      empty.appendChild(footer);
    }

    var fullSchedule = group.getAttribute("data-full-schedule-link");
    if (fullSchedule) {
      var scheduleFooter = document.createElement("p");
      var scheduleAnchor = document.createElement("a");
      scheduleAnchor.className = "text-link";
      scheduleAnchor.href = fullSchedule;
      scheduleAnchor.textContent = "See all 910CPR classes";
      scheduleFooter.appendChild(scheduleAnchor);
      empty.appendChild(scheduleFooter);
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
      removeEmptyDayCards(group);
      promoteCurtainItems(group);
      if (!hasVisibleItems(group)) {
        appendFallback(group);
      }
    });
  }

  window.pruneExpiredSessions = window.pruneExpiredSessions || refreshLiveSessionGroups;
  window.addEventListener("DOMContentLoaded", refreshLiveSessionGroups);
})();
