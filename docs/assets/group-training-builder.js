(function () {
  "use strict";

  var builder = document.querySelector("[data-training-day-builder]");
  var form = document.getElementById("training-day-form");
  if (!builder || !form) return;

  var trainingAliases = {
    "bls": "bls",
    "bls on site": "bls",
    "bls onsite": "bls",
    "first aid cpr aed": "first_aid_cpr_aed",
    "heartsaver": "first_aid_cpr_aed",
    "acls": "acls",
    "pals": "pals",
    "bloodborne pathogens": "bloodborne_pathogens",
    "bbp": "bloodborne_pathogens",
    "fire extinguisher": "fire_extinguisher"
  };

  function normalized(value) {
    return String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  }

  function field(name) {
    return form.elements.namedItem(name);
  }

  function value(name) {
    var control = field(name);
    return control ? String(control.value || "").trim() : "";
  }

  function radioValue(name) {
    var checked = form.querySelector('input[name="' + name + '"]:checked');
    return checked ? checked.value : "";
  }

  function selectedTraining() {
    return Array.prototype.map.call(form.querySelectorAll('input[name="training"]:checked'), function (checkbox) {
      var key = checkbox.value;
      var count = form.querySelector('[data-count-for="' + key + '"]');
      var delivery = form.querySelector('[data-delivery-for="' + key + '"]');
      return {
        training_key: key,
        label: checkbox.getAttribute("data-training-label") || key,
        participant_count: Number(count && count.value ? count.value : 0),
        delivery_preference: delivery ? delivery.value : "not_applicable"
      };
    });
  }

  function buildRequest() {
    return {
      schema_version: "training_day_request_v1",
      request_type: "group_training_day",
      organization: {
        name: value("organization_name"),
        team_type: value("team_type"),
        requirement_text: value("requirement_text")
      },
      training_items: selectedTraining(),
      location: {
        mode: radioValue("location_mode"),
        street_address: value("street_address"),
        city: value("city"),
        state: value("state"),
        postal_code: value("postal_code")
      },
      timing: {
        mode: radioValue("timing_mode"),
        preferred_windows: value("preferred_windows"),
        deadline: value("deadline"),
        operational_notes: value("operational_notes")
      },
      contact: {
        name: value("contact_name"),
        email: value("email"),
        mobile: value("mobile"),
        preferred_channel: value("preferred_channel")
      },
      evaluation_status: {
        travel: "pending",
        instructor_availability: "pending",
        duration: "pending",
        pricing: "pending",
        tentative_reservation: "not_offered"
      }
    };
  }

  function humanSummary(request) {
    var lines = [
      "910CPR training-day request",
      "",
      "Organization: " + (request.organization.name || "Not provided"),
      "Team type: " + (request.organization.team_type || "Not provided"),
      "Requirement: " + (request.organization.requirement_text || "Not provided"),
      "",
      "Training requested:"
    ];
    request.training_items.forEach(function (item) {
      lines.push("- " + item.participant_count + " × " + item.label + " (format: " + item.delivery_preference + ")");
    });
    lines.push(
      "",
      "Location mode: " + request.location.mode,
      "Address: " + [request.location.street_address, request.location.city, request.location.state, request.location.postal_code].filter(Boolean).join(", "),
      "Timing: " + request.timing.mode,
      "Preferred windows: " + (request.timing.preferred_windows || "Not provided"),
      "Deadline: " + (request.timing.deadline || "Not provided"),
      "Operational notes: " + (request.timing.operational_notes || "None"),
      "",
      "Contact: " + request.contact.name,
      "Email: " + request.contact.email,
      "Mobile: " + (request.contact.mobile || "Not provided"),
      "Preferred reply: " + request.contact.preferred_channel,
      "",
      "Structured request:",
      JSON.stringify(request, null, 2)
    );
    return lines.join("\n");
  }

  function renderSummary() {
    var request = buildRequest();
    window.landerwareTrainingDayRequest = request;
    var empty = builder.querySelector("[data-summary-empty]");
    var content = builder.querySelector("[data-summary-content]");
    var details = builder.querySelector("[data-summary-details]");
    var training = builder.querySelector("[data-summary-training]");
    var mobile = builder.querySelector("[data-mobile-summary]");
    var count = request.training_items.length;
    var assignments = request.training_items.reduce(function (total, item) { return total + item.participant_count; }, 0);

    empty.hidden = count > 0;
    content.hidden = count === 0;
    details.innerHTML = "<div><dt>Organization</dt><dd>" + escapeHtml(request.organization.name || "Not entered") + "</dd></div>" +
      "<div><dt>Team</dt><dd>" + escapeHtml(request.organization.team_type || "Not selected") + "</dd></div>" +
      "<div><dt>Location</dt><dd>" + escapeHtml(request.location.mode.replace(/_/g, " ")) + "</dd></div>" +
      "<div><dt>Timing</dt><dd>" + escapeHtml(request.timing.mode.replace(/_/g, " ")) + "</dd></div>";
    training.innerHTML = request.training_items.map(function (item) {
      return "<div><strong>" + escapeHtml(item.label) + "</strong><span>" + item.participant_count + " participant" + (item.participant_count === 1 ? "" : "s") + "</span></div>";
    }).join("");
    mobile.firstChild.nodeValue = count + " training" + (count === 1 ? "" : "s") + " · " + assignments + " participant assignment" + (assignments === 1 ? "" : "s") + " ";
  }

  function escapeHtml(value) {
    return String(value || "").replace(/[&<>'"]/g, function (character) {
      return {"&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"}[character];
    });
  }

  function setTrainingEnabled(checkbox) {
    var key = checkbox.value;
    var row = checkbox.closest("[data-training-row]");
    var controls = row.querySelectorAll("input[type=number], select");
    row.classList.toggle("selected", checkbox.checked);
    controls.forEach(function (control) {
      control.disabled = !checkbox.checked;
      if (checkbox.checked && control.type === "number" && !control.value) control.value = "1";
    });
  }

  function prefillFromQuery() {
    var params = new URLSearchParams(window.location.search);
    var program = normalized(params.get("program"));
    if (program) {
      var key = trainingAliases[program] || Object.keys(trainingAliases).find(function (alias) { return program.indexOf(alias) !== -1; });
      key = trainingAliases[key] || key;
      var checkbox = key ? form.querySelector('input[name="training"][value="' + key + '"]') : null;
      if (checkbox) {
        checkbox.checked = true;
        setTrainingEnabled(checkbox);
      } else {
        var other = form.querySelector('input[name="training"][value="other"]');
        other.checked = true;
        setTrainingEnabled(other);
        field("requirement_text").value = params.get("program") || "";
      }
    }
    if (params.get("location")) field("city").value = params.get("location");
    if (params.get("preferred_date") || params.get("preferred_time") || params.get("preferred_month")) {
      field("preferred_windows").value = [params.get("preferred_date"), params.get("preferred_time"), params.get("preferred_month")].filter(Boolean).join(" ");
    }
  }

  form.addEventListener("change", function (event) {
    if (event.target.matches('input[name="training"]')) setTrainingEnabled(event.target);
    renderSummary();
  });
  form.addEventListener("input", renderSummary);
  builder.querySelector("[data-jump-summary]").addEventListener("click", function () {
    builder.querySelector(".training-day-summary").scrollIntoView({behavior: "smooth", block: "start"});
  });
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    var request = buildRequest();
    var invalidTraining = request.training_items.length === 0 || request.training_items.some(function (item) { return item.participant_count < 1; });
    builder.querySelector("[data-training-error]").hidden = !invalidTraining;
    if (invalidTraining || !form.reportValidity()) return;
    window.landerwareTrainingDayRequest = request;
    if (window.dataLayer) window.dataLayer.push({event: "group_training_day_request", training_count: request.training_items.length, location_mode: request.location.mode, timing_mode: request.timing.mode, method: "email"});
    var subject = "Training day request - " + (request.organization.name || request.contact.name || "910CPR");
    window.location.href = "mailto:info@910cpr.com?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(humanSummary(request));
  });

  prefillFromQuery();
  renderSummary();
})();
