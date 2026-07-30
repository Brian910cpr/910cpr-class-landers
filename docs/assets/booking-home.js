(function () {
  const sectionsRoot = document.querySelector("[data-home-sections]");
  if (!sectionsRoot) return;

  const COURSES = [
    {
      title: "AHA BLS",
      href: "/bls.html",
      image: "/images/bls_general.png",
    },
    {
      title: "AHA ACLS",
      href: "/acls.html",
      image: "/images/acls_general.png",
    },
    {
      title: "AHA PALS",
      href: "/pals.html",
      image: "/images/pals_general.png",
    },
    {
      title: "AHA Heartsaver First Aid CPR AED",
      href: "/heartsaver.html#first-aid-cpr-aed",
      image: "/images/heartsaver_general.png",
    },
    {
      title: "AHA Heartsaver CPR AED",
      href: "/heartsaver.html#cpr-aed",
      image: "/images/HS-FA-CPR-AED.jpeg",
    },
    {
      title: "ARC Programs",
      subtitle: "BLS and First Aid/CPR/AED",
      href: "/arc.html",
      image: "/images/0arc.png",
    },
    {
      title: "HSI Programs",
      subtitle: "BLS and First Aid/CPR/AED",
      href: "/hsi.html",
      image: "/images/0hsi.png",
    },
    {
      title: "USCG / Maritime",
      href: "/courses/uscg-first-aid-cpr-aed.html",
      image: "/images/maritime-first-aid.svg",
    },
    {
      title: "Family & Friends CPR",
      href: "/family-cpr.html",
      image: "/images/FF-CPR-2.jpg",
    },
  ];

  function renderCourseTile(course) {
    return `
      <a class="home-course-tile" href="${escapeAttribute(course.href)}">
        <img src="${escapeAttribute(course.image)}" alt="" loading="lazy" onerror="this.hidden=true">
        <span class="home-course-tile-copy">
          <strong>${escapeHtml(course.title)}</strong>
          ${course.subtitle ? `<span>${escapeHtml(course.subtitle)}</span>` : ""}
        </span>
      </a>
    `;
  }

  sectionsRoot.innerHTML = `
    <div class="home-course-grid" aria-label="Choose a course">
      ${COURSES.map(renderCourseTile).join("")}
    </div>
    <section class="home-help-panel" aria-label="Help choosing a class">
      <div>
        <h3>Need help choosing the right class?</h3>
        <p>If you have exact wording from an employer, school, clinical program, or licensing board, use it. We’ll help first-time students and experienced providers reach the correct credential without oversimplifying the requirement.</p>
      </div>
      <div class="home-help-actions">
        <button class="button primary" type="button" data-course-chooser-toggle aria-expanded="false" aria-controls="guided-course-chooser">Help Me Choose the Right Class</button>
        <a class="button secondary" href="/group-training.html">Training for a group or workplace</a>
        <a class="button secondary" href="tel:9103955193">Call 910-395-5193</a>
      </div>
      <div class="home-course-chooser" id="guided-course-chooser" hidden tabindex="-1">
        <div class="home-course-chooser-grid">
          <section class="home-course-choice-group" aria-labelledby="chooser-healthcare">
            <h4 id="chooser-healthcare">Healthcare job or school</h4>
            <div class="home-choice-links">
              <a href="/bls.html">BLS</a>
              <a href="/acls.html">ACLS</a>
              <a href="/pals.html">PALS</a>
              <a href="/hsi.html#bls">HSI BLS</a>
            </div>
          </section>
          <section class="home-course-choice-group" aria-labelledby="chooser-workplace">
            <h4 id="chooser-workplace">Workplace, childcare, or safety requirement</h4>
            <div class="home-choice-links">
              <a href="/heartsaver.html#first-aid-cpr-aed">First Aid + CPR/AED</a>
              <a href="/heartsaver.html#cpr-aed">CPR/AED</a>
              <a href="/heartsaver.html#pediatric-first-aid-cpr-aed">Pediatric First Aid + CPR/AED</a>
            </div>
          </section>
          <section class="home-course-choice-group" aria-labelledby="chooser-family">
            <h4 id="chooser-family">Family or personal preparedness</h4>
            <div class="home-choice-links">
              <a href="/family-cpr.html">Family &amp; Friends CPR</a>
            </div>
          </section>
          <section class="home-course-choice-group" aria-labelledby="chooser-help">
            <h4 id="chooser-help">I still need help</h4>
            <div class="home-choice-links">
              <a href="tel:9103955193">Call 910CPR</a>
            </div>
          </section>
        </div>
        <section class="home-exact-wording" aria-labelledby="chooser-exact-wording">
          <h4 id="chooser-exact-wording">My employer or school gave me exact wording</h4>
          <label for="course-requirement-text">Paste the exact requirement here.</label>
          <textarea id="course-requirement-text" rows="3" maxlength="5000" data-course-requirement-text></textarea>
          <div class="home-requirement-contact">
            <label>Your name (optional)<input type="text" maxlength="120" autocomplete="name" data-requirement-name></label>
            <label>Email<input type="email" maxlength="254" autocomplete="email" data-requirement-email></label>
            <label>Phone<input type="tel" maxlength="40" autocomplete="tel" data-requirement-phone></label>
          </div>
          <p class="home-requirement-note">Enter an email or phone so we can follow up.</p>
          <div class="home-help-secondary-actions">
            <button class="button primary" type="button" data-submit-requirement>Send this requirement to 910CPR</button>
          </div>
          <div class="home-requirement-status" role="status" aria-live="polite" data-requirement-status></div>
          <input type="text" class="home-requirement-honeypot" tabindex="-1" autocomplete="off" aria-hidden="true" data-requirement-company>
        </section>
      </div>
    </section>
  `;

  const chooserToggle = sectionsRoot.querySelector("[data-course-chooser-toggle]");
  const chooser = sectionsRoot.querySelector("#guided-course-chooser");
  const requirementText = sectionsRoot.querySelector("[data-course-requirement-text]");
  const requirementName = sectionsRoot.querySelector("[data-requirement-name]");
  const requirementEmail = sectionsRoot.querySelector("[data-requirement-email]");
  const requirementPhone = sectionsRoot.querySelector("[data-requirement-phone]");
  const requirementCompany = sectionsRoot.querySelector("[data-requirement-company]");
  const requirementSubmit = sectionsRoot.querySelector("[data-submit-requirement]");
  const requirementStatus = sectionsRoot.querySelector("[data-requirement-status]");
  const requirementSessionKey = "910cprRequirementContext";
  const requirementEndpoint =
    "https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/requirement-inquiry";
  const requirementOpenedAt = Date.now();

  function readSessionJson(key) {
    try {
      return JSON.parse(sessionStorage.getItem(key) || "null");
    } catch (_error) {
      return null;
    }
  }

  function existingCustomerContext() {
    const candidates = [
      readSessionJson("910cprCustomer"),
      readSessionJson("910cprInquiry"),
      readSessionJson("910cprRegistration"),
      readSessionJson("registrationDraft"),
      readSessionJson("inquiryDraft"),
    ].filter(Boolean);
    return candidates.reduce((result, value) => ({ ...result, ...value }), {});
  }

  function selectedCourseContext() {
    return (
      readSessionJson("910cprSelectedCourse") || {
        title: document.querySelector("h1")?.textContent?.trim() || "",
        href: location.pathname + location.hash,
      }
    );
  }

  function saveRequirementSession(overrides) {
    const current = readSessionJson(requirementSessionKey) || {};
    const value = {
      ...current,
      requirement: requirementText?.value || "",
      name: requirementName?.value || "",
      email: requirementEmail?.value || "",
      phone: requirementPhone?.value || "",
      selectedCourse: selectedCourseContext(),
      updatedAt: new Date().toISOString(),
      ...overrides,
    };
    sessionStorage.setItem(requirementSessionKey, JSON.stringify(value));
    return value;
  }

  function restoreRequirementSession() {
    const saved = readSessionJson(requirementSessionKey);
    const customer = existingCustomerContext();
    if (requirementText) requirementText.value = saved?.requirement || "";
    if (requirementName) requirementName.value = saved?.name || customer.name || customer.customerName || "";
    if (requirementEmail) requirementEmail.value = saved?.email || customer.email || customer.customerEmail || "";
    if (requirementPhone) requirementPhone.value = saved?.phone || customer.phone || customer.customerPhone || "";
  }

  async function submitRequirement() {
    if (!requirementSubmit || !requirementStatus) return;
    const requirement = requirementText?.value || "";
    const email = requirementEmail?.value.trim() || "";
    const phone = requirementPhone?.value.trim() || "";
    if (requirement.trim().length < 10) {
      requirementStatus.textContent = "Please enter the exact requirement before sending.";
      requirementText?.focus();
      return;
    }
    if (!email && !phone) {
      requirementStatus.textContent = "Please enter an email or phone so 910CPR can follow up.";
      (requirementEmail || requirementPhone)?.focus();
      return;
    }
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      requirementStatus.textContent = "Please enter a valid email address.";
      requirementEmail?.focus();
      return;
    }
    if (!email && phone.replace(/\D/g, "").length < 7) {
      requirementStatus.textContent = "Please enter a valid phone number.";
      requirementPhone?.focus();
      return;
    }

    const saved = saveRequirementSession();
    const customer = existingCustomerContext();
    const clientInquiryId =
      saved.clientInquiryId ||
      (crypto.randomUUID ? crypto.randomUUID() : `inq-${Date.now()}-${Math.random().toString(36).slice(2)}`);
    saveRequirementSession({ clientInquiryId });
    requirementSubmit.disabled = true;
    requirementSubmit.textContent = "Sending…";
    requirementStatus.textContent = "";

    try {
      const response = await fetch(requirementEndpoint, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          name: requirementName?.value.trim() || customer.name || customer.customerName || "",
          email,
          phone,
          requirement,
          selectedCourse: selectedCourseContext(),
          pageTitle: document.title,
          pageUrl: location.href,
          clientInquiryId,
          inquiryId: customer.inquiryId || customer.inquiry_id || null,
          registrationId: customer.registrationId || customer.registration_id || null,
          companyWebsite: requirementCompany?.value || "",
          formElapsedMs: Date.now() - requirementOpenedAt,
        }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok || !result.sent || !result.inquiryId) {
        throw new Error(result.error || "The message could not be delivered.");
      }
      saveRequirementSession({
        serverInquiryId: result.inquiryId,
        sentAt: result.sentAt || new Date().toISOString(),
      });
      requirementStatus.textContent =
        "Sent to 910CPR. We’ll review the wording and help you determine the correct course.";
    } catch (error) {
      requirementStatus.textContent =
        "We couldn’t send this yet. Your wording is still here—please check your connection and try again.";
    } finally {
      requirementSubmit.disabled = false;
      requirementSubmit.textContent = "Send this requirement to 910CPR";
    }
  }

  chooserToggle?.addEventListener("click", () => {
    if (!chooser || !chooserToggle) return;
    const expanded = chooserToggle.getAttribute("aria-expanded") === "true";
    chooser.hidden = expanded;
    chooserToggle.setAttribute("aria-expanded", String(!expanded));
    if (!expanded) {
      const firstLink = chooser.querySelector("a, button, textarea");
      (firstLink || chooser).focus();
    }
  });

  restoreRequirementSession();
  [requirementText, requirementName, requirementEmail, requirementPhone].forEach((field) =>
    field?.addEventListener("input", () => saveRequirementSession())
  );
  requirementSubmit?.addEventListener("click", submitRequirement);
  window.get910CPRRequirementContext = () => readSessionJson(requirementSessionKey);

  sectionsRoot.querySelectorAll(".home-choice-links a, .home-course-tile").forEach((link) => {
    link.addEventListener("click", () => {
      sessionStorage.setItem(
        "910cprSelectedCourse",
        JSON.stringify({
          title: link.textContent.trim(),
          href: link.getAttribute("href") || "",
        })
      );
      saveRequirementSession();
    });
  });

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function escapeAttribute(value) {
    return escapeHtml(value);
  }
})();
