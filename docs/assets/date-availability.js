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
})();
