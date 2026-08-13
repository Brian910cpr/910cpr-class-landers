(function () {
  "use strict";
  const page = document.body;
  const base = {
    course_family: page.dataset.pageId?.split("-")[0] || "",
    availability_state: page.dataset.pageState || "",
    page_type: "date_availability"
  };
  function push(event, extra) {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(Object.assign({ event }, base, extra || {}));
  }
  document.addEventListener("click", function (event) {
    const link = event.target.closest("[data-event]");
    if (!link) return;
    const name = link.dataset.event;
    const registration = link.hasAttribute("data-registration");
    push(name, {
      is_anchor: link.dataset.anchor === "true",
      registration_type: registration ? (link.dataset.anchor === "true" ? "seated_class" : "appointment") : "",
      destination_host: link.href ? new URL(link.href, location.href).host : ""
    });
    if (registration) push("begin_registration", {
      is_anchor: link.dataset.anchor === "true",
      registration_type: link.dataset.anchor === "true" ? "seated_class" : "appointment"
    });
  });
  const courseFilter = document.getElementById("course-option-filter");
  if (courseFilter) {
    const choices = Array.from(document.querySelectorAll("[data-course-option]"));
    const empty = document.getElementById("course-filter-empty");
    const status = document.getElementById("course-filter-status");
    const applyCourseFilter = function (trackInteraction) {
      const selected = courseFilter.value;
      let shown = 0;
      choices.forEach(function (choice) {
        const visible = selected === "all" || choice.dataset.courseOption === selected;
        choice.hidden = !visible;
        if (visible) shown += 1;
      });
      document.querySelectorAll("[data-filter-group]").forEach(function (group) {
        group.hidden = !group.querySelector("[data-course-option]:not([hidden])");
      });
      if (empty) empty.hidden = shown !== 0;
      if (status) status.textContent = `${shown} available start ${shown === 1 ? "time" : "times"} shown`;
      if (trackInteraction) {
        push("filter_date_availability", {
          course_filter: selected === "all" ? "all" : courseFilter.options[courseFilter.selectedIndex].text,
          visible_start_times: shown
        });
      }
    };
    courseFilter.addEventListener("change", function () { applyCourseFilter(true); });
    applyCourseFilter(false);
  }
  document.getElementById("copy-diagnostics")?.addEventListener("click", async function () {
    const text = [
      `URL: ${location.href}`,
      `Page: ${page.dataset.pageId || ""}`,
      `State: ${page.dataset.pageState || ""}`,
      `Build: ${page.dataset.buildId || ""}`,
      "CSS: date-availability.css?v=20260725",
      "JS: date-availability.js?v=20260725"
    ].join("\n");
    await navigator.clipboard.writeText(text);
    this.textContent = "Diagnostics copied";
  });
})();
